"""Local embedding wrapper using sentence-transformers (no AI API calls)."""

from __future__ import annotations

_embedder = None


def get_embedder():
    """Lazy-load the sentence-transformers model (downloaded on first use)."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def embed(text: str) -> list[float]:
    """Return embedding vector for a single text string."""
    model = get_embedder()
    return model.encode(text).tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    import numpy as np
    a_arr = np.array(a)
    b_arr = np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)
