"""
LLM 工具函数（共享）
"""


def clean_json_response(text: str) -> str:
    """
    清洗模型返回的JSON

    Args:
        text: LLM 返回的原始文本

    Returns:
        str: 清洗后的 JSON 字符串
    """
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
