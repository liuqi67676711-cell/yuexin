"""
数据库迁移脚本 - 创建所有必需的表，并修复 chat_messages 表结构
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, Base
from app.db.models import User, Book, Bookshelf, UserPreference, ChatSession, ChatMessage
from sqlalchemy import inspect
from sqlalchemy import text

print("🔄 开始数据库迁移...")

# 创建所有表（包括新的 ChatSession 和 ChatMessage 表）
Base.metadata.create_all(bind=engine)

# 修复 chat_messages 表：若缺少 session_id 则添加（兼容旧库）
inspector = inspect(engine)
if "chat_messages" in inspector.get_table_names():
    columns = [c["name"] for c in inspector.get_columns("chat_messages")]
    if "session_id" not in columns:
        print("🔄 为 chat_messages 表添加缺失的 session_id 列...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE chat_messages ADD COLUMN session_id INTEGER NOT NULL DEFAULT 1"))
            conn.commit()
        print("✅ 已添加 session_id 列")
    else:
        print("✅ chat_messages 表已包含 session_id 列")

print("✅ 数据库迁移完成！")
print("   已创建/更新所有表，包括 ChatSession 和 ChatMessage 表")

# 验证表是否创建成功
tables = inspector.get_table_names()

required_tables = ['users', 'books', 'bookshelves', 'user_preferences', 'chat_sessions', 'chat_messages']
print("\n📊 验证表创建情况：")
for table in required_tables:
    if table in tables:
        print(f"  ✅ {table}")
    else:
        print(f"  ❌ {table} - 缺失！")

missing_tables = [t for t in required_tables if t not in tables]
if missing_tables:
    print(f"\n⚠️  警告：以下表未创建: {', '.join(missing_tables)}")
    print("   请检查 models.py 中的表定义")
else:
    print("\n✅ 所有必需的表都已创建！")
