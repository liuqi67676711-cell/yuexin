"""
清空数据库（谨慎使用！）
"""
import sys
import os
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine, Base
from app.db.models import Book, User, Bookshelf, UserPreference

db = SessionLocal()

try:
    print("⚠️  警告：这将删除所有书籍数据！")
    print("   用户数据不会被删除")
    
    # 统计
    book_count = db.query(Book).count()
    print(f"\n当前数据库中有 {book_count} 本书籍")
    
    if book_count == 0:
        print("数据库已经是空的，无需清空")
    else:
        confirm = input("\n确认要清空书籍数据吗？(yes/no): ")
        if confirm.lower() == 'yes':
            # 删除所有书籍
            db.query(Book).delete()
            db.commit()
            print(f"✅ 已删除 {book_count} 本书籍")
            
            # 删除向量数据库
            chroma_dir = "./chroma_db"
            if os.path.exists(chroma_dir):
                shutil.rmtree(chroma_dir)
                print("✅ 已删除向量数据库")
            
            print("\n现在可以重新运行初始化脚本了：")
            print("python scripts/init_books.py")
        else:
            print("取消操作")
            
finally:
    db.close()
