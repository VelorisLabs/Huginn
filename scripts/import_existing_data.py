#!/usr/bin/env python
"""
导入现有 CLI 数据到数据库
将 data/summary/_all_papers.csv 中的论文导入到指定用户账户下
"""
import asyncio
import csv
from pathlib import Path
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from passlib.context import CryptContext

# 数据库配置 - 与后端配置一致
DATABASE_URL = "sqlite+aiosqlite:///./paper_analysis.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# 密码加密 - 使用 argon2 与 API 保持一致
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 导入模型定义（避免循环导入）
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Theme(Base):
    __tablename__ = "themes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    tags = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    theme_id = Column(Integer, ForeignKey("themes.id"), nullable=True)
    theme_name = Column(String, nullable=True)
    title = Column(String, nullable=False)
    authors = Column(String)
    year = Column(Integer)
    venue = Column(String)
    keywords = Column(Text)
    domain_tags = Column(String)
    paper_type = Column(String)
    problem = Column(Text)
    methodology = Column(Text)
    conclusion = Column(Text)
    contribution = Column(Text)
    score_rigor = Column(Float)
    score_innovation = Column(Float)
    score_practicality = Column(Float)
    score_impact = Column(Float)
    score_readability = Column(Float)
    overall_score = Column(Float)
    recommendation_level = Column(String)
    scenario_scores = Column(JSON)
    cluster_id = Column(Integer)
    cluster_topic = Column(String)
    file_path = Column(String)
    original_filename = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_type = Column(String, nullable=False)
    status = Column(String, default="pending")
    progress = Column(Float, default=0.0)
    config = Column(JSON)
    result = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


async def rebuild_database():
    """重建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表已重建")


async def create_admin_user():
    """创建 admin 用户"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"ℹ️  admin 用户已存在 (ID: {user.id})")
            return user.id
        
        user = User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("admin666"),
            is_active=True,
            is_superuser=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"✅ 创建 admin 用户成功 (ID: {user.id})")
        return user.id


async def init_themes_for_user(user_id: int):
    """为用户初始化主题"""
    async with async_session_maker() as session:
        # 检查是否已有主题
        result = await session.execute(
            select(Theme).where(Theme.user_id == user_id)
        )
        existing = result.scalars().all()
        if existing:
            print(f"ℹ️  用户已有 {len(existing)} 个主题")
            return {t.name: t.id for t in existing}
        
        # 读取配置文件
        theme_file = Path("config/theme_buckets.md")
        content = theme_file.read_text(encoding='utf-8')
        
        themes_data = []
        lines = content.split('\n')
        current_theme = None
        current_tags = []
        order = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                if current_theme:
                    themes_data.append({
                        "name": current_theme,
                        "tags": ",".join(current_tags),
                        "order": order
                    })
                    order += 1
                current_theme = line[3:].strip()
                current_tags = []
            elif line.startswith('- '):
                tag = line[2:].strip()
                if tag and current_theme:
                    current_tags.append(tag)
        
        if current_theme:
            themes_data.append({
                "name": current_theme,
                "tags": ",".join(current_tags),
                "order": order
            })
        
        theme_map = {}
        for td in themes_data:
            theme = Theme(
                user_id=user_id,
                name=td["name"],
                tags=td["tags"],
                order=td["order"]
            )
            session.add(theme)
            await session.flush()
            theme_map[td["name"]] = theme.id
        
        await session.commit()
        print(f"✅ 为用户创建 {len(themes_data)} 个主题")
        return theme_map


async def import_papers(user_id: int, theme_map: dict):
    """导入论文数据"""
    csv_file = Path("data/summary/_all_papers.csv")
    if not csv_file.exists():
        print(f"❌ 文件不存在: {csv_file}")
        return
    
    async with async_session_maker() as session:
        # 检查是否已有论文
        result = await session.execute(
            select(Paper).where(Paper.user_id == user_id)
        )
        existing = result.scalars().all()
        if existing:
            print(f"ℹ️  用户已有 {len(existing)} 篇论文，跳过导入")
            return
        
        # 读取 CSV
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            papers = []
            
            for row in reader:
                # 解析领域标签，匹配主题
                domain_tags = row.get('领域标签', '')
                theme_id = None
                theme_name = None
                
                for tname, tid in theme_map.items():
                    if tname in domain_tags:
                        theme_id = tid
                        theme_name = tname
                        break
                
                # 解析场景评分
                scenario_scores = {}
                for key in theme_map.keys():
                    # 尝试从 CSV 中找到该场景的评分
                    if key in row:
                        try:
                            scenario_scores[key] = float(row[key])
                        except:
                            pass
                
                paper = Paper(
                    user_id=user_id,
                    theme_id=theme_id,
                    theme_name=theme_name,
                    title=row.get('标题', ''),
                    authors=row.get('作者', ''),
                    year=int(row.get('年份', 0)) if row.get('年份') else None,
                    venue=row.get('期刊', ''),
                    keywords=row.get('关键词', ''),
                    domain_tags=row.get('领域标签', ''),
                    paper_type=row.get('论文类型', ''),
                    problem=row.get('研究问题', ''),
                    methodology=row.get('研究方法', ''),
                    conclusion=row.get('核心结论', ''),
                    contribution=row.get('主要贡献', ''),
                    score_rigor=float(row.get('学术严谨度', 0)) if row.get('学术严谨度') else None,
                    score_innovation=float(row.get('创新程度', 0)) if row.get('创新程度') else None,
                    score_practicality=float(row.get('实用价值', 0)) if row.get('实用价值') else None,
                    score_impact=float(row.get('影响范围', 0)) if row.get('影响范围') else None,
                    score_readability=float(row.get('可读性', 0)) if row.get('可读性') else None,
                    overall_score=float(row.get('综合评分', 0)) if row.get('综合评分') else None,
                    recommendation_level=row.get('推荐等级', ''),
                    scenario_scores=scenario_scores if scenario_scores else None,
                    file_path=None,
                    status='completed'
                )
                papers.append(paper)
            
            session.add_all(papers)
            await session.commit()
            print(f"✅ 成功导入 {len(papers)} 篇论文")


async def create_test_user():
    """创建 test 用户（空白状态）"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"ℹ️  test 用户已存在 (ID: {user.id})")
            return user.id
        
        user = User(
            email="test@example.com",
            username="test",
            hashed_password=get_password_hash("test"),
            is_active=True,
            is_superuser=False
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"✅ 创建 test 用户成功 (ID: {user.id})")
        return user.id


async def main():
    print("=" * 50)
    print("导入现有 CLI 数据到 Web 应用数据库")
    print("=" * 50)
    
    # 0. 重建数据库
    print("\n[0/4] 重建数据库表...")
    await rebuild_database()
    
    # 1. 创建 admin 用户
    print("\n[1/4] 创建 admin 用户...")
    admin_id = await create_admin_user()
    
    # 2. 初始化主题
    print("\n[2/4] 初始化主题...")
    theme_map = await init_themes_for_user(admin_id)
    
    # 3. 导入论文
    print("\n[3/4] 导入论文数据...")
    await import_papers(admin_id, theme_map)
    
    # 4. 创建 test 用户（空白状态）
    print("\n[4/4] 创建 test 用户...")
    await create_test_user()
    
    print("\n" + "=" * 50)
    print("导入完成！")
    print("admin 账号: admin@example.com / admin666")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
