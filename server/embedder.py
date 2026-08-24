"""
Shared model singletons for embedding and cross-encoder reranking.

Loading 90 MB + 86 MB models is expensive — do it once per process and
cache in module scope. Both ingest.py and search.py import from here.
"""
from __future__ import annotations

from sentence_transformers import CrossEncoder, SentenceTransformer

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_embed_model: SentenceTransformer | None = None
_rerank_model: CrossEncoder | None = None


def get_embed_model() -> SentenceTransformer:
    """Return the cached embedding model, loading it on first call."""
    global _embed_model
    if _embed_model is None:
        print(f"[embedder] Loading embedding model: {EMBED_MODEL_NAME}")
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embed_model


def get_rerank_model() -> CrossEncoder:
    """Return the cached cross-encoder, loading it on first call."""
    global _rerank_model
    if _rerank_model is None:
        print(f"[embedder] Loading rerank model: {RERANK_MODEL_NAME}")
        _rerank_model = CrossEncoder(RERANK_MODEL_NAME)
    return _rerank_model
