"""
管理员 API — 邀请码管理 + 积分管理 + 用户管理
"""
import secrets
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..core.database import get_db
from ..core.deps import get_current_user
from ..core.credit_service import add_credits
from ..models.user import User
from ..models.invite_code import InviteCode
from ..models.credit import CreditTransaction, CreditType
from ..schemas.invite_code import InviteCodeCreate, InviteCodeOut
from ..schemas.credit import CreditAdjust, CreditTransactionOut

logger = logging.getLogger(__name__)

router = APIRouter(tags=["管理员"])


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# ── 邀请码管理 ──

@router.post("/invite-codes", response_model=InviteCodeOut)
async def create_invite_code(
    data: InviteCodeCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """生成邀请码"""
    code_str = secrets.token_urlsafe(8)[:12].upper()

    invite = InviteCode(
        code=code_str,
        credits=data.credits,
        max_uses=data.max_uses,
        note=data.note,
        expires_at=data.expires_at,
        created_by=admin.id,
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    logger.info(f"管理员 {admin.id} 创建邀请码 {code_str}（{data.credits} 积分，{data.max_uses} 次）")
    return invite


@router.get("/invite-codes", response_model=list[InviteCodeOut])
async def list_invite_codes(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """列出所有邀请码"""
    result = await db.execute(
        select(InviteCode).order_by(InviteCode.created_at.desc())
    )
    return list(result.scalars().all())


@router.patch("/invite-codes/{code_id}")
async def toggle_invite_code(
    code_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """启用/停用邀请码"""
    result = await db.execute(select(InviteCode).where(InviteCode.id == code_id))
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="邀请码不存在")

    invite.is_active = not invite.is_active
    await db.commit()
    return {"id": code_id, "is_active": invite.is_active}


@router.delete("/invite-codes/{code_id}")
async def delete_invite_code(
    code_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """删除邀请码"""
    result = await db.execute(select(InviteCode).where(InviteCode.id == code_id))
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="邀请码不存在")

    await db.delete(invite)
    await db.commit()
    return {"detail": "已删除"}


# ── 用户管理 ──

@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """列出所有用户"""
    result = await db.execute(
        select(User).order_by(User.id)
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "credits": u.credits,
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.post("/users/{user_id}/credits")
async def adjust_user_credits(
    user_id: int,
    data: CreditAdjust,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """管理员调整用户积分"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    desc = data.description or f"管理员 {admin.username} 手动调整"
    txn = await add_credits(db, user, data.amount, CreditType.ADMIN_ADJUST, desc)
    await db.commit()

    logger.info(f"管理员 {admin.id} 调整用户 {user_id} 积分 {data.amount:+d}，余额 {user.credits}")
    return {
        "user_id": user_id,
        "credits": user.credits,
        "adjusted": data.amount,
        "description": desc,
    }


@router.patch("/users/{user_id}/toggle")
async def toggle_user_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """启用/禁用用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_superuser:
        raise HTTPException(status_code=400, detail="不能禁用管理员账户")

    user.is_active = not user.is_active
    await db.commit()
    logger.info(f"管理员 {admin.id} {'启用' if user.is_active else '禁用'}用户 {user_id}")
    return {"id": user_id, "is_active": user.is_active}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """删除用户及其所有数据（论文、主题、工作区、积分流水）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_superuser:
        raise HTTPException(status_code=400, detail="不能删除管理员账户")

    from ..models.paper import Paper
    from ..models.theme import Theme
    from ..models.workspace import Workspace

    # 删除用户的论文（物理文件 + 记录）
    papers_result = await db.execute(select(Paper).where(Paper.user_id == user_id))
    papers = papers_result.scalars().all()
    for paper in papers:
        if paper.file_path:
            from pathlib import Path
            try:
                fp = Path(paper.file_path)
                if fp.exists():
                    fp.unlink()
            except Exception:
                pass
        await db.delete(paper)

    # 删除积分流水
    await db.execute(
        CreditTransaction.__table__.delete().where(CreditTransaction.user_id == user_id)
    )

    # 删除主题
    await db.execute(Theme.__table__.delete().where(Theme.user_id == user_id))

    # 删除工作区
    await db.execute(Workspace.__table__.delete().where(Workspace.user_id == user_id))

    # 删除用户
    await db.delete(user)
    await db.commit()

    logger.info(f"管理员 {admin.id} 删除用户 {user_id}（{user.email}），包含 {len(papers)} 篇论文")
    return {"detail": f"用户 {user.email} 及其所有数据已删除", "papers_deleted": len(papers)}


@router.post("/users/{user_id}/reset")
async def reset_user(
    user_id: int,
    data: CreditAdjust,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """重置用户积分到指定值"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    old_credits = user.credits
    new_credits = data.amount  # 这里 amount 用作目标值
    diff = new_credits - old_credits
    user.credits = new_credits

    desc = data.description or f"管理员 {admin.username} 重置积分: {old_credits} → {new_credits}"
    txn = CreditTransaction(
        user_id=user.id,
        amount=diff,
        type=CreditType.ADMIN_ADJUST,
        balance_after=new_credits,
        description=desc,
    )
    db.add(txn)
    await db.commit()

    logger.info(f"管理员 {admin.id} 重置用户 {user_id} 积分: {old_credits} → {new_credits}")
    return {
        "user_id": user_id,
        "old_credits": old_credits,
        "new_credits": new_credits,
        "description": desc,
    }


@router.get("/users/{user_id}/credits/transactions", response_model=list[CreditTransactionOut])
async def get_user_transactions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """查看用户积分流水"""
    from ..core.credit_service import get_transactions
    return await get_transactions(db, user_id)
