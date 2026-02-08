"""
LLM API 客户端模块
"""
import logging
from openai import OpenAI, AsyncOpenAI
from .config import API_KEY, BASE_URL, MODEL_NAME, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# 全局客户端实例
client = None
async_client = None


def init_client() -> bool:
    """
    初始化 OpenAI 客户端
    
    Returns:
        bool: 是否初始化成功
    """
    global client
    if not API_KEY:
        return False
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    return True


def test_api_connection() -> bool:
    """
    测试API连接
    
    Returns:
        bool: 是否连接成功
    """
    logger.info("测试API连接... 端点: %s 模型: %s", BASE_URL, MODEL_NAME)
    
    if not API_KEY:
        logger.error("API Key为空，请设置环境变量 DEEPSEEK_API_KEY")
        return False
    
    if not init_client():
        logger.error("客户端初始化失败")
        return False
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "测试"}],
            max_tokens=10,
            timeout=30.0
        )
        if response and response.choices and response.choices[0].message and response.choices[0].message.content:
            logger.info("API连接成功")
            return True
    except Exception as e:
        logger.error("连接失败: %s", e)
    
    return False


def call_llm(full_prompt: str) -> str:
    """
    调用LLM API
    
    Args:
        full_prompt: 完整的提示词
        
    Returns:
        str: LLM 返回的内容
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
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
        timeout=REQUEST_TIMEOUT
    )
    
    if not response or not response.choices:
        raise RuntimeError("LLM API 返回空响应: response.choices 为空")
    
    message = response.choices[0].message
    if message is None or message.content is None:
        raise RuntimeError("LLM API 返回空内容: message.content 为 None")
    
    return message.content


# ============================================================
# 异步版本 (供 Web API 使用)
# ============================================================

def init_async_client() -> bool:
    """
    初始化异步 OpenAI 客户端
    
    Returns:
        bool: 是否初始化成功
    """
    global async_client
    if not API_KEY:
        return False
    async_client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
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
            raise RuntimeError("异步 LLM 客户端初始化失败，请检查 DEEPSEEK_API_KEY")
    
    response = await async_client.chat.completions.create(
        model=MODEL_NAME,
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
        timeout=REQUEST_TIMEOUT
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
