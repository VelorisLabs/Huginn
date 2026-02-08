"""
配置模块
包含所有配置常量和路径定义
"""

import os
import logging
import sys
from pathlib import Path


# ============================================================
# 日志配置
# ============================================================
def setup_logging(level: int = logging.INFO) -> None:
    """统一日志配置，供 src/ 下所有模块使用"""
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# 模块导入时自动初始化（仅执行一次）
setup_logging()

# ============================================================
# API 配置
# ============================================================
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

# ============================================================
# 路径配置
# ============================================================
# 项目根目录（从 src/core/config.py 向上两级）
BASE_DIR = Path(__file__).parent.parent.parent.resolve()

# 数据目录
PDF_DIR = BASE_DIR / "00_inbox_pdfs"
JSON_DIR = BASE_DIR / "01_extracted_json"
CSV_DIR = BASE_DIR / "02_summary_csv"

# 配置文件目录
CONFIG_DIR = BASE_DIR / "config"
PROMPT_FILE = CONFIG_DIR / "prompt_paper_extraction.md"
THEME_FILE = CONFIG_DIR / "theme_buckets.md"
WEIGHTS_FILE = CONFIG_DIR / "scenario_weights.json"

# 日志文件
ERROR_LOG = BASE_DIR / "error_log.txt"

# ============================================================
# 请求配置
# ============================================================
REQUEST_TIMEOUT = 180.0
REQUEST_INTERVAL = 5
MAX_PDF_CHARS = 30000

# ============================================================
# CSV 配置
# ============================================================
ALL_CSV_NAME = "_all_papers.csv"

CSV_FIELD_MAP = {
    "index": "编号",
    "year": "年份",
    "venue": "期刊",
    "authors": "作者",
    "title": "标题",
    "paper_type": "论文类型",
    "domain_tags": "领域标签",
    "keywords": "关键词",
    "research_object": "研究对象",
    "methodology": "研究方法",
    "problem": "研究问题",
    "conclusion": "核心结论",
    "implementation_path": "具体实现路径_简明",
    "contribution": "主要贡献",
    "score_rigor": "学术严谨度",
    "score_innovation": "创新程度",
    "score_practicality": "实用价值",
    "score_impact": "影响范围",
    "score_readability": "可读性",
    "overall_score": "综合评分",
    "recommendation_level": "推荐等级",
}

CSV_FIELDS = list(CSV_FIELD_MAP.keys())
