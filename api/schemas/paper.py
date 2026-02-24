"""
论文相关 Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class PaperInDB(BaseModel):
    """数据库中的论文"""
    id: int
    user_id: int
    theme_id: int
    theme_name: str
    title: str
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    keywords: Optional[str] = None
    domain_tags: Optional[str] = None
    paper_type: Optional[str] = None
    problem: Optional[str] = None
    methodology: Optional[str] = None
    conclusion: Optional[str] = None
    contribution: Optional[str] = None
    implementation_path: Optional[str] = None
    score_rigor: Optional[float] = None
    score_innovation: Optional[float] = None
    score_practicality: Optional[float] = None
    score_impact: Optional[float] = None
    score_readability: Optional[float] = None
    overall_score: Optional[float] = None
    recommendation_level: Optional[str] = None
    scenario_scores: Optional[Dict] = None
    cluster_id: Optional[int] = None
    cluster_topic: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """文件上传响应"""
    filename: str
    file_path: str
    file_size: int
    task_id: Optional[str] = None


class ExportRequest(BaseModel):
    """数据导出请求"""
    paper_ids: Optional[List[int]] = None
    format: str = Field(..., pattern="^(csv|json|excel)$")
    include_scenarios: bool = True
