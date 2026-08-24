"""
Vector search with FAISS + cross-encoder reranking.

Pipeline
--------
1. Embed the query with the same all-MiniLM-L6-v2 model used at ingest.
2. Search every persisted FAISS index (one per document), collecting up
   to FAISS_CANDIDATES candidates per index.
3. Optionally filter candidates to a specific clause_type.
4. Re-rank the surviving candidates with a cross-encoder
   (ms-marco-MiniLM-L-6-v2), which scores query–passage relevance directly.
5. Return the top top_k results sorted by cross-encoder score.

Score semantics
---------------
- FAISS returns L2 distance (lower = closer). We use it only for the
  initial candidate set; it is NOT exposed in the final ClauseResult.
- The cross-encoder score is exposed as `score`. Positive = relevant,
  negative = less relevant. There is no fixed scale — values typically
  range from roughly -10 to +10.
"""
from __future__ import annotations

import numpy as np

from server.embedder import get_embed_model, get_rerank_model
from server.ingest import DATA_DIR, load_index
from server.models import ClauseResult, ClauseType

# How many FAISS candidates to pull per document before reranking.
# Spec asks for top 15 total; we pull 15 per doc to give the reranker
# enough material when multiple docs are ingested.
FAISS_CANDIDATES = 15


def search_clauses(
    query: str,
    clause_type: str | None = None,
    top_k: int = 5,
) -> list[ClauseResult]:
    """
    Search all ingested documents and return top_k reranked results.

    Parameters
    ----------
    query:       Natural-language question or keyword phrase.
    clause_type: Optional filter. If provided, only chunks classified into
                 this type are returned (falls back to all if filter yields
                 nothing).
    top_k:       Maximum results to return. Capped at actual candidate count.

    Returns
    -------
    List of ClauseResult sorted by cross-encoder score (highest first).
    Empty list when no documents are ingested or nothing passes filters.
    """
    if not DATA_DIR.exists():
        return []

    # ── Embed query ──────────────────────────────────────────────────────────
    embed_model = get_embed_model()
    q_vec: np.ndarray = embed_model.encode(
        [query], convert_to_numpy=True
    ).astype(np.float32)

    # ── Gather FAISS candidates across all indexes ───────────────────────────
    candidates: list[dict] = []

    for meta_path in DATA_DIR.glob("*.meta.pkl"):
        doc_id = meta_path.stem.replace(".meta", "")
        result = load_index(doc_id)
        if result is None:
            continue
        index, chunks = result

        k = min(FAISS_CANDIDATES, index.ntotal)
        if k == 0:
            continue

        distances, indices = index.search(q_vec, k)

        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            candidates.append(
                {
                    "chunk": chunks[idx],
                    "l2_dist": float(dist),
                    "clause_id": f"{doc_id}:{idx}",
                }
            )

    if not candidates:
        return []

    # ── Filter by clause_type ────────────────────────────────────────────────
    if clause_type:
        filtered = [
            c for c in candidates if c["chunk"]["clause_type"] == clause_type
        ]
        # Only apply filter if it produces results; otherwise return unfiltered
        if filtered:
            candidates = filtered

    # ── Cross-encoder rerank ─────────────────────────────────────────────────
    reranker = get_rerank_model()
    pairs = [(query, c["chunk"]["text"]) for c in candidates]
    scores: list[float] = reranker.predict(pairs).tolist()

    for cand, score in zip(candidates, scores):
        cand["rerank_score"] = float(score)

    # Sort descending by cross-encoder score
    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)

    # ── Build results ────────────────────────────────────────────────────────
    results: list[ClauseResult] = []
    for cand in candidates[:top_k]:
        chunk = cand["chunk"]
        results.append(
            ClauseResult(
                clause_id=cand["clause_id"],
                clause_type=ClauseType(chunk["clause_type"]),
                text=chunk["text"],
                page=chunk["page"],
                score=round(cand["rerank_score"], 4),
            )
        )

    return results
