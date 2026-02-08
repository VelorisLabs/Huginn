"""测试上传流程"""
import sys
sys.path.insert(0, '.')
from pathlib import Path
import json

from src.core.pdf_extractor import extract_pdf_text
from src.core.llm_client import init_client, call_llm, clean_json_response
from src.core.config import PROMPT_FILE

def test_upload_process():
    pdf_path = Path('uploads/user_1/291bb004-7646-4b12-8167-da7c27548f15.pdf')
    
    print("1. 测试 PDF 提取...")
    if not pdf_path.exists():
        print(f"   错误: PDF 文件不存在: {pdf_path}")
        return
    
    pdf_text = extract_pdf_text(pdf_path)
    print(f"   成功: 提取文本长度 {len(pdf_text)}")
    
    print("2. 读取 Prompt 模板...")
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    print(f"   成功: 模板长度 {len(prompt_template)}")
    
    print("3. 初始化 LLM 客户端...")
    if not init_client():
        print("   错误: LLM 客户端初始化失败")
        return
    print("   成功")
    
    print("4. 调用 LLM API (可能需要几分钟)...")
    full_prompt = f"{prompt_template}\n\n论文内容：\n{pdf_text}"
    try:
        response = call_llm(full_prompt)
        print(f"   成功: 响应长度 {len(response)}")
    except Exception as e:
        print(f"   错误: {e}")
        return
    
    print("5. 解析 JSON...")
    try:
        clean_response = clean_json_response(response)
        paper_data = json.loads(clean_response)
        print(f"   成功: 标题={paper_data.get('title', 'N/A')}")
        print(f"   年份: {paper_data.get('year')}")
        print(f"   作者: {paper_data.get('authors')}")
        print(f"   评分: {paper_data.get('scores', {})}")
    except Exception as e:
        print(f"   错误: {e}")
        print(f"   原始响应: {response[:500]}")
        return
    
    print("\n✅ 上传流程测试完成！")

if __name__ == "__main__":
    test_upload_process()
