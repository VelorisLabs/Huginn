"""
数据模型模块
包含数据结构定义
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FolderStatus:
    """文件夹状态"""
    name: str
    path: Path
    total_pdfs: int = 0
    processed: int = 0
    pending: int = 0
    pdf_files: list = field(default_factory=list)
