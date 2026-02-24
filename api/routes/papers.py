"""
论文管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List
from pathlib import Path
import os
import logging
import base64

from ..core.database import get_db
from ..core.deps import get_current_active_user, get_current_workspace
from ..core.credit_service import check_credits, deduct_credits
from ..models.user import User
from ..models.workspace import Workspace
from ..models.paper import Paper
from ..models.credit import CreditType
from ..schemas.paper import PaperInDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["论文管理"])


@router.get("", response_model=List[PaperInDB])
async def list_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    year: Optional[int] = None,
    cluster_id: Optional[int] = None,
    min_score: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    """获取论文列表（支持筛选，按工作区过滤）"""
    query = select(Paper).where(Paper.user_id == current_user.id, Paper.workspace_id == workspace.id)
    
    # 搜索
    if search:
        query = query.where(
            or_(
                Paper.title.contains(search),
                Paper.keywords.contains(search),
                Paper.authors.contains(search)
            )
        )
    
    # 年份筛选
    if year:
        query = query.where(Paper.year == year)
    
    # 聚类筛选
    if cluster_id is not None:
        query = query.where(Paper.cluster_id == cluster_id)
    
    # 评分筛选
    if min_score is not None:
        query = query.where(Paper.overall_score >= min_score)
    
    # 排序和分页
    query = query.order_by(Paper.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    papers = result.scalars().all()
    
    return papers


@router.get("/{paper_id}", response_model=PaperInDB)
async def get_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单篇论文详情"""
    result = await db.execute(
        select(Paper).where(
            Paper.id == paper_id,
            Paper.user_id == current_user.id
        )
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在"
        )
    
    return paper


@router.get("/{paper_id}/pdf")
async def get_paper_pdf(
    paper_id: int,
    token: Optional[str] = Query(None, description="JWT token (用于浏览器直接打开)"),
    stream: bool = Query(False, description="以 octet-stream 返回，绕过下载管理器拦截"),
    db: AsyncSession = Depends(get_db),
):
    """获取论文 PDF 文件（通过 query token 认证，便于浏览器直接打开）"""
    from ..core.security import decode_access_token

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少认证 token")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 token")

    user_result = await db.execute(select(User).where(User.id == int(user_id_str)))
    current_user = user_result.scalar_one_or_none()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    result = await db.execute(
        select(Paper).where(
            Paper.id == paper_id,
            Paper.user_id == current_user.id
        )
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在"
        )
    
    if not paper.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该论文没有关联的 PDF 文件"
        )
    
    file_path = Path(paper.file_path.strip())
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF 文件不存在，可能已被删除"
        )
    
    # 构造有意义的文件名: {paper_id}_{title}.pdf
    from urllib.parse import quote
    import re as _re
    title = paper.title or "paper"
    # 清理标题中不适合做文件名的字符
    safe_title = _re.sub(r'[\\/:*?"<>|\r\n]+', '_', title).strip('_. ')
    # 截断过长标题
    if len(safe_title) > 80:
        safe_title = safe_title[:80].rstrip('_. ')
    raw_name = f"{paper_id}_{safe_title}.pdf"
    encoded_name = quote(raw_name)

    if stream:
        # 以 octet-stream 返回，前端通过 fetch 获取后自行构造 PDF blob
        # 避免被 IDM 等下载管理器根据 Content-Type 拦截
        disposition = f"inline; filename*=UTF-8''{encoded_name}"
        return FileResponse(
            path=str(file_path),
            media_type="application/octet-stream",
            headers={"Content-Disposition": disposition},
        )

    # Content-Disposition: inline 让浏览器直接展示 PDF 而非下载
    disposition = f"inline; filename*=UTF-8''{encoded_name}"
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": disposition},
    )


@router.get("/{paper_id}/pdf-data")
async def get_paper_pdf_data(
    paper_id: int,
    token: Optional[str] = Query(None, description="JWT token (用于浏览器直接打开)"),
    db: AsyncSession = Depends(get_db),
):
    """以 base64 JSON 返回 PDF 数据，绕过 IDM 等下载管理器对 fetch/XHR 的拦截"""
    from ..core.security import decode_access_token

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少认证 token")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 token")

    user_result = await db.execute(select(User).where(User.id == int(user_id_str)))
    current_user = user_result.scalar_one_or_none()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    result = await db.execute(
        select(Paper).where(
            Paper.id == paper_id,
            Paper.user_id == current_user.id
        )
    )
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")

    if not paper.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该论文没有关联的 PDF 文件")

    file_path = Path(paper.file_path.strip())
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF 文件不存在，可能已被删除")

    pdf_bytes = file_path.read_bytes()
    pdf_base64 = base64.b64encode(pdf_bytes).decode("ascii")

    return JSONResponse(content={"data": pdf_base64, "filename": f"{paper_id}_{paper.title or 'paper'}.pdf"})


@router.get("/{paper_id}/deep-analysis")
async def get_deep_analysis(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取论文深度分析（如果已缓存）"""
    result = await db.execute(
        select(Paper).where(
            Paper.id == paper_id,
            Paper.user_id == current_user.id
        )
    )
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")

    if not paper.deep_analysis:
        return {"status": "not_generated", "data": None}

    return {"status": "ready", "data": paper.deep_analysis}


@router.post("/{paper_id}/deep-analysis")
async def generate_deep_analysis(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """按需生成论文深度精读分析（首次生成后缓存）"""
    result = await db.execute(
        select(Paper).where(
            Paper.id == paper_id,
            Paper.user_id == current_user.id
        )
    )
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")

    # 已有缓存直接返回（不扣积分）
    if paper.deep_analysis:
        return {"status": "ready", "data": paper.deep_analysis}

    # 积分检查与扣减（仅首次生成时扣费，先提交确保扣费不可逆）
    await check_credits(current_user, CreditType.DEEP_ANALYSIS)
    await deduct_credits(db, current_user, CreditType.DEEP_ANALYSIS, f"深度分析: {paper.title or paper_id}")
    await db.commit()

    # 需要 PDF 文本来做深度分析
    if not paper.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该论文没有关联的 PDF 文件，无法进行深度分析"
        )

    file_path = Path(paper.file_path.strip())
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF 文件不存在，无法进行深度分析"
        )

    try:
        # 1. 提取 PDF 文本
        from ..core.pdf_extractor import extract_pdf_text
        pdf_text = extract_pdf_text(file_path)

        # 2. 读取深度分析 prompt
        from ..core.config import settings as app_settings
        with open(app_settings.PROMPT_DEEP_ANALYSIS_FILE, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # 3. 填充已有速览信息到 prompt
        prompt_template = prompt_template.replace("{title}", paper.title or "")
        prompt_template = prompt_template.replace("{problem}", paper.problem or "")
        prompt_template = prompt_template.replace("{methodology}", paper.methodology or "")
        prompt_template = prompt_template.replace("{conclusion}", paper.conclusion or "")

        full_prompt = f"{prompt_template}\n\n论文全文：\n{pdf_text}"

        # 4. 异步调用 LLM
        from ..core.llm_client import async_call_llm, clean_json_response
        import json

        response = await async_call_llm(full_prompt)
        clean_response = clean_json_response(response)
        deep_data = json.loads(clean_response)

        # 5. 缓存到数据库
        paper.deep_analysis = deep_data
        await db.commit()

        return {"status": "ready", "data": deep_data}

    except json.JSONDecodeError as e:
        logger.error(f"深度分析 JSON 解析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI 分析结果解析失败，请重试"
        )
    except Exception as e:
        logger.error(f"深度分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"深度分析失败: {str(e)}"
        )


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除论文（同时删除物理文件）"""
    result = await db.execute(
        select(Paper).where(
            Paper.id == paper_id,
            Paper.user_id == current_user.id
        )
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在"
        )
    
    # 删除物理文件（如果存在）
    if paper.file_path:
        try:
            file_path = Path(paper.file_path)
            if file_path.exists():
                os.remove(file_path)
                logger.info(f"已删除文件: {file_path}")
        except Exception as e:
            logger.error(f"删除文件失败: {paper.file_path}, 错误: {e}")
            # 即使文件删除失败，也继续删除数据库记录
    
    # 删除数据库记录
    await db.delete(paper)
    await db.commit()
    
    return {"message": "删除成功"}


@router.get("/stats/overview")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    """获取统计数据（按工作区过滤）"""
    base_filter = [Paper.user_id == current_user.id, Paper.workspace_id == workspace.id]
    
    # 总论文数
    total_result = await db.execute(
        select(func.count(Paper.id)).where(*base_filter)
    )
    total = total_result.scalar()
    
    # 平均分
    avg_result = await db.execute(
        select(func.avg(Paper.overall_score)).where(*base_filter)
    )
    avg_score = avg_result.scalar() or 0
    
    # 聚类数
    cluster_result = await db.execute(
        select(func.count(func.distinct(Paper.cluster_id))).where(
            *base_filter,
            Paper.cluster_id.isnot(None)
        )
    )
    cluster_count = cluster_result.scalar() or 0
    
    # 年份分布
    year_result = await db.execute(
        select(Paper.year, func.count(Paper.id))
        .where(*base_filter)
        .group_by(Paper.year)
        .order_by(Paper.year.desc())
    )
    year_distribution = {year: count for year, count in year_result.all() if year}
    
    return {
        "total_papers": total,
        "avg_score": round(avg_score, 2),
        "cluster_count": cluster_count,
        "year_distribution": year_distribution
    }
