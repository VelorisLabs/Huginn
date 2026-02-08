"""
PDF 文本提取模块
"""

from pathlib import Path
import fitz  # PyMuPDF
from .config import MAX_PDF_CHARS


def extract_pdf_text(pdf_path: Path) -> str:
    """
    提取PDF文本内容
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        str: 提取的文本内容
    """
    text_parts = []
    with fitz.open(str(pdf_path)) as doc:
        for page_num, page in enumerate(doc, 1):
            text = page.get_text("text")
            if text.strip():
                text_parts.append(f"--- 第 {page_num} 页 ---\n{text}")
    
    full_text = "\n\n".join(text_parts)
    if len(full_text) > MAX_PDF_CHARS:
        full_text = full_text[:MAX_PDF_CHARS] + "\n\n[注: 文本已截断]"
    
    return full_text
