#!/usr/bin/env python
"""检查所有论文"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./paper_analysis.db"

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 统计
        result = await session.execute(text("SELECT COUNT(*) FROM papers WHERE user_id=1"))
        total = result.scalar()
        
        result = await session.execute(text("SELECT COUNT(*) FROM papers WHERE user_id=1 AND file_path IS NOT NULL"))
        with_file = result.scalar()
        
        print(f"=== 论文统计 ===")
        print(f"总论文数: {total}")
        print(f"有文件路径: {with_file}")
        print(f"无文件路径: {total - with_file}")
        
        # 查看最新的几条（按 ID 降序）
        result = await session.execute(text("""
            SELECT id, title, file_path, original_filename, created_at 
            FROM papers 
            WHERE user_id=1 
            ORDER BY id DESC 
            LIMIT 10
        """))
        papers = result.fetchall()
        
        print(f"\n=== 最新的 10 篇论文（按 ID 降序）===")
        for p in papers:
            print(f"\nID: {p[0]}")
            print(f"  标题: {p[1][:60]}...")
            print(f"  文件路径: {p[2]}")
            print(f"  原始文件名: {p[3]}")
            print(f"  创建时间: {p[4]}")

if __name__ == "__main__":
    asyncio.run(main())
