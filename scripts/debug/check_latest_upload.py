#!/usr/bin/env python
"""检查最新上传的论文（使用正确的数据库）"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# 尝试两个数据库
DATABASES = {
    "paper_analysis.db": "sqlite+aiosqlite:///./paper_analysis.db",
    "data/app.db": "sqlite+aiosqlite:///./data/app.db"
}

async def check_db(name, url):
    print(f"\n{'='*60}")
    print(f"检查数据库: {name}")
    print('='*60)
    
    try:
        engine = create_async_engine(url, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession)
        
        async with async_session() as session:
            # 统计
            result = await session.execute(text("SELECT COUNT(*) FROM papers WHERE user_id=1"))
            total = result.scalar()
            
            result = await session.execute(text("SELECT COUNT(*) FROM papers WHERE user_id=1 AND file_path IS NOT NULL"))
            with_file = result.scalar()
            
            print(f"\n总论文数: {total}")
            print(f"有文件路径: {with_file}")
            print(f"无文件路径: {total - with_file}")
            
            # 查看最新的几条（按 created_at 降序）
            result = await session.execute(text("""
                SELECT id, title, file_path, original_filename, created_at 
                FROM papers 
                WHERE user_id=1 
                ORDER BY created_at DESC 
                LIMIT 5
            """))
            papers = result.fetchall()
            
            print(f"\n最新的 5 篇论文：")
            for p in papers:
                print(f"\nID: {p[0]}")
                print(f"  标题: {p[1][:60]}...")
                print(f"  文件路径: {p[2]}")
                print(f"  原始文件名: {p[3]}")
                print(f"  创建时间: {p[4]}")
    except Exception as e:
        print(f"错误: {e}")

async def main():
    for name, url in DATABASES.items():
        await check_db(name, url)

if __name__ == "__main__":
    asyncio.run(main())
