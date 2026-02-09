"""
书籍相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import Book
from pydantic import BaseModel
from app.services.llm import LLMService
import urllib.parse

router = APIRouter()
llm_service = LLMService()


class BookResponse(BaseModel):
    id: int
    isbn: Optional[str]
    title: str
    author: Optional[str]
    publisher: Optional[str]
    description: Optional[str]
    cover_url: Optional[str]
    rating: Optional[float]
    category: Optional[str]
    page_count: Optional[int]
    
    class Config:
        from_attributes = True


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """获取书籍详情"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return book


@router.get("/", response_model=List[BookResponse])
async def list_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取书籍列表"""
    books = db.query(Book).offset(skip).limit(limit).all()
    return books


class GenerateDescriptionRequest(BaseModel):
    book_id: int


class GenerateDescriptionResponse(BaseModel):
    description: str
    used_fallback: bool = False


@router.post("/{book_id}/generate-description", response_model=GenerateDescriptionResponse)
async def generate_description(
    book_id: int,
    db: Session = Depends(get_db)
):
    """AI 生成书籍简介"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 如果已有简介且不为空，直接返回
    if book.description and book.description.strip() and book.description != "暂无简介":
        return GenerateDescriptionResponse(
            description=book.description,
            used_fallback=False
        )
    
    # 使用 DeepSeek LLM 生成简介（120字左右）
    prompt = f"""请为以下书籍生成一段简洁、吸引人的中文简介（约120字），突出书籍的核心内容和价值：

书名：《{book.title}》
作者：{book.author or "未知"}
分类：{book.category or "未分类"}

要求：
1. 简介应简洁明了，控制在120字左右
2. 突出书籍的核心主题、风格或价值
3. 语言流畅，有吸引力
4. 如果书名或作者信息不足，可基于书名合理推测并说明

请直接返回简介内容，不要包含"简介："等前缀，字数控制在120字左右。"""
    
    try:
        reply, used_fallback = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200  # 减少 token 数，确保生成约120字
        )
        
        description = reply.strip()
        if not description or len(description) < 20:
            description = f"《{book.title}》是一本值得一读的书籍。{book.author and f'作者{book.author}。' or ''}{book.category and f'分类：{book.category}。' or ''}"
            used_fallback = True
        
        # 在结尾添加"（由AI生成）"备注
        if not description.endswith("（由AI生成）") and not description.endswith("(由AI生成)"):
            description = f"{description}（由AI生成）"
        
        # 可选：保存到数据库（这里只返回，不自动保存，让前端决定是否保存）
        return GenerateDescriptionResponse(
            description=description,
            used_fallback=used_fallback
        )
    except Exception as e:
        print(f"生成简介失败: {e}")
        fallback_desc = f"《{book.title}》是一本值得一读的书籍。{book.author and f'作者{book.author}。' or ''}（由AI生成）"
        return GenerateDescriptionResponse(
            description=fallback_desc,
            used_fallback=True
        )


class GenerateCoverRequest(BaseModel):
    book_id: int


class GenerateCoverResponse(BaseModel):
    cover_url: str
    used_fallback: bool = False
    message: str = ""


def _generate_placeholder_cover_svg(title: str) -> str:
    """生成统一的占位图 SVG（相同背景，书名动态）"""
    # 统一背景色：#6366f1（紫色），文字：白色
    # 限制书名长度，避免 SVG 过大
    display_title = title[:18] if len(title) > 18 else title
    # 如果书名过长，添加省略号
    if len(title) > 18:
        display_title = display_title + "..."
    
    # 转义书名中的特殊字符，防止 SVG 注入
    display_title = display_title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 创建 SVG，支持中文，使用更好的字体和布局
    svg_content = f'''<svg width="300" height="400" xmlns="http://www.w3.org/2000/svg">
  <rect width="300" height="400" fill="#6366f1"/>
  <text x="150" y="190" font-family="'PingFang SC', 'Microsoft YaHei', 'SimSun', Arial, sans-serif" font-size="22" fill="white" text-anchor="middle" dominant-baseline="middle" font-weight="500">
    {display_title}
  </text>
</svg>'''
    
    # 将 SVG 转换为 data URL
    svg_encoded = urllib.parse.quote(svg_content)
    return f"data:image/svg+xml;charset=utf-8,{svg_encoded}"


@router.post("/{book_id}/generate-cover", response_model=GenerateCoverResponse)
async def generate_cover(
    book_id: int,
    db: Session = Depends(get_db)
):
    """生成书籍封面占位图（统一背景，书名动态）"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 如果已有封面，直接返回
    if book.cover_url and book.cover_url.strip():
        return GenerateCoverResponse(
            cover_url=book.cover_url,
            used_fallback=False
        )
    
    # 生成统一的占位图 SVG（相同背景色 #6366f1，书名动态）
    placeholder_url = _generate_placeholder_cover_svg(book.title)
    
    return GenerateCoverResponse(
        cover_url=placeholder_url,
        used_fallback=True,
        message="使用统一占位图（由AI生成）"
    )
