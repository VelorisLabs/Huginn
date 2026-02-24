"""
工作区管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from ..core.database import get_db
from ..core.deps import get_current_user
from ..core.config import load_scenario_weights
from ..models.user import User
from ..models.workspace import Workspace
from ..models.theme import Theme
from ..models.paper import Paper
from ..schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
)

router = APIRouter()


# ── CRUD ─────────────────────────────────────────────────────

@router.get("", response_model=List[WorkspaceListResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有工作区"""
    result = await db.execute(
        select(Workspace)
        .where(Workspace.user_id == current_user.id)
        .order_by(Workspace.order, Workspace.created_at)
    )
    workspaces = result.scalars().all()

    # 批量统计主题数和论文数
    ws_ids = [w.id for w in workspaces]
    theme_counts: dict[int, int] = {}
    paper_counts: dict[int, int] = {}
    if ws_ids:
        tc = await db.execute(
            select(Theme.workspace_id, func.count(Theme.id))
            .where(Theme.workspace_id.in_(ws_ids))
            .group_by(Theme.workspace_id)
        )
        theme_counts = dict(tc.all())
        pc = await db.execute(
            select(Paper.workspace_id, func.count(Paper.id))
            .where(Paper.workspace_id.in_(ws_ids))
            .group_by(Paper.workspace_id)
        )
        paper_counts = dict(pc.all())

    return [
        WorkspaceListResponse(
            id=w.id,
            name=w.name,
            description=w.description,
            is_default=w.is_default,
            order=w.order,
            theme_count=theme_counts.get(w.id, 0),
            paper_count=paper_counts.get(w.id, 0),
        )
        for w in workspaces
    ]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个工作区详情（含配置）"""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.user_id == current_user.id,
        )
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="工作区不存在")

    # 统计
    tc = await db.execute(
        select(func.count(Theme.id)).where(Theme.workspace_id == workspace.id)
    )
    pc = await db.execute(
        select(func.count(Paper.id)).where(Paper.workspace_id == workspace.id)
    )

    return WorkspaceResponse(
        id=workspace.id,
        user_id=workspace.user_id,
        name=workspace.name,
        description=workspace.description,
        scenario_weights=workspace.scenario_weights,
        prompt_config=workspace.prompt_config,
        is_default=workspace.is_default,
        order=workspace.order,
        theme_count=tc.scalar() or 0,
        paper_count=pc.scalar() or 0,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新工作区"""
    # 名称唯一性
    existing = await db.execute(
        select(Workspace).where(
            Workspace.user_id == current_user.id,
            Workspace.name == data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该工作区名称已存在")

    # 如果没有提供场景权重，使用全局默认
    weights = data.scenario_weights
    if weights is None:
        weights = load_scenario_weights()

    workspace = Workspace(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        scenario_weights=weights,
        prompt_config=data.prompt_config,
        is_default=False,
        order=0,
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    return WorkspaceResponse(
        id=workspace.id,
        user_id=workspace.user_id,
        name=workspace.name,
        description=workspace.description,
        scenario_weights=workspace.scenario_weights,
        prompt_config=workspace.prompt_config,
        is_default=workspace.is_default,
        order=workspace.order,
        theme_count=0,
        paper_count=0,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新工作区"""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.user_id == current_user.id,
        )
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="工作区不存在")

    if data.name is not None:
        workspace.name = data.name
    if data.description is not None:
        workspace.description = data.description
    if data.scenario_weights is not None:
        workspace.scenario_weights = data.scenario_weights
    if data.prompt_config is not None:
        workspace.prompt_config = data.prompt_config
    if data.order is not None:
        workspace.order = data.order

    await db.commit()
    await db.refresh(workspace)

    tc = await db.execute(
        select(func.count(Theme.id)).where(Theme.workspace_id == workspace.id)
    )
    pc = await db.execute(
        select(func.count(Paper.id)).where(Paper.workspace_id == workspace.id)
    )

    return WorkspaceResponse(
        id=workspace.id,
        user_id=workspace.user_id,
        name=workspace.name,
        description=workspace.description,
        scenario_weights=workspace.scenario_weights,
        prompt_config=workspace.prompt_config,
        is_default=workspace.is_default,
        order=workspace.order,
        theme_count=tc.scalar() or 0,
        paper_count=pc.scalar() or 0,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除工作区（默认工作区不可删除，有论文的工作区需确认）"""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.user_id == current_user.id,
        )
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="工作区不存在")

    if workspace.is_default:
        raise HTTPException(status_code=400, detail="默认工作区不可删除")

    pc = await db.execute(
        select(func.count(Paper.id)).where(Paper.workspace_id == workspace.id)
    )
    paper_count = pc.scalar() or 0
    if paper_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该工作区下还有 {paper_count} 篇论文，请先迁移或删除论文"
        )

    await db.delete(workspace)
    await db.commit()


@router.post("/{workspace_id}/activate")
async def activate_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """切换用户的活跃工作区"""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.user_id == current_user.id,
        )
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="工作区不存在")

    current_user.active_workspace_id = workspace.id
    await db.commit()

    return {"message": "已切换到工作区", "workspace_id": workspace.id, "workspace_name": workspace.name}
