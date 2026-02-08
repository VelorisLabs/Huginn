#!/usr/bin/env python
"""测试删除论文功能（验证文件也被删除）"""
import asyncio
import httpx
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 登录
        print("1. 登录...")
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@example.com", "password": "admin666"}
        )
        print(f"   状态: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   登录失败: {response.text}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 上传一个测试 PDF
        print("\n2. 上传测试 PDF...")
        test_pdf = Path("uploads/user_1/0721a86b-dd58-4e1b-bd4f-4c951433258e.pdf")
        
        if not test_pdf.exists():
            print(f"   错误: 测试文件不存在 {test_pdf}")
            return
        
        with open(test_pdf, "rb") as f:
            files = {"file": ("test_delete.pdf", f, "application/pdf")}
            data = {"theme_id": "1"}
            
            response = await client.post(
                f"{BASE_URL}/upload/pdf",
                files=files,
                data=data,
                headers=headers
            )
        
        print(f"   状态: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   上传失败: {response.json()}")
            return
        
        result = response.json()
        paper_id = result["task_id"]
        file_path = Path(result["file_path"])
        
        print(f"   成功! Paper ID: {paper_id}")
        print(f"   文件路径: {file_path}")
        print(f"   文件存在: {file_path.exists()}")
        
        # 3. 删除论文
        print(f"\n3. 删除论文 ID {paper_id}...")
        response = await client.delete(
            f"{BASE_URL}/papers/{paper_id}",
            headers=headers
        )
        
        print(f"   状态: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 4. 验证文件是否被删除
        print(f"\n4. 验证文件是否删除...")
        print(f"   文件路径: {file_path}")
        print(f"   文件存在: {file_path.exists()}")
        
        if not file_path.exists():
            print("   ✅ 成功！文件已被同步删除")
        else:
            print("   ❌ 失败！文件仍然存在")

if __name__ == "__main__":
    asyncio.run(main())
