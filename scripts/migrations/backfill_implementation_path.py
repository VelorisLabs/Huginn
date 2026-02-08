#!/usr/bin/env python
"""从CSV文件中读取"具体实现路径_简明"并更新到数据库"""
import asyncio
import csv
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./paper_analysis.db"
CSV_PATH = Path("data/summary/_all_papers.csv")

async def backfill():
    # 1. 读取CSV数据
    print("1. 读取CSV文件...")
    csv_data = {}
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get('标题', '').strip()
            impl_path = row.get('具体实现路径_简明', '').strip()
            if title and impl_path:
                csv_data[title] = impl_path
    
    print(f"   找到 {len(csv_data)} 条有[具体实现路径]的记录")
    
    # 2. 连接数据库
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 3. 获取所有论文
        result = await session.execute(text("SELECT id, title, implementation_path FROM papers"))
        papers = result.fetchall()
        
        print(f"2. 数据库中共有 {len(papers)} 篇论文")
        
        # 4. 匹配并更新
        updated = 0
        skipped = 0
        not_found = 0
        
        for paper_id, title, existing_impl in papers:
            if existing_impl:
                skipped += 1
                continue
            
            # 尝试精确匹配
            impl_path = csv_data.get(title)
            
            if not impl_path:
                # 尝试模糊匹配（去除空格后匹配）
                title_clean = title.replace(' ', '').replace('\u3000', '')
                for csv_title, csv_impl in csv_data.items():
                    csv_title_clean = csv_title.replace(' ', '').replace('\u3000', '')
                    if title_clean == csv_title_clean:
                        impl_path = csv_impl
                        break
            
            if impl_path:
                await session.execute(
                    text("UPDATE papers SET implementation_path = :impl WHERE id = :id"),
                    {"impl": impl_path, "id": paper_id}
                )
                updated += 1
                print(f"   ✅ 更新: {title[:40]}...")
            else:
                not_found += 1
                print(f"   ⚠️ 未找到: {title[:40]}...")
        
        await session.commit()
        
        print(f"\n3. 更新完成:")
        print(f"   ✅ 成功更新: {updated} 篇")
        print(f"   ⏭️ 已有数据跳过: {skipped} 篇")
        print(f"   ⚠️ CSV中未找到: {not_found} 篇")

if __name__ == "__main__":
    asyncio.run(backfill())
