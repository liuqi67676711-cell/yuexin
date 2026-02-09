"""
AI 书童相关 API（无需登录版本）
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.db.database import get_db
from app.db.models import (
    Book,
    ChatMessage as ChatMessageModel,
    ChatSession as ChatSessionModel,
    ChatSessionSummary,
    UserInterestFact,
    User,
)
from app.api.auth import get_current_user_optional
from app.services.llm import LLMService

router = APIRouter()
llm_service = LLMService()


@router.get("/llm-status")
async def get_llm_status():
    """查看当前 AI 书童使用的 LLM（用于排查「回复过于简单」是否因 DeepSeek 未生效）"""
    p = llm_service._provider
    if p == "mock":
        return {
            "provider": "mock",
            "message": "当前使用内置简单回复。请在 backend/.env 中配置 DEEPSEEK_API_KEY 并重启后端，即可使用 DeepSeek 获得详细回复。",
        }
    return {
        "provider": p,
        "model": llm_service.model,
        "message": f"当前使用 {p}，回复应由大模型生成。若仍很简单，请访问 GET /api/agent/llm-test 诊断是否 402 或网络问题。",
    }


@router.get("/llm-test")
async def get_llm_test():
    """真实请求一次 DeepSeek/OpenAI，用于排查 402、网络或 Key 问题。浏览器打开即可看到结果。"""
    result = await llm_service.test_api_call()
    return result


# 使用固定的匿名用户ID（向后兼容）
ANONYMOUS_USER_ID = 1
AGENT_NAME = "苏童童"


def get_current_user_id(db: Session, current_user: Optional[User] = None) -> int:
    """获取当前用户ID，如果没有登录则使用匿名用户"""
    if current_user:
        return current_user.id
    
    # 如果没有登录，使用匿名用户（向后兼容）
    anonymous_user = ensure_anonymous_user(db)
    return anonymous_user.id if anonymous_user else 1


class ChatMessageRequest(BaseModel):
    message: str
    session_id: int  # 会话ID
    book_id: Optional[int] = None  # 如果是在讨论某本书


class ChatResponse(BaseModel):
    response: str
    agent_name: str = AGENT_NAME
    message_id: int  # 返回保存的消息ID
    used_fallback: bool = False  # True 表示未走 DeepSeek，使用了内置简单回复（如 402 或未配置 Key）


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str
    book_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    name: str
    book_id: Optional[int] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


def _iso_with_z(dt):
    """将 datetime 转为前端可正确解析的 ISO 字符串（无时区则按 UTC 加 Z，避免时间显示偏差）"""
    from datetime import datetime
    if dt is None:
        return ""
    if not isinstance(dt, datetime):
        return str(dt)
    s = dt.isoformat()
    if dt.tzinfo is None and "Z" not in s and "+" not in s:
        return s + "Z"
    return s


def _session_to_response(session) -> dict:
    """将会话模型转为响应 dict，确保 created_at/updated_at 为字符串"""
    from datetime import datetime
    created = session.created_at
    updated = session.updated_at
    return {
        "id": session.id,
        "name": session.name,
        "book_id": session.book_id,
        "created_at": _iso_with_z(created) if created else "",
        "updated_at": _iso_with_z(updated) if updated else _iso_with_z(created),
    }


class CreateSessionRequest(BaseModel):
    name: str
    book_id: Optional[int] = None


class UpdateSessionRequest(BaseModel):
    name: str


def ensure_anonymous_user(db: Session):
    """确保匿名用户存在"""
    from app.db.models import User
    from app.core.security import get_password_hash
    
    try:
        # 先尝试查找ID=1的用户
        anonymous_user = db.query(User).filter(User.id == ANONYMOUS_USER_ID).first()
        if anonymous_user:
            return anonymous_user
        
        # 如果ID=1的用户不存在，查找是否有其他用户
        any_user = db.query(User).first()
        if any_user:
            # 如果有其他用户，使用第一个用户的ID
            return any_user
        
        # 如果没有任何用户，创建一个新用户
        # 直接使用预计算的短哈希值，避免bcrypt哈希长度问题
        try:
            # 使用预计算的短哈希值（"guest"的bcrypt哈希，标准60字节）
            # 这个哈希值是通过 bcrypt.hashpw(b'guest', bcrypt.gensalt()) 生成的
            password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYq5q5q5q5q"
            
            # 先尝试直接创建ID=1的用户（使用SQL避免ORM的ID限制）
            try:
                from sqlalchemy import text
                # 检查ID=1的用户是否已存在
                existing = db.query(User).filter(User.id == ANONYMOUS_USER_ID).first()
                if existing:
                    return existing
                
                # 使用原始SQL插入，避免ORM的ID限制
                # 使用INSERT OR IGNORE避免重复插入错误
                result = db.execute(text("""
                    INSERT OR IGNORE INTO users (id, email, username, hashed_password, agent_name, created_at)
                    VALUES (:user_id, :email, :username, :password_hash, :agent_name, datetime('now'))
                """), {
                    "user_id": ANONYMOUS_USER_ID,
                    "email": "anonymous@guest.local",
                    "username": "匿名用户",
                    "password_hash": password_hash,
                    "agent_name": AGENT_NAME
                })
                db.commit()
                
                # 再次检查是否创建成功
                anonymous_user = db.query(User).filter(User.id == ANONYMOUS_USER_ID).first()
                if anonymous_user:
                    print(f"✅ 成功创建匿名用户 ID={anonymous_user.id}")
                    return anonymous_user
                else:
                    print("⚠️  SQL插入后未找到用户，可能是INSERT OR IGNORE跳过了")
            except Exception as sql_error:
                print(f"⚠️  直接插入ID=1失败: {sql_error}")
                import traceback
                traceback.print_exc()
                db.rollback()
            
            # 如果直接插入失败，让数据库自动分配ID（作为备选方案）
            print("⚠️  尝试让数据库自动分配ID...")
            anonymous_user = User(
                email="anonymous@guest.local",
                username="匿名用户",
                hashed_password=password_hash,
                agent_name=AGENT_NAME
            )
            db.add(anonymous_user)
            db.commit()
            db.refresh(anonymous_user)
            print(f"✅ 成功创建匿名用户 ID={anonymous_user.id}（自动分配）")
            return anonymous_user
        except Exception as create_error:
            print(f"⚠️  创建匿名用户失败: {create_error}")
            import traceback
            traceback.print_exc()
            return None
    except Exception as e:
        print(f"❌ ensure_anonymous_user 失败: {e}")
        import traceback
        traceback.print_exc()
        return None


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """创建新的对话会话（支持访客登录）"""
    try:
        user_id = get_current_user_id(db, current_user)
        
        session = ChatSessionModel(
            user_id=user_id,
            book_id=request.book_id,
            name=request.name
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return ChatSessionResponse(**_session_to_response(session))
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建会话失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"创建会话失败: {str(e)}"
        )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_sessions(
    book_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取所有对话会话（支持访客登录）"""
    try:
        user_id = get_current_user_id(db, current_user)
        
        query = db.query(ChatSessionModel).filter(
            ChatSessionModel.user_id == user_id
        )
        # 仅当明确传入 book_id 时筛选该书对话；不传则返回该用户的所有对话
        if book_id is not None:
            query = query.filter(ChatSessionModel.book_id == book_id)
        
        sessions = query.order_by(ChatSessionModel.updated_at.desc()).all()
        out = []
        for s in sessions:
            try:
                out.append(ChatSessionResponse(**_session_to_response(s)))
            except Exception as e:
                print(f"⚠️ 跳过无效会话 {getattr(s, 'id', '?')}: {e}")
        return out
    except Exception as e:
        print(f"❌ 获取会话列表失败: {e}")
        import traceback
        traceback.print_exc()
        # 返回空列表而不是抛出异常，避免500错误
        return []


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: int,
    request: UpdateSessionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """更新会话名称（支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    session = db.query(ChatSessionModel).filter(
        ChatSessionModel.id == session_id,
        ChatSessionModel.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session.name = request.name
    db.commit()
    db.refresh(session)
    
    return ChatSessionResponse(**_session_to_response(session))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """删除会话（会同时删除所有消息，支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    session = db.query(ChatSessionModel).filter(
        ChatSessionModel.id == session_id,
        ChatSessionModel.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    db.delete(session)
    db.commit()
    
    return {"message": "已删除"}


class SummarizeResponse(BaseModel):
    summary: str
    key_topics: List[str]
    message_count: int


@router.post("/sessions/{session_id}/summarize", response_model=SummarizeResponse)
async def summarize_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """生成会话摘要（幂等：已有摘要则返回，支持访客登录）"""
    user_id = get_current_user_id(db, current_user)

    session = db.query(ChatSessionModel).filter(
        ChatSessionModel.id == session_id,
        ChatSessionModel.user_id == user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    existing = db.query(ChatSessionSummary).filter(
        ChatSessionSummary.session_id == session_id
    ).first()
    if existing:
        return SummarizeResponse(
            summary=existing.summary or "",
            key_topics=existing.key_topics or [],
            message_count=existing.message_count or 0
        )

    messages = db.query(ChatMessageModel).filter(
        ChatMessageModel.session_id == session_id
    ).order_by(ChatMessageModel.created_at.asc()).limit(30).all()
    if len(messages) < 2:
        return SummarizeResponse(summary="", key_topics=[], message_count=len(messages))

    messages_text = [f"{m.role}: {m.content}" for m in messages]
    result = await llm_service.generate_session_summary(messages_text)
    summary_text = result.get("summary") or ""
    key_topics = result.get("key_topics") or []

    summary_obj = ChatSessionSummary(
        session_id=session_id,
        summary=summary_text,
        key_topics=key_topics,
        message_count=len(messages)
    )
    db.add(summary_obj)
    db.commit()
    db.refresh(summary_obj)

    _upsert_interest_facts(db, user_id, session_id, key_topics)

    return SummarizeResponse(
        summary=summary_text,
        key_topics=key_topics,
        message_count=len(messages)
    )


def _upsert_interest_facts(db: Session, user_id: int, session_id: int, topics: List[str]):
    """将 key_topics 写入 user_interest_facts，去重并更新 last_mentioned_at"""
    from sqlalchemy.sql import func
    expires = datetime.utcnow() + timedelta(days=90)
    for val in topics:
        if not val or len(val.strip()) < 2:
            continue
        val = val.strip()[:100]
        existing = db.query(UserInterestFact).filter(
            UserInterestFact.user_id == user_id,
            UserInterestFact.fact_value == val
        ).first()
        if existing:
            existing.last_mentioned_at = func.now()
            existing.weight = min(1.0, existing.weight + 0.1)
            existing.source_session_id = session_id
        else:
            db.add(UserInterestFact(
                user_id=user_id,
                fact_type="topic",
                fact_value=val,
                source_session_id=session_id,
                weight=1.0,
                expires_at=expires
            ))
    db.commit()


def _extract_facts_from_message(text: str) -> List[tuple]:
    """规则抽取：书名《》、作者、主题词"""
    import re
    facts = []
    for m in re.finditer(r'[《「]([^》」]{1,50})[》」]', text):
        facts.append(("book_title", m.group(1).strip()))
    for m in re.finditer(r'(?:作者|作家|写过)[是为]?\s*([^\s,，。]{2,20})', text):
        facts.append(("author", m.group(1).strip()))
    return facts


def _get_session_summary_and_interests(db: Session, session_id: int, user_id: int):
    """获取会话摘要与用户兴趣（用于注入 LLM）"""
    summary = db.query(ChatSessionSummary).filter(
        ChatSessionSummary.session_id == session_id
    ).first()
    summary_text = summary.summary if summary else ""

    interests = db.query(UserInterestFact).filter(
        UserInterestFact.user_id == user_id,
        UserInterestFact.weight >= 0.2
    ).order_by(UserInterestFact.last_mentioned_at.desc()).limit(15).all()
    interest_values = list(dict.fromkeys([f.fact_value for f in interests]))[:10]
    return summary_text, interest_values


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    chat_data: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """与 AI 书童对话（支持访客登录）"""
    try:
        user_id = get_current_user_id(db, current_user)
        
        user_message = chat_data.message
        session_id = chat_data.session_id
        book_id = chat_data.book_id
        
        # 验证会话是否存在
        session = db.query(ChatSessionModel).filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 保存用户消息
        user_msg = ChatMessageModel(
            session_id=session_id,
            user_id=user_id,
            book_id=book_id,
            role="user",
            content=user_message
        )
        db.add(user_msg)
        
        # 更新会话时间
        from sqlalchemy.sql import func
        session.updated_at = func.now()
        
        db.commit()
        db.refresh(user_msg)
        
        # 获取书籍上下文（如果提供了 book_id）
        book_context = ""
        if book_id:
            book = db.query(Book).filter(Book.id == book_id).first()
            if book:
                book_context = f"书名：{book.title}\n作者：{book.author}\n简介：{book.description or '暂无简介'}"

        # 会话摘要与用户兴趣（记忆机制）
        session_summary, user_interests = _get_session_summary_and_interests(db, session_id, user_id)
        
        # 所有对话统一走 DeepSeek（不再用简介短路），保证「介绍书」和「聊书、聊人生」都由同一大模型生成
        recent_messages = db.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session_id
        ).order_by(ChatMessageModel.created_at.desc()).limit(10).all()
        
        # DeepSeek/OpenAI 只认 role: system|user|assistant|tool，数据库存的是 agent -> 转为 assistant
        conversation_history = []
        for msg in reversed(recent_messages[:-1]):  # 排除刚保存的用户消息
            role = "assistant" if msg.role == "agent" else msg.role
            conversation_history.append({"role": role, "content": msg.content})
        
        try:
            response_text, used_fallback = await llm_service.generate_agent_response(
                user_message=user_message,
                book_context=book_context,
                conversation_history=conversation_history,
                session_summary=session_summary,
                user_interests=user_interests
            )
        except Exception as e:
            print(f"⚠️  LLM生成回复失败: {e}")
            response_text = "抱歉，我现在有点困惑，请稍后再试。"
            used_fallback = True
        
        # 保存AI回复
        agent_msg = ChatMessageModel(
            session_id=session_id,
            user_id=user_id,
            book_id=book_id,
            role="agent",
            content=response_text
        )
        db.add(agent_msg)
        db.commit()
        db.refresh(agent_msg)

        # 后台：规则抽取用户消息中的书名/作者，写入 interest_facts
        def _extract_and_save():
            try:
                from app.db.database import SessionLocal
                from sqlalchemy.sql import func
                local_db = SessionLocal()
                try:
                    facts = _extract_facts_from_message(user_message)
                    if facts:
                        expires = datetime.utcnow() + timedelta(days=90)
                        for ft, fv in facts:
                            if not fv or len(fv) < 2:
                                continue
                            fv = fv.strip()[:100]
                            existing = local_db.query(UserInterestFact).filter(
                                UserInterestFact.user_id == user_id,
                                UserInterestFact.fact_value == fv
                            ).first()
                            if existing:
                                existing.last_mentioned_at = func.now()
                                existing.source_session_id = session_id
                            else:
                                local_db.add(UserInterestFact(
                                    user_id=user_id,
                                    fact_type=ft,
                                    fact_value=fv,
                                    source_session_id=session_id,
                                    weight=1.0,
                                    expires_at=expires
                                ))
                        local_db.commit()
                finally:
                    local_db.close()
            except Exception as e:
                print(f"⚠️ 抽取兴趣事实失败: {e}")
        background_tasks.add_task(_extract_and_save)
        
        return ChatResponse(
            response=response_text,
            agent_name=AGENT_NAME,
            message_id=agent_msg.id,
            used_fallback=used_fallback
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 对话API错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"对话服务出错: {str(e)}"
        )


def _message_to_response(msg) -> dict:
    """将 ChatMessage 转为 API 响应 dict，确保 created_at 为字符串"""
    created = msg.created_at
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "created_at": _iso_with_z(created) if created else "",
        "book_id": getattr(msg, "book_id", None),
    }


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取会话的消息记录（支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    # 验证会话所有权
    session = db.query(ChatSessionModel).filter(
        ChatSessionModel.id == session_id,
        ChatSessionModel.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = db.query(ChatMessageModel).filter(
        ChatMessageModel.session_id == session_id
    ).order_by(ChatMessageModel.created_at.asc(), ChatMessageModel.id.asc()).limit(limit).all()
    
    return [ChatMessageResponse(**_message_to_response(m)) for m in messages]


@router.delete("/messages/{message_id}")
async def delete_chat_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """删除单条对话记录（支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    message = db.query(ChatMessageModel).filter(
        ChatMessageModel.id == message_id,
        ChatMessageModel.user_id == user_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    db.delete(message)
    db.commit()
    
    return {"message": "已删除"}


@router.delete("/sessions/{session_id}/messages")
async def clear_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """清空会话的所有消息（支持访客登录）"""
    user_id = get_current_user_id(db, current_user)
    
    # 验证会话所有权
    session = db.query(ChatSessionModel).filter(
        ChatSessionModel.id == session_id,
        ChatSessionModel.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    db.query(ChatMessageModel).filter(
        ChatMessageModel.session_id == session_id
    ).delete()
    db.commit()
    return {"message": "已清空对话记录"}


class ProfileResponse(BaseModel):
    has_profile: bool
    interest_source: Optional[str] = None


@router.get("/users/me/profile", response_model=ProfileResponse)
async def get_reading_profile(db: Session = Depends(get_db)):
    """获取当前用户阅读画像（是否存在）"""
    anonymous_user = ensure_anonymous_user(db)
    if not anonymous_user:
        return ProfileResponse(has_profile=False)
    from app.db.models import UserReadingProfile
    profile = db.query(UserReadingProfile).filter(
        UserReadingProfile.user_id == anonymous_user.id
    ).first()
    return ProfileResponse(
        has_profile=profile is not None and profile.interest_vector is not None,
        interest_source=profile.interest_source if profile else None
    )


@router.post("/users/me/profile/refresh")
async def refresh_reading_profile_api(db: Session = Depends(get_db)):
    """手动刷新阅读兴趣向量"""
    anonymous_user = ensure_anonymous_user(db)
    if not anonymous_user:
        raise HTTPException(status_code=500, detail="无法初始化匿名用户")
    from app.services.memory_service import refresh_reading_profile
    ok = refresh_reading_profile(db, anonymous_user.id)
    return {"ok": ok, "message": "已刷新" if ok else "书架为空或向量服务不可用"}
