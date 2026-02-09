# 修复连接问题指南

## 问题诊断

前端显示 `ECONNREFUSED ::1:8000` 错误，表明：
1. 前端尝试连接 IPv6 的 localhost (`::1`)，但后端可能只监听 IPv4 (`127.0.0.1`)
2. 后端服务可能没有运行
3. 匿名用户初始化可能失败

## 已修复的问题

### 1. Vite 代理配置
- **文件**: `frontend/vite.config.ts`
- **修复**: 将代理目标从 `http://localhost:8000` 改为 `http://127.0.0.1:8000`（强制使用 IPv4）

### 2. 匿名用户初始化
- **文件**: `backend/app/api/agent.py`, `backend/app/api/bookshelf.py`
- **修复**: 
  - 改进了 `ensure_anonymous_user` 函数，增加了错误处理和回退机制
  - 所有 API 端点现在都使用返回的用户对象，而不是硬编码的 `ANONYMOUS_USER_ID`
  - 添加了适当的错误处理，避免 500 错误

## 启动步骤

### 1. 启动后端服务

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"

# 激活虚拟环境
source venv/bin/activate

# 启动后端服务（监听 127.0.0.1:8000）
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**预期输出**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2. 启动前端服务

**在新的终端窗口中**:

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/frontend"

# 启动前端开发服务器
npm run dev
```

**预期输出**:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 3. 验证连接

1. 打开浏览器访问 `http://localhost:5173`
2. 打开浏览器开发者工具（F12），查看 Console 标签
3. 应该不再看到 `ECONNREFUSED` 错误
4. 尝试以下操作：
   - 搜索书籍
   - 点击情绪胶囊
   - 打开 AI 书童对话框
   - 查看"大家都在看"

## 如果仍然遇到问题

### 检查后端是否运行
```bash
# 检查端口 8000 是否被占用
lsof -i :8000

# 如果端口被占用，杀死进程
kill -9 <PID>
```

### 检查数据库
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate

# 运行数据库检查脚本
python -c "from app.db.database import engine; from app.db.models import Base; Base.metadata.create_all(bind=engine); print('✅ 数据库表已创建')"
```

### 检查匿名用户是否存在
```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate

python -c "
from app.db.database import SessionLocal
from app.db.models import User
db = SessionLocal()
user = db.query(User).first()
if user:
    print(f'✅ 找到用户: ID={user.id}, 用户名={user.username}')
else:
    print('⚠️  没有找到用户，将在首次API调用时自动创建')
db.close()
"
```

### 查看后端日志
后端终端应该显示详细的错误信息。如果看到错误，请检查：
1. 数据库文件是否存在 (`yuexin.db`)
2. 依赖是否已安装 (`pip install -r requirements.txt`)
3. 虚拟环境是否已激活

## 测试 API

可以使用以下命令测试后端 API：

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate

# 测试推荐API
curl -X POST "http://127.0.0.1:8000/api/recommendation/semantic" \
  -H "Content-Type: application/json" \
  -d '{"query": "想看点治愈的小说"}'

# 测试热门书籍API
curl "http://127.0.0.1:8000/api/popular/everyone-watching?limit=5"

# 测试AI会话API
curl -X POST "http://127.0.0.1:8000/api/agent/sessions" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试会话"}'
```

## 常见错误及解决方案

### 错误: `ModuleNotFoundError: No module named 'fastapi'`
**解决**: 确保虚拟环境已激活并安装了所有依赖
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 错误: `Address already in use`
**解决**: 端口被占用，杀死占用进程或使用其他端口
```bash
lsof -i :8000
kill -9 <PID>
```

### 错误: `无法初始化匿名用户`
**解决**: 检查数据库文件权限和 SQLite 版本
```bash
cd backend
ls -la yuexin.db
chmod 644 yuexin.db  # 如果需要
```
