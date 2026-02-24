"""
聚类核心算法（共享）
"""

import jieba
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


STOPWORDS = {
    '的', '了', '是', '在', '和', '与', '等', '对', '为', '以', '及', '或',
    '中', '上', '下', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '个', '种', '类', '方面', '问题', '研究', '分析', '探讨', '论文', '文章',
    '通过', '进行', '提出', '基于', '采用', '针对', '结合', '围绕', '关于',
    '主要', '其中', '同时', '并且', '因此', '然而', '但是', '如何', '什么',
    '可以', '需要', '应该', '能够', '具有', '存在', '包括', '涉及', '体现',
    '不同', '相关', '重要', '有效', '积极', '显著', '明显', '充分', '进一步',
}


def tokenize(text: str) -> list[str]:
    """jieba 分词 + 过滤停用词和短词"""
    words = jieba.lcut(text)
    return [w for w in words if len(w) >= 2 and not w.isdigit() and w not in STOPWORDS]


def find_best_k(tfidf_matrix, min_k: int = 3, max_k: int = 8) -> int:
    """使用轮廓系数自动选择最优聚类数"""
    n_samples = tfidf_matrix.shape[0]
    min_k = max(2, min(min_k, n_samples - 1))
    max_k = max(min_k, min(max_k, n_samples - 1))

    if n_samples < 3:
        return min(2, n_samples)

    best_k, best_score = min_k, -1
    for k in range(min_k, max_k + 1):
        if k >= n_samples:
            break
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(tfidf_matrix)
        score = silhouette_score(tfidf_matrix, labels)
        if score > best_score:
            best_score = score
            best_k = k

    return best_k


def generate_topic_label(cluster_indices, vectorizer, tfidf_matrix, top_n: int = 5) -> list[str]:
    """基于 TF-IDF 权重生成话题标签"""
    cluster_tfidf = tfidf_matrix[cluster_indices].toarray()
    mean_tfidf = cluster_tfidf.mean(axis=0)
    feature_names = vectorizer.get_feature_names_out()
    top_indices = mean_tfidf.argsort()[-top_n:][::-1]
    return [feature_names[i] for i in top_indices]
