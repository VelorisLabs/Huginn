"""
P1.1 权重自适应评分系统 - 场景重算脚本

功能：
  1. 读取P0 CSV文件（包含5维基础评分）
  2. 加载权重场景配置
  3. 为每篇论文计算多个场景下的综合评分
  4. 生成分层输出（方案C）：
     - 保留原P0表不变
     - 生成多场景对比表
     - 生成按各场景排序的排序表（top 10高亮）

作者: Claude
日期: 2026-01-13
"""

import csv
import json
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple

# ============================================================
# 配置
# ============================================================
from .core.config import BASE_DIR, CSV_DIR, WEIGHTS_FILE
from shared.scoring import compute_weighted_score

P0_CSV_PATH = CSV_DIR / "_all_papers.csv"
WEIGHTS_CONFIG_PATH = WEIGHTS_FILE
OUTPUT_DIR = CSV_DIR
SCENARIO_RANKINGS_DIR = OUTPUT_DIR / "scenario_rankings"

# 推荐等级映射
SCORE_TO_LEVEL = [
    (9.0, "⭐⭐⭐⭐⭐"),
    (7.5, "⭐⭐⭐⭐"),
    (6.0, "⭐⭐⭐"),
    (4.0, "⭐⭐"),
    (0.0, "⭐")
]

# ============================================================
# 数据结构
# ============================================================
@dataclass
class PaperRecord:
    """论文记录"""
    index: str
    title: str
    rigor: float
    innovation: float
    practicality: float
    impact: float
    readability: float
    p0_overall: float
    p0_level: str
    original_row: dict  # 保存原始行数据，用于输出

@dataclass
class ScenarioScore:
    """场景评分"""
    scenario_name: str
    overall_score: float
    level: str


# ============================================================
# 工具函数
# ============================================================
def score_to_level(score: float) -> str:
    """根据评分映射推荐等级"""
    for threshold, level in SCORE_TO_LEVEL:
        if score >= threshold:
            return level
    return "⭐"


def load_weights_config() -> Dict:
    """加载权重配置"""
    with open(WEIGHTS_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_p0_csv() -> List[PaperRecord]:
    """读取P0 CSV并解析为PaperRecord对象"""
    papers = []

    with open(P0_CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                paper = PaperRecord(
                    index=row.get('编号', '').strip(),
                    title=row.get('标题', '').strip(),
                    rigor=float(row.get('学术严谨度', 0) or 0),
                    innovation=float(row.get('创新程度', 0) or 0),
                    practicality=float(row.get('实用价值', 0) or 0),
                    impact=float(row.get('影响范围', 0) or 0),
                    readability=float(row.get('可读性', 0) or 0),
                    p0_overall=float(row.get('综合评分', 0) or 0),
                    p0_level=row.get('推荐等级', ''),
                    original_row=row
                )
                papers.append(paper)
            except ValueError as e:
                print(f"⚠️  跳过第{row.get('编号', '?')}篇论文: 评分数据格式错误 - {e}")
                continue

    return papers


def calculate_scenario_score(paper: PaperRecord, weights: Dict) -> ScenarioScore:
    """计算单篇论文在某个场景下的综合评分"""
    overall = compute_weighted_score(
        paper.rigor, paper.innovation, paper.practicality,
        paper.impact, paper.readability, weights
    )
    # Round to 1 decimal for CLI display
    overall = round(overall, 1)
    level = score_to_level(overall)

    return ScenarioScore(
        scenario_name="",
        overall_score=overall,
        level=level
    )


def create_comparison_table(papers: List[PaperRecord], config: Dict, output_path: Path):
    """
    创建多场景对比表

    列结构：编号 | 标题 | 5维原始评分 | P0评分+等级 | 各场景评分+等级
    """
    scenarios = config['scenarios']

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        # 构建表头
        headers = [
            '编号', '标题',
            '学术严谨度', '创新程度', '实用价值', '影响范围', '可读性',
            '综合评分_P0', '推荐等级_P0'
        ]

        # 添加各场景的列
        for scenario_name in scenarios.keys():
            headers.extend([
                f'综合评分_{scenario_name}',
                f'推荐等级_{scenario_name}'
            ])

        writer = csv.writer(f)
        writer.writerow(headers)

        # 写入数据行
        for paper in papers:
            row = [
                paper.index,
                paper.title,
                paper.rigor,
                paper.innovation,
                paper.practicality,
                paper.impact,
                paper.readability,
                paper.p0_overall,
                paper.p0_level
            ]

            # 计算各场景评分
            for scenario_name, scenario_config in scenarios.items():
                scenario_score = calculate_scenario_score(paper, scenario_config['weights'])
                row.extend([
                    scenario_score.overall_score,
                    scenario_score.level
                ])

            writer.writerow(row)

    print(f"[OK] Comparison table generated: {output_path}")


def create_scenario_ranking_tables(papers: List[PaperRecord], config: Dict, output_dir: Path):
    """
    为每个场景创建排序表

    按该场景的综合评分降序排列，top 10高亮
    """
    scenarios = config['scenarios']
    output_dir.mkdir(parents=True, exist_ok=True)

    for scenario_name, scenario_config in scenarios.items():
        # 计算每篇论文在该场景下的评分
        scored_papers = []
        for paper in papers:
            scenario_score = calculate_scenario_score(paper, scenario_config['weights'])
            scored_papers.append((paper, scenario_score))

        # 按评分降序排序
        scored_papers.sort(key=lambda x: x[1].overall_score, reverse=True)

        # 生成文件
        filename = f"排序表_{scenario_name}.csv"
        filepath = output_dir / filename

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            # 表头与原P0相同，但添加该场景的综合评分和等级
            headers = list(papers[0].original_row.keys()) + [
                f'综合评分_{scenario_name}',
                f'推荐等级_{scenario_name}',
                '★推荐指数'  # 用于标记top 10
            ]

            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            # 写入数据行
            for rank, (paper, scenario_score) in enumerate(scored_papers, 1):
                row = paper.original_row.copy()
                row[f'综合评分_{scenario_name}'] = scenario_score.overall_score
                row[f'推荐等级_{scenario_name}'] = scenario_score.level

                # 标记top 10
                if rank <= 10:
                    row['★推荐指数'] = f"🔥 TOP {rank}"
                else:
                    row['★推荐指数'] = ""

                writer.writerow(row)

        print(f"[OK] Ranking table generated: {filepath}")
        print(f"   ({scenario_name} - sorted by score, top 10 highlighted)")


def print_summary(papers: List[PaperRecord], config: Dict):
    """打印汇总统计信息"""
    print("\n" + "=" * 70)
    print("P1.1 Weight-adaptive Scoring System - Execution Complete")
    print("=" * 70)
    print(f"\nSummary Statistics:")
    print(f"  - Total papers processed: {len(papers)}")
    print(f"  - Weight scenario count: {len(config['scenarios'])}")
    print(f"  - Output plan: Layered output (Plan C)")

    print(f"\nScenario List:")
    for name, scenario_config in config['scenarios'].items():
        print(f"  * {name}")
        print(f"    Description: {scenario_config['description']}")
        print(f"    Weights: rigor={scenario_config['weights']['rigor']}, "
              f"innovation={scenario_config['weights']['innovation']}, "
              f"practicality={scenario_config['weights']['practicality']}, "
              f"impact={scenario_config['weights']['impact']}, "
              f"readability={scenario_config['weights']['readability']}")

    print(f"\nOutput Files:")
    print(f"  [ok] {OUTPUT_DIR / '_all_papers_多场景对比表.csv'}")
    print(f"  [ok] {SCENARIO_RANKINGS_DIR / '排序表_应用导向型.csv'}")
    print(f"  [ok] {SCENARIO_RANKINGS_DIR / '排序表_理论突破型.csv'}")
    print(f"  [ok] {SCENARIO_RANKINGS_DIR / '排序表_综合均衡型.csv'}")

    print(f"\nUsage Suggestions:")
    print(f"  1. Open '_all_papers_多场景对比表.csv' for in-depth analysis")
    print(f"     - Observe ranking changes for same paper across scenarios")
    print(f"     - Understand impact of weight adjustments on scores")
    print(f"  2. Open ranking tables in 'scenario_rankings/' for quick review")
    print(f"     - For application-oriented papers, open '排序表_应用导向型.csv'")
    print(f"     - Top 10 marked with 'TOP N' for quick location")
    print(f"  3. Original P0 '_all_papers.csv' unchanged for baseline comparison")

    print("\n" + "=" * 70 + "\n")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("P1.1 Weight-adaptive Scoring System - Launching")
    print("=" * 70)

    # 检查依赖文件
    print("\nChecking dependency files...")
    if not P0_CSV_PATH.exists():
        print(f"ERROR: Cannot find P0 CSV file: {P0_CSV_PATH}")
        return
    if not WEIGHTS_CONFIG_PATH.exists():
        print(f"ERROR: Cannot find weights config file: {WEIGHTS_CONFIG_PATH}")
        return
    print(f"[OK] P0 CSV file: {P0_CSV_PATH}")
    print(f"[OK] Weights config file: {WEIGHTS_CONFIG_PATH}")

    # 加载数据
    print("\nLoading data...")
    config = load_weights_config()
    papers = load_p0_csv()
    print(f"[OK] Successfully loaded {len(papers)} papers")
    print(f"[OK] Successfully loaded {len(config['scenarios'])} weight scenarios")

    # 创建输出目录
    print("\nPreparing output directory...")
    SCENARIO_RANKINGS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Output directory ready: {OUTPUT_DIR}")

    # 生成多场景对比表
    print("\nGenerating multi-scenario comparison table...")
    comparison_table_path = OUTPUT_DIR / "_all_papers_多场景对比表.csv"
    create_comparison_table(papers, config, comparison_table_path)

    # 生成按场景排序的表
    print("\nGenerating per-scenario ranking tables...")
    create_scenario_ranking_tables(papers, config, SCENARIO_RANKINGS_DIR)

    # 打印汇总
    print_summary(papers, config)


if __name__ == "__main__":
    main()
