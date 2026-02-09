"""
热门推荐 API - 个性化推荐（评分 + 热度 + 书架偏好）
"""
import asyncio
import math
import random
import time
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Tuple, Optional, Set
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Book, UserPreference, Bookshelf, User
from app.api.books import BookResponse
from app.api.auth import get_current_user_optional
from app.services.llm import LLMService

router = APIRouter()
llm_service = LLMService()

# 延迟初始化，避免导入时 Chroma 未就绪
_vector_db = None


def _get_vector_db():
    global _vector_db
    if _vector_db is None:
        from app.services.vector_db import VectorDBService
        _vector_db = VectorDBService()
    return _vector_db


# 推荐语短期缓存
_reason_cache: Dict[int, Tuple[str, float]] = {}
_REASON_CACHE_TTL = 300.0


def _get_cached_reason(book_id: int) -> Optional[str]:
    if book_id not in _reason_cache:
        return None
    reason, ts = _reason_cache[book_id]
    if time.time() - ts > _REASON_CACHE_TTL:
        del _reason_cache[book_id]
        return None
    return reason


def _set_cached_reason(book_id: int, reason: str) -> None:
    _reason_cache[book_id] = (reason, time.time())


async def _generate_reason_with_ai(
    title: str,
    author: str = "",
    description: str = "",
    rating: float = None,
) -> str:
    """使用 AI 根据书籍内容生成推荐语"""
    try:
        book_info = f"书名：《{title}》"
        if author:
            book_info += f"\n作者：{author}"
        if description:
            book_info += f"\n简介：{description[:300]}"
        if rating:
            book_info += f"\n评分：{rating:.1f}分"
        prompt = f"""请为以下书籍生成一段50-100字的推荐语，要求：
1. 风格温暖、有感染力，能够引起读者的共鸣
2. 突出书籍的核心价值和独特之处
3. 语言优美、有诗意，但不过于华丽
4. 能够激发读者的阅读兴趣
5. 不要使用"这本书"、"这部作品"等词汇，直接描述内容

书籍信息：
{book_info}

请直接输出推荐语，不要添加任何解释或前缀："""
        messages = [
            {"role": "system", "content": "你是一个专业的阅读推荐助手，擅长用温暖、有感染力的语言推荐书籍。"},
            {"role": "user", "content": prompt}
        ]
        reason, _ = await llm_service.chat_completion(
            messages=messages, temperature=0.8, max_tokens=200, timeout=8.0
        )
        reason = reason.strip()
        if reason.startswith('"') and reason.endswith('"'):
            reason = reason[1:-1]
        if reason.startswith("'") and reason.endswith("'"):
            reason = reason[1:-1]
        if reason and len(reason) > 10:
            return reason
        if rating:
            return f"《{title}》是一本值得一读的书籍。豆瓣{rating:.1f}分，不妨一试。"
        elif author:
            return f"《{title}》是{author}的代表作，值得细细品味。"
        return f"《{title}》是一本值得一读的书籍，不妨一试。"
    except Exception as e:
        print(f"⚠️ AI生成推荐语失败: {e}")
        if rating:
            return f"《{title}》是一本值得一读的书籍。豆瓣{rating:.1f}分，不妨一试。"
        elif author:
            return f"《{title}》是{author}的代表作，值得细细品味。"
        return f"《{title}》是一本值得一读的书籍，不妨一试。"


def _get_shelf_count_map(db: Session) -> Dict[int, int]:
    """获取每本书被加入书架的次数（热度）"""
    try:
        rows = db.query(Bookshelf.book_id, func.count(Bookshelf.id).label("cnt")).group_by(Bookshelf.book_id).all()
        return {int(bid): int(cnt) for bid, cnt in rows}
    except Exception:
        return {}


def _get_user_shelf_profile(db: Session, user_id: int) -> Tuple[List[int], Set[str], Set[str], Set[str]]:
    """
    获取用户书架画像：想读+已读 book_ids、偏好作者、偏好类别、弃读作者
    返回: (shelf_book_ids, preferred_authors, preferred_categories, dropped_authors)
    """
    shelf_ids = []
    preferred_authors = set()
    preferred_categories = set()
    dropped_authors = set()
    try:
        # 想读 + 已读
        positive = db.query(Bookshelf).filter(
            Bookshelf.user_id == user_id,
            Bookshelf.status.in_(["to_read", "read"])
        ).all()
        for bs in positive:
            shelf_ids.append(bs.book_id)
            if bs.book:
                if bs.book.author:
                    preferred_authors.add(bs.book.author.strip())
                if bs.book.category:
                    preferred_categories.add(bs.book.category.strip())
        # 弃读：记录作者以便惩罚
        dropped = db.query(Bookshelf).filter(
            Bookshelf.user_id == user_id,
            Bookshelf.status == "dropped"
        ).all()
        for bs in dropped:
            if bs.book and bs.book.author:
                dropped_authors.add(bs.book.author.strip())
    except Exception as e:
        print(f"⚠️ 获取书架画像失败: {e}")
    return shelf_ids, preferred_authors, preferred_categories, dropped_authors


def _average_embeddings(embeddings: List[List[float]]) -> Optional[List[float]]:
    """对多个向量求平均"""
    if not embeddings:
        return None
    n = len(embeddings)
    dim = len(embeddings[0])
    avg = [0.0] * dim
    for emb in embeddings:
        for i, v in enumerate(emb):
            avg[i] += v
    return [x / n for x in avg]


def _normalize_scores(values: List[float], use_log: bool = False) -> List[float]:
    """Min-max 归一化到 [0, 1]"""
    if not values:
        return []
    if use_log:
        values = [math.log1p(max(0, v)) for v in values]
    lo, hi = min(values), max(values)
    if hi <= lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _apply_diversity(books: List[Book], target: int) -> List[Book]:
    """类别与作者多样性：尽量包含不同类别与作者，支持返回大量书籍用于分页"""
    if len(books) <= target:
        return books
    result = []
    used_cats = set()
    used_authors = set()
    rest = list(books)
    random.shuffle(rest)
    while len(result) < target and rest:
        best_idx = -1
        best_diversity = -1
        for i, b in enumerate(rest[:min(20, len(rest))]):
            cat = (b.category or "").strip()
            author = (b.author or "").strip()
            d = (0 if cat in used_cats else 2) + (0 if author in used_authors else 1)
            if d > best_diversity:
                best_diversity = d
                best_idx = i
        if best_idx >= 0:
            b = rest.pop(best_idx)
            result.append(b)
            if b.category:
                used_cats.add(b.category.strip())
            if b.author:
                used_authors.add(b.author.strip())
        else:
            result.append(rest.pop(0))
    return result[:target]


class BookWithReason(BookResponse):
    reason: str = ""


@router.get("/everyone-watching", response_model=List[BookWithReason])
async def get_everyone_watching(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    refresh: bool = Query(False, description="重新推荐时传 True，增加随机性"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """推荐你看 - 个性化推荐（新用户：评分+热度；有书架：个性化+评分+热度，支持访客登录）"""
    try:
        from app.api.agent import get_current_user_id
        user_id = get_current_user_id(db, current_user)

        not_interested_ids: Set[int] = set()
        try:
            rows = db.query(UserPreference.book_id).filter(
                UserPreference.user_id == user_id,
                UserPreference.preference_type == "not_interested"
            ).all()
            not_interested_ids = {r[0] for r in rows}
        except Exception:
            pass

        shelf_count_map = _get_shelf_count_map(db)
        shelf_ids, preferred_authors, preferred_categories, dropped_authors = _get_user_shelf_profile(db, user_id)
        has_shelf_data = len(shelf_ids) > 0

        pool_size = 500
        personalized_ids: Set[int] = set()
        sim_map: Dict[int, float] = {}

        if has_shelf_data:
            try:
                vdb = _get_vector_db()
                id_to_emb = vdb.get_embeddings_by_ids([str(bid) for bid in shelf_ids])
                embeddings = [id_to_emb[str(bid)] for bid in shelf_ids if str(bid) in id_to_emb]
                avg_emb = _average_embeddings(embeddings) if embeddings else None
                if not avg_emb:
                    from app.services.memory_service import get_user_interest_vector
                    avg_emb = get_user_interest_vector(db, user_id)
                if avg_emb:
                    similar = await vdb.search_similar(avg_emb, top_k=150)
                    if similar:
                        max_dist = max((s.get("distance") or 1) for s in similar) or 1
                        for s in similar:
                            try:
                                bid = int(s.get("book_id", 0))
                                personalized_ids.add(bid)
                                d = float(s.get("distance", 1))
                                sim_map[bid] = 1.0 - (d / max_dist) if max_dist > 0 else 1.0
                            except (ValueError, TypeError):
                                pass
            except Exception as e:
                print(f"⚠️ 向量检索失败: {e}")

        # 候选池：个性化结果 + 按评分排序的书籍
        base_query = db.query(Book)
        if not_interested_ids:
            base_query = base_query.filter(Book.id.notin_(list(not_interested_ids)))
        other_books = base_query.order_by(func.coalesce(Book.rating, 0).desc(), Book.id.desc()).limit(pool_size).all()
        id_to_book = {b.id: b for b in other_books if b.id not in not_interested_ids}
        if personalized_ids:
            extra = db.query(Book).filter(Book.id.in_(list(personalized_ids))).all()
            for b in extra:
                if b.id not in not_interested_ids:
                    id_to_book[b.id] = b
        all_books = list(id_to_book.values())

        if not all_books:
            return []

        # 评分与热度归一化
        ratings = [float(b.rating or 0) / 10.0 for b in all_books]
        pops = [shelf_count_map.get(b.id, 0) for b in all_books]
        norm_ratings = _normalize_scores(ratings)
        norm_pops = _normalize_scores(pops, use_log=True)
        rating_map = {b.id: norm_ratings[i] for i, b in enumerate(all_books)}
        pop_map = {b.id: norm_pops[i] for i, b in enumerate(all_books)}

        scored_books: List[Tuple[Book, float]] = []

        if has_shelf_data:
            for b in all_books:
                bid = b.id
                r = rating_map.get(bid, 0)
                p = pop_map.get(bid, 0)
                sim = sim_map.get(bid, 0)

                author = (b.author or "").strip()
                cat = (b.category or "").strip()
                author_match = 0.3 if author and author in preferred_authors else 0
                cat_match = 0.2 if cat and cat in preferred_categories else 0
                dropped_penalty = 0.4 if author and author in dropped_authors else 0
                personal = sim * 0.5 + author_match + cat_match - dropped_penalty
                personal = max(0, min(1, personal))

                final = 0.5 * personal + 0.3 * r + 0.2 * p
                scored_books.append((b, final))
        else:
            # 新用户：评分 + 热度
            for b in all_books:
                r = rating_map.get(b.id, 0)
                p = pop_map.get(b.id, 0)
                final = 0.6 * r + 0.4 * p
                scored_books.append((b, final))

        scored_books.sort(key=lambda x: -x[1])
        # 扩大候选池以支持分页（各分类下滚动加载更多）
        max_pool = min(300, len(scored_books))
        top_candidates = [b for b, _ in scored_books[:max_pool]]
        if refresh:
            random.shuffle(top_candidates)
        selected = _apply_diversity(top_candidates, max_pool)
        # 分页：支持 skip=0,20,40,... 直至池耗尽
        start = min(skip, len(selected))
        books = selected[start : start + limit]

        if not books:
            return []

        cache_hits = {}
        to_generate = []
        for book in books:
            cached = _get_cached_reason(book.id)
            if cached is not None:
                cache_hits[book.id] = cached
            else:
                to_generate.append(book)

        async def gen_one(b):
            try:
                r = await _generate_reason_with_ai(
                    title=b.title or "",
                    author=b.author or "",
                    description=b.description or "",
                    rating=float(b.rating) if b.rating is not None else None,
                )
                _set_cached_reason(b.id, r)
                return b.id, r
            except Exception as e:
                print(f"⚠️ 书籍 {b.id} 推荐语生成失败: {e}")
                rating_val = float(b.rating) if b.rating is not None else None
                if rating_val:
                    default = f"《{b.title or ''}》是一本值得一读的书籍。豆瓣{rating_val:.1f}分，不妨一试。"
                elif b.author:
                    default = f"《{b.title or ''}》是{b.author}的代表作，值得细细品味。"
                else:
                    default = f"《{b.title or ''}》是一本值得一读的书籍，不妨一试。"
                return b.id, default

        generated = await asyncio.gather(*[gen_one(b) for b in to_generate])
        reason_by_id = dict(cache_hits)
        for bid, r in generated:
            reason_by_id[bid] = r

        result = []
        for book in books:
            try:
                reason = reason_by_id.get(book.id)
                if reason is None:
                    rating_val = float(book.rating) if book.rating is not None else None
                    if rating_val:
                        reason = f"《{book.title or ''}》是一本值得一读的书籍。豆瓣{rating_val:.1f}分，不妨一试。"
                    elif book.author:
                        reason = f"《{book.title or ''}》是{book.author}的代表作，值得细细品味。"
                    else:
                        reason = f"《{book.title or ''}》是一本值得一读的书籍，不妨一试。"
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
                print(f"⚠️ 跳过书籍 {getattr(book, 'id', 0)}: {e}")
                continue
        return result
    except Exception as e:
        print(f"❌ 获取热门书籍失败: {e}")
        import traceback
        traceback.print_exc()
        return []
