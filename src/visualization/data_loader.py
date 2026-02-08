"""
数据加载模块
统一的数据加载和预处理功能
"""

import pandas as pd
from pathlib import Path

# 默认路径
from ..core.config import CSV_DIR

DEFAULT_CSV = CSV_DIR / "_all_papers.csv"
SCENARIO_CSV = CSV_DIR / "_all_papers_多场景对比表.csv"
CLUSTERING_DIR = CSV_DIR / "clustering_analysis"


def load_papers_data(csv_path: Path = None) -> pd.DataFrame:
    """
    加载论文数据
    
    Args:
        csv_path: CSV文件路径，默认使用 _all_papers.csv
        
    Returns:
        pd.DataFrame: 论文数据
    """
    if csv_path is None:
        csv_path = DEFAULT_CSV
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV文件不存在: {csv_path}")
    
    return pd.read_csv(csv_path, encoding='utf-8-sig')


def load_scenario_comparison() -> pd.DataFrame:
    """加载场景对比数据"""
    if not SCENARIO_CSV.exists():
        raise FileNotFoundError(f"场景对比文件不存在: {SCENARIO_CSV}")
    return pd.read_csv(SCENARIO_CSV, encoding='utf-8-sig')


def load_clustering_results() -> pd.DataFrame:
    """加载聚类结果"""
    clustering_csv = CLUSTERING_DIR / "_clustering_results.csv"
    if not clustering_csv.exists():
        raise FileNotFoundError(f"聚类结果文件不存在: {clustering_csv}")
    return pd.read_csv(clustering_csv, encoding='utf-8-sig')


def load_similarity_matrix() -> pd.DataFrame:
    """加载相似度矩阵"""
    similarity_csv = CLUSTERING_DIR / "_similarity_matrix.csv"
    if not similarity_csv.exists():
        raise FileNotFoundError(f"相似度矩阵文件不存在: {similarity_csv}")
    return pd.read_csv(similarity_csv, encoding='utf-8-sig', index_col=0)


def get_stats(df: pd.DataFrame = None) -> dict:
    """
    获取统计数据
    
    Args:
        df: 论文数据 DataFrame，如果为 None 则自动加载
        
    Returns:
        dict: 统计数据
    """
    if df is None:
        try:
            df = load_papers_data()
        except FileNotFoundError:
            return {
                'total_papers': 0,
                'total_topics': 0,
                'avg_score': 0,
                'max_score': 0,
                'year_min': 0,
                'year_max': 0,
            }
    
    stats = {
        'total_papers': len(df),
        'total_topics': df['领域标签'].nunique() if '领域标签' in df.columns else 0,
        'avg_score': df['综合评分'].mean() if '综合评分' in df.columns else 0,
        'max_score': df['综合评分'].max() if '综合评分' in df.columns else 0,
        'year_min': int(df['年份'].min()) if '年份' in df.columns else 0,
        'year_max': int(df['年份'].max()) if '年份' in df.columns else 0,
    }
    
    return stats
