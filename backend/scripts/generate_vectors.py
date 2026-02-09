"""
为数据库中已有的书籍生成向量（不重新拉取数据）
用于：向量库为空或维度不匹配时，为现有书籍补向量
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Book
from app.services.embedding import EmbeddingService
from app.services.vector_db import VectorDBService


async def generate_vectors_for_existing_books():
    """为数据库中已有的书籍生成向量"""
    db: Session = SessionLocal()
    embedding_service = EmbeddingService()
    vector_db_service = VectorDBService()
    
    try:
        # 获取所有书籍
        books = db.query(Book).all()
        total = len(books)
        print(f"📚 找到 {total} 本书籍，开始生成向量...")
        
        if total == 0:
            print("⚠️  数据库中没有书籍，请先运行 init_books.py 初始化数据")
            return
        
        success_count = 0
        error_count = 0
        
        for idx, book in enumerate(books, 1):
            try:
                # 构建向量化文本
                text_for_embedding = f"{book.title} {book.author or ''} {book.description or ''}"
                if len(text_for_embedding.strip()) == 0:
                    text_for_embedding = book.title
                
                print(f"[{idx}/{total}] 生成向量: {book.title[:40]}...")
                
                # 生成向量
                embedding = await embedding_service.get_embedding(text_for_embedding)
                
                if not embedding or len(embedding) == 0:
                    print(f"  ⚠️  向量生成失败，跳过")
                    error_count += 1
                    continue
                
                # 保存到向量数据库
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
                
                success_count += 1
                
                if idx % 10 == 0:
                    print(f"\n📊 进度: {idx}/{total}，成功: {success_count}，失败: {error_count}\n")
                    
            except Exception as e:
                error_count += 1
                print(f"  ❌ 失败: {str(e)[:100]}")
                if error_count <= 5:
                    import traceback
                    traceback.print_exc()
        
        print(f"\n✅ 完成！成功: {success_count}，失败: {error_count}")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(generate_vectors_for_existing_books())
