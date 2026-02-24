"""
数据库迁移：添加积分系统和邀请码
====================================
1. 为 users 表添加 credits 列
2. 创建 invite_codes 表
3. 创建 credit_transactions 表
4. 为现有用户补充初始积分
5. 生成初始管理员邀请码

使用方法：
  cd e:\\MyProject\\Huginn
  uv run python scripts/migrations/add_credits_and_invites.py
"""

import sqlite3
import secrets
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "paper_analysis.db"

INITIAL_CREDITS = 50  # 给现有用户补充的积分


def migrate():
    if not DB_PATH.exists():
        print(f"❌ 数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("=" * 50)
    print("积分系统 & 邀请码迁移")
    print("=" * 50)

    # 1. 为 users 表添加 credits 列
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN credits INTEGER NOT NULL DEFAULT 0")
        print("✅ users 表添加 credits 列")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("ℹ️  users.credits 列已存在")
        else:
            raise

    # 2. 创建 invite_codes 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invite_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            credits INTEGER NOT NULL DEFAULT 50,
            max_uses INTEGER NOT NULL DEFAULT 1,
            used_count INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            note TEXT,
            created_by INTEGER NOT NULL REFERENCES users(id),
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_invite_codes_code ON invite_codes(code)")
    print("✅ invite_codes 表已创建")

    # 3. 创建 credit_transactions 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            balance_after INTEGER NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_credit_transactions_user_id ON credit_transactions(user_id)")
    print("✅ credit_transactions 表已创建")

    # 4. 为现有用户补充积分
    cursor.execute("SELECT id, username, credits FROM users")
    users = cursor.fetchall()
    now = datetime.now(timezone.utc).isoformat()
    
    for user_id, username, current_credits in users:
        if current_credits == 0:
            cursor.execute("UPDATE users SET credits = ? WHERE id = ?", (INITIAL_CREDITS, user_id))
            cursor.execute(
                "INSERT INTO credit_transactions (user_id, amount, type, balance_after, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, INITIAL_CREDITS, "admin_adjust", INITIAL_CREDITS, "系统迁移：初始积分赠送", now)
            )
            print(f"  ✅ 用户 {username} (ID:{user_id}) 补充 {INITIAL_CREDITS} 积分")
        else:
            print(f"  ℹ️  用户 {username} (ID:{user_id}) 已有 {current_credits} 积分，跳过")

    # 5. 生成初始管理员邀请码（供分发）
    # 查找管理员用户
    cursor.execute("SELECT id FROM users WHERE is_superuser = 1 LIMIT 1")
    admin_row = cursor.fetchone()
    admin_id = admin_row[0] if admin_row else 1

    # 生成 5 个邀请码
    print("\n生成初始邀请码：")
    for i in range(5):
        code = secrets.token_urlsafe(8)[:12].upper()
        cursor.execute(
            "INSERT OR IGNORE INTO invite_codes (code, credits, max_uses, used_count, is_active, note, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (code, 50, 1, 0, 1, f"初始邀请码 #{i+1}", admin_id, now)
        )
        print(f"  📨 {code}  (50 积分, 1 次使用)")

    conn.commit()
    conn.close()

    print("\n" + "=" * 50)
    print("迁移完成！")
    print("=" * 50)


if __name__ == "__main__":
    migrate()
