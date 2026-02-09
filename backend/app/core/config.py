"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 大模型 API：二选一或只配一个即可。优先使用 DeepSeek，其次 OpenAI，都未配置则使用内置简单回复
    # DeepSeek 公开接口（优先）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    # OpenAI 公开接口（Chat + Embedding，可选）
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    # 智谱 BigModel Embedding（语义检索，优先于 OpenAI）
    BIGMODEL_API_KEY: str = ""
    BIGMODEL_EMBEDDING_BASE_URL: str = "https://open.bigmodel.cn"
    BIGMODEL_EMBEDDING_MODEL: str = "embedding-3"
    BIGMODEL_EMBEDDING_DIMENSIONS: int = 1024  # 256/512/1024/2048，与向量库一致
    
    # JWT
    JWT_SECRET_KEY: str = "yuexin_secret_key_2024_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Database
    DATABASE_URL: str = "sqlite:///./yuexin.db"
    
    # Chroma
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    
    # 豆瓣 API（可选，无 Key 时可能返回 400，init_books 会回退到仅用 Open Library）
    DOUBAN_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
