import hashlib
from cachetools import LRUCache
import numpy as np

# Lazy-loaded model (only loads when first needed)
_model = None
_embedding_cache: LRUCache = LRUCache(maxsize=512)

MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def embed(text: str) -> np.ndarray:
    """Embed a single text string."""
    key = _cache_key(text)
    if key in _embedding_cache:
        return _embedding_cache[key]
    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    _embedding_cache[key] = vec
    return vec


def embed_batch(texts: list[str]) -> list[np.ndarray]:
    """Embed a list of texts efficiently in one batch call."""
    results = [None] * len(texts)
    to_encode = []
    to_encode_idx = []

    for i, text in enumerate(texts):
        key = _cache_key(text)
        if key in _embedding_cache:
            results[i] = _embedding_cache[key]
        else:
            to_encode.append(text)
            to_encode_idx.append(i)

    if to_encode:
        model = _get_model()
        vecs = model.encode(to_encode, normalize_embeddings=True, batch_size=64)
        for idx, text, vec in zip(to_encode_idx, to_encode, vecs):
            _embedding_cache[_cache_key(text)] = vec
            results[idx] = vec

    return results


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two normalized vectors."""
    return float(np.dot(a, b))