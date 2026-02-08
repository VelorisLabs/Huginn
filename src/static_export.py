"""
生成静态 HTML 网站
将 Streamlit 应用转换为可以离线查看的静态 HTML 页面
"""

import html as html_mod
import pandas as pd
from pathlib import Path
import json

# 数据路径
from .core.config import BASE_DIR, CSV_DIR

DATA_DIR = CSV_DIR
OUTPUT_DIR = BASE_DIR / "static_html_export"

# 延迟加载的数据缓存
_data_cache = {}


def _load_data():
    """延迟加载数据，避免模块导入时就执行 pd.read_csv()"""
    if _data_cache:
        return _data_cache
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print("正在加载数据...")
    papers = pd.read_csv(DATA_DIR / "_all_papers.csv", encoding='utf-8-sig')
    scenario_comparison = pd.read_csv(DATA_DIR / "_all_papers_多场景对比表.csv", encoding='utf-8-sig')
    
    _data_cache['papers'] = papers
    _data_cache['scenario_comparison'] = scenario_comparison
    _data_cache['total_papers'] = len(papers)
    _data_cache['total_topics'] = papers['主题聚类'].nunique() if '主题聚类' in papers.columns else 6
    _data_cache['avg_score'] = papers['综合评分'].mean() if '综合评分' in papers.columns else 0
    _data_cache['max_score'] = papers['综合评分'].max() if '综合评分' in papers.columns else 0
    _data_cache['year_min'] = papers['年份'].min() if '年份' in papers.columns else 2020
    _data_cache['year_max'] = papers['年份'].max() if '年份' in papers.columns else 2024
    
    return _data_cache


def _esc(value) -> str:
    """HTML 转义，防止 XSS"""
    return html_mod.escape(str(value)) if value is not None else ''

# 通用样式
COMMON_STYLE = """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
        background: linear-gradient(135deg, #0e1117 0%, #1a1d29 100%);
        color: #FAFAFA;
        min-height: 100vh;
        padding: 20px;
    }
    
    .container {
        max-width: 1400px;
        margin: 0 auto;
        animation: fadeIn 0.6s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    /* 导航栏 */
    .navbar {
        background: linear-gradient(135deg, #1a1d29 0%, #2d3748 100%);
        padding: 20px 30px;
        border-radius: 16px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    
    .navbar h1 {
        font-size: 1.8rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0;
    }
    
    .nav-links {
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
    }
    
    .nav-links a {
        color: #E2E8F0;
        text-decoration: none;
        padding: 10px 20px;
        border-radius: 8px;
        transition: all 0.3s ease;
        font-weight: 600;
    }
    
    .nav-links a:hover,
    .nav-links a.active {
        background: rgba(102, 126, 234, 0.2);
        transform: translateY(-2px);
    }
    
    /* 标题 */
    h1 {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        animation: slideIn 0.6s ease-out;
    }
    
    h2 {
        color: #E2E8F0;
        font-weight: 700;
        margin: 2rem 0 1rem 0;
        animation: slideIn 0.7s ease-out;
    }
    
    h3 {
        color: #CBD5E0;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* 指标卡片 */
    .metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin: 30px 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeIn 0.5s ease-out;
    }
    
    .metric-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 12px 24px rgba(102, 126, 234, 0.4);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .metric-value {
        font-size: 2rem;
        color: #FFFFFF;
        font-weight: 700;
    }
    
    /* 表格 */
    table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        margin: 20px 0;
        animation: fadeIn 0.7s ease-out;
    }
    
    thead th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 700;
        padding: 15px;
        text-align: left;
    }
    
    tbody td {
        padding: 15px;
        border-bottom: 1px solid rgba(226, 232, 240, 0.1);
        background: rgba(255, 255, 255, 0.05);
        transition: background-color 0.2s ease;
    }
    
    tbody tr:hover td {
        background-color: rgba(102, 126, 234, 0.1);
    }
    
    /* 分隔线 */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.5), transparent);
        margin: 2rem 0;
    }
    
    /* 内容区域 */
    .content {
        color: #E2E8F0;
        line-height: 1.8;
    }
    
    .content p {
        margin-bottom: 1rem;
    }
    
    .content strong {
        color: #FFFFFF;
        font-weight: 700;
    }
    
    .content ul {
        margin-left: 20px;
        margin-bottom: 1rem;
    }
    
    .content li {
        color: #CBD5E0;
        margin-bottom: 0.5rem;
    }
    
    /* 卡片 */
    .card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    /* 标签 */
    .tag {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.875rem;
        margin-right: 8px;
        margin-bottom: 8px;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    /* 滚动条 */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* 搜索框 */
    .search-box {
        width: 100%;
        padding: 12px 20px;
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.05);
        color: #FAFAFA;
        font-size: 1rem;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .search-box:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
    }
    
    /* 响应式 */
    @media (max-width: 768px) {
        .navbar {
            flex-direction: column;
            gap: 15px;
        }
        
        .nav-links {
            width: 100%;
            justify-content: center;
        }
        
        h1 {
            font-size: 2rem;
        }
        
        .metrics {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        }
        
        table {
            font-size: 0.9rem;
        }
    }
</style>
"""

def generate_navbar(active_page="index"):
    """生成导航栏"""
    pages = [
        ("index.html", "📚 主页", "index"),
        ("dashboard.html", "📊 数据面板", "dashboard"),
        ("papers.html", "📚 论文列表", "papers"),
        ("scenarios.html", "🔄 场景对比", "scenarios"),
    ]
    
    links_html = ""
    for href, title, page_id in pages:
        active_class = ' class="active"' if page_id == active_page else ''
        links_html += f'<a href="{href}"{active_class}>{title}</a>'
    
    return f"""
    <div class="navbar">
        <h1>📚 论文分析可视化系统</h1>
        <div class="nav-links">
            {links_html}
        </div>
    </div>
    """

def generate_index_page():
    """生成首页"""
    data = _load_data()
    total_papers = data['total_papers']
    total_topics = data['total_topics']
    avg_score = data['avg_score']
    max_score = data['max_score']
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>论文分析可视化系统 - 主页</title>
    {COMMON_STYLE}
</head>
<body>
    <div class="container">
        {generate_navbar("index")}
        
        <h1>📚 论文分析可视化系统</h1>
        <h3>欢迎使用论文可视化仪表板</h3>
        
        <div class="content">
            <p>本系统为 <strong>{_esc(total_papers)} 篇学术论文</strong> 提供交互式可视化分析：</p>
            
            <ul>
                <li><strong>五维评分体系</strong>：严谨性、创新性、实用性、影响力、可读性</li>
                <li><strong>四种评估场景</strong>：P0 基准线、应用导向、理论突破、平衡型</li>
                <li><strong>六大主题聚类</strong>：基于 TF-IDF + K-means 自动生成</li>
                <li><strong>相似度矩阵</strong>：74×74 论文相似度评分</li>
            </ul>
            
            <hr>
            
            <h3>使用导航栏浏览不同页面：</h3>
            
            <div class="card">
                <h3>📊 数据面板</h3>
                <p>统计概览、评分分布、TOP 10 论文</p>
            </div>
            
            <div class="card">
                <h3>📚 论文列表</h3>
                <p>搜索、筛选和浏览所有论文</p>
            </div>
            
            <div class="card">
                <h3>🔄 场景对比</h3>
                <p>对比不同评估场景下的排名变化</p>
            </div>
        </div>
        
        <hr>
        
        <h2>快速统计</h2>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">论文总数</div>
                <div class="metric-value">{_esc(total_papers)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">主题聚类</div>
                <div class="metric-value">{_esc(total_topics)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">平均评分</div>
                <div class="metric-value">{avg_score:.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">最高评分</div>
                <div class="metric-value">{max_score:.2f}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html

def generate_dashboard_page():
    """生成数据面板页"""
    data = _load_data()
    papers = data['papers']
    total_papers = data['total_papers']
    total_topics = data['total_topics']
    avg_score = data['avg_score']
    max_score = data['max_score']
    year_min = data['year_min']
    year_max = data['year_max']
    
    # 获取 TOP 10 论文
    score_col = '综合评分' if '综合评分' in papers.columns else papers.columns[0]
    top_10 = papers.nlargest(10, score_col)
    
    top_papers_html = ""
    for idx, (_, paper) in enumerate(top_10.iterrows(), 1):
        title = _esc(paper.get('标题', 'N/A'))
        paper_id = _esc(paper.get('编号', 'N/A'))
        score = paper.get(score_col, 0)
        
        top_papers_html += f"""
        <div class="card">
            <h3>#{idx} {paper_id}</h3>
            <p><strong>标题：</strong>{title}</p>
            <p><strong>评分：</strong><span class="tag">{score:.2f}</span></p>
        </div>
        """
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据面板 - 论文分析系统</title>
    {COMMON_STYLE}
</head>
<body>
    <div class="container">
        {generate_navbar("dashboard")}
        
        <h1>📊 数据面板</h1>
        <p class="content">所有论文的总览和关键统计数据</p>
        
        <h2>关键指标</h2>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">论文总数</div>
                <div class="metric-value">{_esc(total_papers)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">主题聚类</div>
                <div class="metric-value">{_esc(total_topics)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">平均评分</div>
                <div class="metric-value">{avg_score:.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">最高评分</div>
                <div class="metric-value">{max_score:.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">年份范围</div>
                <div class="metric-value">{_esc(year_min)}-{_esc(year_max)}</div>
            </div>
        </div>
        
        <hr>
        
        <h2>TOP 10 推荐论文</h2>
        {top_papers_html}
    </div>
</body>
</html>
"""
    return html

def generate_papers_list_page():
    """生成论文列表页"""
    data = _load_data()
    papers = data['papers']
    total_papers = data['total_papers']
    
    # 生成论文表格
    papers_html = """
    <input type="text" id="searchBox" class="search-box" placeholder="🔍 搜索论文标题、编号或作者..." onkeyup="filterTable()">
    
    <table id="papersTable">
        <thead>
            <tr>
                <th>编号</th>
                <th>标题</th>
                <th>作者</th>
                <th>年份</th>
                <th>综合评分</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for _, paper in papers.iterrows():
        paper_id = _esc(paper.get('编号', 'N/A'))
        title = _esc(paper.get('标题', 'N/A'))
        author = _esc(paper.get('作者', 'N/A'))
        year = _esc(paper.get('年份', 'N/A'))
        score = paper.get('综合评分', 0)
        
        papers_html += f"""
            <tr>
                <td>{paper_id}</td>
                <td>{title}</td>
                <td>{author}</td>
                <td>{year}</td>
                <td><span class="tag">{score:.2f}</span></td>
            </tr>
        """
    
    papers_html += """
        </tbody>
    </table>
    
    <script>
    function filterTable() {
        const input = document.getElementById('searchBox');
        const filter = input.value.toUpperCase();
        const table = document.getElementById('papersTable');
        const tr = table.getElementsByTagName('tr');
        
        for (let i = 1; i < tr.length; i++) {
            const td = tr[i].getElementsByTagName('td');
            let found = false;
            
            for (let j = 0; j < td.length; j++) {
                if (td[j]) {
                    const txtValue = td[j].textContent || td[j].innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        found = true;
                        break;
                    }
                }
            }
            
            tr[i].style.display = found ? '' : 'none';
        }
    }
    </script>
    """
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>论文列表 - 论文分析系统</title>
    {COMMON_STYLE}
</head>
<body>
    <div class="container">
        {generate_navbar("papers")}
        
        <h1>📚 论文列表</h1>
        <p class="content">浏览所有 {total_papers} 篇论文</p>
        
        <hr>
        
        {papers_html}
    </div>
</body>
</html>
"""
    return html

def generate_scenarios_page():
    """生成场景对比页"""
    data = _load_data()
    scenario_comparison = data['scenario_comparison']
    
    # 获取场景数据
    scenarios_html = ""
    
    if '综合评分_应用导向型' in scenario_comparison.columns:
        scenarios = ['P0基准', '应用导向型', '理论突破型', '综合均衡型']
        score_cols = {
            'P0基准': '综合评分',
            '应用导向型': '综合评分_应用导向型',
            '理论突破型': '综合评分_理论突破型',
            '综合均衡型': '综合评分_综合均衡型'
        }
        
        for scenario in scenarios:
            col = score_cols.get(scenario, '综合评分')
            if col in scenario_comparison.columns:
                top_5 = scenario_comparison.nlargest(5, col)
                
                scenarios_html += f"""
                <div class="card">
                    <h3>{scenario}</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>排名</th>
                                <th>编号</th>
                                <th>标题</th>
                                <th>评分</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                
                for idx, (_, paper) in enumerate(top_5.iterrows(), 1):
                    paper_id = _esc(paper.get('编号', 'N/A'))
                    title = _esc(paper.get('标题', 'N/A'))
                    if len(title) > 50:
                        title = title[:50] + "..."
                    score = paper.get(col, 0)
                    
                    scenarios_html += f"""
                            <tr>
                                <td>#{idx}</td>
                                <td>{paper_id}</td>
                                <td>{title}</td>
                                <td><span class="tag">{score:.2f}</span></td>
                            </tr>
                    """
                
                scenarios_html += """
                        </tbody>
                    </table>
                </div>
                """
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>场景对比 - 论文分析系统</title>
    {COMMON_STYLE}
</head>
<body>
    <div class="container">
        {generate_navbar("scenarios")}
        
        <h1>🔄 场景对比</h1>
        <p class="content">对比不同评估场景下的 TOP 5 论文排名</p>
        
        <hr>
        
        {scenarios_html}
    </div>
</body>
</html>
"""
    return html

def main():
    """生成所有静态 HTML 页面（入口函数）"""
    print("正在生成静态 HTML 页面...")

    pages = {
        "index.html": generate_index_page(),
        "dashboard.html": generate_dashboard_page(),
        "papers.html": generate_papers_list_page(),
        "scenarios.html": generate_scenarios_page(),
    }

    for filename, content in pages.items():
        output_path = OUTPUT_DIR / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ 已生成: {filename}")

    # 创建 README
    readme_content = """# 论文分析可视化系统 - 静态 HTML 版本

## 使用说明

1. 双击打开 `index.html` 即可在浏览器中查看
2. 使用顶部导航栏在不同页面间切换
3. 所有数据已预加载，可以离线查看

## 页面说明

- **index.html**: 主页，系统介绍和快速统计
- **dashboard.html**: 数据面板，关键指标和 TOP 10 论文
- **papers.html**: 论文列表，可搜索的完整论文表格
- **scenarios.html**: 场景对比，不同评估场景的排名对比

## 注意事项

- 这是静态版本，不包含交互式图表和动态筛选功能
- 如需完整功能，请使用 Streamlit 应用版本
- 数据快照时间：生成时的数据状态

---

生成时间：2026-01-14
"""

    with open(OUTPUT_DIR / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"\n✅ 所有文件已生成到: {OUTPUT_DIR.absolute()}")
    print(f"\n📂 包含文件:")
    for file in OUTPUT_DIR.glob("*"):
        print(f"   - {file.name}")
    print(f"\n💡 打开 {OUTPUT_DIR.absolute() / 'index.html'} 即可查看")


if __name__ == "__main__":
    main()
