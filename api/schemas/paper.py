"""
论文相关 Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class PaperBase(BaseModel):
    """论文基础信息"""
    title: str
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    keywords: Optional[str] = None


class PaperCreate(PaperBase):
    """创建论文"""
    pass


class PaperInDB(PaperBase):
    """数据库中的论文"""
    id: int
    user_id: int
    theme_id: int
    theme_name: str
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


class TaskCreate(BaseModel):
    """创建任务"""
    task_type: str = Field(..., pattern="^(extract|rescore|cluster)$")
    config: Optional[Dict] = None


class TaskProgress(BaseModel):
    """任务进度"""
    task_id: str
    status: str
    progress: int = Field(..., ge=0, le=100)
    current_step: Optional[str] = None
    total_items: Optional[int] = None
    processed_items: Optional[int] = None


class TaskInDB(BaseModel):
    """数据库中的任务"""
    id: int
    task_id: str
    task_type: str
    status: str
    progress: int
    current_step: Optional[str] = None
    result: Optional[Dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
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
