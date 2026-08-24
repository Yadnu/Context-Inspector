"""
Ingest pipeline: PDF -> chunks -> embeddings -> FAISS index on disk.

Key design decisions
--------------------
- doc_id is SHA-256[:16] of "<original_filename>:<file_byte_size>".
  Cheap, stable across restarts, collision-resistant for contract scale.
- Index lives at DATA_DIR/<doc_id>.faiss; metadata at DATA_DIR/<doc_id>.meta.pkl.
  A meta.pkl stores the chunk list (text + page + clause_type) so we never
  need to re-read the PDF for search.
- If both files exist, ingest_document() returns cached stats immediately
  without loading the models.
- DATA_DIR is configurable via CLAUSE_LENS_DATA_DIR env var.
"""
from __future__ import annotations

import hashlib
import os
import pickle
from pathlib import Path

import faiss
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from server.classifier import classify_chunk
from server.embedder import get_embed_model

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_DATA_DIR = Path(__file__).parent / "data" / "indexes"
DATA_DIR = Path(os.getenv("CLAUSE_LENS_DATA_DIR", str(_DEFAULT_DATA_DIR)))

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_doc_id(filename: str, file_size: int) -> str:
    """Stable, short doc identifier from filename + size."""
    raw = f"{filename}:{file_size}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _index_paths(doc_id: str) -> tuple[Path, Path]:
    return DATA_DIR / f"{doc_id}.faiss", DATA_DIR / f"{doc_id}.meta.pkl"


# ---------------------------------------------------------------------------
# Pipeline stages (public for testing / eval)
# ---------------------------------------------------------------------------


def parse_pdf(path: Path) -> list[dict]:
    """
    Extract text per page from a PDF.

    Returns a list of {"page": int, "text": str} dicts (1-indexed pages).
    Pages with no extractable text are skipped.
    """
    reader = PdfReader(str(path))
    pages: list[dict] = []
    for i, page_obj in enumerate(reader.pages, start=1):
        text = page_obj.extract_text() or ""
        if text.strip():
            pages.append({"page": i, "text": text})
    return pages


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Split page texts with RecursiveCharacterTextSplitter.

    Each output chunk carries the page number of the *source* page. For
    text that spans a page break, the chunk inherits the page where it
    started (pypdf concatenates per page, so cross-page splits are rare).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks: list[dict] = []
    for page_info in pages:
        for chunk_text in splitter.split_text(page_info["text"]):
            if chunk_text.strip():
                chunks.append({"page": page_info["page"], "text": chunk_text})
    return chunks


# ---------------------------------------------------------------------------
# Main ingest entry point
# ---------------------------------------------------------------------------


def ingest_document(
    pdf_path: Path,
    *,
    doc_id: str | None = None,
    original_filename: str | None = None,
) -> dict:
    """
    Ingest a PDF into a FAISS index.

    Parameters
    ----------
    pdf_path:
        Absolute path to the PDF file (may be a temporary file for uploads).
    doc_id:
        Pre-computed doc ID (pass when the caller already has it, e.g. from
        the upload handler which reads file size before writing to disk).
        If omitted, computed from original_filename and file size.
    original_filename:
        Human-readable filename shown in results. Falls back to pdf_path.name.

    Returns
    -------
    dict with keys: doc_id, filename, page_count, clause_count, cached.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    filename = original_filename or pdf_path.name
    file_size = pdf_path.stat().st_size

    if doc_id is None:
        doc_id = _make_doc_id(filename, file_size)

    index_path, meta_path = _index_paths(doc_id)

    # ── Fast path: already indexed ──────────────────────────────────────────
    if index_path.exists() and meta_path.exists():
        print(f"[ingest] Cached index found for '{filename}' ({doc_id})")
        with open(meta_path, "rb") as f:
            meta: dict = pickle.load(f)
        return {
            "doc_id": doc_id,
            "filename": filename,
            "page_count": meta["page_count"],
            "clause_count": meta["clause_count"],
            "cached": True,
        }

    # ── Parse ────────────────────────────────────────────────────────────────
    print(f"[ingest] Parsing '{filename}'…")
    pages = parse_pdf(pdf_path)
    page_count = max((p["page"] for p in pages), default=0)

    # ── Chunk ────────────────────────────────────────────────────────────────
    print(f"[ingest] Chunking {len(pages)} pages…")
    chunks = chunk_pages(pages)

    # ── Classify ─────────────────────────────────────────────────────────────
    for chunk in chunks:
        chunk["clause_type"] = classify_chunk(chunk["text"]).value
        chunk["doc_id"] = doc_id
        chunk["filename"] = filename

    # ── Embed ────────────────────────────────────────────────────────────────
    print(f"[ingest] Embedding {len(chunks)} chunks…")
    model = get_embed_model()
    texts = [c["text"] for c in chunks]
    embeddings: np.ndarray = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).astype(np.float32)

    # ── Build FAISS index ────────────────────────────────────────────────────
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # ── Persist ──────────────────────────────────────────────────────────────
    faiss.write_index(index, str(index_path))
    meta = {
        "doc_id": doc_id,
        "filename": filename,
        "chunks": chunks,
        "page_count": page_count,
        "clause_count": len(chunks),
        "dim": dim,
    }
    with open(meta_path, "wb") as f:
        pickle.dump(meta, f)

    print(
        f"[ingest] Done: {len(chunks)} chunks across {page_count} pages -> {index_path.name}"
    )
    return {
        "doc_id": doc_id,
        "filename": filename,
        "page_count": page_count,
        "clause_count": len(chunks),
        "cached": False,
    }


# ---------------------------------------------------------------------------
# Index access utilities (used by search.py)
# ---------------------------------------------------------------------------


def load_index(doc_id: str) -> tuple[faiss.Index, list[dict]] | None:
    """
    Load a persisted FAISS index and its chunk metadata.

    Returns (index, chunks) or None if not found.
    """
    index_path, meta_path = _index_paths(doc_id)
    if not (index_path.exists() and meta_path.exists()):
        return None
    index = faiss.read_index(str(index_path))
    with open(meta_path, "rb") as f:
        meta: dict = pickle.load(f)
    return index, meta["chunks"]


def list_ingested_docs() -> list[dict]:
    """
    Return metadata for all ingested documents.

    Used by list_documents() in Stage 2.
    """
    if not DATA_DIR.exists():
        return []
    docs: list[dict] = []
    for meta_path in DATA_DIR.glob("*.meta.pkl"):
        try:
            with open(meta_path, "rb") as f:
                meta: dict = pickle.load(f)
            docs.append(
                {
                    "doc_id": meta["doc_id"],
                    "filename": meta["filename"],
                    "page_count": meta["page_count"],
                    "clause_count": meta["clause_count"],
                }
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[ingest] Warning: could not read {meta_path}: {exc}")
    return docs
