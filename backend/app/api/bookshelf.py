"""
书架相关 API（支持访客登录版本）
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Bookshelf, Book, UserPreference, User
from app.api.books import BookResponse
from app.api.auth import get_current_user_optional

router = APIRouter()


def get_current_user_id(db: Session, current_user: Optional[User] = None) -> int:
    """获取当前用户ID，如果没有登录则使用匿名用户"""
    if current_user:
        return current_user.id
    
    # 如果没有登录，使用匿名用户（向后兼容）
    from app.api.agent import ensure_anonymous_user
    anonymous_user = ensure_anonymous_user(db)
    return anonymous_user.id if anonymous_user else 1


class BookshelfItem(BaseModel):
    id: int
    book: BookResponse
    status: str  # to_read, reading, read, dropped
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class AddToBookshelfRequest(BaseModel):
    book_id: int
    status: str = "to_read"  # to_read, reading, read, dropped


class UpdateBookshelfRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class NotInterestedRequest(BaseModel):
    book_id: int
    reason: Optional[str] = None


@router.get("/", response_model=List[BookshelfItem])
async def get_bookshelf(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取用户书架（支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    query = db.query(Bookshelf).filter(Bookshelf.user_id == user_id)
    
    if status:
        query = query.filter(Bookshelf.status == status)
    
    bookshelves = query.all()
    
    result = []
    for bs in bookshelves:
        result.append({
            "id": bs.id,
            "book": bs.book,
            "status": bs.status,
            "notes": bs.notes
        })
    
    return result


def _refresh_reading_profile_task(user_id: int):
    from app.db.database import SessionLocal
    from app.services.memory_service import refresh_reading_profile
    local_db = SessionLocal()
    try:
        refresh_reading_profile(local_db, user_id)
    except Exception as e:
        print(f"⚠️ 刷新阅读画像失败: {e}")
    finally:
        local_db.close()


@router.post("/add", response_model=BookshelfItem)
async def add_to_bookshelf(
    request: AddToBookshelfRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """添加书籍到书架（支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    # 检查书籍是否存在
    book = db.query(Book).filter(Book.id == request.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 检查是否已在书架中
    existing = db.query(Bookshelf).filter(
        Bookshelf.user_id == user_id,
        Bookshelf.book_id == request.book_id
    ).first()
    
    if existing:
        # 更新状态
        existing.status = request.status
        db.commit()
        db.refresh(existing)
        background_tasks.add_task(_refresh_reading_profile_task, user_id)
        return {
            "id": existing.id,
            "book": book,
            "status": existing.status,
            "notes": existing.notes
        }
    
    # 创建新的书架项（user_id已经在上面获取了）
    bookshelf = Bookshelf(
        user_id=user_id,
        book_id=request.book_id,
        status=request.status
    )
    db.add(bookshelf)
    db.commit()
    db.refresh(bookshelf)

    background_tasks.add_task(_refresh_reading_profile_task, user_id)
    
    return {
        "id": bookshelf.id,
        "book": book,
        "status": bookshelf.status,
        "notes": bookshelf.notes
    }


@router.put("/{bookshelf_id}", response_model=BookshelfItem)
async def update_bookshelf(
    bookshelf_id: int,
    request: UpdateBookshelfRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """更新书架项（支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    bookshelf = db.query(Bookshelf).filter(
        Bookshelf.id == bookshelf_id,
        Bookshelf.user_id == user_id
    ).first()
    
    if not bookshelf:
        raise HTTPException(status_code=404, detail="书架项不存在")
    
    if request.status:
        bookshelf.status = request.status
    if request.notes is not None:
        bookshelf.notes = request.notes
    
    db.commit()
    db.refresh(bookshelf)

    background_tasks.add_task(_refresh_reading_profile_task, user_id)
    
    return {
        "id": bookshelf.id,
        "book": bookshelf.book,
        "status": bookshelf.status,
        "notes": bookshelf.notes
    }


@router.delete("/{bookshelf_id}")
async def remove_from_bookshelf(
    bookshelf_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """从书架移除书籍（支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    bookshelf = db.query(Bookshelf).filter(
        Bookshelf.id == bookshelf_id,
        Bookshelf.user_id == user_id
    ).first()
    
    if not bookshelf:
        raise HTTPException(status_code=404, detail="书架项不存在")
    
    db.delete(bookshelf)
    db.commit()

    background_tasks.add_task(_refresh_reading_profile_task, user_id)
    
    return {"message": "已从书架移除"}


@router.post("/not-interested")
async def mark_not_interested(
    request: NotInterestedRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """标记不感兴趣（用于推荐反馈，支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    preference = UserPreference(
        user_id=user_id,
        book_id=request.book_id,
        preference_type="not_interested",
        feedback_data={"reason": request.reason} if request.reason else {}
    )
    db.add(preference)
    db.commit()
    
    return {"message": "已记录您的偏好"}
