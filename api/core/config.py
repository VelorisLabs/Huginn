"""
应用配置
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional
import json


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目信息
    PROJECT_NAME: str = "论文分析系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # 安全配置
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 分钟（短期）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 天（长期）
    
    # Cookie 配置
    COOKIE_SECURE: bool = False  # 生产环境应设为 True（HTTPS）
    COOKIE_SAMESITE: str = "lax"
    
    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./paper_analysis.db"
    
    # 文件上传
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".zip"}
    
    # LLM 配置
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"
    LLM_TIMEOUT: float = 180.0
    
    # 模型列表（支持切换）
    AVAILABLE_MODELS: dict = {
        "deepseek": {
            "name": "DeepSeek Chat",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        },
        "openai-gpt4": {
            "name": "OpenAI GPT-4",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o"
        },
        "openai-gpt35": {
            "name": "OpenAI GPT-3.5",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo"
        }
    }
    
    # CORS - 从环境变量读取，支持 JSON 数组格式
    BACKEND_CORS_ORIGINS: str = '["http://localhost:4321", "http://localhost:3000"]'
    
    # 项目路径
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    CONFIG_DIR: Path = PROJECT_ROOT / "config"
    PROMPT_FILE: Path = PROJECT_ROOT / "config" / "prompt_paper_extraction.md"
    PROMPT_DEEP_ANALYSIS_FILE: Path = PROJECT_ROOT / "config" / "prompt_deep_analysis.md"
    
    # PDF 处理
    MAX_PDF_CHARS: int = 30000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    def get_cors_origins(self) -> list:
        """解析 CORS 配置"""
        try:
            if isinstance(self.BACKEND_CORS_ORIGINS, str):
                return json.loads(self.BACKEND_CORS_ORIGINS)
            return self.BACKEND_CORS_ORIGINS
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:4321", "http://localhost:3000"]


settings = Settings()

# 启动时校验 SECRET_KEY
_INSECURE_KEYS = {"", "your-secret-key-change-in-production", "change-this-secret-key-in-production"}
if settings.SECRET_KEY in _INSECURE_KEYS:
    import warnings
    if settings.DEBUG:
        warnings.warn(
            "⚠️  SECRET_KEY 未配置或使用了不安全的默认值！"
            "请在 .env 文件中设置 SECRET_KEY。当前以调试模式运行，使用临时密钥。",
            stacklevel=1,
        )
        settings.SECRET_KEY = "debug-only-insecure-key-do-not-use-in-production"
    else:
        raise RuntimeError(
            "❌ SECRET_KEY 未配置！生产环境必须在 .env 文件中设置 SECRET_KEY。"
            "请设置环境变量 SECRET_KEY 或在 .env 文件中添加 SECRET_KEY=<your-secure-key>"
        )

# 确保 CORS 配置正确解析
settings.BACKEND_CORS_ORIGINS = settings.get_cors_origins()

# 确保上传目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── 场景权重加载（全局缓存，供多个模块共用） ──
_SCENARIO_WEIGHTS_CACHE: dict | None = None


def load_scenario_weights() -> dict:
    """加载 config/scenario_weights.json 中的场景权重（带缓存）"""
    global _SCENARIO_WEIGHTS_CACHE
    if _SCENARIO_WEIGHTS_CACHE is None:
        weights_file = settings.CONFIG_DIR / "scenario_weights.json"
        if weights_file.exists():
            with open(weights_file, "r", encoding="utf-8") as f:
                _SCENARIO_WEIGHTS_CACHE = json.load(f)
        else:
            _SCENARIO_WEIGHTS_CACHE = {}
    return _SCENARIO_WEIGHTS_CACHE
