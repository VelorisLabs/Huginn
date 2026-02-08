"""
图表生成模块
统一的图表创建功能
"""

import pandas as pd
from pathlib import Path

# 延迟导入，避免依赖问题
plt = None
sns = None


def _init_matplotlib():
    """延迟初始化 matplotlib"""
    global plt
    if plt is None:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as _plt
        plt = _plt
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
    return plt


def _init_seaborn():
    """延迟初始化 seaborn"""
    global sns
    if sns is None:
        import seaborn as _sns
        sns = _sns
    return sns


def _get_chinese_font_path():
    """获取中文字体路径"""
    possible_fonts = [
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/msyh.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    ]
    for fp in possible_fonts:
        if Path(fp).exists():
            return fp
    return None


def create_wordcloud(df: pd.DataFrame, output_path: Path = None):
    """
    生成关键词词云
    
    Args:
        df: 包含'关键词'列的DataFrame
        output_path: 输出图片路径，如果为 None 则返回词云对象
        
    Returns:
        WordCloud 对象或 None
    """
    try:
        from wordcloud import WordCloud
    except ImportError:
        print("[!] 词云功能需要安装wordcloud库: pip install wordcloud")
        return None
    
    plt = _init_matplotlib()
    
    if '关键词' not in df.columns:
        print("[!] CSV中没有'关键词'列")
        return None
    
    keywords_series = df['关键词'].dropna()
    if keywords_series.empty:
        print("[!] 关键词列为空")
        return None
    
    # 拆分关键词并统计频率
    all_keywords = []
    for kw_str in keywords_series:
        keywords = [k.strip() for k in str(kw_str).split(',') if k.strip()]
        all_keywords.extend(keywords)
    
    if not all_keywords:
        print("[!] 没有有效关键词")
        return None
    
    word_freq = pd.Series(all_keywords).value_counts().to_dict()
    
    font_path = _get_chinese_font_path()
    
    wc = WordCloud(
        font_path=font_path,
        width=1200,
        height=600,
        background_color='white',
        max_words=100,
        colormap='viridis',
    )
    wc.generate_from_frequencies(word_freq)
    
    if output_path:
        plt.figure(figsize=(12, 6))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.title('Keywords Word Cloud', fontsize=16, pad=10)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[OK] 词云已保存: {output_path}")
    
    return wc


def create_type_distribution(df: pd.DataFrame, output_path: Path = None):
    """
    生成论文类型分布图
    
    Args:
        df: 包含'论文类型'列的DataFrame
        output_path: 输出图片路径
    """
    plt = _init_matplotlib()
    
    if '论文类型' not in df.columns:
        print("[!] CSV中没有'论文类型'列")
        return None
    
    type_counts = df['论文类型'].dropna().value_counts()
    if type_counts.empty:
        print("[!] 论文类型列为空")
        return None
    
    colors = plt.cm.Set3(range(len(type_counts)))
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 饼图
    ax1.pie(
        type_counts.values,
        labels=type_counts.index,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        pctdistance=0.75,
    )
    ax1.set_title('Paper Type Distribution (Pie)', fontsize=14)
    
    # 柱状图
    bars = ax2.bar(type_counts.index, type_counts.values, color=colors)
    ax2.set_xlabel('Paper Type', fontsize=12)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('Paper Type Distribution (Bar)', fontsize=14)
    ax2.tick_params(axis='x', rotation=30)
    
    for bar, count in zip(bars, type_counts.values):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            str(count),
            ha='center',
            va='bottom',
            fontsize=10
        )
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[OK] 分布图已保存: {output_path}")
    
    return fig


def create_year_theme_heatmap(df: pd.DataFrame, output_path: Path = None):
    """
    生成年份-主题热力图
    
    Args:
        df: 包含'年份'和'领域标签'列的DataFrame
        output_path: 输出图片路径
    """
    plt = _init_matplotlib()
    sns = _init_seaborn()
    
    if '年份' not in df.columns or '领域标签' not in df.columns:
        print("[!] CSV中缺少'年份'或'领域标签'列")
        return None
    
    def extract_theme_bucket(tags_str):
        if pd.isna(tags_str):
            return None
        tags = str(tags_str).split(',')
        return tags[0].strip() if tags else None
    
    df_copy = df.copy()
    df_copy['主题桶'] = df_copy['领域标签'].apply(extract_theme_bucket)
    df_copy = df_copy.dropna(subset=['年份', '主题桶'])
    
    if df_copy.empty:
        print("[!] 没有有效的年份-主题数据")
        return None
    
    df_copy['年份'] = df_copy['年份'].astype(int)
    pivot = pd.crosstab(df_copy['主题桶'], df_copy['年份'])
    
    if pivot.empty:
        print("[!] 交叉表为空")
        return None
    
    n_themes = len(pivot.index)
    n_years = len(pivot.columns)
    fig_width = max(10, n_years * 0.8)
    fig_height = max(6, n_themes * 0.6)
    
    plt.figure(figsize=(fig_width, fig_height))
    sns.heatmap(
        pivot,
        annot=True,
        fmt='d',
        cmap='YlOrRd',
        linewidths=0.5,
        cbar_kws={'label': 'Paper Count'}
    )
    plt.title('Year-Theme Distribution Heatmap', fontsize=14, pad=15)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Theme Bucket', fontsize=12)
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[OK] 热力图已保存: {output_path}")
    
    return pivot
