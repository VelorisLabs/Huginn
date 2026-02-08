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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clustering", tags=["聚类分析"])


# ── 聚类核心逻辑（从 src/clustering.py 移植，适配 DB 数据） ──

STOPWORDS = {
    '的', '了', '是', '在', '和', '与', '等', '对', '为', '以', '及', '或',
    '中', '上', '下', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '个', '种', '类', '方面', '问题', '研究', '分析', '探讨', '论文', '文章',
    '通过', '进行', '提出', '基于', '采用', '针对', '结合', '围绕', '关于',
    '主要', '其中', '同时', '并且', '因此', '然而', '但是', '如何', '什么',
    '可以', '需要', '应该', '能够', '具有', '存在', '包括', '涉及', '体现',
    '不同', '相关', '重要', '有效', '积极', '显著', '明显', '充分', '进一步',
}

TEXT_FIELDS = ['keywords', 'problem', 'conclusion', 'contribution']


def _preprocess_paper(paper: Paper) -> str:
    """合并论文多个文本字段"""
    parts = []
    for field in TEXT_FIELDS:
        val = getattr(paper, field, None)
        if val:
            parts.append(str(val))
    return ' '.join(parts)


def _tokenize(text: str) -> list:
    """jieba 分词 + 过滤停用词"""
    import jieba
    words = jieba.lcut(text)
    return [w for w in words if len(w) >= 2 and not w.isdigit() and w not in STOPWORDS]


def _find_best_k(tfidf_matrix, min_k=3, max_k=8):
    """轮廓系数自动选择最优 K"""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    n_samples = tfidf_matrix.shape[0]
    min_k = max(2, min(min_k, n_samples - 1))
    max_k = max(min_k, min(max_k, n_samples - 1))

    if n_samples < 3:
        return 2

    best_k, best_score = min_k, -1
    for k in range(min_k, max_k + 1):
        if k >= n_samples:
            break
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(tfidf_matrix)
        score = silhouette_score(tfidf_matrix, labels)
        if score > best_score:
            best_score = score
            best_k = k

    return best_k


def _generate_topic_label(cluster_indices, vectorizer, tfidf_matrix, top_n=5):
    """基于 TF-IDF 权重生成话题标签"""
    cluster_tfidf = tfidf_matrix[cluster_indices].toarray()
    mean_tfidf = cluster_tfidf.mean(axis=0)
    feature_names = vectorizer.get_feature_names_out()
    top_indices = mean_tfidf.argsort()[-top_n:][::-1]
    return [feature_names[i] for i in top_indices]


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
            tokenizer=_tokenize,
            token_pattern=None,
            max_features=500,
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(texts)

        task_manager.update_task(task_id, progress=50, current_step="正在寻找最优聚类数")

        # 最优 K
        best_k = _find_best_k(tfidf_matrix)

        task_manager.update_task(task_id, progress=65, current_step=f"K={best_k}，正在执行 KMeans 聚类")

        # KMeans
        kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(tfidf_matrix)

        task_manager.update_task(task_id, progress=80, current_step="正在生成话题标签")

        # 生成每个聚类的话题标签
        topic_labels = {}
        for cid in range(best_k):
            indices = np.where(labels == cid)[0]
            topic_labels[cid] = _generate_topic_label(indices, vectorizer, tfidf_matrix)

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
async def get_clustering_status(task_id: str):
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
