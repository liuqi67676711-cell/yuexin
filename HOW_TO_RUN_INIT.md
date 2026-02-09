# 如何正确运行数据初始化脚本

## ✅ 正确的方式

### 步骤 1：打开终端，进入 backend 目录

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
```

### 步骤 2：确认当前目录

运行以下命令确认你在正确的目录：
```bash
pwd
```

**应该显示**：
```
/Users/sixsevensconsubine/Desktop/阅心/backend
```

### 步骤 3：查看当前目录的文件

运行：
```bash
ls
```

**应该能看到**：
- `main.py`
- `requirements.txt`
- `app/` 目录
- `scripts/` 目录
- `.env` 文件
- 等等

### 步骤 4：运行脚本（重要：不要进入 scripts 目录）

**✅ 正确的方式**（在 backend 目录下）：
```bash
python scripts/init_books.py
```

**❌ 错误的方式**（不要这样做）：
```bash
cd scripts          # ❌ 不要进入 scripts 目录
python init_books.py  # ❌ 这样会报错
```

## 📁 目录结构说明

```
阅心/
└── backend/              ← 你应该在这里运行命令
    ├── main.py
    ├── requirements.txt
    ├── app/
    └── scripts/         ← 脚本在这个目录里
        └── init_books.py ← 但不要进入这个目录
```

## 🔍 如何判断你在正确的目录？

### 方法 1：查看终端提示符

在 macOS/Linux 终端，提示符通常会显示当前目录：
```
sixsevensconsubine@MacBook backend %
```
看到 `backend` 就对了！

### 方法 2：运行 pwd 命令

```bash
pwd
```

**正确输出**：
```
/Users/sixsevensconsubine/Desktop/阅心/backend
```

**错误输出**（如果在 scripts 目录）：
```
/Users/sixsevensconsubine/Desktop/阅心/backend/scripts
```

### 方法 3：查看文件列表

运行：
```bash
ls
```

**应该能看到 `scripts` 目录**，而不是看到 `init_books.py` 文件。

## 🚀 完整操作流程

```bash
# 1. 打开终端

# 2. 进入 backend 目录
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

# 3. 确认目录（可选但推荐）
pwd
# 应该显示：/Users/sixsevensconsubine/Desktop/阅心/backend

# 4. 查看文件（可选但推荐）
ls
# 应该能看到 scripts 目录

# 5. 运行脚本
python scripts/init_books.py
```

## ⚠️ 如果进错了目录怎么办？

### 情况 1：你在 scripts 目录里

如果你不小心进入了 scripts 目录：
```bash
cd scripts  # 你在这里
```

**解决方法**：返回上一级目录
```bash
cd ..       # 返回 backend 目录
pwd         # 确认现在在 backend 目录
python scripts/init_books.py  # 现在可以运行了
```

### 情况 2：你在项目根目录

如果你在 `阅心` 目录：
```bash
pwd
# 显示：/Users/sixsevensconsubine/Desktop/阅心
```

**解决方法**：进入 backend 目录
```bash
cd backend
pwd         # 确认现在在 backend 目录
python scripts/init_books.py
```

## 💡 为什么要在 backend 目录运行？

脚本中使用了相对导入：
```python
from app.db.database import ...
from app.services.book_data import ...
```

这些导入路径是相对于 `backend` 目录的，所以必须在 `backend` 目录下运行。

## 🎯 快速检查清单

运行脚本前，确认：
- [ ] 在 `backend` 目录（不是 `scripts` 目录）
- [ ] 能看到 `scripts` 目录（不是 `init_books.py` 文件）
- [ ] 能看到 `app` 目录
- [ ] 能看到 `main.py` 文件

如果以上都满足，就可以运行：
```bash
python scripts/init_books.py
```
