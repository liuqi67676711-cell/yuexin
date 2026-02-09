# 阅心 - 项目设置指南

## 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 yarn

## 后端设置

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下信息：

```env
# DeepSeek API（需要注册获取 API Key）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# JWT Secret（生产环境请使用强随机字符串）
JWT_SECRET_KEY=your_secret_key_here_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database
DATABASE_URL=sqlite:///./yuexin.db

# Chroma
CHROMA_PERSIST_DIR=./chroma_db

# CORS
FRONTEND_URL=http://localhost:5173
```

### 3. 初始化数据库和书籍数据

```bash
# 运行初始化脚本（会从 Open Library API 获取书籍数据）
python scripts/init_books.py
```

### 4. 启动后端服务

```bash
uvicorn main:app --reload
```

后端将在 `http://localhost:8000` 运行

## 前端设置

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量（可选）

创建 `frontend/.env` 文件（如果需要自定义 API 地址）：

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:5173` 运行

## API 文档

启动后端后，访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

## 获取 DeepSeek API Key

1. 访问 [DeepSeek 官网](https://www.deepseek.com/)
2. 注册账户并获取 API Key
3. 将 API Key 填入 `.env` 文件

## 语义检索（Embedding）配置

语义检索的向量来源（按优先级）：

1. **智谱 BigModel Embedding-3**：在 `.env` 中配置 `BIGMODEL_API_KEY` 后启用，模型 `embedding-3`，支持维度 256/512/1024/2048（默认 1024）。
2. **OpenAI Embedding**：配置 `OPENAI_API_KEY` 且未配置 BigModel 时使用。
3. **本地 sentence-transformers**：两者都未配置时使用（384 维）。

**重要**：更换 Embedding 来源或维度后，需**重建向量库**，否则维度不一致会报错：

```bash
cd backend
rm -rf chroma_db
python scripts/init_books.py
```

## 注意事项

1. **免费 API 限制**：DeepSeek / OpenAI API 有额度限制，请合理使用
2. **书籍数据**：初始数据来自 Open Library API，数据量可能有限
3. **向量数据库**：Chroma 数据库文件存储在 `backend/chroma_db` 目录
4. **SQLite 数据库**：数据库文件存储在 `backend/yuexin.db`

## 常见问题

### Q: 向量检索没有结果？
A: 确保已运行 `init_books.py` 脚本初始化书籍数据

### Q: LLM API 调用失败？
A: 检查 `.env` 中的 `DEEPSEEK_API_KEY` 是否正确，以及 API 额度是否充足

### Q: 前端无法连接后端？
A: 确保后端服务已启动，并检查 CORS 配置
