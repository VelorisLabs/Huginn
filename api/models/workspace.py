"""
工作区（Workspace）数据模型
"""
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..core.database import Base


class Workspace(Base):
    """工作区模型 — 主题桶的顶层容器，每个工作区有独立的评分权重和 prompt 配置"""
    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_workspace_user_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 每个工作区独立的场景评分权重 (JSON, 同 scenario_weights.json 的 scenarios 结构)
    scenario_weights = Column(JSON, nullable=True)

    # 每个工作区独立的 LLM / prompt 配置 (JSON)
    # 可包含: extraction_prompt, deep_analysis_prompt, llm_model, llm_temperature 等
    prompt_config = Column(JSON, nullable=True)

    is_default = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    user = relationship("User", back_populates="workspaces")
    themes = relationship("Theme", back_populates="workspace", cascade="all, delete-orphan")
