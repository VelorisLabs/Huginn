"""
P2 论文聚类分析脚本
功能：基于论文结构化数据计算相似度、自动聚类、生成话题标签
输入：02_summary_csv/_all_papers.csv
输出：02_summary_csv/clustering_analysis/ 目录下的聚类结果文件
"""

import logging
import pandas as pd
import numpy as np
import jieba
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from collections import Counter

logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
from .core.config import CSV_DIR

INPUT_CSV = CSV_DIR / "_all_papers.csv"
OUTPUT_DIR = CSV_DIR / "clustering_analysis"

# 用于计算相似度的文本字段
TEXT_FIELDS = ['关键词', '研究问题', '核心结论', '主要贡献']

# 聚类参数
MIN_K = 3  # 最小聚类数
MAX_K = 8  # 最大聚类数

# 停用词（常见无意义词）
STOPWORDS = {
    '的', '了', '是', '在', '和', '与', '等', '对', '为', '以', '及', '或',
    '中', '上', '下', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '个', '种', '类', '方面', '问题', '研究', '分析', '探讨', '论文', '文章',
    '通过', '进行', '提出', '基于', '采用', '针对', '结合', '围绕', '关于',
    '主要', '其中', '同时', '并且', '因此', '然而', '但是', '如何', '什么',
    '可以', '需要', '应该', '能够', '具有', '存在', '包括', '涉及', '体现',
    '不同', '相关', '重要', '有效', '积极', '显著', '明显', '充分', '进一步',
}


# ============================================================
# 文本预处理
# ============================================================
def preprocess_text(row):
    """合并论文的多个文本字段"""
    text_parts = []
    for field in TEXT_FIELDS:
        if field in row and pd.notna(row[field]):
            text_parts.append(str(row[field]))
    return ' '.join(text_parts)


def tokenize(text):
    """jieba分词 + 过滤停用词和短词"""
    words = jieba.lcut(text)
    # 过滤：长度<2、纯数字、停用词
    filtered = [w for w in words
                if len(w) >= 2
                and not w.isdigit()
                and w not in STOPWORDS]
    return filtered


# ============================================================
# 聚类分析核心
# ============================================================
def find_best_k(tfidf_matrix, min_k=None, max_k=None):
    """使用轮廓系数自动选择最优聚类数（根据数据集大小动态调整范围）"""
    n_samples = tfidf_matrix.shape[0]
    
    if min_k is None:
        min_k = max(2, min(MIN_K, n_samples - 1))
    if max_k is None:
        max_k = max(min_k, min(MAX_K, n_samples - 1))
    
    if n_samples < 3:
        return 1
    
    best_k = min_k
    best_score = -1
    scores = {}

    for k in range(min_k, max_k + 1):
        if k >= n_samples:
            break
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(tfidf_matrix)
        score = silhouette_score(tfidf_matrix, labels)
        scores[k] = score
        if score > best_score:
            best_score = score
            best_k = k

    logger.info("Silhouette score analysis:")
    for k, score in scores.items():
        marker = " <- BEST" if k == best_k else ""
        logger.info("  K=%d: %.4f%s", k, score, marker)

    return best_k


def generate_topic_label(cluster_indices, df, vectorizer, tfidf_matrix, top_n=5):
    """基于聚类内论文的高频词生成话题标签"""
    # 方法1：基于TF-IDF权重
    cluster_tfidf = tfidf_matrix[cluster_indices].toarray()
    mean_tfidf = cluster_tfidf.mean(axis=0)

    feature_names = vectorizer.get_feature_names_out()
    top_indices = mean_tfidf.argsort()[-top_n:][::-1]
    top_words = [feature_names[i] for i in top_indices]

    return top_words


# ============================================================
# 输出生成
# ============================================================
def save_similarity_matrix(similarity_matrix, paper_ids, output_path):
    """保存相似度矩阵"""
    sim_df = pd.DataFrame(
        similarity_matrix,
        index=paper_ids,
        columns=paper_ids
    )
    sim_df.index.name = 'paper_id'
    sim_df.to_csv(output_path, encoding='utf-8-sig')
    logger.info("[OK] Similarity matrix saved: %s", output_path)


def save_clustering_results(df, labels, topic_labels, output_path):
    """保存聚类结果"""
    result_df = pd.DataFrame({
        'id': df['编号'],
        'title': df['标题'],
        'cluster_id': labels,
        'topic_keywords': [', '.join(topic_labels[label]) for label in labels]
    })
    result_df = result_df.sort_values(['cluster_id', 'id'])
    result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info("[OK] Clustering results saved: %s", output_path)
    return result_df


def save_topics_summary(df, labels, topic_labels, output_path):
    """保存话题汇总报告"""
    unique_labels = sorted(set(labels))

    lines = [
        "# Paper Topic Clustering Report\n",
        f"**Analysis Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"**Total Papers**: {len(df)}\n",
        f"**Number of Clusters**: {len(unique_labels)}\n",
        "\n---\n"
    ]

    for cluster_id in unique_labels:
        cluster_mask = labels == cluster_id
        cluster_papers = df[cluster_mask]
        topic_words = topic_labels[cluster_id]

        lines.append(f"\n## Topic {cluster_id + 1}: {' | '.join(topic_words[:3])}\n")
        lines.append(f"\n**Keywords**: {', '.join(topic_words)}\n")
        lines.append(f"\n**Paper Count**: {len(cluster_papers)}\n")
        lines.append("\n**Papers in this cluster**:\n")

        for _, paper in cluster_papers.iterrows():
            lines.append(f"- [{paper['编号']}] {paper['标题']}\n")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    logger.info("[OK] Topics summary saved: %s", output_path)


# ============================================================
# 主流程
# ============================================================
def main():
    logger.info("=" * 60)
    logger.info("  P2 Paper Clustering Analysis")
    logger.info("=" * 60)

    # 1. 读取数据
    logger.info("[1/8] Reading data: %s", INPUT_CSV)
    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    logger.info("  Total papers: %d", len(df))

    # 2. 文本预处理
    logger.info("[2/8] Text preprocessing...")
    df['combined_text'] = df.apply(preprocess_text, axis=1)

    # 3. TF-IDF向量化
    logger.info("[3/8] TF-IDF vectorization...")
    vectorizer = TfidfVectorizer(tokenizer=tokenize, token_pattern=None)
    tfidf_matrix = vectorizer.fit_transform(df['combined_text'])
    logger.info("  Feature dimensions: %d", tfidf_matrix.shape[1])

    # 4. 计算相似度矩阵
    logger.info("[4/8] Computing similarity matrix...")
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # 5. 自动选择最优K值并聚类
    logger.info("[5/8] K-means clustering...")
    best_k = find_best_k(tfidf_matrix, MIN_K, MAX_K)
    logger.info("  Selected K=%d", best_k)

    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(tfidf_matrix)

    # 6. 生成话题标签
    logger.info("[6/8] Generating topic labels...")
    topic_labels = {}
    for cluster_id in range(best_k):
        cluster_indices = np.where(labels == cluster_id)[0]
        topic_labels[cluster_id] = generate_topic_label(
            cluster_indices, df, vectorizer, tfidf_matrix
        )
        logger.info("  Topic %d: %s", cluster_id + 1, ', '.join(topic_labels[cluster_id][:3]))

    # 7. 保存结果
    logger.info("[7/8] Saving results...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_similarity_matrix(
        similarity_matrix,
        df['编号'].tolist(),
        OUTPUT_DIR / "_similarity_matrix.csv"
    )
    save_clustering_results(
        df, labels, topic_labels,
        OUTPUT_DIR / "_clustering_results.csv"
    )
    save_topics_summary(
        df, labels, topic_labels,
        OUTPUT_DIR / "_topics_summary.md"
    )

    # 8. 打印统计
    logger.info("[8/8] Clustering statistics:")
    for cluster_id in range(best_k):
        count = (labels == cluster_id).sum()
        logger.info("  Topic %d: %d papers", cluster_id + 1, count)

    logger.info("=" * 60)
    logger.info("  DONE! Clustering analysis completed.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
