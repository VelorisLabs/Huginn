#!/usr/bin/env python
"""重新处理指定论文的conclusion字段"""
import asyncio
import json
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# 导入LLM客户端和配置
import sys
sys.path.insert(0, str(Path(__file__).parent))
from src.core.llm_client import call_llm
from src.core.config import PROMPT_FILE, THEME_FILE

DATABASE_URL = "sqlite+aiosqlite:///./paper_analysis.db"


def load_prompt_template():
    """加载Prompt模板"""
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        template = f.read()
    with open(THEME_FILE, "r", encoding="utf-8") as f:
        theme_buckets = f.read()
    return template.replace("{THEME_BUCKETS}", theme_buckets)


async def reprocess_paper(paper_id: int):
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 获取论文信息
        result = await session.execute(
            text("SELECT id, title, file_path, problem FROM papers WHERE id = :id"),
            {"id": paper_id}
        )
        row = result.fetchone()
        if not row:
            print(f"未找到论文 ID={paper_id}")
            return
        
        paper_id, title, file_path, current_problem = row
        print(f"论文: {title}")
        print(f"文件: {file_path}")
        print(f"当前problem: {current_problem}")
        
        # 读取PDF文本
        if not file_path or not Path(file_path).exists():
            print("PDF文件不存在，无法重新处理")
            return
        
        import fitz
        doc = fitz.open(file_path)
        text_content = ""
        for page in doc:
            text_content += page.get_text()
        doc.close()
        
        # 调用LLM重新分析
        prompt_template = load_prompt_template()
        prompt = prompt_template + "\n\n---\n\n## 论文全文\n\n" + text_content[:30000]
        
        print("\n正在调用LLM重新分析...")
        result_json = call_llm(prompt)
        
        if not result_json:
            print("LLM返回空结果")
            return
        
        paper_data = json.loads(result_json)
        
        # 提取新的problem和conclusion
        new_problem = paper_data.get("problem", [])
        new_conclusion = paper_data.get("conclusion", [])
        
        print(f"\n新的problem ({len(new_problem)}个):")
        for i, p in enumerate(new_problem, 1):
            print(f"  {i}. {p}")
        
        print(f"\n新的conclusion ({len(new_conclusion)}个):")
        for i, c in enumerate(new_conclusion, 1):
            print(f"  {i}. {c}")
        
        # 格式化为编号文本
        def format_list(items):
            if isinstance(items, list):
                return " ".join(f"{i}. {item}" for i, item in enumerate(items, 1))
            return str(items)
        
        new_problem_text = format_list(new_problem)
        new_conclusion_text = format_list(new_conclusion)
        
        # 更新数据库
        await session.execute(
            text("UPDATE papers SET problem = :problem, conclusion = :conclusion WHERE id = :id"),
            {"problem": new_problem_text, "conclusion": new_conclusion_text, "id": paper_id}
        )
        await session.commit()
        
        print(f"\n✅ 已更新论文 ID={paper_id} 的problem和conclusion")


if __name__ == "__main__":
    # 处理ID=78的论文
    asyncio.run(reprocess_paper(78))
