"""
认证相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Cookie
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from typing import Optional

from ..core.database import get_db
from ..core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_access_token
)
from ..core.config import settings
from ..core.deps import get_current_user
from ..models.user import User
from ..schemas.user import UserCreate, UserLogin, UserInDB, Token

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已被使用"
        )
    
    # 创建用户
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    # 查找用户
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账号已被停用"
        )
    
    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # 同时通过 JSON 和 httpOnly Cookie 返回（兼容旧前端 + 新前端）
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )
    return response


@router.get("/me", response_model=UserInDB)
async def read_users_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """使用 refresh_token 获取新的 access_token"""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="缺少刷新令牌")
    
    payload = decode_access_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    
    # 验证用户是否存在且活跃
    result = await db.execute(select(User).where(User.id == int(user_id_str)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已停用")
    
    new_access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    response = JSONResponse(content={"access_token": new_access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/logout")
async def logout():
    """登出，清除 Cookie"""
    response = JSONResponse(content={"detail": "已登出"})
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    return response
