"""
检查数据库中的书籍数量
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models import Book

db = SessionLocal()

try:
    count = db.query(Book).count()
    print(f"数据库中的书籍数量: {count}")
    
    if count > 0:
        print("\n前10本书籍：")
        books = db.query(Book).limit(10).all()
        for i, book in enumerate(books, 1):
            print(f"{i}. {book.title} - {book.author or '未知'} (ID: {book.id}, ISBN: {book.isbn or 'N/A'})")
    else:
        print("\n数据库为空")
        
finally:
    db.close()
