#!/bin/bash

# 数据库修复脚本

cd "$(dirname "$0")"

echo "🔧 开始修复数据库..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 start.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查Python版本
python_version=$(python --version 2>&1)
echo "📌 Python版本: $python_version"

# 检查依赖
echo "📦 检查依赖..."
pip show sqlalchemy > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  sqlalchemy 未安装，正在安装..."
    pip install -q sqlalchemy
fi

# 运行数据库迁移
echo "🔄 运行数据库迁移..."
python migrate_db.py

# 检查表
echo ""
echo "📊 检查数据库表..."
python -c "
import sys
sys.path.insert(0, '.')
from app.db.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print('数据库中的表：')
for table in tables:
    print(f'  ✅ {table}')

required_tables = ['users', 'books', 'bookshelves', 'user_preferences', 'chat_sessions', 'chat_messages']
missing_tables = [t for t in required_tables if t not in tables]

if missing_tables:
    print(f'\n⚠️  缺少表: {missing_tables}')
    print('请检查 migrate_db.py 是否正确执行')
else:
    print('\n✅ 所有必需的表都存在')
    
    # 检查书籍数量
    from app.db.database import SessionLocal
    from app.db.models import Book
    db = SessionLocal()
    book_count = db.query(Book).count()
    print(f'\n📚 数据库中的书籍数量: {book_count}')
    if book_count == 0:
        print('⚠️  数据库中没有书籍，请运行数据初始化:')
        print('   bash init_data.sh')
    db.close()
"

echo ""
echo "✅ 数据库检查完成！"
