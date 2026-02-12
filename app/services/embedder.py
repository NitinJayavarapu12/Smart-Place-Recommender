from functools import lru_cache
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    # Cached so it loads once per process
    return SentenceTransformer(MODEL_NAME)

def embed_texts(texts: List[str]) -> np.ndarray:
    model = get_model()
    emb = model.encode(texts, normalize_embeddings=True)
    return np.array(emb)

def cosine_sim_matrix(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    # both are normalized => cosine = dot product
    return doc_vecs @ query_vec
