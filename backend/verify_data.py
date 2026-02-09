"""
验证数据库和向量数据库中的数据
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Book
from app.services.vector_db import VectorDBService

db = SessionLocal()
vector_db = VectorDBService()

try:
    # 检查数据库
    count = db.query(Book).count()
    print(f"📚 数据库中的书籍数量: {count}")
    
    if count > 0:
        print("\n前10本书籍：")
        books = db.query(Book).limit(10).all()
        for i, book in enumerate(books, 1):
            print(f"{i}. {book.title}")
            print(f"   作者: {book.author or '未知'}")
            print(f"   ISBN: {book.isbn or 'N/A'}")
            print(f"   封面: {'有' if book.cover_url else '无'}")
            print()
        
        # 检查向量数据库
        print("🔍 检查向量数据库...")
        try:
            # 尝试获取一些向量数据
            collection = vector_db.collection
            count_result = collection.count()
            print(f"📊 向量数据库中的向量数量: {count_result}")
            
            if count_result > 0:
                print("✅ 向量数据正常！")
            else:
                print("⚠️  向量数据库为空，但书籍数据存在")
                print("   这不会影响精确搜索，但会影响语义推荐")
        except Exception as e:
            print(f"⚠️  检查向量数据库时出错: {e}")
    else:
        print("\n❌ 数据库为空！")
        print("   需要运行初始化脚本")
        
finally:
    db.close()
