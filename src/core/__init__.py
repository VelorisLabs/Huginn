"""
核心模块包
提供论文提取的核心功能组件
"""

from .config import *
from .models import FolderStatus
from .utils import (
    print_separator,
    print_header,
    get_display_width,
    pad_center,
    pad_left,
    log_error,
    extract_number_from_filename,
    format_list_as_numbered,
    extract_scores_from_json,
    format_implementation_path,
)
from .pdf_extractor import extract_pdf_text
from .llm_client import init_client, call_llm, test_api_connection, clean_json_response
from .csv_handler import init_csv, append_to_csv

__all__ = [
    # Config
    'API_KEY', 'BASE_URL', 'MODEL_NAME',
    'BASE_DIR', 'PDF_DIR', 'JSON_DIR', 'CSV_DIR',
    'CONFIG_DIR', 'PROMPT_FILE', 'THEME_FILE', 'WEIGHTS_FILE', 'ERROR_LOG',
    'REQUEST_TIMEOUT', 'REQUEST_INTERVAL', 'MAX_PDF_CHARS',
    'ALL_CSV_NAME', 'CSV_FIELD_MAP', 'CSV_FIELDS',
    # Models
    'FolderStatus',
    # Utils
    'print_separator', 'print_header',
    'get_display_width', 'pad_center', 'pad_left',
    'log_error', 'extract_number_from_filename',
    'format_list_as_numbered', 'extract_scores_from_json',
    'format_implementation_path',
    # PDF
    'extract_pdf_text',
    # LLM
    'init_client', 'call_llm', 'test_api_connection', 'clean_json_response',
    # CSV
    'init_csv', 'append_to_csv',
]
