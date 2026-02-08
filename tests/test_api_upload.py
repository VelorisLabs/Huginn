"""测试 API 上传"""
import requests
import os

BASE_URL = "http://localhost:8000/api/v1"

# 1. 登录获取 token
print("1. 登录...")
login_resp = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "admin@example.com",
        "password": "admin666"
    }
)
print(f"   状态: {login_resp.status_code}")

if login_resp.status_code != 200:
    print(f"   错误: {login_resp.text}")
    exit(1)

token = login_resp.json().get("access_token")
print(f"   Token: {token[:20]}...")

# 2. 获取主题列表
print("2. 获取主题...")
headers = {"Authorization": f"Bearer {token}"}
themes_resp = requests.get(f"{BASE_URL}/themes/", headers=headers)
print(f"   状态: {themes_resp.status_code}")
if themes_resp.status_code == 200:
    themes = themes_resp.json()
    print(f"   主题数: {len(themes)}")
    if themes:
        theme_id = themes[0]["id"]
        print(f"   使用主题 ID: {theme_id}")
    else:
        print("   错误: 没有主题")
        exit(1)
else:
    print(f"   错误: {themes_resp.text}")
    exit(1)

# 3. 上传 PDF
print("3. 上传 PDF...")
pdf_path = "uploads/user_1/291bb004-7646-4b12-8167-da7c27548f15.pdf"
if not os.path.exists(pdf_path):
    print(f"   错误: 文件不存在: {pdf_path}")
    exit(1)

with open(pdf_path, "rb") as f:
    files = {"file": ("test.pdf", f, "application/pdf")}
    data = {"theme_id": str(theme_id)}
    resp = requests.post(
        f"{BASE_URL}/upload/pdf",
        files=files,
        data=data,
        headers=headers,
        timeout=300
    )

print(f"   状态: {resp.status_code}")
if resp.status_code == 200:
    print(f"   成功: {resp.json()}")
else:
    try:
        data = resp.json()
        print(f"   错误: {data}")
    except Exception:
        print(f"   错误: {resp.text}")
