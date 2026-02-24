"""
评分计算（共享）
"""


def compute_weighted_score(
    rigor: float,
    innovation: float,
    practicality: float,
    impact: float,
    readability: float,
    weights: dict,
) -> float:
    """
    根据五维分数和权重字典计算加权评分。

    Args:
        rigor, innovation, practicality, impact, readability: 五维原始评分
        weights: 权重字典，需包含 rigor/innovation/practicality/impact/readability

    Returns:
        加权后的综合评分（保留2位小数）
    """
    score = (
        rigor * weights.get("rigor", 0)
        + innovation * weights.get("innovation", 0)
        + practicality * weights.get("practicality", 0)
        + impact * weights.get("impact", 0)
        + readability * weights.get("readability", 0)
    )
    return round(score, 2)
