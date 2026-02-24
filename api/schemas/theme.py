"""
主题相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ThemeBase(BaseModel):
    """主题基础模型"""
    name: str = Field(..., description="主题名称")
    tags: Optional[str] = Field(None, description="次级标签，逗号分隔")
    order: int = Field(0, description="排序顺序")


class ThemeCreate(ThemeBase):
    """创建主题"""
    pass


class ThemeUpdate(BaseModel):
    """更新主题"""
    name: Optional[str] = None
    tags: Optional[str] = None
    order: Optional[int] = None


class ThemeInDB(ThemeBase):
    """数据库中的主题"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ThemeResponse(ThemeInDB):
    """主题响应"""
    paper_count: Optional[int] = 0


class ThemeBucketsImport(BaseModel):
    """导入 theme_buckets.md"""
    content: str = Field(..., description="theme_buckets.md 文件内容")


class ThemeBucketsExport(BaseModel):
    """导出 theme_buckets.md"""
    content: str
    filename: str = "theme_buckets.md"


class ThemeBucketsGenerate(BaseModel):
    """AI 生成主题桶请求"""
    topic: str = Field(..., description="研究领域/工作区名称，例如'教育心理学'")
    bucket_count: int = Field(8, ge=3, le=15, description="生成的主题桶数量")
