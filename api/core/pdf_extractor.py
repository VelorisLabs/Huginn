"""
PDF 文本提取模块 — 委托给 shared/
"""
from shared.pdf_extractor import extract_pdf_text as _extract
from .config import settings


def extract_pdf_text(pdf_path):
    return _extract(pdf_path, max_chars=settings.MAX_PDF_CHARS)
