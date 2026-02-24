"""
聚类分析 API
基于 TF-IDF + 余弦相似度 + KMeans，不依赖 Celery/Redis
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..core.database import get_db
from ..core.deps import get_current_active_user, get_current_workspace
from ..core.task_manager import task_manager, TaskStatus
from ..models.user import User
from ..models.paper import Paper
from ..models.workspace import Workspace
from shared.clustering_core import STOPWORDS, tokenize, find_best_k, generate_topic_label

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clustering", tags=["聚类分析"])


# ── 聚类核心逻辑（共享模块 + 本地适配） ──

TEXT_FIELDS = ['keywords', 'problem', 'conclusion', 'contribution']


def _preprocess_paper(paper: Paper) -> str:
    """合并论文多个文本字段"""
    parts = []
    for field in TEXT_FIELDS:
        val = getattr(paper, field, None)
        if val:
            parts.append(str(val))
    return ' '.join(parts)



# ── 后台聚类协程 ──

async def _run_clustering_async(task_id: str, user_id: int, workspace_id: int):
    """后台异步执行聚类分析"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from ..core.database import async_session_maker

    task_manager.update_task(task_id, progress=5, current_step="正在加载论文数据")

    async with async_session_maker() as db:
        result = await db.execute(
            select(Paper).where(
                Paper.user_id == user_id,
                Paper.workspace_id == workspace_id
            )
        )
        papers = result.scalars().all()

        if len(papers) < 3:
            raise ValueError(f"论文数量不足（当前 {len(papers)} 篇），至少需要 3 篇才能聚类")

        task_manager.update_task(task_id, progress=15, current_step=f"正在预处理 {len(papers)} 篇论文文本")

        # 文本预处理
        texts = [_preprocess_paper(p) for p in papers]

        task_manager.update_task(task_id, progress=30, current_step="正在 TF-IDF 向量化")

        # TF-IDF
        vectorizer = TfidfVectorizer(
            tokenizer=tokenize,
            token_pattern=None,
            max_features=500,
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(texts)

        task_manager.update_task(task_id, progress=50, current_step="正在寻找最优聚类数")

        # 最优 K
        best_k = find_best_k(tfidf_matrix)

        task_manager.update_task(task_id, progress=65, current_step=f"K={best_k}，正在执行 KMeans 聚类")

        # KMeans
        kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(tfidf_matrix)

        task_manager.update_task(task_id, progress=80, current_step="正在生成话题标签")

        # 生成每个聚类的话题标签
        topic_labels = {}
        for cid in range(best_k):
            indices = np.where(labels == cid)[0]
            topic_labels[cid] = generate_topic_label(indices, vectorizer, tfidf_matrix)

        task_manager.update_task(task_id, progress=90, current_step="正在保存聚类结果到数据库")

        # 保存到 DB
        for idx, paper in enumerate(papers):
            cid = int(labels[idx])
            paper.cluster_id = cid
            paper.cluster_topic = ', '.join(topic_labels[cid][:3])

        await db.commit()

        # 构建返回结果
        clusters_summary = []
        for cid in range(best_k):
            mask = labels == cid
            cluster_paper_ids = [papers[i].id for i in range(len(papers)) if labels[i] == cid]
            clusters_summary.append({
                "cluster_id": cid,
                "topic_keywords": topic_labels[cid],
                "paper_count": int(mask.sum()),
                "paper_ids": cluster_paper_ids,
            })

        return {
            "cluster_count": best_k,
            "paper_count": len(papers),
            "clusters": clusters_summary,
        }


# ── API 端点 ──

@router.post("/run")
async def run_clustering(
    current_user: User = Depends(get_current_active_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    """触发聚类分析（异步后台任务）"""
    task_id = task_manager.create_task()
    task_manager.submit_async_task(
        task_id,
        _run_clustering_async,
        current_user.id,
        workspace.id
    )
    return {"task_id": task_id, "message": "聚类分析已启动"}


@router.get("/status/{task_id}")
async def get_clustering_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """查询聚类任务进度"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "progress": task.progress,
        "current_step": task.current_step,
        "result": task.result,
        "error": task.error,
    }


@router.get("/results")
async def get_clustering_results(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    """获取当前工作区的聚类结果（按 cluster 分组）"""
    base_filter = [
        Paper.user_id == current_user.id,
        Paper.workspace_id == workspace.id,
        Paper.cluster_id.isnot(None),
    ]

    # 获取有聚类结果的论文
    result = await db.execute(
        select(Paper).where(*base_filter).order_by(Paper.cluster_id, Paper.overall_score.desc())
    )
    papers = result.scalars().all()

    if not papers:
        return {"has_results": False, "clusters": [], "total_papers": 0}

    # 按 cluster_id 分组
    clusters_map = {}
    for p in papers:
        cid = p.cluster_id
        if cid not in clusters_map:
            clusters_map[cid] = {
                "cluster_id": cid,
                "topic_keywords": (p.cluster_topic or '').split(', '),
                "papers": [],
            }
        clusters_map[cid]["papers"].append({
            "id": p.id,
            "title": p.title,
            "authors": p.authors,
            "year": p.year,
            "venue": p.venue,
            "keywords": p.keywords,
            "overall_score": p.overall_score,
            "theme_name": p.theme_name,
            "cluster_topic": p.cluster_topic,
        })

    clusters = sorted(clusters_map.values(), key=lambda c: c["cluster_id"])
    for c in clusters:
        c["paper_count"] = len(c["papers"])

    # 统计未聚类论文数
    total_result = await db.execute(
        select(func.count(Paper.id)).where(
            Paper.user_id == current_user.id,
            Paper.workspace_id == workspace.id,
        )
    )
    total = total_result.scalar() or 0
    clustered = len(papers)

    return {
        "has_results": True,
        "cluster_count": len(clusters),
        "total_papers": total,
        "clustered_papers": clustered,
        "clusters": clusters,
    }
