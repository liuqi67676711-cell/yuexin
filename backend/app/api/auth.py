"""
认证相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db.database import get_db
from app.db.models import User
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    agent_name: str


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    print(f"🔍 收到 token，长度: {len(token) if token else 0}, 前50字符: {token[:50] if token else 'None'}...")
    payload = decode_access_token(token)
    if payload is None:
        print(f"❌ Token 解码失败")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    user_id = payload.get("sub")
    # 确保 user_id 是整数类型（JWT 可能返回字符串）
    if isinstance(user_id, str):
        try:
            user_id = int(user_id)
        except ValueError:
            print(f"❌ user_id 无法转换为整数: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )
    
    print(f"🔍 验证 token，user_id: {user_id}, type: {type(user_id)}")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"❌ 用户不存在: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    print(f"✅ 用户验证成功: user_id={user_id}, username={user.username}")
    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选，未登录时返回None）"""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except:
        return None


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


class UpdateAgentNameRequest(BaseModel):
    agent_name: str


@router.put("/agent-name", response_model=UserResponse)
async def update_agent_name(
    request: UpdateAgentNameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新AI书童名称"""
    if not request.agent_name or len(request.agent_name.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="书童名称不能为空"
        )
    
    current_user.agent_name = request.agent_name.strip()
    db.commit()
    db.refresh(current_user)
    
    return current_user


class GuestLoginRequest(BaseModel):
    browser_id: str


class GuestLoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


@router.post("/guest-login", response_model=GuestLoginResponse)
async def guest_login(
    request: GuestLoginRequest,
    db: Session = Depends(get_db)
):
    """访客登录 - 自动创建账户"""
    try:
        browser_id = request.browser_id
        print(f"🔍 访客登录请求，browser_id: {browser_id[:50]}...")  # 只打印前50个字符
        
        # 生成唯一的 email（限制长度，避免数据库约束问题）
        # email 字段可能有长度限制，使用 hash 缩短
        import hashlib
        email_hash = hashlib.md5(browser_id.encode()).hexdigest()[:16]
        guest_email = f"{email_hash}@guest.local"
        print(f"🔍 生成的 guest_email: {guest_email}")
        
        # 检查是否已存在该浏览器ID的用户
        guest_user = db.query(User).filter(
            User.email == guest_email
        ).first()
        
        if not guest_user:
            # 创建新的访客用户
            # 使用一个固定的密码hash（访客用户不需要密码）
            dummy_password = "guest"
            hashed_password = get_password_hash(dummy_password)
            
            # 生成唯一的 username（使用 email_hash 确保唯一性，限制长度）
            guest_username = f"访客_{email_hash[:8]}"
            
            # 如果用户名已存在，添加随机后缀
            existing_username = db.query(User).filter(User.username == guest_username).first()
            if existing_username:
                import random
                guest_username = f"{guest_username}_{random.randint(1000, 9999)}"
            
            try:
                guest_user = User(
                    email=guest_email,
                    username=guest_username,
                    hashed_password=hashed_password,
                    agent_name="苏童童"
                )
                db.add(guest_user)
                db.commit()
                db.refresh(guest_user)
                print(f"✅ 成功创建访客用户: id={guest_user.id}, email={guest_email}, username={guest_username}")
            except Exception as create_error:
                db.rollback()
                print(f"❌ 创建用户失败: {create_error}")
                import traceback
                traceback.print_exc()
                raise
        else:
            # 如果用户已存在，更新 browser_id 映射（可选：存储在用户表的某个字段）
            pass
    
        # 生成token
        access_token = create_access_token(data={"sub": guest_user.id})
        print(f"🔍 生成的 token，长度: {len(access_token)}, 前50字符: {access_token[:50]}...")
        print(f"🔍 user_id: {guest_user.id}, type: {type(guest_user.id)}")
        
        # 将 User 对象转换为 UserResponse
        user_response = UserResponse(
            id=guest_user.id,
            email=guest_user.email,
            username=guest_user.username,
            agent_name=guest_user.agent_name
        )
        
        return GuestLoginResponse(
            user=user_response,
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = f"访客登录失败: {str(e)}\n{error_trace}"
        print(f"❌ {error_msg}")
        # 同时输出到 stderr，确保日志能捕获
        import sys
        print(error_msg, file=sys.stderr)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"访客登录失败: {str(e)}"
        )
