"""
依赖注入
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .database import get_db
from .security import decode_access_token
from ..models.user import User
from ..models.workspace import Workspace

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（优先 Bearer header，回退到 httpOnly Cookie）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 优先从 Authorization header 获取 token
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token
    
    if not token:
        raise credentials_exception
    
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception
    
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户账号已被停用")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    return current_user


async def get_current_workspace(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Workspace:
    """获取当前工作区（优先 X-Workspace-Id header，回退到用户的 active_workspace_id）"""
    workspace_id = None

    # 1. 从 header 获取
    header_val = request.headers.get("X-Workspace-Id")
    if header_val:
        try:
            workspace_id = int(header_val)
        except (ValueError, TypeError):
            pass

    # 2. 回退到用户的 active_workspace_id
    if workspace_id is None:
        workspace_id = current_user.active_workspace_id

    # 3. 查询工作区
    if workspace_id:
        result = await db.execute(
            select(Workspace).where(
                Workspace.id == workspace_id,
                Workspace.user_id == current_user.id
            )
        )
        workspace = result.scalar_one_or_none()
        if workspace:
            return workspace

    # 4. 回退到默认工作区
    result = await db.execute(
        select(Workspace).where(
            Workspace.user_id == current_user.id,
            Workspace.is_default == True
        )
    )
    workspace = result.scalar_one_or_none()
    if workspace:
        return workspace

    # 5. 没有任何工作区 → 自动创建默认工作区
    workspace = Workspace(
        user_id=current_user.id,
        name="默认工作区",
        description="系统自动创建的默认工作区",
        is_default=True,
        order=0
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return workspace


async def get_optional_workspace(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Optional[Workspace]:
    """可选的工作区依赖（部分接口可能不需要强制工作区）"""
    header_val = request.headers.get("X-Workspace-Id")
    if not header_val:
        return None
    try:
        workspace_id = int(header_val)
    except (ValueError, TypeError):
        return None
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.user_id == current_user.id
        )
    )
    return result.scalar_one_or_none()
