#!/usr/bin/env python
"""添加 implementation_path 列到 papers 表"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./paper_analysis.db"

async def add_column():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 检查列是否已存在
        result = await session.execute(text("PRAGMA table_info(papers)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'implementation_path' in columns:
            print("✅ implementation_path 列已存在，无需添加")
            return
        
        # 添加新列
        await session.execute(text("ALTER TABLE papers ADD COLUMN implementation_path TEXT"))
        await session.commit()
        print("✅ 成功添加 implementation_path 列")

if __name__ == "__main__":
    asyncio.run(add_column())
