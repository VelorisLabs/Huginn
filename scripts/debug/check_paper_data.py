#!/usr/bin/env python
"""检查论文的problem和conclusion数据"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./paper_analysis.db"

async def check():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, title, problem, conclusion FROM papers WHERE title LIKE '%新时代背景下青年价值%'")
        )
        row = result.fetchone()
        if row:
            print(f"ID: {row[0]}")
            print(f"Title: {row[1]}")
            print(f"\nPROBLEM:\n{row[2]}")
            print(f"\nCONCLUSION:\n{row[3]}")
        else:
            print("未找到该论文")

if __name__ == "__main__":
    asyncio.run(check())
