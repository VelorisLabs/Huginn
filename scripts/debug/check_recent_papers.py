#!/usr/bin/env python
"""检查最新上传的论文（带文件路径）"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./data/app.db"

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 查找有 file_path 的论文
        result = await session.execute(text("""
            SELECT id, title, file_path, original_filename, created_at 
            FROM papers 
            WHERE user_id=1 AND file_path IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT 15
        """))
        papers = result.fetchall()
        
        print("=== 通过 Web 上传的论文（有文件路径）===")
        print(f"共 {len(papers)} 篇\n")
        for p in papers:
            print(f"ID: {p[0]}")
            print(f"  标题: {p[1][:60]}...")
            print(f"  文件路径: {p[2]}")
            print(f"  原始文件名: {p[3]}")
            print(f"  上传时间: {p[4]}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
