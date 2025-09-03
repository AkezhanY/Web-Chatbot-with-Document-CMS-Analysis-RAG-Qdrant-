# embeddings.py
from __future__ import annotations
from typing import List, Union
from sentence_transformers import SentenceTransformer

# Модель e5-base-v2 (768-мерная)
dim = 768

_MODEL: SentenceTransformer | None = None

def get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("intfloat/e5-base-v2")
    return _MODEL

def embed_passage(text: str) -> List[float]:
    """
    Эмбеддинг ОДНОГО фрагмента (chunk).
    e5 требует префикс 'passage: '.
    """
    m = get_model()
    vec = m.encode([f"passage: {text}"], normalize_embeddings=True)
    return vec[0].tolist()

def embed_passages(texts: List[str]) -> List[List[float]]:
    """
    Батч для нескольких фрагментов (ускоряет аплоад).
    """
    if not texts:
        return []
    m = get_model()
    inputs = [f"passage: {t}" for t in texts]
    vecs = m.encode(inputs, normalize_embeddings=True)
    return vecs.tolist()

def embed_query(text: str) -> List[float]:
    """
    Эмбеддинг запроса пользователя.
    e5 требует префикс 'query: '.
    """
    m = get_model()
    vec = m.encode([f"query: {text}"], normalize_embeddings=True)
    return vec[0].tolist()
