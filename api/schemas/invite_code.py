"""
邀请码相关 Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InviteCodeCreate(BaseModel):
    """创建邀请码"""
    credits: int = Field(default=50, ge=1, le=9999, description="携带积分")
    max_uses: int = Field(default=1, ge=1, le=100, description="最大使用次数")
    note: Optional[str] = Field(default=None, max_length=200, description="备注")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")


class InviteCodeOut(BaseModel):
    """邀请码输出"""
    id: int
    code: str
    credits: int
    max_uses: int
    used_count: int
    is_active: bool
    note: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
