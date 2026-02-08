# 问题排查指南 (Troubleshooting Guide)

本文档记录了论文分析系统开发过程中遇到的常见问题和解决方案，帮助快速定位和解决类似问题。

---

## 目录

- [文件上传失败问题](#文件上传失败问题)
- [多进程端口占用问题](#多进程端口占用问题)
- [数据库相关问题](#数据库相关问题)
- [前端 UI 交互问题](#前端-ui-交互问题)
- [文件删除同步问题](#文件删除同步问题)

---

## 文件上传失败问题

### 问题描述

**症状：**
1. 点击"选择文件"按钮无反应，文件选择框不弹出
2. 拖拽文件上传时卡住，最终报 500 错误
3. 后端日志显示 `Error binding parameter X: type 'list' is not supported`

**根本原因：**

这是**两个独立问题叠加**：

#### 问题 1：前端点击事件被拦截

**原因：** Astro dev toolbar 的浮层拦截了点击事件

**定位方法：**
```bash
# 检查浏览器开发者工具
# Elements 面板查看是否有高 z-index 的覆盖层
# 查看 astro.config.mjs 配置
```

**解决方案：**
```javascript
// frontend/astro.config.mjs
export default defineConfig({
  devToolbar: {
    enabled: false  // 禁用开发工具栏
  },
  // ...
});
```

**附加修复：**
```tsx
// frontend/src/components/UploadZone.tsx
// 将 hidden 改为 sr-only 避免浏览器安全限制
<input
  type="file"
  className="sr-only"  // 替代 hidden
  // ...
/>
```

#### 问题 2：后端数据类型不匹配

**原因：** LLM 返回的 list/dict 类型字段直接插入 SQLite 导致参数绑定错误

**错误信息：**
```
Error binding parameter 11: type 'list' is not supported
[SQL: INSERT INTO papers (user_id, theme_id, ..., problem, methodology, ...)]
[parameters: (..., ['问题1', '问题2'], ['方法1', '方法2'], ...)]
```

**定位方法：**
```python
# 在后端添加日志查看数据类型
logger.info(f"problem type: {type(paper_data.get('problem'))}")
logger.info(f"problem value: {paper_data.get('problem')}")
```

**解决方案：**
```python
# api/api/upload.py
def _to_text(value) -> str | None:
    """将 list/dict 归一化为字符串"""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        # 拼接列表项为多行字符串
        parts = []
        for item in value:
            if item and isinstance(item, str):
                parts.append(item.strip())
        return "\n".join(parts) if parts else None
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)

# 应用归一化
paper = Paper(
    problem=_to_text(paper_data.get("problem")),
    methodology=_to_text(paper_data.get("methodology")),
    # ...
)
```

---

## 多进程端口占用问题

### 问题描述

**症状：**
- 修改代码后重启服务器，但行为依然是旧代码
- 测试脚本有时成功有时失败（随机）
- 日志中看不到新加的调试信息

**根本原因：**

多个 `uvicorn` 进程同时监听 8000 端口，请求被随机分配到旧进程

**为什么会发生：**

Windows 允许多进程绑定同一端口（SO_REUSEADDR），不像 Linux 会报 "Address already in use"

**定位方法：**

```powershell
# 检查 8000 端口监听进程
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique

# 查看所有 Python/uvicorn 进程
Get-Process | Where-Object {$_.ProcessName -like '*python*' -or $_.ProcessName -like '*uvicorn*'}
```

**解决方案：**

```powershell
# 1. 停掉所有旧进程
Stop-Process -Id <PID1>,<PID2>,<PID3> -Force

# 2. 清理 Python 缓存
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -Force | Remove-Item -Force

# 3. 启动唯一新进程
uv run uvicorn api.main:app --reload --port 8000

# 4. 验证只有一个进程
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

**预防措施：**

1. 每次启动前检查端口占用
2. 使用脚本管理进程启停
3. 添加进程 PID 记录文件

---

## 数据库相关问题

### 多数据库混淆

**问题：** 项目中存在多个数据库文件，不确定使用哪个

**定位方法：**

```python
# 查看配置文件
# api/core/config.py
DATABASE_URL: str = "sqlite+aiosqlite:///./paper_analysis.db"

# 搜索所有 .db 文件
find . -name "*.db"
```

**发现的数据库：**
- `paper_analysis.db` - 后端使用的数据库（正确）
- `data/app.db` - 旧数据库（不再使用）

**解决方案：**

确认配置文件中的 `DATABASE_URL` 指向正确的数据库

### Web 上传数据存储位置

**问题：** Web 上传的论文数据保存在哪里？

**答案：**

- **CLI 方式（旧）：** PDF → 提取 → LLM → 保存到 `summary/` → 手动导入数据库
- **Web 上传（新）：** PDF → 提取 → LLM → **直接存入数据库**
  - 文件保存：`uploads/user_<id>/<UUID>.pdf`
  - 数据保存：数据库 `papers` 表
  - **不生成 summary 文件**

**验证方法：**

```python
# 查询有 file_path 的论文（Web 上传）
SELECT id, title, file_path, original_filename, created_at 
FROM papers 
WHERE user_id=1 AND file_path IS NOT NULL
ORDER BY created_at DESC;
```

---

## 前端 UI 交互问题

### Astro Dev Toolbar 拦截点击

**问题：** 按钮明明存在，点击却无反应

**排查步骤：**

1. 打开浏览器开发者工具
2. Elements 面板检查按钮上方是否有覆盖层
3. 查看 z-index 和 pointer-events 样式
4. 检查 Astro 配置

**解决方案：**

禁用开发工具栏或调整 z-index

### File Input 隐藏导致无法触发

**问题：** `display: none` 的 file input 在某些浏览器中无法触发

**解决方案：**

```tsx
// 使用 sr-only 替代 hidden
<input type="file" className="sr-only" />
```

---

## 文件删除同步问题

### 问题描述

**症状：**
- 在前端删除论文后，数据库记录删除了
- 但 `uploads/` 目录下的 PDF 文件仍然存在
- 导致磁盘空间浪费和文件泄露

**根本原因：**

删除 API 只删除了数据库记录，未删除物理文件

**修复方案：**

```python
# api/api/papers.py
from pathlib import Path
import os

@router.delete("/{paper_id}")
async def delete_paper(paper_id: int, ...):
    # 查询论文
    paper = ...
    
    # 删除物理文件（如果存在）
    if paper.file_path:
        try:
            file_path = Path(paper.file_path)
            if file_path.exists():
                os.remove(file_path)
                logger.info(f"已删除文件: {file_path}")
        except Exception as e:
            logger.error(f"删除文件失败: {paper.file_path}, 错误: {e}")
    
    # 删除数据库记录
    await db.delete(paper)
    await db.commit()
    
    return {"message": "删除成功"}
```

**验证方法：**

```python
# 测试删除功能
import httpx

# 1. 删除论文
response = await client.delete(f"/api/v1/papers/{paper_id}", headers=headers)

# 2. 检查文件是否删除
assert not Path(file_path).exists()
```

---

## 通用排查流程

### 1. 前端问题排查

```bash
# 检查控制台错误
浏览器 F12 → Console

# 检查网络请求
浏览器 F12 → Network → 查看请求状态码和响应

# 检查元素层级
浏览器 F12 → Elements → 查看 z-index 和覆盖层
```

### 2. 后端问题排查

```bash
# 查看后端日志
# 查找 ERROR 或 WARNING 关键字

# 添加调试日志
logger.warning(f"🔥🔥🔥 调试点：变量值 = {value}")

# 检查进程
Get-Process | Where-Object {$_.ProcessName -like '*python*'}

# 检查端口占用
Get-NetTCPConnection -LocalPort 8000
```

### 3. 数据库问题排查

```python
# 创建查询脚本快速检查
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

async def check():
    engine = create_async_engine("sqlite+aiosqlite:///./paper_analysis.db")
    async_session = async_sessionmaker(engine)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT * FROM papers WHERE id=?"), (paper_id,))
        print(result.fetchall())

asyncio.run(check())
```

---

## 最佳实践

### 开发环境管理

1. **单进程原则：** 确保只有一个后端进程在运行
2. **日志优先：** 遇到问题先查日志，添加明显的调试标记
3. **增量测试：** 每次修改后立即测试，不要堆积问题
4. **清理缓存：** 修改代码后清理 `__pycache__` 和 `.pyc`

### 调试技巧

1. **使用明显的日志标记：**
   ```python
   logger.warning("🔥🔥🔥 DEBUG: 函数被调用了")
   ```

2. **分离前后端问题：**
   - 前端：浏览器开发者工具 + 网络面板
   - 后端：独立测试脚本（`test_xxx.py`）

3. **验证假设：**
   - 不要猜测，用工具验证
   - 用脚本查询数据库、检查文件、测试 API

### 文档维护

遇到新问题时，及时更新本文档：
1. 问题描述（症状）
2. 根本原因
3. 定位方法
4. 解决方案
5. 验证步骤

---

## 常用命令速查

```powershell
# 后端管理
uv run uvicorn api.main:app --reload --port 8000
Get-NetTCPConnection -LocalPort 8000 | Select OwningProcess
Stop-Process -Id <PID> -Force

# 前端管理
cd frontend
npm run dev

# 清理缓存
Get-ChildItem -Recurse -Include __pycache__ | Remove-Item -Recurse -Force

# 数据库查询
uv run python check_db.py

# API 测试
uv run python test_api_upload.py
```

---

## 更新日志

- **2026-02-05：** 初始版本，记录文件上传和多进程问题
- **2026-02-05：** 添加文件删除同步问题和解决方案

---

**记住：遇到问题时，先查本文档，可能已经有解决方案！**
