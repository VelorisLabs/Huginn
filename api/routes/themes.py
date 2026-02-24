"""
主题管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List

from ..core.deps import get_current_user, get_db, get_current_workspace
from ..models.user import User
from ..models.workspace import Workspace
from ..models.theme import Theme
from ..models.paper import Paper
from ..schemas.theme import (
    ThemeCreate,
    ThemeUpdate,
    ThemeResponse,
    ThemeBucketsImport,
    ThemeBucketsExport,
    ThemeBucketsGenerate
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def parse_theme_buckets_md(content: str) -> List[dict]:
    """
    解析 theme_buckets.md 文件
    返回主题列表: [{"name": "主题名", "tags": "tag1,tag2", "order": 1}, ...]
    """
    themes = []
    lines = content.split('\n')
    current_theme = None
    current_tags = []
    order = 0
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行和注释
        if not line or line.startswith('>'):
            continue
        
        # 匹配二级标题（主题名称）
        if line.startswith('## '):
            # 保存上一个主题
            if current_theme:
                themes.append({
                    "name": current_theme,
                    "tags": ",".join(current_tags),
                    "order": order
                })
                order += 1
            
            # 开始新主题
            current_theme = line[3:].strip()
            current_tags = []
        
        # 匹配列表项（次级标签）
        elif line.startswith('- '):
            tag = line[2:].strip()
            if tag and current_theme:
                current_tags.append(tag)
    
    # 保存最后一个主题
    if current_theme:
        themes.append({
            "name": current_theme,
            "tags": ",".join(current_tags),
            "order": order
        })
    
    return themes


def generate_theme_buckets_md(themes: List[Theme]) -> str:
    """
    生成 theme_buckets.md 文件内容
    """
    lines = [
        "# 主题桶配置",
        "",
        "> 说明：",
        "> - 一级标题(##)为主题桶名称",
        "> - 列表项为次级标签",
        "> - 修改此文件后重新导入即可更新",
        ""
    ]
    
    for theme in sorted(themes, key=lambda t: t.order):
        lines.append(f"## {theme.name}")
        
        if theme.tags:
            for tag in theme.tags.split(','):
                tag = tag.strip()
                if tag:
                    lines.append(f"- {tag}")
        
        lines.append("")
    
    return "\n".join(lines)


@router.get("", response_model=List[ThemeResponse])
async def get_themes(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """获取当前工作区的所有主题"""
    result = await db.execute(
        select(Theme)
        .where(Theme.user_id == current_user.id, Theme.workspace_id == workspace.id)
        .order_by(Theme.order, Theme.created_at)
    )
    themes = result.scalars().all()
    
    # 单次查询获取所有主题的论文数量（避免 N+1 查询）
    theme_ids = [t.id for t in themes]
    paper_counts = {}
    if theme_ids:
        count_result = await db.execute(
            select(Paper.theme_id, func.count(Paper.id))
            .where(Paper.theme_id.in_(theme_ids), Paper.workspace_id == workspace.id)
            .group_by(Paper.theme_id)
        )
        paper_counts = dict(count_result.all())
    
    theme_responses = []
    for theme in themes:
        theme_responses.append(
            ThemeResponse(
                id=theme.id,
                user_id=theme.user_id,
                name=theme.name,
                tags=theme.tags,
                order=theme.order,
                created_at=theme.created_at,
                updated_at=theme.updated_at,
                paper_count=paper_counts.get(theme.id, 0)
            )
        )
    
    return theme_responses


@router.post("", response_model=ThemeResponse, status_code=status.HTTP_201_CREATED)
async def create_theme(
    theme_data: ThemeCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """创建新主题"""
    # 检查主题名称是否已存在
    result = await db.execute(
        select(Theme).where(
            Theme.user_id == current_user.id,
            Theme.workspace_id == workspace.id,
            Theme.name == theme_data.name
        )
    )
    existing_theme = result.scalar_one_or_none()
    if existing_theme:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该主题名称已存在"
        )
    
    # 创建主题
    theme = Theme(
        user_id=current_user.id,
        workspace_id=workspace.id,
        name=theme_data.name,
        tags=theme_data.tags,
        order=theme_data.order
    )
    
    db.add(theme)
    await db.commit()
    await db.refresh(theme)
    
    return ThemeResponse(
        id=theme.id,
        user_id=theme.user_id,
        name=theme.name,
        tags=theme.tags,
        order=theme.order,
        created_at=theme.created_at,
        updated_at=theme.updated_at,
        paper_count=0
    )


@router.put("/{theme_id}", response_model=ThemeResponse)
async def update_theme(
    theme_id: int,
    theme_data: ThemeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新主题"""
    result = await db.execute(
        select(Theme).where(
            Theme.id == theme_id,
            Theme.user_id == current_user.id
        )
    )
    theme = result.scalar_one_or_none()
    
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="主题不存在"
        )
    
    # 更新字段
    if theme_data.name is not None:
        theme.name = theme_data.name
    if theme_data.tags is not None:
        theme.tags = theme_data.tags
    if theme_data.order is not None:
        theme.order = theme_data.order
    
    await db.commit()
    await db.refresh(theme)
    
    # 如果主题名称变了，更新关联论文的 theme_name
    if theme_data.name is not None:
        await db.execute(
            Paper.__table__.update()
            .where(Paper.theme_id == theme_id)
            .values(theme_name=theme.name)
        )
        await db.commit()
    
    # 统计论文数量
    paper_count_result = await db.execute(
        select(func.count(Paper.id)).where(Paper.theme_id == theme.id)
    )
    paper_count = paper_count_result.scalar() or 0
    
    return ThemeResponse(
        id=theme.id,
        user_id=theme.user_id,
        name=theme.name,
        tags=theme.tags,
        order=theme.order,
        created_at=theme.created_at,
        updated_at=theme.updated_at,
        paper_count=paper_count
    )


@router.delete("/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theme(
    theme_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除主题（如果有论文关联则拒绝）"""
    result = await db.execute(
        select(Theme).where(
            Theme.id == theme_id,
            Theme.user_id == current_user.id
        )
    )
    theme = result.scalar_one_or_none()
    
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="主题不存在"
        )
    
    # 检查是否有论文关联
    paper_count_result = await db.execute(
        select(func.count(Paper.id)).where(Paper.theme_id == theme_id)
    )
    paper_count = paper_count_result.scalar() or 0
    
    if paper_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该主题下还有 {paper_count} 篇论文，无法删除"
        )
    
    await db.delete(theme)
    await db.commit()


@router.post("/import", response_model=List[ThemeResponse])
async def import_theme_buckets(
    import_data: ThemeBucketsImport,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """导入 theme_buckets.md 文件，会覆盖当前工作区的现有主题"""
    # 解析文件
    parsed_themes = parse_theme_buckets_md(import_data.content)
    
    if not parsed_themes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未能解析出任何主题，请检查文件格式"
        )
    
    # 删除当前工作区现有的所有主题（没有论文关联的）
    result = await db.execute(
        select(Theme).where(Theme.user_id == current_user.id, Theme.workspace_id == workspace.id)
    )
    existing_themes = result.scalars().all()
    
    for theme in existing_themes:
        # 检查是否有论文关联
        paper_count_result = await db.execute(
            select(func.count(Paper.id)).where(Paper.theme_id == theme.id)
        )
        paper_count = paper_count_result.scalar() or 0
        
        if paper_count == 0:
            await db.delete(theme)
    
    await db.commit()
    
    # 创建新主题
    new_themes = []
    for theme_data in parsed_themes:
        theme = Theme(
            user_id=current_user.id,
            workspace_id=workspace.id,
            name=theme_data["name"],
            tags=theme_data["tags"],
            order=theme_data["order"]
        )
        db.add(theme)
        new_themes.append(theme)
    
    await db.commit()
    
    # 刷新并返回
    theme_responses = []
    for theme in new_themes:
        await db.refresh(theme)
        theme_responses.append(
            ThemeResponse(
                id=theme.id,
                user_id=theme.user_id,
                name=theme.name,
                tags=theme.tags,
                order=theme.order,
                created_at=theme.created_at,
                updated_at=theme.updated_at,
                paper_count=0
            )
        )
    
    return theme_responses


@router.get("/export", response_model=ThemeBucketsExport)
async def export_theme_buckets(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """导出当前工作区的主题为 theme_buckets.md 格式"""
    result = await db.execute(
        select(Theme)
        .where(Theme.user_id == current_user.id, Theme.workspace_id == workspace.id)
        .order_by(Theme.order, Theme.created_at)
    )
    themes = result.scalars().all()
    
    if not themes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="您还没有创建任何主题"
        )
    
    content = generate_theme_buckets_md(themes)
    
    return ThemeBucketsExport(
        content=content,
        filename="theme_buckets.md"
    )


@router.post("/generate", response_model=ThemeBucketsExport)
async def generate_theme_buckets(
    gen_data: ThemeBucketsGenerate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """AI 自动生成主题桶配置（基于工作区主题/研究领域）"""
    from ..core.llm_client import async_call_llm, init_async_client
    from ..core.credit_service import check_credits, deduct_credits
    from ..models.credit import CreditType

    # 积分检查与扣减
    await check_credits(current_user, CreditType.PAPER_EXTRACT)
    await deduct_credits(db, current_user, CreditType.PAPER_EXTRACT, f"AI生成主题桶: {gen_data.topic}")
    await db.commit()

    # 构造提示词
    prompt = f"""你是一个学术研究领域的专家。请根据给定的研究领域，生成一份主题桶配置文件。

研究领域：{gen_data.topic}
要求生成 {gen_data.bucket_count} 个主题桶。

输出格式要求（严格按照以下 Markdown 格式）：
- 使用 ## 作为主题桶名称
- 每个主题桶下用 - 列出 4-8 个相关的次级标签/关键词
- 主题桶名称应该是该研究领域下的具体研究方向
- 次级标签应该是该方向下的细分关键词，便于论文分类匹配

以下是一个"教育管理"领域的参考示例：

## 教育数智化与智能治理
- 大数据
- 人工智能
- 教育数字化
- 教育信息化
- 数智素养
- 智慧教育
- 数字化转型

## 教育治理与治理体系现代化
- 教育治理体系
- 管理体制
- 治理能力现代化
- 多元共治
- 教育督导

请根据"{gen_data.topic}"领域，生成 {gen_data.bucket_count} 个类似的主题桶。
只输出 Markdown 内容，不要添加任何额外说明、代码块标记或前后缀。"""

    try:
        content = await async_call_llm(
            prompt,
            system_message="你是一个学术研究领域分类专家。请根据用户提供的研究领域，生成结构化的主题桶配置。只输出 Markdown 格式内容，不要添加代码块标记或额外说明。",
            temperature=0.7,
        )
        # 清理可能的代码块标记
        content = content.strip()
        if content.startswith("```markdown"):
            content = content[len("```markdown"):]
        elif content.startswith("```md"):
            content = content[len("```md"):]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
    except Exception as e:
        logger.error(f"AI 生成主题桶失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 生成失败: {str(e)}"
        )

    # 验证生成的内容是否可解析
    parsed = parse_theme_buckets_md(content)
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI 生成的内容格式不正确，请重试"
        )

    return ThemeBucketsExport(
        content=content,
        filename="theme_buckets.md"
    )
