"""
积分交易模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class CreditType(str, enum.Enum):
    """积分变动类型"""
    INVITE_REGISTER = "invite_register"  # 邀请码注册赠送
    ADMIN_ADJUST = "admin_adjust"        # 管理员手动调整
    PAPER_EXTRACT = "paper_extract"      # 论文提取消耗
    DEEP_ANALYSIS = "deep_analysis"      # 深度分析消耗


class CreditTransaction(Base):
    """积分流水表"""
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # 正数=增加，负数=消耗
    type = Column(SAEnum(CreditType), nullable=False)
    balance_after = Column(Integer, nullable=False)  # 变动后余额
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
