"""
积分服务层 — 统一管理积分的检查、扣减、增加
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from ..models.user import User
from ..models.credit import CreditTransaction, CreditType

logger = logging.getLogger(__name__)

# 各操作的积分消耗
CREDIT_COSTS = {
    CreditType.PAPER_EXTRACT: 1,   # 论文提取（每篇1积分）
    CreditType.DEEP_ANALYSIS: 1,   # 深度分析（每次1积分）
}


async def check_credits(user: User, operation: CreditType) -> int:
    """检查用户积分是否足够，返回所需积分数。不足则抛 HTTPException"""
    cost = CREDIT_COSTS.get(operation, 0)
    if user.credits < cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "积分不足",
                "required": cost,
                "current": user.credits,
                "operation": operation.value,
            }
        )
    return cost


async def deduct_credits(
    db: AsyncSession,
    user: User,
    operation: CreditType,
    description: str = "",
) -> CreditTransaction:
    """原子扣减积分并记录流水。使用 SQL 级 UPDATE … WHERE credits >= cost 防止并发竞态和余额透支。"""
    cost = CREDIT_COSTS.get(operation, 0)
    if cost <= 0:
        return None

    # 原子扣减：UPDATE users SET credits = credits - :cost WHERE id = :uid AND credits >= :cost
    result = await db.execute(
        update(User)
        .where(User.id == user.id, User.credits >= cost)
        .values(credits=User.credits - cost)
        .returning(User.credits)
    )
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "积分不足（并发扣减失败）",
                "required": cost,
                "current": user.credits,
                "operation": operation.value,
            }
        )

    balance_after = row[0]
    # 同步 ORM 对象的内存状态
    user.credits = balance_after

    txn = CreditTransaction(
        user_id=user.id,
        amount=-cost,
        type=operation,
        balance_after=balance_after,
        description=description or f"{operation.value} 消耗 {cost} 积分",
    )
    db.add(txn)
    await db.flush()

    logger.info(f"用户 {user.id} 原子扣减 {cost} 积分 ({operation.value})，余额 {balance_after}")
    return txn


async def add_credits(
    db: AsyncSession,
    user: User,
    amount: int,
    credit_type: CreditType,
    description: str = "",
) -> CreditTransaction:
    """增加积分并记录流水"""
    user.credits += amount
    balance_after = user.credits

    txn = CreditTransaction(
        user_id=user.id,
        amount=amount,
        type=credit_type,
        balance_after=balance_after,
        description=description,
    )
    db.add(txn)
    await db.flush()

    logger.info(f"用户 {user.id} 增加 {amount} 积分 ({credit_type.value})，余额 {balance_after}")
    return txn


async def get_transactions(
    db: AsyncSession,
    user_id: int,
    limit: int = 50,
) -> list[CreditTransaction]:
    """获取积分流水"""
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user_id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
