# 数据库修复指南

如果遇到以下问题：
- 大家都在看无法加载
- AI书童、搜索和情绪胶囊功能都不能使用
- 后端返回500错误

## 快速修复步骤

### 1. 运行数据库修复脚本

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
bash fix_database.sh
```

这个脚本会：
- 检查虚拟环境
- 安装缺失的依赖
- 运行数据库迁移
- 检查所有表是否创建成功
- 显示数据库中的书籍数量

### 2. 如果数据库中没有书籍

如果脚本显示书籍数量为0，需要初始化数据：

```bash
bash init_data.sh
```

### 3. 重启后端服务

```bash
# 停止当前服务（Ctrl+C）
bash start.sh
```

## 手动检查步骤

如果自动脚本失败，可以手动执行：

### 1. 激活虚拟环境

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate
```

### 2. 检查依赖

```bash
pip install -q sqlalchemy
```

### 3. 运行迁移

```bash
python migrate_db.py
```

### 4. 检查表

```bash
python -c "
from app.db.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print('数据库中的表：')
for table in tables:
    print(f'  ✅ {table}')
"
```

### 5. 检查书籍数量

```bash
python -c "
from app.db.database import SessionLocal
from app.db.models import Book
db = SessionLocal()
book_count = db.query(Book).count()
print(f'书籍数量: {book_count}')
db.close()
"
```

## 常见问题

### 问题1: ModuleNotFoundError: No module named 'sqlalchemy'

**解决**：
```bash
source venv/bin/activate
pip install sqlalchemy
```

### 问题2: 表已存在错误

**解决**：这是正常的，`create_all` 不会重复创建已存在的表。

### 问题3: 数据库文件损坏

**解决**：删除数据库文件重新创建（**注意：会丢失所有数据**）
```bash
rm yuexin.db
python migrate_db.py
bash init_data.sh
```

## 验证修复

修复后，检查以下内容：

1. ✅ 所有6个表都存在：users, books, bookshelves, user_preferences, chat_sessions, chat_messages
2. ✅ 数据库中有书籍数据（至少1本）
3. ✅ 后端服务正常启动，没有错误
4. ✅ 前端可以正常访问API

如果仍有问题，请查看后端终端的错误日志。
