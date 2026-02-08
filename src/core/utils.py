"""
工具函数模块
包含通用工具函数
"""

import re
import time
import unicodedata
from .config import ERROR_LOG


def print_separator(char="=", length=70):
    """打印分隔线"""
    print(char * length)


def print_header(text: str):
    """打印标题"""
    print_separator()
    print(f"  {text}")
    print_separator()


def get_display_width(s: str) -> int:
    """计算字符串的显示宽度（中文/全角=2，其他=1）"""
    width = 0
    for char in s:
        ea = unicodedata.east_asian_width(char)
        if ea in ('F', 'W'):  # Fullwidth, Wide
            width += 2
        else:
            width += 1
    return width


def pad_center(s: str, width: int) -> str:
    """居中对齐到指定显示宽度"""
    current = get_display_width(s)
    if current >= width:
        return s
    total_pad = width - current
    left = total_pad // 2
    right = total_pad - left
    return ' ' * left + s + ' ' * right


def pad_left(s: str, width: int) -> str:
    """左对齐到指定显示宽度"""
    current = get_display_width(s)
    if current >= width:
        return s
    return s + ' ' * (width - current)


def log_error(filename: str, error: str):
    """记录错误到日志文件"""
    with open(ERROR_LOG, 'a', encoding='utf-8') as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {filename}: {error}\n")


def extract_number_from_filename(filename: str) -> str:
    """从文件名提取编号前缀（如 01_xxx.pdf -> 01）"""
    match = re.match(r'^(\d+)[_\-]', filename)
    return match.group(1) if match else ""


def format_list_as_numbered(val) -> str:
    """将数组转为编号文本，单元素直接返回"""
    if isinstance(val, list):
        if len(val) == 0:
            return ""
        if len(val) == 1:
            return str(val[0])
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(val))
    return str(val) if val is not None else ""


def extract_scores_from_json(json_obj: dict) -> dict:
    """
    从JSON中提取评分信息

    Args:
        json_obj: LLM返回的完整JSON对象

    Returns:
        dict: {score_rigor, score_innovation, score_practicality, score_impact, score_readability, overall_score, recommendation_level}
    """
    scores = json_obj.get("scores", {})
    recommendation = json_obj.get("recommendation", {})

    return {
        "score_rigor": scores.get("rigor", ""),
        "score_innovation": scores.get("innovation", ""),
        "score_practicality": scores.get("practicality", ""),
        "score_impact": scores.get("impact", ""),
        "score_readability": scores.get("readability", ""),
        "overall_score": scores.get("overall", ""),
        "recommendation_level": recommendation.get("level", ""),
    }


def format_implementation_path(impl_path_dict) -> str:
    """
    将implementation_path字典转为CSV简明格式

    格式: 维度 [关键词1 | 关键词2] → 描述

    Args:
        impl_path_dict: implementation_path字段的值（字典或其他格式）

    Returns:
        str: 格式化后的字符串（多行时用\n分隔）
    """
    if not impl_path_dict:
        return ""

    # 如果是字符串（旧格式兼容），直接返回
    if isinstance(impl_path_dict, str):
        return impl_path_dict

    # 如果不是字典，转为字符串返回
    if not isinstance(impl_path_dict, dict):
        return str(impl_path_dict) if impl_path_dict else ""

    lines = []
    for idx, (key, value) in enumerate(impl_path_dict.items(), 1):
        if isinstance(value, dict):
            # 新结构：包含description和keywords
            keywords = value.get("keywords", [])
            description = value.get("description", "").strip()

            # 构建关键词部分
            if keywords:
                keywords_str = " | ".join(str(kw) for kw in keywords)
                lines.append(f"{idx}. {key} [{keywords_str}]")
            else:
                lines.append(f"{idx}. {key}")

            # 添加描述行
            if description:
                lines.append(f"   → {description}")
        else:
            # 兼容旧格式（纯字符串）
            lines.append(f"{idx}. {key}: {value}")

    return "\n".join(lines)
