#!/usr/bin/env python
"""数据库查看工具 - 以易读格式展示数据库内容"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import json

DATABASE_URL = "sqlite+aiosqlite:///./paper_analysis.db"

async def show_users():
    """显示所有用户"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, email, username FROM users"))
        users = result.fetchall()
        
        print("\n" + "="*80)
        print("用户列表")
        print("="*80)
        for u in users:
            print(f"ID: {u[0]} | Email: {u[1]} | Username: {u[2]}")

async def show_themes(user_id=None):
    """显示主题列表"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        if user_id:
            result = await session.execute(
                text("SELECT id, name, tags, user_id FROM themes WHERE user_id=:uid ORDER BY id"),
                {"uid": user_id}
            )
        else:
            result = await session.execute(text("SELECT id, name, tags, user_id FROM themes ORDER BY id"))
        
        themes = result.fetchall()
        
        print("\n" + "="*80)
        print(f"主题列表 {'(用户 ID: ' + str(user_id) + ')' if user_id else ''}")
        print("="*80)
        for t in themes:
            print(f"ID: {t[0]} | 用户: {t[3]} | 名称: {t[1]}")
            print(f"  标签: {t[2]}")
            print()

async def show_papers(user_id=None, limit=10):
    """显示论文列表（简要信息）"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        if user_id:
            result = await session.execute(
                text("""
                    SELECT id, title, authors, year, theme_name, file_path, created_at 
                    FROM papers 
                    WHERE user_id=:uid 
                    ORDER BY created_at DESC 
                    LIMIT :lim
                """),
                {"uid": user_id, "lim": limit}
            )
        else:
            result = await session.execute(
                text("""
                    SELECT id, title, authors, year, theme_name, file_path, created_at 
                    FROM papers 
                    ORDER BY created_at DESC 
                    LIMIT :lim
                """),
                {"lim": limit}
            )
        
        papers = result.fetchall()
        
        print("\n" + "="*80)
        print(f"论文列表 {'(用户 ID: ' + str(user_id) + ')' if user_id else ''} - 最新 {limit} 篇")
        print("="*80)
        for p in papers:
            print(f"\nID: {p[0]} | 创建时间: {p[6]}")
            print(f"标题: {p[1][:70]}{'...' if len(p[1]) > 70 else ''}")
            print(f"作者: {p[2] or 'N/A'} | 年份: {p[3] or 'N/A'}")
            print(f"主题: {p[4] or 'N/A'}")
            print(f"文件: {p[5] or '无（CLI导入）'}")

async def show_paper_detail(paper_id):
    """显示单篇论文的详细信息"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM papers WHERE id=:pid"),
            {"pid": paper_id}
        )
        columns = result.keys()
        paper = result.fetchone()
        
        if not paper:
            print(f"\n❌ 未找到 ID 为 {paper_id} 的论文")
            return
        
        print("\n" + "="*80)
        print(f"论文详细信息 (ID: {paper_id})")
        print("="*80)
        
        # 转换为字典
        paper_dict = dict(zip(columns, paper))
        
        # 分组展示
        print("\n【基本信息】")
        print(f"  ID: {paper_dict['id']}")
        print(f"  标题: {paper_dict['title']}")
        print(f"  作者: {paper_dict['authors'] or 'N/A'}")
        print(f"  年份: {paper_dict['year'] or 'N/A'}")
        print(f"  期刊/会议: {paper_dict['venue'] or 'N/A'}")
        
        print("\n【分类信息】")
        print(f"  用户ID: {paper_dict['user_id']}")
        print(f"  主题ID: {paper_dict['theme_id']}")
        print(f"  主题名称: {paper_dict['theme_name']}")
        print(f"  领域标签: {paper_dict['domain_tags'] or 'N/A'}")
        print(f"  论文类型: {paper_dict['paper_type'] or 'N/A'}")
        
        print("\n【研究内容】")
        print(f"  关键词: {paper_dict['keywords'] or 'N/A'}")
        print(f"  问题: {paper_dict['problem'][:100] if paper_dict['problem'] else 'N/A'}...")
        print(f"  方法: {paper_dict['methodology'][:100] if paper_dict['methodology'] else 'N/A'}...")
        print(f"  结论: {paper_dict['conclusion'][:100] if paper_dict['conclusion'] else 'N/A'}...")
        print(f"  贡献: {paper_dict['contribution'][:100] if paper_dict['contribution'] else 'N/A'}...")
        
        print("\n【评分】")
        print(f"  严谨性: {paper_dict.get('score_rigor') or 'N/A'}")
        print(f"  创新性: {paper_dict.get('score_innovation') or 'N/A'}")
        print(f"  实用性: {paper_dict.get('score_practicality') or 'N/A'}")
        print(f"  影响力: {paper_dict.get('score_impact') or 'N/A'}")
        print(f"  可读性: {paper_dict.get('score_readability') or 'N/A'}")
        print(f"  综合得分: {paper_dict.get('composite_score') or 'N/A'}")
        
        print("\n【文件信息】")
        print(f"  文件路径: {paper_dict['file_path'] or '无（CLI导入）'}")
        print(f"  原始文件名: {paper_dict['original_filename'] or 'N/A'}")
        
        print("\n【时间信息】")
        print(f"  创建时间: {paper_dict['created_at']}")
        print(f"  更新时间: {paper_dict['updated_at']}")

async def export_paper_to_json(paper_id, output_dir="summary"):
    """将论文导出为 JSON 文件（类似 CLI 方式的输出）"""
    import os
    from pathlib import Path
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM papers WHERE id=:pid"),
            {"pid": paper_id}
        )
        columns = result.keys()
        paper = result.fetchone()
        
        if not paper:
            print(f"\n❌ 未找到 ID 为 {paper_id} 的论文")
            return
        
        # 转换为字典
        paper_dict = dict(zip(columns, paper))
        
        # 转换日期为字符串
        for key in ['created_at', 'updated_at']:
            if paper_dict[key]:
                paper_dict[key] = str(paper_dict[key])
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        filename = f"{paper_dict['title'][:50].replace('/', '_')}_{paper_id}.json"
        filepath = output_path / filename
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(paper_dict, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已导出到: {filepath}")

async def show_stats():
    """显示统计信息"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 用户统计
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        # 论文统计
        result = await session.execute(text("SELECT COUNT(*) FROM papers"))
        paper_count = result.scalar()
        
        # Web上传的论文
        result = await session.execute(text("SELECT COUNT(*) FROM papers WHERE file_path IS NOT NULL"))
        web_count = result.scalar()
        
        # 主题统计
        result = await session.execute(text("SELECT COUNT(*) FROM themes"))
        theme_count = result.scalar()
        
        print("\n" + "="*80)
        print("数据库统计")
        print("="*80)
        print(f"用户总数: {user_count}")
        print(f"主题总数: {theme_count}")
        print(f"论文总数: {paper_count}")
        print(f"  ├─ Web上传: {web_count}")
        print(f"  └─ CLI导入: {paper_count - web_count}")

async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("""
数据库查看工具使用说明
====================

查看统计信息:
  python view_database.py stats

查看用户列表:
  python view_database.py users

查看主题列表:
  python view_database.py themes [user_id]

查看论文列表:
  python view_database.py papers [user_id] [limit]

查看论文详情:
  python view_database.py detail <paper_id>

导出论文为JSON:
  python view_database.py export <paper_id> [output_dir]

示例:
  python view_database.py stats
  python view_database.py papers 1 20
  python view_database.py detail 76
  python view_database.py export 76 summary/
        """)
        return
    
    command = sys.argv[1]
    
    if command == "stats":
        await show_stats()
    elif command == "users":
        await show_users()
    elif command == "themes":
        user_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        await show_themes(user_id)
    elif command == "papers":
        user_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        await show_papers(user_id, limit)
    elif command == "detail":
        if len(sys.argv) < 3:
            print("❌ 请提供论文ID")
            return
        paper_id = int(sys.argv[2])
        await show_paper_detail(paper_id)
    elif command == "export":
        if len(sys.argv) < 3:
            print("❌ 请提供论文ID")
            return
        paper_id = int(sys.argv[2])
        output_dir = sys.argv[3] if len(sys.argv) > 3 else "summary"
        await export_paper_to_json(paper_id, output_dir)
    else:
        print(f"❌ 未知命令: {command}")
        print("运行 'python view_database.py' 查看帮助")

if __name__ == "__main__":
    asyncio.run(main())
