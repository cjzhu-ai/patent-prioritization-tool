"""Embedding and agglomerative clustering logic (no UI)."""

from typing import Tuple

import numpy as np

from config import EMBEDDING_MODEL


def run_embedding(texts: list) -> np.ndarray:
    """Compute sentence embeddings for a list of strings. Returns (n, dim) array."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)
    return model.encode(texts)


def run_clustering(embeddings: np.ndarray, n_clusters: int) -> Tuple[np.ndarray, float]:
    """
    Run agglomerative hierarchical clustering on embeddings.
    Returns (labels, silhouette_score).
    """
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score

    clustering = AgglomerativeClustering(n_clusters=n_clusters)
    labels = clustering.fit_predict(embeddings)
    sil = (
        silhouette_score(embeddings, labels)
        if len(set(labels)) > 1
        else 0.0
    )
    return labels, sil
