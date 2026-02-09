"""
检查数据库表是否存在
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print("数据库中的表：")
for table in tables:
    print(f"  ✅ {table}")

required_tables = ['users', 'books', 'bookshelves', 'user_preferences', 'chat_sessions', 'chat_messages']
missing_tables = [t for t in required_tables if t not in tables]

if missing_tables:
    print(f"\n⚠️  缺少表: {', '.join(missing_tables)}")
    print("请运行: python migrate_db.py")
else:
    print("\n✅ 所有必需的表都存在")
