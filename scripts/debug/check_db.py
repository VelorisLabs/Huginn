#!/usr/bin/env python
"""检查数据库状态"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./paper_analysis.db"

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 检查用户
        result = await session.execute(text("SELECT id, email, username FROM users"))
        users = result.fetchall()
        print("=== 用户列表 ===")
        for u in users:
            print(f"  ID: {u[0]}, Email: {u[1]}, Username: {u[2]}")
        
        # 检查论文数量
        result = await session.execute(text("SELECT user_id, COUNT(*) as cnt FROM papers GROUP BY user_id"))
        papers = result.fetchall()
        print("\n=== 论文统计 ===")
        for p in papers:
            print(f"  User ID: {p[0]}, 论文数: {p[1]}")
        
        # 检查主题
        result = await session.execute(text("SELECT user_id, COUNT(*) as cnt FROM themes GROUP BY user_id"))
        themes = result.fetchall()
        print("\n=== 主题统计 ===")
        for t in themes:
            print(f"  User ID: {t[0]}, 主题数: {t[1]}")

if __name__ == "__main__":
    asyncio.run(main())
