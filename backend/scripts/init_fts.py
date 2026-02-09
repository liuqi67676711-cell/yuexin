"""
初始化 FTS 全文搜索索引
首次使用精确搜索前运行此脚本，或当书籍数据更新后重建索引
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.services.fts_search import FTSSearchService


def init_fts():
    """初始化 FTS 全文搜索索引"""
    db = SessionLocal()
    try:
        print("🔍 初始化 FTS 全文搜索索引...")
        fts_service = FTSSearchService(db)
        
        # 检查书籍数量
        from app.db.models import Book
        book_count = db.query(Book).count()
        print(f"📚 数据库中有 {book_count} 本书籍")
        
        # 重建索引（确保数据同步）
        fts_service.rebuild_fts_index()
        
        print("✅ FTS 索引初始化完成！精确搜索性能已优化。")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    init_fts()
