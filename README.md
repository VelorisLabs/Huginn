# 🪶 Huginn

> **Huginn (胡金)** 是北欧神话中主神奥丁肩上的两只渡鸦之一，名字在古诺尔斯语中意为 **"思想"**。  
> 每日清晨，Huginn 与 Muninn 飞越九界，将世间万象带回奥丁的王座。  
> 本项目是一个基于 **AI 大语言模型** 构建的学术论文智能分析平台 —— 如同 Huginn 飞越论文的海洋，带回知识与洞察。

## 📖 项目简介

Huginn 是一个为研究者打造的论文智能分析系统，专注于 **AI 驱动的文献解读** 与 **结构化知识提取**。它采用 FastAPI + Astro 的前后端分离架构，结合 DeepSeek 大模型，实现了从 PDF 上传到多维度分析的全自动流水线。

**核心理念**: 让 AI 成为你的学术渡鸦，飞越万卷论文，带回你需要的一切。

## ✨ 核心特性

- **📄 智能提取**: 从 PDF 自动提取标题、作者、研究问题、方法论、核心结论、实现路径等结构化信息，生成"论文身份卡"。
- **🎯 场景化评分**: 应用导向型 / 理论突破型 / 综合均衡型三种评分模式，五维雷达图（学术严谨度、创新程度、实用价值、影响范围、可读性）。
- **🔬 深度分析**: 基于论文全文的 AI 深度解读，生成详细的技术分析报告，支持二次对话式探索。
- **🧩 主题聚类**: 基于 TF-IDF + 余弦相似度的自动聚类分析，发现论文间的内在关联与研究脉络。
- **📦 批量处理**: 支持 PDF / ZIP 批量上传，异步并行处理，实时进度反馈。
- **�️ 主题管理**: 自定义研究主题分组，多工作区管理，灵活组织文献库。
- **🔐 用户系统**: JWT 认证，多用户隔离，安全的工作区权限管理。

## � 项目结构

```text
Huginn/
├── api/                        # 🚀 FastAPI 后端服务
│   ├── core/                   #    核心模块 (配置、数据库、安全、LLM客户端、任务管理)
│   ├── models/                 #    SQLAlchemy ORM 模型
│   ├── routes/                 #    API 路由 (论文、上传、聚类、主题、导出...)
│   ├── schemas/                #    Pydantic 请求/响应模式
│   └── main.py                 #    FastAPI 应用入口
│
├── frontend/                   # 🎨 Astro + React 前端
│   ├── src/components/         #    React 组件 (Dashboard、聚类视图、证据面板...)
│   ├── src/layouts/            #    页面布局
│   ├── src/lib/                #    API 客户端 & 工具函数
│   └── src/pages/              #    Astro 页面路由
│
├── src/                        # ⚙️ CLI 核心分析引擎
│   ├── core/                   #    配置、LLM客户端、PDF提取器
│   ├── extraction.py           #    论文信息提取
│   ├── rescoring.py            #    场景重算评分
│   └── clustering.py           #    聚类分析
│
├── config/                     # 📋 配置文件
│   ├── prompt_paper_extraction.md    # LLM 提取 Prompt 模板
│   ├── prompt_deep_analysis.md       # LLM 深度分析 Prompt 模板
│   ├── scenario_weights.json         # 场景权重配置
│   └── theme_buckets.md              # 主题桶定义
│
├── scripts/                    # 🔧 工具脚本
│   ├── migrations/             #    数据库迁移
│   ├── maintenance/            #    维护工具
│   └── debug/                  #    调试检查
│
├── tests/                      # 🧪 测试用例
├── docs/                       # 📖 项目文档
├── deploy/                     # 🐳 部署配置 (Docker, Nginx)
│
├── run.py                      # 统一 CLI 入口
├── start.ps1                   # ⚡ 一键启动 (PowerShell)
├── start.bat                   # ⚡ 一键启动 (双击运行)
├── requirements.txt            # Python 依赖
└── requirements-dev.txt        # 开发/测试依赖
```

## �️ 前置要求

- **Python**: >= 3.11
- **Node.js**: >= 18.0
- **包管理器**: UV (推荐) 或 pip
- **LLM API Key**: DeepSeek API Key ([申请地址](https://platform.deepseek.com/))

## 🚀 快速开始

### 1. 克隆与初始化

```powershell
# 克隆项目
git clone https://github.com/yourusername/Huginn.git
cd Huginn

# 配置环境变量
cp deploy/.env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY 和 SECRET_KEY
```

### 2. 一键启动

```powershell
# Windows 用户直接双击 start.bat，或在 PowerShell 中运行：
.\start.ps1
```

脚本会自动完成：创建虚拟环境 → 安装依赖 → 初始化数据库 → 启动后端 → 启动前端。

### 3. 手动启动

```powershell
# 终端 1：启动后端
uv run python run.py api

# 终端 2：启动前端
cd frontend
npm install
npm run dev
```

### 4. 开始使用

访问 **http://localhost:4321**，使用测试账号登录：

| 邮箱 | 密码 |
|------|------|
| test@huginn.com | test123 |

上传 PDF 论文，Huginn 会自动提取信息、生成评分、构建论文身份卡。

## 🔧 CLI 模式

用于批量处理本地 PDF 文件（无需启动 Web 服务）：

```powershell
python run.py extract    # 提取论文信息
python run.py rescore    # 场景重算评分
python run.py cluster    # 聚类分析
python run.py full       # 完整流水线
```

## 🎯 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端** | FastAPI + SQLAlchemy + SQLite | 异步架构，轻量部署 |
| **前端** | Astro + React + Tailwind CSS | Islands 架构，按需水合 |
| **AI 引擎** | DeepSeek API (AsyncOpenAI) | 纯异步调用，无阻塞 |
| **文本分析** | TF-IDF + jieba + scikit-learn | 中文论文聚类 |
| **部署** | Docker + Nginx | 容器化一键部署 |

## � 文档

- [完整技术手册](docs/PROJECT_MANUAL.md) — 架构设计、模块详解、API 文档
- [部署指南](deploy/DEPLOYMENT.md) — Docker 部署、Nginx 配置、HTTPS 设置
- [故障排查指南](docs/TROUBLESHOOTING_GUIDE.md) — 常见问题与解决方案

## ❓ 常见问题

**Q: 支持哪些 LLM 模型？**  
A: 默认使用 DeepSeek Chat，同时兼容所有 OpenAI 兼容接口（GPT-4o、GPT-3.5-Turbo 等），在 `.env` 中切换即可。

**Q: 支持英文论文吗？**  
A: 完全支持。LLM 提取和评分对中英文论文均有效，聚类分析使用 jieba 分词主要优化了中文场景。

**Q: 数据存储在哪里？**  
A: 使用本地 SQLite 数据库，所有数据存储在项目根目录的 `paper_analysis.db` 中，PDF 文件存储在 `uploads/` 目录。

---

**License**: MIT  
**Author**: Veloris Lab
