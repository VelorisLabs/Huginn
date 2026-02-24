"""
批量计算 scenario_scores（场景评分）
=======================================
为已有论文计算三种场景的加权评分，无需 Celery/Redis。

使用方法：
  cd e:\MyProject\Huginn
  python -m scripts.backfill_scenario_scores

逻辑：读取 config/scenario_weights.json 中的三种场景权重，
     用论文已有的五维分数做加权求和，写入 scenario_scores 字段。
"""

import json
import sqlite3
from pathlib import Path
from shared.scoring import compute_weighted_score

# ── 路径配置 ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_FILE = PROJECT_ROOT / "config" / "scenario_weights.json"

# 数据库（统一使用 paper_analysis.db）
DB_CANDIDATES = [
    PROJECT_ROOT / "paper_analysis.db",
]


def find_db() -> Path:
    for p in DB_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(f"找不到数据库文件，尝试过: {DB_CANDIDATES}")


def load_scenarios(weights_file: Path) -> dict:
    with open(weights_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("scenarios", {})


def calculate_score(paper_row: dict, weights: dict) -> float:
    return compute_weighted_score(
        paper_row["score_rigor"] or 0,
        paper_row["score_innovation"] or 0,
        paper_row["score_practicality"] or 0,
        paper_row["score_impact"] or 0,
        paper_row["score_readability"] or 0,
        weights,
    )


def main():
    db_path = find_db()
    print(f"📂 数据库: {db_path}")
    print(f"📄 权重配置: {WEIGHTS_FILE}")

    scenarios = load_scenarios(WEIGHTS_FILE)
    if not scenarios:
        print("❌ scenario_weights.json 中没有找到 scenarios 配置")
        return

    print(f"🎯 场景数量: {len(scenarios)}")
    for name in scenarios:
        print(f"   - {name}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 查询所有有五维评分的论文
    cursor.execute("""
        SELECT id, title, score_rigor, score_innovation,
               score_practicality, score_impact, score_readability,
               scenario_scores
        FROM papers
        WHERE score_rigor IS NOT NULL
          AND score_innovation IS NOT NULL
          AND score_practicality IS NOT NULL
          AND score_impact IS NOT NULL
          AND score_readability IS NOT NULL
    """)
    papers = cursor.fetchall()
    print(f"\n📊 符合条件的论文: {len(papers)} 篇")

    updated = 0
    skipped = 0

    for paper in papers:
        paper_dict = dict(paper)
        existing = paper_dict["scenario_scores"]

        # 如果已有 scenario_scores 且有效，跳过（加 --force 参数可覆盖）
        if existing:
            try:
                parsed = json.loads(existing) if isinstance(existing, str) else existing
                if isinstance(parsed, dict) and len(parsed) == len(scenarios):
                    skipped += 1
                    continue
            except (json.JSONDecodeError, TypeError):
                pass

        # 计算每个场景的加权分
        scores = {}
        for scenario_name, scenario_config in scenarios.items():
            weights = scenario_config["weights"]
            scores[scenario_name] = calculate_score(paper_dict, weights)

        # 写入数据库
        cursor.execute(
            "UPDATE papers SET scenario_scores = ? WHERE id = ?",
            (json.dumps(scores, ensure_ascii=False), paper_dict["id"]),
        )
        updated += 1

        # 打印进度
        title_short = (paper_dict["title"] or "")[:40]
        scores_str = " | ".join(f"{k}: {v}" for k, v in scores.items())
        print(f"  ✅ [{paper_dict['id']:3d}] {title_short}...  → {scores_str}")

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"✅ 完成! 更新 {updated} 篇, 跳过 {skipped} 篇 (已有评分)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
