"""
测试保存一本书籍
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.db.models import Book
from app.services.book_data import BookDataService
from app.services.embedding import EmbeddingService
from app.services.vector_db import VectorDBService


async def test_save_one():
    """测试保存一本书籍"""
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    book_data_service = BookDataService()
    embedding_service = EmbeddingService()
    vector_db_service = VectorDBService()
    
    try:
        # 获取一本书
        print("获取测试书籍...")
        books = await book_data_service.search_books("science fiction", limit=1)
        
        if not books:
            print("❌ 无法获取书籍数据")
            return
        
        book_data = books[0]
        print(f"测试书籍: {book_data.get('title')}")
        print(f"  ISBN: {book_data.get('isbn')}")
        print(f"  作者: {book_data.get('author')}")
        
        # 检查是否已存在
        existing = None
        if book_data.get("isbn"):
            existing = db.query(Book).filter(Book.isbn == book_data["isbn"]).first()
        if not existing:
            existing = db.query(Book).filter(Book.title == book_data.get("title", "")).first()
        
        if existing:
            print(f"⚠️  书籍已存在 (ID: {existing.id})")
            print("删除现有记录进行测试...")
            db.delete(existing)
            db.commit()
        
        # 尝试保存
        print("\n尝试保存书籍...")
        book = Book(
            isbn=book_data.get("isbn") or None,
            title=book_data["title"],
            author=book_data.get("author") or None,
            publisher=book_data.get("publisher") or None,
            description=(book_data.get("description", "")[:1000] if book_data.get("description") else "") or None,
            cover_url=book_data.get("cover_url") or None,
            category=book_data.get("category") or None,
            page_count=book_data.get("page_count") or None,
            open_library_id=book_data.get("open_library_id") or None,
        )
        
        print("添加到数据库...")
        db.add(book)
        db.commit()
        db.refresh(book)
        print(f"✅ 书籍已保存 (ID: {book.id})")
        
        # 生成向量
        print("\n生成向量...")
        text_for_embedding = f"{book.title} {book.author or ''} {book.description or ''}"
        embedding = await embedding_service.get_embedding(text_for_embedding)
        print(f"✅ 向量生成成功 (维度: {len(embedding)})")
        
        # 保存到向量数据库
        print("\n保存到向量数据库...")
        await vector_db_service.add_book(
            book_id=str(book.id),
            embedding=embedding,
            metadata={
                "title": book.title,
                "author": book.author or "",
                "isbn": book.isbn or "",
                "category": book.category or "",
            }
        )
        print("✅ 向量已保存")
        
        print("\n✅ 测试成功！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_save_one())
