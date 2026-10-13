"""
Clustering Evaluation and Algorithm Comparison Module
Compares K-Means and Hierarchical Clustering using academic validation metrics.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score


def compare_clustering_algorithms(
    scaled_features: np.ndarray,
    kmeans_labels: np.ndarray,
    hierarchical_labels: np.ndarray,
    k: int
) -> pd.DataFrame:
    """
    Compares K-Means and Agglomerative Hierarchical Clustering across standard unsupervised metrics:
    1. Silhouette Score: [-1, +1] (Higher is better, measures cluster cohesion vs separation).
    2. Davies-Bouldin Index: [0, inf) (Lower is better, measures cluster similarity/overlap).
    3. Calinski-Harabasz Index: [0, inf) (Higher is better, ratio of between-to-within dispersion).
    """
    km_sil = silhouette_score(scaled_features, kmeans_labels)
    km_db = davies_bouldin_score(scaled_features, kmeans_labels)
    km_ch = calinski_harabasz_score(scaled_features, kmeans_labels)

    hc_sil = silhouette_score(scaled_features, hierarchical_labels)
    hc_db = davies_bouldin_score(scaled_features, hierarchical_labels)
    hc_ch = calinski_harabasz_score(scaled_features, hierarchical_labels)

    comparison = pd.DataFrame([
        {
            "Algorithm": "K-Means Clustering",
            "Clusters (K)": k,
            "Silhouette Score": round(km_sil, 4),
            "Davies-Bouldin Index": round(km_db, 4),
            "Calinski-Harabasz Score": round(km_ch, 2),
            "Convergence": "Centroid-based (Partitional)"
        },
        {
            "Algorithm": "Agglomerative Hierarchical",
            "Clusters (K)": k,
            "Silhouette Score": round(hc_sil, 4),
            "Davies-Bouldin Index": round(hc_db, 4),
            "Calinski-Harabasz Score": round(hc_ch, 2),
            "Convergence": "Ward Linkage (Bottom-up Tree)"
        }
    ])

    return comparison


def compute_cluster_cross_tab(kmeans_labels: np.ndarray, hierarchical_labels: np.ndarray) -> pd.DataFrame:
    """
    Generates a cross-tabulation confusion matrix comparing K-Means cluster assignments
    with Hierarchical cluster assignments to quantify alignment.
    """
    ct = pd.crosstab(
        pd.Series(kmeans_labels, name="K-Means Cluster"),
        pd.Series(hierarchical_labels, name="Hierarchical Cluster")
    )
    return ct
