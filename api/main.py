"""
FastAPI 主应用
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.database import init_db
from .routes import auth, upload, papers, export, themes, workspaces, clustering

# 初始化限流器
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    print("✅ 数据库初始化完成")
    yield
    # 关闭时清理资源
    print("👋 应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 注册限流器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Workspace-Id"],
)

# 注册路由
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(workspaces.router, prefix=f"{settings.API_V1_STR}/workspaces", tags=["workspaces"])
app.include_router(themes.router, prefix=f"{settings.API_V1_STR}/themes", tags=["themes"])
app.include_router(upload.router, prefix=settings.API_V1_STR)
app.include_router(papers.router, prefix=settings.API_V1_STR)
app.include_router(export.router, prefix=settings.API_V1_STR)
app.include_router(clustering.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
