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
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
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
    browser_id = request.browser_id
    
    # 检查是否已存在该浏览器ID的用户
    guest_user = db.query(User).filter(
        User.email == f"{browser_id}@guest.local"
    ).first()
    
    if not guest_user:
        # 创建新的访客用户
        # 使用一个固定的密码hash（访客用户不需要密码）
        dummy_password = "guest_no_password"
        hashed_password = get_password_hash(dummy_password)
        
        guest_user = User(
            email=f"{browser_id}@guest.local",
            username=f"访客_{browser_id[-8:]}",  # 只显示最后8位
            hashed_password=hashed_password,
            agent_name="苏童童"
        )
        db.add(guest_user)
        db.commit()
        db.refresh(guest_user)
    
    # 生成token
    access_token = create_access_token(data={"sub": guest_user.id})
    
    return GuestLoginResponse(
        user=guest_user,
        access_token=access_token,
        token_type="bearer"
    )
