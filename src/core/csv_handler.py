"""
CSV 处理模块
"""

import csv
from pathlib import Path
from .config import CSV_FIELD_MAP, CSV_FIELDS
from .utils import format_list_as_numbered, extract_scores_from_json, format_implementation_path


def init_csv(csv_path: Path):
    """
    初始化CSV文件
    
    Args:
        csv_path: CSV文件路径
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists():
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            headers = [CSV_FIELD_MAP[k] for k in CSV_FIELDS]
            writer.writerow(headers)


def append_to_csv(csv_path: Path, data: dict, index_value: str = ""):
    """
    追加数据到CSV

    Args:
        csv_path: CSV文件路径
        data: 论文数据字典
        index_value: 编号值（分主题表用文件名编号，总表用全局编号）
    """
    # 先提取评分信息（如果JSON中包含scores字段）
    scores_data = extract_scores_from_json(data)

    row = []
    for key in CSV_FIELDS:
        if key == "index":
            # 编号字段使用传入的index_value
            row.append(index_value)
        elif key in ("problem", "conclusion"):
            # 研究问题和结论使用编号列表格式
            val = data.get(key, "")
            row.append(format_list_as_numbered(val))
        elif key == "implementation_path":
            # 实现路径使用格式化函数
            val = data.get(key, "")
            row.append(format_implementation_path(val))
        elif key in ("keywords", "domain_tags"):
            # 关键词和领域标签使用逗号分隔
            val = data.get(key, [])
            if isinstance(val, list):
                row.append(", ".join(str(v) for v in val))
            else:
                row.append(str(val) if val else "")
        elif key in ("score_rigor", "score_innovation", "score_practicality", "score_impact", "score_readability", "overall_score", "recommendation_level"):
            # 评分字段从scores_data中取
            val = scores_data.get(key, "")
            row.append(str(val) if val else "")
        else:
            val = data.get(key, "")
            if val is None:
                val = ""
            row.append(str(val))

    with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(row)
