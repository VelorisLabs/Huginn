"""
论文相关模型
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Paper(Base):
    """论文表"""
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    theme_id = Column(Integer, ForeignKey("themes.id"), nullable=False, index=True)
    theme_name = Column(String, nullable=False)
    
    # 基本信息
    title = Column(String, nullable=False)
    authors = Column(String)
    year = Column(Integer)
    venue = Column(String)
    keywords = Column(Text)
    
    # 领域和类型
    domain_tags = Column(String)
    paper_type = Column(String)
    
    # 研究内容
    problem = Column(Text)
    methodology = Column(Text)
    conclusion = Column(Text)
    contribution = Column(Text)
    implementation_path = Column(Text)  # 具体实现路径
    
    # 5维评分
    score_rigor = Column(Float)
    score_innovation = Column(Float)
    score_practicality = Column(Float)
    score_impact = Column(Float)
    score_readability = Column(Float)
    overall_score = Column(Float)
    recommendation_level = Column(String)
    
    # 场景评分（JSON存储）
    scenario_scores = Column(JSON)
    
    # 深度分析（精读报告，按需生成后缓存）
    deep_analysis = Column(JSON)
    
    # 聚类信息
    cluster_id = Column(Integer)
    cluster_topic = Column(String)
    
    # 文件信息
    file_path = Column(String)
    original_filename = Column(String)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", backref="papers")
    theme = relationship("Theme", back_populates="papers")
