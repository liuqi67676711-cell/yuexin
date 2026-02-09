"""
数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    agent_name = Column(String, default="苏童童")  # AI书童名称
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    bookshelves = relationship("Bookshelf", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    interest_facts = relationship("UserInterestFact", back_populates="user", cascade="all, delete-orphan")
    reading_profile = relationship("UserReadingProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Book(Base):
    """书籍模型"""
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String, unique=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True)
    publisher = Column(String)
    description = Column(Text)  # 简介
    cover_url = Column(String)  # 封面URL
    rating = Column(Float)  # 豆瓣评分
    rating_source = Column(String, default="douban")
    category = Column(String)  # 分类
    page_count = Column(Integer)  # 页数
    open_library_id = Column(String)  # Open Library ID
    douban_id = Column(String)  # 豆瓣ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    bookshelves = relationship("Bookshelf", back_populates="book")
    chat_messages = relationship("ChatMessage", back_populates="book")


class Bookshelf(Base):
    """书架模型（用户-书籍关联）"""
    __tablename__ = "bookshelves"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    status = Column(String, default="to_read")  # to_read, reading, read, dropped
    notes = Column(Text)  # 闪念笔记
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="bookshelves")
    book = relationship("Book", back_populates="bookshelves")


class UserPreference(Base):
    """用户偏好模型（记录"不感兴趣"等反馈）"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    preference_type = Column(String)  # not_interested, liked, etc.
    feedback_data = Column(JSON)  # 额外的反馈数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="preferences")


class ChatSession(Base):
    """AI书童对话会话模型"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=True)  # 可选，如果是在讨论某本书
    name = Column(String, nullable=False)  # 对话名称
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="chat_sessions")
    book = relationship("Book")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    summary = relationship("ChatSessionSummary", back_populates="session", uselist=False, cascade="all, delete-orphan")


class ChatSessionSummary(Base):
    """会话摘要（跨 session 记忆）"""
    __tablename__ = "chat_session_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, unique=True)
    summary = Column(Text, nullable=False)  # 1～2 句摘要
    key_topics = Column(JSON)  # ["三体", "刘慈欣", "科幻"]
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("ChatSession", back_populates="summary")


class UserInterestFact(Base):
    """用户兴趣事实（知识索引层）"""
    __tablename__ = "user_interest_facts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fact_type = Column(String)  # book_title | author | topic | genre
    fact_value = Column(String, nullable=False)
    source_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    weight = Column(Float, default=1.0)
    last_mentioned_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="interest_facts")


class UserReadingProfile(Base):
    """用户阅读画像（阅读兴趣向量）"""
    __tablename__ = "user_reading_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    interest_vector = Column(JSON)  # [float] 与书籍 embedding 同维
    interest_source = Column(String, default="bookshelf")  # bookshelf | chat_extracted
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="reading_profile")


class ChatMessage(Base):
    """AI书童对话记录模型"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)  # 所属会话
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=True)  # 可选，如果是在讨论某本书
    role = Column(String, nullable=False)  # 'user' or 'agent'
    content = Column(Text, nullable=False)  # 消息内容
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")
    book = relationship("Book", back_populates="chat_messages")
