"""
书架相关 API（无需登录版本）
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Bookshelf, Book, UserPreference
from app.api.books import BookResponse

router = APIRouter()

# 使用固定的匿名用户ID（所有用户共享）
ANONYMOUS_USER_ID = 1


def ensure_anonymous_user(db: Session):
    """确保匿名用户存在（从agent模块导入）"""
    # 直接从agent模块导入，避免重复代码
    from app.api.agent import ensure_anonymous_user as agent_ensure_anonymous_user
    return agent_ensure_anonymous_user(db)


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
    db: Session = Depends(get_db)
):
    """获取用户书架（无需登录）"""
    anonymous_user = ensure_anonymous_user(db)
    if not anonymous_user:
        return []  # 如果没有用户，返回空列表
    
    user_id = anonymous_user.id
    
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
    db: Session = Depends(get_db)
):
    """添加书籍到书架（无需登录）"""
    anonymous_user = ensure_anonymous_user(db)
    if not anonymous_user:
        raise HTTPException(status_code=500, detail="无法初始化匿名用户")
    
    user_id = anonymous_user.id
    
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
    db: Session = Depends(get_db)
):
    """更新书架项（无需登录）"""
    anonymous_user = ensure_anonymous_user(db)
    if not anonymous_user:
        raise HTTPException(status_code=500, detail="无法初始化匿名用户")
    
    user_id = anonymous_user.id
    
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
    db: Session = Depends(get_db)
):
    """从书架移除书籍（无需登录）"""
    anonymous_user = ensure_anonymous_user(db)
    if not anonymous_user:
        raise HTTPException(status_code=500, detail="无法初始化匿名用户")
    
    user_id = anonymous_user.id
    
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
    db: Session = Depends(get_db)
):
    """标记不感兴趣（用于推荐反馈，无需登录）"""
    anonymous_user = ensure_anonymous_user(db)
    if not anonymous_user:
        raise HTTPException(status_code=500, detail="无法初始化匿名用户")
    
    user_id = anonymous_user.id
    
    preference = UserPreference(
        user_id=user_id,
        book_id=request.book_id,
        preference_type="not_interested",
        feedback_data={"reason": request.reason} if request.reason else {}
    )
    db.add(preference)
    db.commit()
    
    return {"message": "已记录您的偏好"}
