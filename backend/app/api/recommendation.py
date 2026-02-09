"""
推荐相关 API
"""
import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Book, User, UserPreference
# 已移除认证相关导入
from app.services.llm import LLMService
from app.services.embedding import EmbeddingService
from app.services.vector_db import VectorDBService
from app.services.book_data import BookDataService

router = APIRouter()
llm_service = LLMService()
embedding_service = EmbeddingService()
# 延迟初始化 vector_db_service，避免模块导入时的初始化错误
_vector_db_service = None

def get_vector_db_service():
    """获取向量数据库服务（延迟初始化）"""
    global _vector_db_service
    if _vector_db_service is None:
        _vector_db_service = VectorDBService()
    return _vector_db_service

book_data_service = BookDataService()


# 类型/关键词同义词：用户说「推理小说」时，匹配简介中含「悬疑」「侦探」或英文 mystery/detective 等的书籍
# 书库来自 Open Library，简介多为英文，故推理类同时保留中英文匹配词
GENRE_SYNONYMS = {
    "推理": ["推理", "悬疑", "侦探", "本格", "社会派", "解谜", "密室", "谋杀", "反转", "mystery", "detective", "crime", "thriller"],
    "推理小说": ["推理", "悬疑", "侦探", "本格", "社会派", "解谜", "mystery", "detective", "crime", "thriller"],
    "悬疑": ["悬疑", "推理", "侦探", "mystery", "detective", "thriller", "suspense"],
    "科幻": ["科幻", "未来", "太空", "人工智能", "奇幻", "science fiction", "sci-fi", "future"],
    "言情": ["言情", "爱情", "治愈", "温暖", "romance", "love"],
}


def _build_search_query(user_input: str, keywords: List[str], book_types: List[str]) -> str:
    """构建用于向量检索的扩展查询，突出类型与关键词，提高与书籍内容的语义对齐"""
    parts = [user_input.strip()]
    for k in keywords:
        if k and isinstance(k, str) and k.strip():
            parts.append(k.strip())
    for t in book_types:
        if t and isinstance(t, str) and t.strip():
            parts.append(t.strip())
    for bt in book_types:
        if bt and bt in GENRE_SYNONYMS:
            for s in GENRE_SYNONYMS[bt]:
                if s not in parts:
                    parts.append(s)
    return " ".join(parts)


def _get_books_by_genre_keywords(
    db: Session,
    keywords: List[str],
    book_types: List[str],
    not_interested_ids: set,
    limit: int = 50,
) -> List[Dict]:
    """当用户明确要某类型（如推理）时，用关键词从数据库拉取该类型候选，保证库里有就能被推荐到"""
    from sqlalchemy import or_
    match_terms = []
    for k in keywords:
        if k and isinstance(k, str) and k.strip():
            match_terms.append(k.strip())
    for t in book_types:
        if t and isinstance(t, str) and t.strip():
            match_terms.append(t.strip())
    for bt in (book_types or []):
        if bt and bt in GENRE_SYNONYMS:
            match_terms.extend(GENRE_SYNONYMS[bt])
    match_terms = list(dict.fromkeys(match_terms))
    if not match_terms:
        return []
    conditions = []
    for t in match_terms:
        conditions.append(Book.title.ilike(f"%{t}%"))
        conditions.append(Book.description.ilike(f"%{t}%"))
    combined = or_(*conditions)
    books = db.query(Book).filter(combined).limit(limit * 2).all()  # 多取一些再去重
    seen = set()
    result = []
    for b in books:
        if b.id in not_interested_ids or b.id in seen:
            continue
        seen.add(b.id)
        result.append({"book_id": str(b.id), "distance": 0.0})  # 类型命中给最高优先级
        if len(result) >= limit:
            break
    return result


def _rerank_by_keyword_match(
    similar_books: List[Dict],
    db: Session,
    keywords: List[str],
    book_types: List[str],
) -> List[Dict]:
    """按书名、简介中的关键词/类型匹配度对向量检索结果重排序，类型与关键词匹配的优先"""
    if not similar_books:
        return similar_books
    match_terms = []
    for k in keywords:
        if k and isinstance(k, str) and k.strip():
            match_terms.append(k.strip())
    for t in book_types:
        if t and isinstance(t, str) and t.strip():
            match_terms.append(t.strip())
    for bt in (book_types or []):
        if bt and bt in GENRE_SYNONYMS:
            match_terms.extend(GENRE_SYNONYMS[bt])
    match_terms = list(dict.fromkeys(match_terms))  # 去重保序
    if not match_terms:
        return similar_books

    book_ids = []
    for b in similar_books:
        try:
            bid = int(b.get("book_id", 0))
            if bid > 0:
                book_ids.append(bid)
        except (ValueError, TypeError):
            continue
    if not book_ids:
        return similar_books

    books = db.query(Book).filter(Book.id.in_(book_ids)).all()
    id_to_text = {}
    for b in books:
        title = (b.title or "")
        desc = (b.description or "") or ""
        id_to_text[b.id] = (title + " " + desc).lower()  # 小写便于匹配英文 Mystery/detective

    def score(book_id: int) -> int:
        text = id_to_text.get(book_id, "")
        return sum(1 for t in match_terms if t and t.lower() in text)

    return sorted(
        similar_books,
        key=lambda b: (-score(int(b.get("book_id", 0))), float(b.get("distance", 1.0))),
    )


def _extract_random_sentence(text: str) -> str:
    """从推荐语中随机提取一句话用于高亮"""
    import re
    # 按句号、问号、感叹号分割句子
    sentences = re.split(r'[。！？]', text)
    # 过滤空字符串和过短的句子
    valid_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
    if valid_sentences:
        return random.choice(valid_sentences)
    return ""


def _select_diverse_books(similar_books: List[Dict], db: Session, target_count: int = 20) -> List[Dict]:
    """从相似书籍中选择多样化的书籍集合
    
    多样性策略：
    1. 按相似度分层：前20%最相似 + 中间30% + 后50%随机
    2. 确保作者多样性：优先选择不同作者
    3. 确保类别多样性：优先选择不同类别
    4. 混合不同评分区间
    """
    if not similar_books:
        return []
    
    if len(similar_books) <= target_count:
        return similar_books
    
    # 获取书籍详细信息（需要作者和类别信息）
    books_info = {}
    try:
        book_ids = []
        for b in similar_books:
            try:
                book_id = int(b.get("book_id", 0))
                if book_id > 0:
                    book_ids.append(book_id)
            except (ValueError, TypeError):
                continue
        
        # 批量查询书籍信息，提高效率
        if book_ids:
            books = db.query(Book).filter(Book.id.in_(book_ids)).all()
            for book in books:
                books_info[book.id] = {
                    "author": book.author or "未知",
                    "category": book.category or "未分类",
                    "rating": book.rating or 0.0,
                    "distance": next((b.get("distance", 1.0) for b in similar_books if int(b.get("book_id", 0)) == book.id), 1.0)
                }
    except Exception as e:
        print(f"⚠️  获取书籍信息失败: {e}")
        import traceback
        traceback.print_exc()
        # 如果获取信息失败，直接返回前target_count本
        return similar_books[:target_count]
    
    # 按相似度分层
    total = len(similar_books)
    top_count = max(3, int(total * 0.2))  # 前20%最相似
    middle_count = max(5, int(total * 0.3))  # 中间30%
    
    top_books = similar_books[:top_count]
    middle_books = similar_books[top_count:top_count + middle_count]
    remaining_books = similar_books[top_count + middle_count:]
    
    selected = []
    seen_authors = set()
    seen_categories = set()
    
    # 第一轮：从最相似的书籍中选择，优先选择不同作者和类别
    for book in top_books:
        try:
            book_id = int(book.get("book_id", 0))
            if book_id > 0 and book_id in books_info:
                info = books_info[book_id]
                author = info["author"]
                category = info["category"]
                
                # 如果作者或类别还没出现过，优先选择
                if author not in seen_authors or category not in seen_categories:
                    selected.append(book)
                    seen_authors.add(author)
                    seen_categories.add(category)
                    if len(selected) >= target_count:
                        break
            elif book_id > 0:
                # 如果没有书籍信息，也添加（避免遗漏）
                selected.append(book)
                if len(selected) >= target_count:
                    break
        except (ValueError, TypeError, KeyError):
            continue
    
    # 第二轮：从中间层选择，继续增加多样性
    if len(selected) < target_count:
        for book in middle_books:
            try:
                book_id = int(book.get("book_id", 0))
                if book_id > 0 and book_id in books_info:
                    info = books_info[book_id]
                    author = info["author"]
                    category = info["category"]
                    
                    # 优先选择新作者或新类别
                    if author not in seen_authors or category not in seen_categories:
                        selected.append(book)
                        seen_authors.add(author)
                        seen_categories.add(category)
                        if len(selected) >= target_count:
                            break
                elif book_id > 0:
                    # 如果没有书籍信息，也添加
                    selected.append(book)
                    if len(selected) >= target_count:
                        break
            except (ValueError, TypeError, KeyError):
                continue
    
    # 第三轮：如果还不够，从剩余书籍中随机选择
    if len(selected) < target_count:
        needed = target_count - len(selected)
        # 优先选择不同作者/类别的
        for book in remaining_books:
            try:
                book_id = int(book.get("book_id", 0))
                if book_id > 0 and book_id in books_info:
                    info = books_info[book_id]
                    author = info["author"]
                    category = info["category"]
                    
                    if author not in seen_authors or category not in seen_categories:
                        selected.append(book)
                        seen_authors.add(author)
                        seen_categories.add(category)
                        if len(selected) >= target_count:
                            break
                elif book_id > 0:
                    # 如果没有书籍信息，也添加
                    selected.append(book)
                    if len(selected) >= target_count:
                        break
            except (ValueError, TypeError, KeyError):
                continue
        
        # 如果还不够，随机补充
        if len(selected) < target_count:
            remaining_needed = target_count - len(selected)
            available = [b for b in remaining_books if b not in selected]
            if available:
                random_selected = random.sample(available, min(remaining_needed, len(available)))
                selected.extend(random_selected)
    
    # 如果还是不够，从所有书籍中随机补充
    if len(selected) < target_count:
        all_available = [b for b in similar_books if b not in selected]
        if all_available:
            remaining_needed = target_count - len(selected)
            random_selected = random.sample(all_available, min(remaining_needed, len(all_available)))
            selected.extend(random_selected)
    
    # 最后随机打乱顺序，避免总是按相似度排序
    random.shuffle(selected)
    
    return selected[:target_count]


class RecommendationRequest(BaseModel):
    query: str  # 用户输入的自然语言查询


class RecommendationItem(BaseModel):
    book_id: int
    title: str
    author: str
    cover_url: str
    rating: float
    recommendation_text: str  # AI生成的推荐语
    highlighted_words: List[str]  # 需要高亮的词汇


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    message: str  # 如果未匹配到书籍，返回提示信息
    show_agent_suggestion: bool = False  # 是否显示AI书童引导
    agent_name: str = "苏童童"  # AI书童名称


@router.post("/semantic", response_model=RecommendationResponse)
async def semantic_recommendation(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """语义推荐引擎"""
    import asyncio
    
    try:
        user_input = request.query
        
        if not user_input or not user_input.strip():
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        print(f"📚 收到语义推荐请求: {user_input[:50]}...")
        
        # 获取当前用户标记为「不感兴趣」的书籍 ID，后续推荐中排除
        not_interested_ids = set()
        try:
            rows = db.query(UserPreference.book_id).filter(
                UserPreference.user_id == 1,
                UserPreference.preference_type == "not_interested"
            ).all()
            not_interested_ids = {r[0] for r in rows}
        except Exception:
            pass
        
        recommendations = []
        
        # Step 1: 意图识别 - 提取关键词、情绪因子、书籍类型（带超时）
        keywords = []
        book_types = []
        try:
            intent_data = await asyncio.wait_for(
                llm_service.extract_keywords(user_input),
                timeout=5.0  # 5秒超时
            )
            keywords = intent_data.get("keywords", []) or []
            book_types = intent_data.get("book_types", []) or []
        except asyncio.TimeoutError:
            print("⚠️  关键词提取超时，使用简单关键词提取")
            keywords = user_input.split()[:5]  # 简单分词
        except Exception as e:
            print(f"⚠️  关键词提取失败: {e}")
            keywords = user_input.split()[:5]
        
        # Step 2: 向量检索（带超时）
        similar_books = []
        try:
            # 用「用户输入 + 关键词 + 书籍类型」构建扩展查询，使向量更贴近「类型/主题」而非仅口语描述
            search_query = _build_search_query(user_input, keywords, book_types)
            query_embedding = await asyncio.wait_for(
                embedding_service.get_embedding(search_query),
                timeout=90.0
            )
            
            raw_similar = await asyncio.wait_for(
                get_vector_db_service().search_similar(
                    query_embedding=query_embedding,
                    top_k=100
                ),
                timeout=5.0
            )
            similar_books = [b for b in raw_similar if int(b.get("book_id", 0)) not in not_interested_ids]
            # 类型兜底：用户明确要某类（如推理）时，用关键词从 DB 再拉一批候选，避免向量未命中时完全推荐不到
            if keywords or book_types:
                genre_books = _get_books_by_genre_keywords(db, keywords, book_types, not_interested_ids, limit=30)
                if genre_books:
                    genre_ids = {int(b["book_id"]) for b in genre_books}
                    vector_only = [b for b in similar_books if int(b.get("book_id", 0)) not in genre_ids]
                    similar_books = genre_books + vector_only
            # 按书名、简介中的关键词/类型匹配重排序，确保「推理小说」等请求优先得到推理类书籍
            similar_books = _rerank_by_keyword_match(similar_books, db, keywords, book_types)
        except asyncio.TimeoutError:
            print("⚠️  向量检索超时，使用热门书籍作为备选")
            similar_books = []
        except Exception as e:
            print(f"⚠️  向量检索失败: {e}")
            import traceback
            traceback.print_exc()
            # 如果向量检索失败，继续使用热门书籍作为备选
            similar_books = []
        
        if not similar_books:
            # 如果未匹配到，返回热门书籍作为备选（5～8 本，增加推荐数量）
            # 大幅增加候选池，并确保多样性
            k_fallback = random.randint(5, 8)
            # 获取更多热门书籍（100本），然后使用多样性算法选择
            all_popular_books = db.query(Book).filter(
                Book.rating.isnot(None),
                Book.rating > 0
            ).order_by(Book.rating.desc()).limit(100).all()
            all_popular_books = [b for b in all_popular_books if b.id not in not_interested_ids]
            
            # 转换为similar_books格式以便使用多样性算法
            popular_books_dict = [
                {"book_id": str(b.id), "distance": 1.0 - (b.rating or 0) / 10.0}
                for b in all_popular_books
            ]
            
            # 使用多样性算法选择
            diverse_popular = _select_diverse_books(popular_books_dict, db, target_count=k_fallback * 2)
            popular_book_ids = [int(b["book_id"]) for b in diverse_popular[:k_fallback]]
            popular_books = [b for b in all_popular_books if b.id in popular_book_ids]
            
            if len(popular_books) < k_fallback:
                # 如果多样性选择不够，随机补充
                remaining_ids = set(popular_book_ids)
                additional = [b for b in all_popular_books if b.id not in remaining_ids]
                if additional:
                    needed = k_fallback - len(popular_books)
                    popular_books.extend(random.sample(additional, min(needed, len(additional))))
            if not popular_books:
                # 获取匿名用户的AI书童名称
                agent_name = "苏童童"
                try:
                    anonymous_user = db.query(User).filter(User.id == 1).first()
                    if anonymous_user and anonymous_user.agent_name:
                        agent_name = anonymous_user.agent_name
                except Exception:
                    pass  # 如果获取失败，使用默认名称
                
                return RecommendationResponse(
                    recommendations=[],
                    message=f"好像还没读懂你的心哦，不妨试试和{agent_name}仔细聊聊。",
                    show_agent_suggestion=True,
                    agent_name=agent_name
                )
            
            # 并行为热门书籍生成推荐语（提升速度）
            async def generate_for_popular_book(book):
                try:
                    try:
                        recommendation_text = await asyncio.wait_for(
                            llm_service.generate_recommendation_text(
                                user_input=user_input,
                                book_title=book.title,
                                book_author=book.author or "未知作者",
                                book_description=book.description or "暂无简介"
                            ),
                            timeout=8.0  # 增加到8秒，给LLM更多响应时间
                        )
                    except asyncio.TimeoutError:
                        print(f"⚠️  为热门书籍 {book.id} 生成推荐语超时，使用默认推荐语")
                        recommendation_text = f"《{book.title}》或许符合你的需求：{user_input[:30]}"
                    except Exception as e:
                        print(f"⚠️  为热门书籍 {book.id} 生成推荐语失败: {e}")
                        recommendation_text = f"《{book.title}》或许符合你的需求：{user_input[:30]}"
                    
                    # 随机高亮推荐语中的一句话
                    highlighted_sentence = _extract_random_sentence(recommendation_text)
                    
                    return RecommendationItem(
                        book_id=book.id,
                        title=book.title,
                        author=book.author or "未知作者",
                        cover_url=book.cover_url or "",
                        rating=book.rating or 0.0,
                        recommendation_text=recommendation_text,
                        highlighted_words=[highlighted_sentence] if highlighted_sentence else []
                    )
                except Exception as e:
                    print(f"⚠️  为书籍 {book.id} 生成推荐语失败: {e}")
                    return RecommendationItem(
                        book_id=book.id,
                        title=book.title,
                        author=book.author or "未知作者",
                        cover_url=book.cover_url or "",
                        rating=book.rating or 0.0,
                        recommendation_text=f"这本书可能符合你的需求：{book.title}",
                        highlighted_words=[]
                    )
            
            tasks = [generate_for_popular_book(book) for book in popular_books]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if result and isinstance(result, RecommendationItem):
                    recommendations.append(result)
            
            return RecommendationResponse(
                recommendations=recommendations[:k_fallback],
                message="虽然没找到完全匹配的，但这些热门书籍也许适合你：",
                show_agent_suggestion=False,
                agent_name="苏童童"
            )
        
        # Step 3: 并行为每个匹配的书籍生成推荐语（提升速度）
        async def generate_recommendation_for_book(similar_book):
            """为单本书生成推荐语"""
            try:
                book_id = int(similar_book["book_id"])
                book = db.query(Book).filter(Book.id == book_id).first()
                
                if not book:
                    return None
                
                # 生成推荐语（带超时，增加到8秒，给LLM更多时间）
                try:
                    recommendation_text = await asyncio.wait_for(
                        llm_service.generate_recommendation_text(
                            user_input=user_input,
                            book_title=book.title,
                            book_author=book.author or "未知作者",
                            book_description=book.description or "暂无简介"
                        ),
                        timeout=8.0  # 增加到8秒，给LLM更多响应时间
                    )
                except asyncio.TimeoutError:
                    print(f"⚠️  为书籍 {book_id} 生成推荐语超时，使用默认推荐语")
                    recommendation_text = f"《{book.title}》或许符合你的需求：{user_input[:30]}"
                except Exception as e:
                    print(f"⚠️  为书籍 {book_id} 生成推荐语失败: {e}")
                    recommendation_text = f"《{book.title}》或许符合你的需求：{user_input[:30]}"
                
                # 随机高亮推荐语中的一句话
                highlighted_sentence = _extract_random_sentence(recommendation_text)
                
                return RecommendationItem(
                    book_id=book.id,
                    title=book.title,
                    author=book.author or "未知作者",
                    cover_url=book.cover_url or "",
                    rating=book.rating or 0.0,
                    recommendation_text=recommendation_text,
                    highlighted_words=[highlighted_sentence] if highlighted_sentence else []
                )
            except Exception as e:
                print(f"⚠️  处理相似书籍 {similar_book.get('book_id')} 失败: {e}")
                return None
        
        # 使用多样性算法选择书籍（确保作者、类别、评分等维度的多样性）
        # 增加候选数量，提高推荐丰富度；selected_books 已排除不感兴趣
        selected_books = _select_diverse_books(similar_books, db, target_count=40)
        selected_books = [b for b in selected_books if int(b.get("book_id", 0)) not in not_interested_ids]
        
        # 并行处理选中的书籍（最多同时处理40个，增加推荐数量）
        tasks = [generate_recommendation_for_book(book) for book in selected_books[:40]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if result and isinstance(result, RecommendationItem):
                recommendations.append(result)
        
        # 对推荐结果进行去重（按book_id）
        seen_ids = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec.book_id not in seen_ids:
                seen_ids.add(rec.book_id)
                unique_recommendations.append(rec)
        recommendations = unique_recommendations
        
        # 随机打乱顺序，增加多样性
        random.shuffle(recommendations)
        
        # 返回5-8本推荐（增加推荐数量）
        final_count = random.randint(5, 8)
        recommendations = recommendations[:final_count]
        
        if not recommendations:
            # 如果最终没有推荐，返回热门书籍（3～5 本）
            k_final = random.randint(3, 5)
            # 大幅增加候选池，并使用多样性算法
            all_popular_books = db.query(Book).filter(
                Book.rating.isnot(None),
                Book.rating > 0
            ).order_by(Book.rating.desc()).limit(50).all()
            all_popular_books = [b for b in all_popular_books if b.id not in not_interested_ids]
            
            # 转换为similar_books格式以便使用多样性算法
            popular_books_dict = [
                {"book_id": str(b.id), "distance": 1.0 - (b.rating or 0) / 10.0}
                for b in all_popular_books
            ]
            
            # 使用多样性算法选择
            diverse_popular = _select_diverse_books(popular_books_dict, db, target_count=k_final * 2)
            popular_book_ids = [int(b["book_id"]) for b in diverse_popular[:k_final]]
            popular_books = [b for b in all_popular_books if b.id in popular_book_ids]
            
            if len(popular_books) < k_final:
                # 如果多样性选择不够，随机补充
                remaining_ids = set(popular_book_ids)
                additional = [b for b in all_popular_books if b.id not in remaining_ids]
                if additional:
                    needed = k_final - len(popular_books)
                    popular_books.extend(random.sample(additional, min(needed, len(additional))))
            if popular_books:
                async def generate_for_fallback_book(book):
                    try:
                        recommendation_text = await asyncio.wait_for(
                            llm_service.generate_recommendation_text(
                                user_input=user_input,
                                book_title=book.title,
                                book_author=book.author or "未知作者",
                                book_description=book.description or "暂无简介"
                            ),
                            timeout=8.0  # 增加到8秒，给LLM更多响应时间
                        )
                        highlighted_sentence = _extract_random_sentence(recommendation_text)
                        return RecommendationItem(
                            book_id=book.id,
                            title=book.title,
                            author=book.author or "未知作者",
                            cover_url=book.cover_url or "",
                            rating=book.rating or 0.0,
                            recommendation_text=recommendation_text,
                            highlighted_words=[highlighted_sentence] if highlighted_sentence else []
                        )
                    except Exception as e:
                        print(f"⚠️  为热门书籍 {book.id} 生成推荐语失败: {e}")
                        return RecommendationItem(
                            book_id=book.id,
                            title=book.title,
                            author=book.author or "未知作者",
                            cover_url=book.cover_url or "",
                            rating=book.rating or 0.0,
                            recommendation_text=f"这本书可能符合你的需求：{book.title}",
                            highlighted_words=[]
                        )
                
                tasks_fallback = [generate_for_fallback_book(book) for book in popular_books]
                results_fallback = await asyncio.gather(*tasks_fallback, return_exceptions=True)
                for result in results_fallback:
                    if result and isinstance(result, RecommendationItem):
                        recommendations.append(result)
        
        # 情绪搜索推荐 3～5 本，使用多样性算法最终选择
        k = random.randint(3, 5)
        if len(recommendations) > k:
            # 转换为similar_books格式以便使用多样性算法
            recs_dict = [
                {"book_id": str(r.book_id), "distance": 0.5}  # 距离不重要，主要看多样性
                for r in recommendations
            ]
            # 使用多样性算法选择最终推荐
            diverse_final = _select_diverse_books(recs_dict, db, target_count=k)
            final_book_ids = {int(b["book_id"]) for b in diverse_final}
            final_recommendations = [r for r in recommendations if r.book_id in final_book_ids]
            
            # 如果多样性选择不够，随机补充
            if len(final_recommendations) < k:
                remaining = [r for r in recommendations if r.book_id not in final_book_ids]
                if remaining:
                    needed = k - len(final_recommendations)
                    final_recommendations.extend(random.sample(remaining, min(needed, len(remaining))))
        else:
            final_recommendations = recommendations
        
        # 最后随机打乱顺序
        random.shuffle(final_recommendations)
        
        return RecommendationResponse(
            recommendations=final_recommendations,
            message="" if final_recommendations else "暂时没有找到合适的书籍，请换个方式描述一下你的心情？"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 推荐API错误: {e}")
        import traceback
        traceback.print_exc()
        
        # 获取匿名用户的AI书童名称
        agent_name = "苏童童"
        try:
            anonymous_user = db.query(User).filter(User.id == 1).first()
            if anonymous_user and anonymous_user.agent_name:
                agent_name = anonymous_user.agent_name
        except Exception as user_error:
            print(f"⚠️  获取用户书童名称失败: {user_error}")
            # 如果获取失败，使用默认名称
        
        # 返回AI书童引导信息
        return RecommendationResponse(
            recommendations=[],
            message=f"好像还没读懂你的心哦，不妨试试和{agent_name}仔细聊聊。",
            show_agent_suggestion=True,
            agent_name=agent_name
        )
