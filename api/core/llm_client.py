"""
LLM API 客户端模块（供 Web API 使用）
"""
import logging
from openai import AsyncOpenAI
from .config import settings

logger = logging.getLogger(__name__)

# 全局异步客户端实例
async_client = None


def init_async_client() -> bool:
    """
    初始化异步 OpenAI 客户端
    
    Returns:
        bool: 是否初始化成功
    """
    global async_client
    api_key = settings.LLM_API_KEY
    if not api_key:
        return False
    async_client = AsyncOpenAI(api_key=api_key, base_url=settings.LLM_BASE_URL)
    return True


async def async_call_llm(full_prompt: str) -> str:
    """
    异步调用 LLM API（非阻塞，适用于 FastAPI async 上下文）
    
    Args:
        full_prompt: 完整的提示词
        
    Returns:
        str: LLM 返回的内容
    """
    global async_client
    if async_client is None:
        if not init_async_client():
            raise RuntimeError("异步 LLM 客户端初始化失败，请检查 LLM_API_KEY")
    
    response = await async_client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的学术论文分析助手。请严格按照用户提供的JSON Schema格式输出结果，只输出JSON，不要添加任何额外说明。"
            },
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        temperature=0.1,
        max_tokens=4096,
        timeout=settings.LLM_TIMEOUT
    )
    
    if not response or not response.choices:
        raise RuntimeError("LLM API 返回空响应: response.choices 为空")
    
    message = response.choices[0].message
    if message is None or message.content is None:
        raise RuntimeError("LLM API 返回空内容: message.content 为 None")
    
    return message.content


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
