"""
检查书库中某类书籍的数量（如推理、科幻）
用于排查「想看推理小说却推荐不到」是否因库内缺少该类书籍
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import or_, func
from app.db.database import SessionLocal
from app.db.models import Book


def check_genre(genre_name: str, keywords: list):
    """统计 title 或 description 中包含任一关键词的书籍数量，并打印若干示例"""
    db = SessionLocal()
    try:
        total = db.query(func.count(Book.id)).scalar() or 0
        print(f"\n📊 书库总量: {total} 本")

        # 构建 LIKE 条件（不区分大小写用 lower，SQLite 支持）
        conditions = []
        for kw in keywords:
            conditions.append(Book.title.ilike(f"%{kw}%"))
            conditions.append(Book.description.ilike(f"%{kw}%"))
        combined = or_(*conditions)

        # 去重计数：同一本书可能同时匹配多个关键词
        matched = db.query(Book).filter(combined).distinct().all()
        count = len(matched)
        print(f"📚 含「{genre_name}」相关关键词的书籍: {count} 本")
        print(f"   关键词: {keywords}")

        if count > 0:
            print(f"\n   示例（前 5 本）:")
            for b in matched[:5]:
                desc_preview = (b.description or "")[:60].replace("\n", " ")
                print(f"   - 《{b.title}》 {b.author or ''} | {(desc_preview + '...') if len(desc_preview) >= 60 else desc_preview}")
        else:
            print(f"\n   ⚠️ 库内暂无该类书籍，语义推荐无法命中。可运行 init_books 拉取数据，或增加该类型的搜索关键词。")
    finally:
        db.close()


if __name__ == "__main__":
    # 推理类：中英文关键词（与 recommendation.py 中 GENRE_SYNONYMS 对齐）
    check_genre("推理/悬疑/侦探", ["推理", "悬疑", "侦探", "mystery", "detective", "crime", "thriller"])
