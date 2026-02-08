"""
主题（Theme）数据模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..core.database import Base


class Theme(Base):
    """主题模型"""
    __tablename__ = "themes"
    __table_args__ = (
        UniqueConstraint("user_id", "workspace_id", "name", name="uq_theme_workspace_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    tags = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="themes")
    workspace = relationship("Workspace", back_populates="themes")
    papers = relationship("Paper", back_populates="theme")

    def __repr__(self):
        return f"<Theme(id={self.id}, name={self.name})>"
