"""
数据库迁移：添加工作区支持
================================
1. 创建 workspaces 表
2. 为 users 表添加 active_workspace_id 列
3. 为 themes 表添加 workspace_id 列
4. 为 papers 表添加 workspace_id 列
5. 为每个用户创建默认工作区
6. 将已有的 themes 和 papers 关联到默认工作区
7. 加载全局 scenario_weights.json 作为默认工作区的权重配置

使用方法：
  cd e:\\MyProject\\Huginn
  uv run python scripts/migrations/add_workspaces.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
WEIGHTS_FILE = PROJECT_ROOT / "config" / "scenario_weights.json"

DB_CANDIDATES = [
    PROJECT_ROOT / "paper_analysis.db",
]


def find_db() -> Path:
    for p in DB_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(f"找不到数据库文件，尝试过: {DB_CANDIDATES}")


def load_default_weights() -> dict | None:
    if WEIGHTS_FILE.exists():
        with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def table_exists(cursor: sqlite3.Cursor, table: str) -> bool:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None


def main():
    db_path = find_db()
    print(f"📂 数据库: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()

    # ── Step 1: 创建 workspaces 表 ──
    if not table_exists(cursor, "workspaces"):
        print("🔨 创建 workspaces 表...")
        cursor.execute("""
            CREATE TABLE workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                scenario_weights JSON,
                prompt_config JSON,
                is_default BOOLEAN DEFAULT 0,
                "order" INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE (user_id, name)
            )
        """)
        cursor.execute("CREATE INDEX ix_workspaces_user_id ON workspaces(user_id)")
        print("  ✅ workspaces 表已创建")
    else:
        print("  ⏭️  workspaces 表已存在，跳过")

    # ── Step 2: 为 users 表添加 active_workspace_id 列 ──
    if not column_exists(cursor, "users", "active_workspace_id"):
        print("🔨 为 users 添加 active_workspace_id 列...")
        cursor.execute("ALTER TABLE users ADD COLUMN active_workspace_id INTEGER")
        print("  ✅ 已添加")
    else:
        print("  ⏭️  users.active_workspace_id 已存在，跳过")

    # ── Step 3: 为 themes 表添加 workspace_id 列 ──
    if not column_exists(cursor, "themes", "workspace_id"):
        print("🔨 为 themes 添加 workspace_id 列...")
        cursor.execute("ALTER TABLE themes ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_themes_workspace_id ON themes(workspace_id)")
        print("  ✅ 已添加")
    else:
        print("  ⏭️  themes.workspace_id 已存在，跳过")

    # ── Step 4: 为 papers 表添加 workspace_id 列 ──
    if not column_exists(cursor, "papers", "workspace_id"):
        print("🔨 为 papers 添加 workspace_id 列...")
        cursor.execute("ALTER TABLE papers ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_papers_workspace_id ON papers(workspace_id)")
        print("  ✅ 已添加")
    else:
        print("  ⏭️  papers.workspace_id 已存在，跳过")

    conn.commit()

    # ── Step 5: 为每个用户创建默认工作区 ──
    print("\n🔨 创建默认工作区...")
    default_weights = load_default_weights()
    weights_json = json.dumps(default_weights, ensure_ascii=False) if default_weights else None

    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()

    for user in users:
        user_id = user["id"]
        username = user["username"]

        # 检查是否已有默认工作区
        cursor.execute(
            "SELECT id FROM workspaces WHERE user_id = ? AND is_default = 1",
            (user_id,)
        )
        existing = cursor.fetchone()

        if existing:
            ws_id = existing["id"]
            print(f"  ⏭️  用户 {username} (id={user_id}) 已有默认工作区 (id={ws_id})")
        else:
            cursor.execute(
                """INSERT INTO workspaces (user_id, name, description, scenario_weights, is_default, "order", created_at, updated_at)
                   VALUES (?, ?, ?, ?, 1, 0, ?, ?)""",
                (user_id, "默认工作区", "系统自动创建的默认工作区", weights_json, now, now)
            )
            ws_id = cursor.lastrowid
            print(f"  ✅ 用户 {username} (id={user_id}) → 默认工作区 (id={ws_id})")

        # 设置 active_workspace_id
        cursor.execute(
            "UPDATE users SET active_workspace_id = ? WHERE id = ? AND (active_workspace_id IS NULL OR active_workspace_id = 0)",
            (ws_id, user_id)
        )

    conn.commit()

    # ── Step 6: 回填 workspace_id ──
    print("\n🔨 回填 workspace_id...")

    # 回填 themes
    cursor.execute("""
        UPDATE themes SET workspace_id = (
            SELECT w.id FROM workspaces w
            WHERE w.user_id = themes.user_id AND w.is_default = 1
            LIMIT 1
        )
        WHERE workspace_id IS NULL
    """)
    themes_updated = cursor.rowcount
    print(f"  ✅ themes: {themes_updated} 条记录已更新")

    # 回填 papers
    cursor.execute("""
        UPDATE papers SET workspace_id = (
            SELECT w.id FROM workspaces w
            WHERE w.user_id = papers.user_id AND w.is_default = 1
            LIMIT 1
        )
        WHERE workspace_id IS NULL
    """)
    papers_updated = cursor.rowcount
    print(f"  ✅ papers: {papers_updated} 条记录已更新")

    conn.commit()

    # ── 验证 ──
    print("\n📊 迁移结果验证:")
    cursor.execute("SELECT COUNT(*) FROM workspaces")
    print(f"  工作区总数: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM themes WHERE workspace_id IS NULL")
    null_themes = cursor.fetchone()[0]
    print(f"  themes.workspace_id 为 NULL: {null_themes}")

    cursor.execute("SELECT COUNT(*) FROM papers WHERE workspace_id IS NULL")
    null_papers = cursor.fetchone()[0]
    print(f"  papers.workspace_id 为 NULL: {null_papers}")

    if null_themes > 0 or null_papers > 0:
        print("  ⚠️  存在未关联工作区的记录，请检查")
    else:
        print("  ✅ 所有记录已关联到工作区")

    conn.close()
    print("\n" + "=" * 50)
    print("✅ 工作区迁移完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
