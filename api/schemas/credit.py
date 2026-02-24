"""
积分相关 Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreditAdjust(BaseModel):
    """管理员调整积分"""
    amount: int = Field(..., description="调整数量（正数增加，负数扣减）")
    description: Optional[str] = Field(default=None, max_length=200, description="调整原因")


class CreditTransactionOut(BaseModel):
    """积分流水输出"""
    id: int
    amount: int
    type: str
    balance_after: int
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CreditBalance(BaseModel):
    """积分余额"""
    credits: int
    user_id: int
