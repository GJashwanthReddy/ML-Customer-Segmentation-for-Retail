"""
Clustering and Dimensionality Reduction Module
Handles skewness transformation, feature scaling, K-Means, Hierarchical Clustering, and PCA.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score


def preprocess_rfm_for_ml(rfm_df: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame, StandardScaler]:
    """
    Preprocesses raw RFM features for unsupervised clustering:
    1. Applies log-transformation (log1p) to normalize heavily right-skewed distributions.
    2. Standardizes features to mean=0 and variance=1 using StandardScaler.

    Returns:
        scaled_features: 2D numpy array of scaled features.
        transformed_df: DataFrame with log-transformed and standardized features.
        scaler: Fitted StandardScaler instance.
    """
    features = ["Recency", "Frequency", "Monetary"]
    
    # Handle non-positive monetary values if any edge cases exist
    rfm_clean = rfm_df[features].copy()
    rfm_clean["Monetary"] = rfm_clean["Monetary"].clip(lower=0.01)

    # Log1p transformation to mitigate severe right skewness
    rfm_log = np.log1p(rfm_clean)

    # Standardization
    scaler = StandardScaler()
    scaled_matrix = scaler.fit_transform(rfm_log)

    scaled_df = pd.DataFrame(
        scaled_matrix,
        columns=[f"{col}_scaled" for col in features],
        index=rfm_df.index
    )

    return scaled_matrix, scaled_df, scaler


def evaluate_k_range(scaled_features: np.ndarray, k_range: range = range(2, 9)) -> pd.DataFrame:
    """
    Evaluates K-Means clustering across a range of K values.
    Calculates Inertia (within-cluster sum of squares) and Silhouette Score for each K.

    Returns:
        pd.DataFrame with columns: ['K', 'Inertia', 'Silhouette_Score', 'Davies_Bouldin', 'Calinski_Harabasz']
    """
    results = []
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, init="k-means++", n_init=10, max_iter=300, random_state=42)
        labels = kmeans.fit_predict(scaled_features)
        
        inertia = kmeans.inertia_
        sil = silhouette_score(scaled_features, labels)
        db = davies_bouldin_score(scaled_features, labels)
        ch = calinski_harabasz_score(scaled_features, labels)

        results.append({
            "K": k,
            "Inertia": round(inertia, 2),
            "Silhouette_Score": round(sil, 4),
            "Davies_Bouldin": round(db, 4),
            "Calinski_Harabasz": round(ch, 2)
        })

    return pd.DataFrame(results)


def fit_kmeans(scaled_features: np.ndarray, k: int = 4) -> Tuple[KMeans, np.ndarray]:
    """
    Fits final K-Means model for chosen K.
    """
    kmeans = KMeans(n_clusters=k, init="k-means++", n_init=10, max_iter=300, random_state=42)
    labels = kmeans.fit_predict(scaled_features)
    return kmeans, labels


def fit_hierarchical(scaled_features: np.ndarray, k: int = 4) -> Tuple[AgglomerativeClustering, np.ndarray]:
    """
    Fits Agglomerative Hierarchical Clustering with Ward linkage.
    """
    agg = AgglomerativeClustering(n_clusters=k, metric="euclidean", linkage="ward")
    labels = agg.fit_predict(scaled_features)
    return agg, labels


def compute_pca_2d(scaled_features: np.ndarray) -> Tuple[np.ndarray, PCA]:
    """
    Applies Principal Component Analysis (PCA) to reduce 3D RFM to 2 principal components.
    Returns:
        pca_coords: 2D array of (PC1, PC2) coordinates.
        pca_model: Fitted PCA instance with explained_variance_ratio_.
    """
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(scaled_features)
    return coords, pca
