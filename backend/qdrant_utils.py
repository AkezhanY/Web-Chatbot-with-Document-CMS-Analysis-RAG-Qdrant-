# qdrant_utils.py
import os, uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from embeddings import embed_query, embed_passage, embed_passages, dim

Q_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
Q_API_KEY = os.getenv("QDRANT_API_KEY")
BASE_COL = os.getenv("QDRANT_COLLECTION", "docs_auto")  

client = QdrantClient(url=Q_URL, api_key=Q_API_KEY)

def _col_name() -> str:
    
    return f"{BASE_COL}_{dim}"

def ensure_collection():
    name = _col_name()
    try:
        info = client.get_collection(name)
        size = info.config.params.vectors.size
        if size != dim:
            # пересобираем под нужную размерность
            client.recreate_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
    except Exception:
        client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

def upsert_chunks(chunks: List[str], meta: Dict[str, Any]):
    ensure_collection()
    if not chunks:
        return
    name = _col_name()

    
    vecs = embed_passages(chunks)  # List[List[float]]
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vecs[i],
            payload={**meta, "text": chunks[i], "chunk_id": i},
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=name, points=points)

def search_chunks(question: str, top_k: int = 5, thr: float = 0.0):
    """
    НИЗКИЙ порог по умолчанию: thr=0.0 — иначе легко «не найти».
    Для e5 (нормализованный косинус) похожие фрагменты обычно дают 0.5–0.8.
    """
    ensure_collection()
    name = _col_name()
    vec = embed_query(question)
    hits = client.search(
        collection_name=name,
        query_vector=vec,
        limit=max(1, int(top_k) or 5),
        with_payload=True,
        score_threshold=thr,  # чем больше — тем жестче фильтрация
    )
    out = []
    for h in hits:
        pl = h.payload or {}
        out.append({
            "text": pl.get("text", ""),
            "file_name": pl.get("file_name"),
            "file_type": pl.get("file_type"),
            "summary": pl.get("summary"),
            "score": float(h.score),
        })
    return out

def unique_files(limit: int = 5):
    ensure_collection()
    name = _col_name()
    points, _ = client.scroll(collection_name=name, with_payload=True, limit=1000)
    seen, out = set(), []
    for p in points:
        pl = p.payload or {}
        fn = pl.get("file_name")
        if fn and fn not in seen:
            seen.add(fn)
            out.append({
                "file_name": fn,
                "file_type": pl.get("file_type"),
                "summary": pl.get("summary") or "",
            })
        if len(out) >= limit:
            break
    return out

