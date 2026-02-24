#!/usr/bin/env python
"""
创建测试用户
"""
import asyncio
from api.core.database import async_session_maker
from api.models.user import User
from api.core.security import get_password_hash
from sqlalchemy import select


async def create_test_user():
    """创建测试用户 test@huginn.com / test123"""
    async with async_session_maker() as session:
        # 检查用户是否已存在
        result = await session.execute(
            select(User).where(User.email == "test@huginn.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("✅ 测试用户已存在")
            print(f"   邮箱: {existing_user.email}")
            print(f"   用户名: {existing_user.username}")
            return
        
        # 创建新用户
        test_user = User(
            email="test@huginn.com",
            username="test",
            hashed_password=get_password_hash("test123")
        )
        
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        print("✅ 测试用户创建成功")
        print(f"   邮箱: {test_user.email}")
        print(f"   用户名: {test_user.username}")
        print(f"   密码: test123")


if __name__ == "__main__":
    asyncio.run(create_test_user())
