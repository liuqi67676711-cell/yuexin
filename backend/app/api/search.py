"""
搜索相关 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from app.db.database import get_db
from app.db.models import Book
from app.api.books import BookResponse
from app.api.popular import BookWithReason
from app.api.popular_reason_templates import get_reason_for_user_template, get_reason_by_index
from app.services.book_data import BookDataService
from app.services.llm import LLMService
from app.services.fts_search import FTSSearchService
from app.db.models import Book as BookModel

router = APIRouter()
book_data_service = BookDataService()
llm_service = LLMService()


def _is_chinese(text: str) -> bool:
    """检测文本是否包含中文字符"""
    import re
    return bool(re.search(r'[\u4e00-\u9fff]', text))


async def _translate_to_english(text: str) -> str:
    """将中文文本翻译成英文（用于搜索外文书）"""
    if not _is_chinese(text):
        # 如果输入不是中文，直接返回
        return text
    
    try:
        # 使用LLM服务翻译
        prompt = f"""请将以下中文文本翻译成英文，保持原意和语气。只返回翻译结果，不要添加任何解释。

中文文本：{text}

英文翻译："""
        
        messages = [
            {"role": "system", "content": "你是一个专业的翻译助手，擅长将中文翻译成自然流畅的英文。"},
            {"role": "user", "content": prompt}
        ]
        
        # 设置5秒超时，避免翻译耗时过长
        translated_text, _ = await asyncio.wait_for(
            llm_service.chat_completion(messages, temperature=0.3),
            timeout=5.0
        )
        
        # 清理翻译结果（移除可能的引号等）
        translated_text = translated_text.strip().strip('"').strip("'")
        return translated_text if translated_text else text
        
    except asyncio.TimeoutError:
        print("⚠️  翻译超时，使用原始文本")
        return text
    except Exception as e:
        print(f"⚠️  翻译失败: {e}，使用原始文本")
        return text


def _fallback_like_search(
    db: Session,
    isbn: Optional[str],
    title: Optional[str],
    author: Optional[str]
) -> List[Book]:
    """回退到普通 LIKE 搜索（当 FTS 不可用时）"""
    from sqlalchemy import or_, distinct
    
    query = db.query(Book)
    conditions = []
    
    if isbn:
        conditions.append(Book.isbn.contains(isbn))
    
    if title:
        title_conditions = [Book.title.contains(title)]
        if _is_chinese(title):
            title_conditions.append(Book.description.contains(title))
        else:
            title_conditions.append(Book.description.contains(title))
        if len(title_conditions) > 1:
            conditions.append(or_(*title_conditions))
        else:
            conditions.append(title_conditions[0])
    
    if author:
        all_authors = db.query(distinct(Book.author)).filter(
            Book.author.isnot(None),
            Book.author != ""
        ).all()
        author_list = [a[0] for a in all_authors if a[0]]
        matching_authors = []
        search_lower = author.lower()
        
        for author_name in author_list:
            if not author_name:
                continue
            author_parts = author_name.replace('，', ',').replace('；', ';').split(',')
            author_parts.extend(author_name.replace('，', ',').replace('；', ';').split(';'))
            for part in author_parts:
                part_clean = part.strip()
                if search_lower in part_clean.lower():
                    matching_authors.append(author_name)
                    break
        
        if matching_authors:
            author_conditions = [Book.author == auth for auth in matching_authors]
            if len(author_conditions) > 1:
                conditions.append(or_(*author_conditions))
            else:
                conditions.append(author_conditions[0])
        else:
            conditions.append(Book.author.contains(author))
    
    if len(conditions) > 1:
        query = query.filter(or_(*conditions))
    elif len(conditions) == 1:
        query = query.filter(conditions[0])
    
    return query.limit(100).all()


def _build_search_reason(
    title: str,
    author: str = "",
    description: str = "",
    rating: float = None,
    used_reasons: set = None,
    fallback_index: int = 0,
) -> str:
    """为搜索结果生成推荐理由（使用与热门书籍相同的模板逻辑）"""
    used_reasons = used_reasons or set()
    desc = (description or "").strip()

    def _dedup(reason: str) -> str:
        if reason not in used_reasons:
            return reason
        if rating is not None:
            return f"{reason.rstrip('。')} 豆瓣{rating:.1f}分。"
        if author:
            return f"{reason.rstrip('。')}（{author}代表作）。"
        return f"{reason.rstrip('。')} 不妨一试。"

    # 1. 按简介关键词匹配 50 类，命中则用该类 6 条之一
    user_reason = get_reason_for_user_template(desc, title, fallback_index)
    if user_reason is not None:
        return _dedup(user_reason)

    # 2. 无匹配时，按 fallback_index 从 50×6 中轮取一条（仍只用产品范本）
    reason = get_reason_by_index(fallback_index, title)
    return _dedup(reason)


@router.get("/exact", response_model=List[BookWithReason])
async def exact_search(
    isbn: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """精确搜索（ISBN/书名/作者）- 优先使用 FTS 全文搜索，性能比 LIKE 快 10-100 倍
    
    优化说明：
    1. 使用 SQLite FTS5 全文搜索（如果可用），性能大幅提升
    2. 保留评分排序逻辑，确保最匹配的结果在前
    3. 如果 FTS 不可用，自动回退到普通 LIKE 搜索
    4. 返回的每本书都包含推荐理由（reason字段）。
    """
    try:
        from sqlalchemy import or_, distinct, func as sql_func
        
        # 检查是否有搜索条件
        if not isbn and not title and not author:
            return []
        
        # 优先使用 FTS 全文搜索（性能更好）
        try:
            fts_service = FTSSearchService(db)
            books = fts_service.search(isbn=isbn, title=title, author=author, limit=100)
            
            # 如果 FTS 返回结果，使用 FTS 结果；否则回退到普通搜索
            if not books:
                # FTS 无结果时，尝试普通搜索（可能 FTS 索引未同步）
                books = _fallback_like_search(db, isbn, title, author)
        except Exception as e:
            # FTS 不可用或出错，回退到普通 LIKE 搜索
            print(f"⚠️  FTS 搜索失败，使用普通搜索: {e}")
            books = _fallback_like_search(db, isbn, title, author)
        
        if not books:
            return []
        
        # 对搜索结果进行排序，最匹配的排在前面
        def calculate_match_score(book: Book) -> int:
            """计算匹配分数，分数越高越匹配"""
            score = 0
            
            # ISBN完全匹配：最高优先级（1000分）
            if isbn and book.isbn and book.isbn.strip() == isbn.strip():
                score += 1000
            
            # ISBN包含匹配（500分）
            elif isbn and book.isbn and isbn.strip() in book.isbn:
                score += 500
            
            # 书名完全匹配（800分）
            if title and book.title:
                title_lower = title.lower().strip()
                book_title_lower = book.title.lower().strip()
                if book_title_lower == title_lower:
                    score += 800
                # 书名开头匹配（600分）
                elif book_title_lower.startswith(title_lower):
                    score += 600
                # 书名包含匹配（400分）
                elif title_lower in book_title_lower:
                    score += 400
            
            # 作者完全匹配（700分）
            if author and book.author:
                author_lower = author.lower().strip()
                book_author_lower = book.author.lower().strip()
                if book_author_lower == author_lower:
                    score += 700
                # 作者包含匹配（300分）
                elif author_lower in book_author_lower or book_author_lower in author_lower:
                    score += 300
            
            # 评分加成（评分越高，加分越多，最多100分）
            if book.rating:
                score += int(book.rating * 10)  # 9.5分 = 95分
            
            return score
        
        # 按匹配分数排序，分数高的在前
        sorted_books = sorted(books, key=calculate_match_score, reverse=True)
        
        # 为每本书生成推荐理由
        result = []
        used_reasons = set()
        for i, book in enumerate(sorted_books):
            try:
                reason = _build_search_reason(
                    title=book.title or "",
                    author=book.author or "",
                    description=book.description or "",
                    rating=float(book.rating) if book.rating is not None else None,
                    used_reasons=used_reasons,
                    fallback_index=i,
                )
                used_reasons.add(reason)
                # 确保 rating 为 float（SQLite 可能返回 Decimal）
                rating_val = float(book.rating) if book.rating is not None else None
                book_dict = {
                    "id": book.id,
                    "isbn": book.isbn,
                    "title": book.title or "",
                    "author": book.author,
                    "publisher": book.publisher,
                    "description": book.description,
                    "cover_url": book.cover_url,
                    "rating": rating_val,
                    "category": book.category,
                    "page_count": book.page_count,
                    "reason": reason,
                }
                result.append(BookWithReason(**book_dict))
            except Exception as e:
                print(f"⚠️ 跳过书籍 {getattr(book, 'id', i)} 推荐理由生成: {e}")
                # 即使生成推荐理由失败，也返回书籍（不带推荐理由）
                rating_val = float(book.rating) if book.rating is not None else None
                book_dict = {
                    "id": book.id,
                    "isbn": book.isbn,
                    "title": book.title or "",
                    "author": book.author,
                    "publisher": book.publisher,
                    "description": book.description,
                    "cover_url": book.cover_url,
                    "rating": rating_val,
                    "category": book.category,
                    "page_count": book.page_count,
                    "reason": "",
                }
                result.append(BookWithReason(**book_dict))
        
        return result
    except Exception as e:
        print(f"❌ 搜索API错误: {e}")
        import traceback
        traceback.print_exc()
        # 返回空列表而不是抛出异常
        return []
