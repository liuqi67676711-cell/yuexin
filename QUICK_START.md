# 阅心 - 快速启动指南

## 🚀 一键启动（推荐）

### macOS/Linux 用户：

1. **启动后端**（打开第一个终端窗口）：
```bash
cd backend
chmod +x start.sh
./start.sh
```

2. **启动前端**（打开第二个终端窗口）：
```bash
cd frontend
chmod +x start.sh
./start.sh
```

### Windows 用户：

1. **启动后端**（打开第一个 PowerShell/CMD 窗口）：
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_books.py
uvicorn main:app --reload
```

2. **启动前端**（打开第二个 PowerShell/CMD 窗口）：
```bash
cd frontend
npm install
npm run dev
```

## 📍 访问地址

启动成功后，在浏览器中访问：

- **前端网站**: http://localhost:5173
- **后端 API 文档**: http://localhost:8000/docs

## ⚙️ 配置说明

### 1. DeepSeek API Key（可选）

项目已经配置为**无需 API Key 即可运行**，会使用本地模型。

如果你想使用 DeepSeek API 获得更好的效果：

1. 访问 https://www.deepseek.com/ 注册账户
2. 获取 API Key
3. 编辑 `backend/.env` 文件，填入：
```env
DEEPSEEK_API_KEY=你的API_Key
```

### 2. 数据初始化

首次运行时会自动从 Open Library API 获取书籍数据并初始化向量数据库。

这个过程可能需要几分钟，请耐心等待。

## 🐛 常见问题

### Q: 端口被占用？
A: 如果 8000 或 5173 端口被占用，可以修改：
- 后端：编辑 `backend/main.py` 中的端口
- 前端：编辑 `frontend/vite.config.ts` 中的端口

### Q: 依赖安装失败？
A: 
- 确保 Python 版本 >= 3.9
- 确保 Node.js 版本 >= 18
- 尝试使用 `pip install --user` 或创建虚拟环境

### Q: 数据库初始化失败？
A: 
- 检查网络连接（需要访问 Open Library API）
- 手动运行：`cd backend && python scripts/init_books.py`

### Q: 前端无法连接后端？
A: 
- 确保后端服务已启动
- 检查 `frontend/vite.config.ts` 中的代理配置
- 检查 `backend/.env` 中的 `FRONTEND_URL` 配置

## 📝 功能说明

### 游客模式
- ✅ 可以搜索书籍
- ✅ 可以查看推荐结果
- ❌ 无法使用书架功能
- ❌ 无法使用 AI 书童

### 注册登录后
- ✅ 所有功能可用
- ✅ 个人书架管理
- ✅ AI 书童对话
- ✅ 推荐偏好记录

## 🎯 下一步

1. 访问 http://localhost:5173
2. 尝试语义搜索（例如："最近工作压力大，想看点轻松的书"）
3. 注册账户体验完整功能
4. 查看推荐结果并添加到书架

祝使用愉快！📚
