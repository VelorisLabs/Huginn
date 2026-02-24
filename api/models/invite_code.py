"""
邀请码模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base


class InviteCode(Base):
    """邀请码表"""
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    credits = Column(Integer, default=50, nullable=False)  # 邀请码携带的积分
    max_uses = Column(Integer, default=1, nullable=False)  # 最大使用次数
    used_count = Column(Integer, default=0, nullable=False)  # 已使用次数
    is_active = Column(Boolean, default=True)
    note = Column(String, nullable=True)  # 备注（给谁用的）

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 过期时间，null=永不过期
    created_at = Column(DateTime(timezone=True), server_default=func.now())
