# 📚 论文身份卡自动提取系统 - 完整技术手册

> 基于 LLM 的学术论文批量智能分析工具，自动从 PDF 论文中提取结构化信息，生成"论文身份卡"，并提供多场景权重自适应评分系统。

---

## 目录

1. [系统概述](#1-系统概述)
2. [快速开始](#2-快速开始)
3. [项目架构](#3-项目架构)
4. [核心模块详解](#4-核心模块详解)
5. [评分框架](#5-评分框架)
6. [场景权重系统](#6-场景权重系统)
7. [聚类分析](#7-聚类分析)
8. [可视化系统](#8-可视化系统)
9. [配置说明](#9-配置说明)
10. [故障排查](#10-故障排查)
11. [扩展指南](#11-扩展指南)

---

## 1. 系统概述

### 1.1 核心能力

| 能力 | 说明 |
|------|------|
| 📄 **自动提取** | 从 PDF 中自动提取论文元数据、5维评分 |
| 🎯 **场景化推荐** | 按应用导向/理论突破/综合均衡等场景推荐论文 |
| 📊 **多维评分** | 学术严谨度、创新程度、实用价值、影响范围、可读性 |
| 🔄 **权重自适应** | 同一论文在不同场景下的评分动态调整 |
| 🔗 **关联分析** | 发现论文间的相似性和聚类关系 |
| 🎨 **可视化** | 静态报告 + 交互式 Streamlit Web 应用 |

### 1.2 适用场景

- **备考复试**：快速了解目标专业的研究热点和核心议题
- **文献综述**：批量处理大量论文，提取关键信息建立文献库
- **研究选题**：发现领域趋势，识别研究空白
- **日常阅读**：建立个人论文知识库，高效管理文献
- **场景化筛选**：根据不同需求快速定位合适论文

### 1.3 功能模块状态

| 模块 | 状态 | 说明 |
|------|------|------|
| **P0 基础提取** | ✅ 完成 | LLM 智能分析 + 5维评分 + 结构化输出 |
| **P1.1 权重自适应** | ✅ 完成 | 3个场景权重评分 |
| **P1.2 数据清洁** | ✅ 完成 | 编号优化、字段结构调整 |
| **P2 关联分析** | ✅ 完成 | 论文聚类、相似度计算、话题标注 |
| **P3 可视化** | ✅ 完成 | 静态报告 + Streamlit Web 应用 |

---

## 2. 快速开始

### 2.1 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 或使用 uv（推荐）
uv pip install -r requirements.txt
```

### 2.2 设置 API Key

```bash
# Windows CMD
set DEEPSEEK_API_KEY=your_api_key_here

# Windows PowerShell
$env:DEEPSEEK_API_KEY="your_api_key_here"

# Linux / macOS
export DEEPSEEK_API_KEY="your_api_key_here"
```

### 2.3 配置主题桶

编辑 `theme_buckets.md`，定义研究主题分类：

```markdown
## 你的主题1
- 次级标签A
- 次级标签B

## 你的主题2
- 次级标签C
```

### 2.4 运行完整流水线

```bash
# 使用统一 CLI 入口
python run.py extract      # P0: 基础提取
python run.py rescore      # P1: 场景重算
python run.py cluster      # P2: 聚类分析
python run.py visualize    # P3: 生成可视化图表
python run.py export       # P3: 导出静态HTML
python run.py webapp       # 启动 Streamlit Web 应用
python run.py full         # 运行完整流水线 (extract → rescore → cluster)

# 查看帮助
python run.py help
```

---

## 3. 项目架构

### 3.1 目录结构

```
MyPaperAutoSummarize/
├── 📁 src/                         # 源代码目录
│   ├── core/                       # 核心模块
│   │   ├── __init__.py             # 包入口
│   │   ├── config.py               # 配置常量
│   │   ├── models.py               # 数据结构
│   │   ├── utils.py                # 工具函数
│   │   ├── pdf_extractor.py        # PDF 文本提取
│   │   ├── llm_client.py           # LLM API 客户端
│   │   └── csv_handler.py          # CSV 操作
│   ├── visualization/              # 可视化模块
│   │   ├── __init__.py
│   │   ├── data_loader.py          # 数据加载
│   │   └── charts.py               # 图表生成
│   ├── extraction.py               # P0: 提取脚本
│   ├── rescoring.py                # P1: 重算脚本
│   ├── clustering.py               # P2: 聚类脚本
│   ├── visualize.py                # P3: 可视化脚本
│   └── static_export.py            # P3: 静态导出
│
├── 📁 config/                      # 配置文件
│   ├── prompt_paper_extraction.md  # LLM Prompt 模板
│   ├── theme_buckets.md            # 主题桶配置
│   └── scenario_weights.json       # 场景权重配置
│
├── 📁 webapp/                      # Web 应用
│   ├── app.py                      # Streamlit 主入口
│   ├── pages/                      # 页面组件
│   │   ├── 1_📊_Dashboard.py       # 概览仪表盘
│   │   ├── 2_📚_Paper_List.py      # 论文库
│   │   ├── 3_🔄_Scenario.py        # 场景对比
│   │   └── 4_🗺️_Topic_Map.py       # 话题地图
│   └── utils/                      # 工具模块
│
├── 📁 tools/                       # 独立工具
│   └── rename_pdfs.py              # PDF 重命名工具
│
├── 📁 docs/                        # 文档目录
│   └── PROJECT_MANUAL.md           # 本文件
│
├── 📁 00_inbox_pdfs/               # PDF 输入目录
├── 📁 01_extracted_json/           # JSON 输出目录
├── 📁 02_summary_csv/              # CSV 输出目录
│   ├── _all_papers.csv             # 总汇总表
│   ├── _all_papers_多场景对比表.csv # 场景对比表
│   ├── scenario_rankings/          # 场景排序表
│   └── clustering_analysis/        # 聚类结果
│
├── 📜 run.py                       # 统一 CLI 入口
└── � requirements.txt             # 依赖列表
```

### 3.2 数据流

```
PDF文件 → src/extraction.py → JSON身份卡 + CSV汇总表
                              ↓
                    src/rescoring.py → 多场景对比表 + 排序表
                              ↓
                    src/clustering.py → 聚类结果 + 相似度矩阵
                              ↓
                    webapp/ → 交互式 Web 可视化
```

---

## 4. 核心模块详解

### 4.1 auto_runner.py（P0 基础提取）

**功能**：
- 自动同步主题桶配置到文件夹结构
- 扫描 PDF 文件，显示处理状态
- 调用 LLM 提取论文信息
- 生成 JSON 身份卡和 CSV 汇总表

**输出格式**：

```json
{
  "title": "区块链赋能区域教育治理：逻辑、框架与路径",
  "authors": "郑旭东, 狄璇, 岳婷燕",
  "year": 2022,
  "venue": "现代远程教育研究",
  "keywords": ["区域教育治理", "教育数据治理", "区块链技术"],
  "domain_tags": ["教育数智化与智能治理", "区块链"],
  "paper_type": "理论研究",
  "problem": "区域教育治理存在理念缺失、结构失衡等问题",
  "methodology": "文献分析、逻辑推演与框架构建",
  "conclusion": "区块链技术可通过四层框架实现数据驱动的教育善治",
  "scores": {
    "rigor": 8.0,
    "innovation": 7.5,
    "practicality": 7.0,
    "impact": 6.5,
    "readability": 8.0,
    "overall": 7.4
  }
}
```

### 4.2 scenario_rescoring.py（P1 场景重算）

**功能**：
- 读取 P0 生成的 CSV
- 按三种场景重新计算综合评分
- 生成多场景对比表和排序表

**输出文件**：
- `_all_papers_多场景对比表.csv` - 对比同一论文在不同场景的评分
- `排序表_应用导向型.csv` - 按应用导向排序
- `排序表_理论突破型.csv` - 按理论突破排序
- `排序表_综合均衡型.csv` - 按综合均衡排序

### 4.3 paper_clustering.py（P2 聚类分析）

**功能**：
- 基于 TF-IDF 向量化论文文本
- 使用 K-means 进行聚类
- 计算论文间相似度矩阵
- 为每个聚类生成话题关键词

**输出文件**：
- `_clustering_results.csv` - 聚类结果（含话题分配）
- `_similarity_matrix.csv` - 论文相似度矩阵

---

## 5. 评分框架

### 5.1 五维评分体系

| 维度 | 英文 | 默认权重 | 定义 |
|------|------|----------|------|
| 学术严谨度 | Rigor | 30% | 方法论、证据、逻辑推导的科学性 |
| 创新程度 | Innovation | 25% | 相对于既有研究的新颖性和原创性 |
| 实用价值 | Practicality | 25% | 对实际教学、管理、工程应用的指导意义 |
| 影响范围 | Impact | 15% | 对学科发展和实践领域的潜在影响 |
| 可读性 | Readability | 5% | 表达清晰度、逻辑性、版面易读性 |

### 5.2 评分等级标准

| 分数范围 | 等级 | 典型特征 |
|----------|------|----------|
| 9-10 | 优秀 | 文献充分(>100篇)，实验严密，有对照组，统计完整 |
| 7-8.9 | 良好 | 文献充分(50-100篇)，设计合理，统计恰当 |
| 5-6.9 | 中等 | 文献适度(20-50篇)，方法描述不够详细 |
| 3-4.9 | 较差 | 文献不足(<20篇)，方法论有缺陷 |
| 0-2.9 | 不合格 | 无充分文献支撑，逻辑混乱 |

### 5.3 综合评分计算

```
综合评分 = 严谨度×0.30 + 创新度×0.25 + 实用价值×0.25 + 影响范围×0.15 + 可读性×0.05
```

### 5.4 推荐等级映射

| 综合评分 | 推荐等级 | 符号 | 建议 |
|----------|---------|------|------|
| 9.0-10.0 | 五星 | ⭐⭐⭐⭐⭐ | 强烈推荐，必读经典 |
| 7.5-8.9 | 四星 | ⭐⭐⭐⭐ | 值得深入阅读 |
| 6.0-7.4 | 三星 | ⭐⭐⭐ | 有参考价值 |
| 4.0-5.9 | 二星 | ⭐⭐ | 参考价值有限 |
| 0-3.9 | 一星 | ⭐ | 不推荐 |

---

## 6. 场景权重系统

### 6.1 三种评分场景

#### 应用导向型
**权重**：practicality 40% | rigor 25% | innovation 15% | impact 15% | readability 5%

**适用场景**：
- 学校想引入 AI 辅助教学，需要找有成熟案例的论文
- 企业想优化流程，需要找有具体工具/方法的研究
- 教师设计新课程，需要找可直接借鉴的教学方案

#### 理论突破型
**权重**：innovation 40% | impact 20% | rigor 25% | practicality 10% | readability 5%

**适用场景**：
- 博士生需要找学位论文的理论基础
- 研究员想了解最前沿的思想框架
- 学科评估时需要找代表性的创新论文

#### 综合均衡型（默认）
**权重**：rigor 30% | innovation 25% | practicality 25% | impact 15% | readability 5%

**适用场景**：
- 全面了解领域研究现状
- 综述论文作者选择代表性文献
- 学科主任了解整体研究水平

### 6.2 扩展新场景

编辑 `scenario_weights.json` 添加新场景：

```json
{
  "scenarios": {
    "新场景名称": {
      "description": "场景描述",
      "weights": {
        "rigor": 0.25,
        "innovation": 0.25,
        "practicality": 0.25,
        "impact": 0.20,
        "readability": 0.05
      }
    }
  }
}
```

---

## 7. 聚类分析

### 7.1 聚类流程

```
论文 → 提取文本字段 → 分词 → 向量化 → 计算相似度 → 聚类
```

### 7.2 各步骤详解

| 步骤 | 操作 | 当前实现 |
|------|------|----------|
| 文本合并 | 拼接关键字段 | 关键词 + 研究问题 + 核心结论 + 主要贡献 |
| 分词 | 中文切词 | jieba 分词，过滤停用词 |
| 向量化 | 文本→数值向量 | TF-IDF（词频-逆文档频率） |
| 聚类 | 相似向量归组 | K-means（基于向量距离） |

### 7.3 TF-IDF 核心思想

```
词的重要性 = 该词在本文出现频率(TF) × 该词在所有文档中的稀有度(IDF)
```

- **高频常见词**（如"教育"、"研究"）→ 权重低
- **低频特征词**（如"职业教育"、"政策执行"）→ 权重高

### 7.4 优化方向

| 优化项 | 工作量 | 效果预期 |
|--------|--------|----------|
| 增加关键词权重 | 5分钟 | 中等 |
| 加入领域标签字段 | 5分钟 | 中等 |
| 自定义词典 | 10分钟 | 较好 |
| 换用 LDA 主题模型 | 30分钟 | 较好（允许多话题） |
| 手动指定 K 值 | 1分钟 | 快速验证 |

修改 `paper_clustering.py` 中的配置：
```python
MIN_K = 3  # 最小聚类数
MAX_K = 8  # 最大聚类数
```

---

## 8. 可视化系统

### 8.1 Streamlit Web 应用

**启动命令**：
```bash
uv run streamlit run paper_visualization/app.py
```

**访问地址**：http://localhost:8501

### 8.2 功能页面

#### 📊 Dashboard（概览仪表盘）
- 关键统计指标
- 5维评分分布箱线图
- 年份分布柱状图
- TOP 10 推荐论文卡片（带雷达图）

#### 📚 Paper List（论文库）
- 全文搜索（标题/关键词/作者）
- 多维筛选（年份/话题/评分等级）
- 论文详情展开（5维雷达图、相似论文推荐）

#### 🔄 Scenario Comparison（场景对比）
- 双场景排名对比
- Bump Chart（4场景排名变化轨迹）
- 排名波动分析表

#### 🗺️ Topic Map（话题地图）
- 话题聚类气泡图
- 话题详情面板（关键词、统计）
- 话题内论文浏览

### 8.3 配色方案

| 类型 | 颜色 | 色值 |
|------|------|------|
| Primary | 蓝 | #2563EB |
| Secondary | 紫 | #7C3AED |
| Success | 绿 | #10B981 |
| Warning | 橙 | #F59E0B |
| Danger | 红 | #EF4444 |

---

## 9. 配置说明

### 9.1 API 配置

编辑 `core/config.py` 或 `auto_runner.py`：

```python
# DeepSeek（默认）
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

# OpenAI
# API_KEY = os.environ.get("OPENAI_API_KEY", "")
# BASE_URL = "https://api.openai.com/v1"
# MODEL_NAME = "gpt-4o"
```

### 9.2 请求参数

```python
REQUEST_TIMEOUT = 180.0   # API 超时时间（秒）
REQUEST_INTERVAL = 5      # 请求间隔（秒）
MAX_PDF_CHARS = 30000     # PDF 文本最大字符数
```

### 9.3 PDF 命名规范

建议使用数字前缀命名：

```
01_区块链赋能教育治理_郑旭东.pdf
02_人工智能赋能教育评价_王某某.pdf
...
09_智慧教育平台建设_张某某.pdf
10_教育数字化转型_陈某某.pdf
```

> ⚠️ 使用两位数字前缀（01, 02, ..., 09, 10），避免排序问题

---

## 10. 故障排查

### 10.1 API 连接失败

1. 检查环境变量是否正确设置
2. 检查 API Key 是否有效
3. 检查网络连接是否正常

### 10.2 JSON 解析失败

可能原因：
- 模型返回格式不规范
- PDF 内容提取不完整

解决方法：
- 检查 `error_log.txt` 查看具体错误
- 重新运行，使用覆盖模式处理失败的文件

### 10.3 数据加载失败（可视化）

- 检查数据文件路径是否正确
- 确认文件编码为 UTF-8-BOM
- 检查 CSV 文件是否包含必需列

### 10.4 图表显示异常

- 刷新页面
- 清除 Streamlit 缓存：`streamlit cache clear`
- 检查数据是否包含 NaN 值

### 10.5 中文路径报错

- 确保使用 UTF-8 编码
- 避免路径中包含特殊字符

---

## 11. 扩展指南

### 11.1 添加新的评分维度

1. 修改 `prompt_paper_extraction.md` 中的 JSON Schema
2. 更新 `core/config.py` 中的 `CSV_FIELD_MAP`
3. 更新 `scenario_weights.json` 中的权重配置

### 11.2 添加新的可视化页面

1. 在 `paper_visualization/pages/` 创建新页面
2. 使用 `utils/data_loader.py` 加载数据
3. 使用 `utils/charts.py` 生成图表

### 11.3 自定义聚类

修改 `paper_clustering.py`：

```python
# 自定义词典
jieba.load_userdict("custom_dict.txt")

# 调整输入字段权重
def preprocess_text(row):
    keywords = str(row['关键词']) if pd.notna(row['关键词']) else ''
    text_parts = [
        keywords, keywords, keywords,  # 关键词权重×3
        row['领域标签'],
        row['研究问题'],
        row['核心结论'],
    ]
    return ' '.join([str(t) for t in text_parts if pd.notna(t)])
```

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.1 | 2026-02 | P2 重构：拆分模块、统一可视化 |
| v2.0 | 2026-01 | 完成 P0-P3 全部功能 |
| v1.0 | 2026-01 | 初始版本，P0 基础提取 |

---

## 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供 LLM API 服务
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF 文本提取
- [Streamlit](https://streamlit.io/) - Web 可视化框架
- [Plotly](https://plotly.com/) - 交互式图表库

---

**License**: MIT License
