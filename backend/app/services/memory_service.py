"""
AI 书童记忆服务：阅读兴趣向量、会话摘要、兴趣事实
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Bookshelf, UserReadingProfile, UserInterestFact

logger = logging.getLogger(__name__)


def refresh_reading_profile(db: Session, user_id: int) -> bool:
    """
    根据书架计算用户阅读兴趣向量并写入 user_reading_profile。
    权重：想读=0.3, 在读=0.6, 已读=1.0, 弃读=-0.2
    """
    try:
        from app.services.vector_db import VectorDBService
        vdb = VectorDBService()
    except Exception as e:
        logger.warning("向量服务不可用，跳过阅读画像更新: %s", e)
        return False

    items = db.query(Bookshelf).filter(Bookshelf.user_id == user_id).all()
    if not items:
        profile = db.query(UserReadingProfile).filter(
            UserReadingProfile.user_id == user_id
        ).first()
        if profile:
            db.delete(profile)
            db.commit()
        return True

    status_weight = {"to_read": 0.3, "reading": 0.6, "read": 1.0, "dropped": -0.2}
    book_ids = [str(b.book_id) for b in items]
    weights = [status_weight.get(b.status, 0.5) for b in items]

    id_to_emb = vdb.get_embeddings_by_ids(book_ids)
    embeddings = []
    w_list = []
    for i, bid in enumerate(book_ids):
        if bid in id_to_emb and id_to_emb[bid]:
            embeddings.append(id_to_emb[bid])
            w_list.append(max(0, weights[i]))

    if not embeddings:
        return False

    dim = len(embeddings[0])
    total_w = sum(w_list)
    if total_w <= 0:
        return False
    avg = [0.0] * dim
    for emb, w in zip(embeddings, w_list):
        for j in range(dim):
            avg[j] += emb[j] * w
    avg = [x / total_w for x in avg]

    profile = db.query(UserReadingProfile).filter(
        UserReadingProfile.user_id == user_id
    ).first()
    if profile:
        profile.interest_vector = avg
        profile.interest_source = "bookshelf"
        profile.last_updated = func.now()
    else:
        db.add(UserReadingProfile(
            user_id=user_id,
            interest_vector=avg,
            interest_source="bookshelf"
        ))
    db.commit()
    return True


def get_user_interest_vector(db: Session, user_id: int) -> Optional[List[float]]:
    """获取用户阅读兴趣向量（若存在）"""
    profile = db.query(UserReadingProfile).filter(
        UserReadingProfile.user_id == user_id
    ).first()
    if profile and profile.interest_vector:
        return profile.interest_vector
    return None
