"""
用户相关 Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础信息"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """用户创建"""
    password: str = Field(..., min_length=6)
    invite_code: str = Field(..., min_length=1, max_length=32, description="邀请码")


class UserLogin(BaseModel):
    """用户登录"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """用户更新"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """数据库中的用户"""
    id: int
    is_active: bool
    is_superuser: bool
    credits: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT 令牌"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据"""
    user_id: Optional[int] = None
