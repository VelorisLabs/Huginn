"""
工作区相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class WorkspaceBase(BaseModel):
    """工作区基础模型"""
    name: str = Field(..., description="工作区名称", max_length=200)
    description: Optional[str] = Field(None, description="工作区描述")


class WorkspaceCreate(WorkspaceBase):
    """创建工作区"""
    scenario_weights: Optional[Dict[str, Any]] = Field(None, description="场景评分权重配置")
    prompt_config: Optional[Dict[str, Any]] = Field(None, description="LLM / Prompt 配置")


class WorkspaceUpdate(BaseModel):
    """更新工作区"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    scenario_weights: Optional[Dict[str, Any]] = None
    prompt_config: Optional[Dict[str, Any]] = None
    order: Optional[int] = None


class WorkspaceResponse(WorkspaceBase):
    """工作区响应"""
    id: int
    user_id: int
    scenario_weights: Optional[Dict[str, Any]] = None
    prompt_config: Optional[Dict[str, Any]] = None
    is_default: bool = False
    order: int = 0
    theme_count: int = 0
    paper_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    """工作区列表响应（轻量版，不含配置详情）"""
    id: int
    name: str
    description: Optional[str] = None
    is_default: bool = False
    order: int = 0
    theme_count: int = 0
    paper_count: int = 0

    class Config:
        from_attributes = True
