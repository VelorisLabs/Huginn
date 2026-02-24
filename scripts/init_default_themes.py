#!/usr/bin/env python
"""
初始化默认主题（从 config/theme_buckets.md）
"""
import asyncio
from pathlib import Path
from api.core.database import async_session_maker
from api.models.theme import Theme
from api.models.user import User
from sqlalchemy import select


async def init_themes_for_user(email: str):
    """为指定用户初始化主题"""
    async with async_session_maker() as session:
        # 查找用户
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ 用户 {email} 不存在")
            return
        
        # 读取 theme_buckets.md
        theme_file = Path("config/theme_buckets.md")
        if not theme_file.exists():
            print(f"❌ 配置文件不存在: {theme_file}")
            return
        
        content = theme_file.read_text(encoding='utf-8')
        
        # 解析主题
        themes_data = []
        lines = content.split('\n')
        current_theme = None
        current_tags = []
        order = 0
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('>') or line.startswith('#'):
                if line.startswith('# ') and not line.startswith('## '):
                    continue
                if not line.startswith('## '):
                    continue
            
            # 匹配二级标题（主题名称）
            if line.startswith('## '):
                # 保存上一个主题
                if current_theme:
                    themes_data.append({
                        "name": current_theme,
                        "tags": ",".join(current_tags),
                        "order": order
                    })
                    order += 1
                
                # 开始新主题
                current_theme = line[3:].strip()
                current_tags = []
            
            # 匹配列表项（次级标签）
            elif line.startswith('- '):
                tag = line[2:].strip()
                if tag and current_theme:
                    current_tags.append(tag)
        
        # 保存最后一个主题
        if current_theme:
            themes_data.append({
                "name": current_theme,
                "tags": ",".join(current_tags),
                "order": order
            })
        
        # 检查是否已有主题
        result = await session.execute(
            select(Theme).where(Theme.user_id == user.id)
        )
        existing_themes = result.scalars().all()
        
        if existing_themes:
            print(f"ℹ️  用户已有 {len(existing_themes)} 个主题，跳过初始化")
            for theme in existing_themes:
                print(f"   - {theme.name}")
            return
        
        # 创建主题
        for theme_data in themes_data:
            theme = Theme(
                user_id=user.id,
                name=theme_data["name"],
                tags=theme_data["tags"],
                order=theme_data["order"]
            )
            session.add(theme)
        
        await session.commit()
        
        print(f"✅ 成功为用户 {email} 创建 {len(themes_data)} 个主题")
        for theme_data in themes_data:
            print(f"   {theme_data['order'] + 1}. {theme_data['name']}")


if __name__ == "__main__":
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else "test@huginn.com"
    asyncio.run(init_themes_for_user(email))
