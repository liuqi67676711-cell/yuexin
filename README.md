# 阅心 - AI 阅读伴侣

一个基于 LLM 和向量检索技术的"懂情绪、懂场景"的 AI 阅读推荐平台。

## 项目结构

```
阅心/
├── frontend/          # React + TypeScript + Tailwind CSS 前端
├── backend/           # Python + FastAPI 后端
└── README.md
```

## 技术栈

### 前端
- React 18 + TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios

### 后端
- Python 3.11+
- FastAPI
- SQLite（开发阶段）
- Chroma（向量数据库）
- DeepSeek API（LLM + Embedding）

## 快速开始

### 后端启动
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

## 功能模块

- ✅ 模块一：语义推荐引擎
- ✅ 模块二：推荐结果呈现
- ✅ 模块三：基础详情展示
- ✅ AI 书童（RAG对话）
- ✅ 全功能检索系统
- ✅ 智能书架

## 开发状态

项目正在开发中...
