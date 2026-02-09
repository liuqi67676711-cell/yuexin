"""
阅心 - 后端主入口
"""
import logging
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from sqlalchemy import inspect, text

from app.api import auth, books, search, recommendation, agent, bookshelf, popular
from app.core.config import settings
from app.db.database import engine, Base

# 导入模型以注册到 Base.metadata（确保新表被创建）
from app.db import models  # noqa: F401
# 创建数据库表
Base.metadata.create_all(bind=engine)

# 修复旧库：缺失列时自动添加
def _migrate_db():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    with engine.connect() as conn:
        if "chat_messages" in tables:
            cols = [c["name"] for c in inspector.get_columns("chat_messages")]
            if "session_id" not in cols:
                conn.execute(text("ALTER TABLE chat_messages ADD COLUMN session_id INTEGER NOT NULL DEFAULT 1"))
                conn.commit()
        if "users" in tables:
            cols = [c["name"] for c in inspector.get_columns("users")]
            if "agent_name" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN agent_name VARCHAR DEFAULT '苏童童'"))
                conn.commit()
        if "books" in tables:
            cols = [c["name"] for c in inspector.get_columns("books")]
            if "douban_id" not in cols:
                conn.execute(text("ALTER TABLE books ADD COLUMN douban_id VARCHAR"))
                conn.commit()
            if "rating_source" not in cols:
                conn.execute(text("ALTER TABLE books ADD COLUMN rating_source VARCHAR DEFAULT 'douban'"))
                conn.commit()
try:
    _migrate_db()
except Exception as e:
    print(f"⚠️  数据库迁移检查跳过: {e}")

app = FastAPI(
    title="阅心 API",
    description="AI 阅读伴侣后端 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(books.router, prefix="/api/books", tags=["书籍"])
app.include_router(search.router, prefix="/api/search", tags=["搜索"])
app.include_router(recommendation.router, prefix="/api/recommendation", tags=["推荐"])
app.include_router(popular.router, prefix="/api/popular", tags=["热门"])
app.include_router(agent.router, prefix="/api/agent", tags=["AI书童"])
app.include_router(bookshelf.router, prefix="/api/bookshelf", tags=["书架"])


def _log_llm_provider():
    """启动时打印当前 LLM 提供方，便于排查「回复过于简单」是否因未走 DeepSeek"""
    from app.services.llm import LLMService
    s = LLMService()
    if s._provider == "mock":
        msg = "阅心 LLM: 当前使用【内置简单回复】。若需详细回复，请在 backend/.env 中配置 DEEPSEEK_API_KEY 并重启后端。"
        logging.warning(msg)
        print("⚠️ ", msg)
    else:
        msg = f"阅心 LLM: 当前使用 {s._provider} (model={s.model})"
        logging.info(msg)
        print("✅", msg)


@app.on_event("startup")
async def startup():
    _log_llm_provider()


@app.get("/")
async def root():
    return {"message": "阅心 API 服务运行中", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获未处理的异常，返回 500 并打印到控制台便于排查"""
    if isinstance(exc, HTTPException):
        raise exc
    tb = traceback.format_exc()
    logging.error(f"未处理异常: {exc}\n{tb}")
    print(f"❌ 500 错误: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
        },
    )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("RUN_ENV") != "production"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
