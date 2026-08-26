"""
Vector search with FAISS + cross-encoder reranking, plus clause lookup.

Pipeline
--------
1. Embed the query with the same all-MiniLM-L6-v2 model used at ingest.
2. Search every persisted FAISS index (one per document), collecting up
   to FAISS_CANDIDATES candidates per index.
3. Optionally filter candidates to a specific clause_type.
4. Re-rank the surviving candidates with a cross-encoder
   (ms-marco-MiniLM-L-6-v2), which scores query-passage relevance directly.
5. Return the top top_k results sorted by cross-encoder score.

get_clause_by_id
----------------
Direct lookup by stable clause_id ("<doc_id>:<chunk_index>").
Returns surrounding context (prev + next chunk) and boundary detection for JIT.

Score semantics
---------------
- FAISS returns L2 distance (lower = closer). Used only for candidate set.
- The cross-encoder score is the returned `score`. No fixed scale; roughly:
    > +5  : very confident
    0-5   : moderate
    < 0   : weak / tangential
"""
from __future__ import annotations

import numpy as np

from server.embedder import get_embed_model, get_rerank_model
from server.ingest import DATA_DIR, load_index, list_ingested_docs
from server.jit import jit_for_get_clause
from server.models import ClauseDetail, ClauseResult, ClauseType, DocumentInfo

# How many FAISS candidates to pull per document before reranking.
FAISS_CANDIDATES = 15


# ---------------------------------------------------------------------------
# search_clauses
# ---------------------------------------------------------------------------


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
    clause_type: Optional filter. Chunks not matching this type are excluded
                 before reranking (falls back to all candidates if filter
                 yields nothing).
    top_k:       Maximum results to return.

    Returns
    -------
    List of ClauseResult sorted by cross-encoder score (highest first).
    Empty list when no documents are ingested or nothing passes filters.
    """
    if not DATA_DIR.exists():
        return []

    # Embed query
    embed_model = get_embed_model()
    q_vec: np.ndarray = embed_model.encode(
        [query], convert_to_numpy=True
    ).astype(np.float32)

    # Gather FAISS candidates across all indexes
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

    # Filter by clause_type
    if clause_type:
        filtered = [
            c for c in candidates if c["chunk"]["clause_type"] == clause_type
        ]
        if filtered:
            candidates = filtered

    # Cross-encoder rerank
    reranker = get_rerank_model()
    pairs = [(query, c["chunk"]["text"]) for c in candidates]
    scores: list[float] = reranker.predict(pairs).tolist()

    for cand, score in zip(candidates, scores):
        cand["rerank_score"] = float(score)

    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)

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
                filename=chunk.get("filename", ""),
                doc_id=chunk.get("doc_id", ""),
            )
        )

    return results


# ---------------------------------------------------------------------------
# get_clause_by_id
# ---------------------------------------------------------------------------


def get_clause_by_id(clause_id: str) -> ClauseDetail | None:
    """
    Look up a single clause by its stable ID and return full detail.

    Surrounding context is built from the immediately adjacent chunks
    (prev and next), labelled with their page numbers. This gives the LLM
    enough context to answer questions about clause boundaries.

    Page-boundary detection: the chunk is considered to "touch a boundary"
    when the next chunk (in document order) has a different page number,
    meaning the clause may be cut off at a page break.
    """
    parts = clause_id.split(":", 1)
    if len(parts) != 2:
        return None

    doc_id, chunk_idx_str = parts
    try:
        chunk_idx = int(chunk_idx_str)
    except ValueError:
        return None

    result = load_index(doc_id)
    if result is None:
        return None
    _, chunks = result

    if chunk_idx < 0 or chunk_idx >= len(chunks):
        return None

    chunk = chunks[chunk_idx]

    # Build surrounding context
    context_parts: list[str] = []
    if chunk_idx > 0:
        prev = chunks[chunk_idx - 1]
        context_parts.append(
            f"[Previous chunk — page {prev['page']}]\n{prev['text']}"
        )
    if chunk_idx < len(chunks) - 1:
        nxt = chunks[chunk_idx + 1]
        context_parts.append(
            f"[Next chunk — page {nxt['page']}]\n{nxt['text']}"
        )
    surrounding_context = "\n\n".join(context_parts)

    # Page-boundary detection: does the clause end where the next chunk starts
    # on a different page? That's the truncation risk.
    touches_boundary = (
        chunk_idx < len(chunks) - 1
        and chunks[chunk_idx + 1]["page"] != chunk["page"]
    )

    return ClauseDetail(
        clause_id=clause_id,
        clause_type=ClauseType(chunk["clause_type"]),
        text=chunk["text"],
        page=chunk["page"],
        surrounding_context=surrounding_context,
        jit=jit_for_get_clause(touches_boundary),
    )


# ---------------------------------------------------------------------------
# list_documents
# ---------------------------------------------------------------------------


def get_document_list() -> list[DocumentInfo]:
    """Return metadata for every ingested document."""
    return [DocumentInfo(**d) for d in list_ingested_docs()]
