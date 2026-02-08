"""
数据导出 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pandas as pd
import json
import os
from pathlib import Path
from typing import Optional, List
import tempfile

from ..core.database import get_db
from ..core.deps import get_current_active_user
from ..models.user import User
from ..models.paper import Paper
from ..schemas.paper import ExportRequest

router = APIRouter(prefix="/export", tags=["数据导出"])


@router.post("/papers")
async def export_papers(
    export_data: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """导出论文数据"""
    # 查询论文
    query = select(Paper).where(Paper.user_id == current_user.id)
    
    if export_data.paper_ids:
        query = query.where(Paper.id.in_(export_data.paper_ids))
    
    result = await db.execute(query)
    papers = result.scalars().all()
    
    if not papers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到论文数据"
        )
    
    # 转换为 DataFrame
    data = []
    for paper in papers:
        row = {
            "ID": paper.id,
            "标题": paper.title,
            "作者": paper.authors,
            "年份": paper.year,
            "期刊": paper.venue,
            "关键词": paper.keywords,
            "领域标签": paper.domain_tags,
            "论文类型": paper.paper_type,
            "研究问题": paper.problem,
            "研究方法": paper.methodology,
            "核心结论": paper.conclusion,
            "主要贡献": paper.contribution,
            "学术严谨度": paper.score_rigor,
            "创新程度": paper.score_innovation,
            "实用价值": paper.score_practicality,
            "影响范围": paper.score_impact,
            "可读性": paper.score_readability,
            "综合评分": paper.overall_score,
            "推荐等级": paper.recommendation_level,
        }
        
        # 添加场景评分
        if export_data.include_scenarios and paper.scenario_scores:
            for scenario, score in paper.scenario_scores.items():
                row[f"{scenario}_评分"] = score
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # 根据格式导出
    temp_dir = Path(tempfile.gettempdir())
    
    if export_data.format == "csv":
        file_path = temp_dir / f"papers_{current_user.id}.csv"
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        media_type = "text/csv"
        
    elif export_data.format == "excel":
        file_path = temp_dir / f"papers_{current_user.id}.xlsx"
        df.to_excel(file_path, index=False, engine='openpyxl')
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
    elif export_data.format == "json":
        file_path = temp_dir / f"papers_{current_user.id}.json"
        df.to_json(file_path, orient='records', force_ascii=False, indent=2)
        media_type = "application/json"
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的导出格式"
        )
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name,
        background=BackgroundTask(os.unlink, str(file_path))
    )
