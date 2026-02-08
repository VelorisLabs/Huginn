#!/usr/bin/env python
"""检查论文数据"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./data/app.db"

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 检查最近上传的论文
        result = await session.execute(text("""
            SELECT id, title, file_path, original_filename, created_at 
            FROM papers 
            WHERE user_id=1 
            ORDER BY created_at DESC 
            LIMIT 20
        """))
        papers = result.fetchall()
        
        print("=== 最近上传的论文 ===")
        for p in papers:
            print(f"ID: {p[0]}")
            print(f"  标题: {p[1][:50]}...")
            print(f"  文件: {p[2]}")
            print(f"  原名: {p[3]}")
            print(f"  时间: {p[4]}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
