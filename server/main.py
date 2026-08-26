"""
Clause Lens -- MCP server entry point.

Architecture (FastMCP 3.x)
--------------------------
FastMCP owns the full ASGI app. Custom HTTP routes (/ingest, /health)
are registered directly on the MCP object via @mcp.custom_route().
CORS is added through mcp.add_middleware().

MCP endpoint : http://host:PORT/mcp/   (Streamable-HTTP transport)
Ingest       : POST http://host:PORT/ingest   (multipart, field "file")
Health       : GET  http://host:PORT/health

For uvicorn / Railway:
    uvicorn server.main:app --host 0.0.0.0 --port $PORT

Constraint: the server NEVER calls an LLM. All reasoning is client-side.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Literal, Optional

import uvicorn
from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from server.ingest import ingest_document
from server.jit import jit_for_compare, jit_for_search
from server.models import IngestResponse
from server.search import (
    get_clause_by_id,
    get_document_list,
    search_clauses as _search_clauses,
)

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "clause-lens",
    instructions=(
        "You are a contract analysis assistant powered by Clause Lens. "
        "ALWAYS use the search_clauses tool to find relevant text before answering. "
        "ALWAYS cite the page number and source document from each result you reference. "
        "If the tool returns no results or the jit field warns of low confidence, "
        "tell the user that no strongly matching clause was found. "
        "NEVER answer from your own training knowledge. "
        "When a jit field is non-empty, follow its instructions exactly."
    ),
)

# CORS is applied by wrapping the ASGI app (see `app =` below)


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_clauses(
    query: str,
    clause_type: Optional[
        Literal[
            "indemnification",
            "termination",
            "liability",
            "confidentiality",
            "payment",
            "governing_law",
            "other",
        ]
    ] = None,
    top_k: int = 5,
) -> dict:
    """
    Search contract clauses by natural-language query.

    Returns ranked results with page numbers and clause types.
    Always check the `jit` field -- it contains mandatory guidance for
    how to present results (e.g. low-confidence warning, multi-doc citation).
    """
    results = _search_clauses(query, clause_type=clause_type, top_k=top_k)
    top_score = results[0].score if results else 0.0
    return {
        "results": [r.model_dump() for r in results],
        "jit": jit_for_search(results, top_score),
    }


@mcp.tool()
def get_clause(clause_id: str) -> dict:
    """
    Retrieve the full text and surrounding context for a single clause.

    Use this when the user wants to read a specific clause in full, or
    when search_clauses returned a truncated preview and more context
    is needed. Check the `jit` field for page-boundary truncation warnings.

    Parameters
    ----------
    clause_id : Stable clause identifier returned by search_clauses
                (format: "<doc_id>:<chunk_index>").
    """
    detail = get_clause_by_id(clause_id)
    if detail is None:
        return {
            "error": f"Clause '{clause_id}' not found. "
            "Use list_documents to see available documents, "
            "then search_clauses to find valid clause IDs."
        }
    return detail.model_dump()


@mcp.tool()
def list_documents() -> dict:
    """
    List all ingested contract documents.

    Returns doc_id, filename, page count, and clause count for each document.
    The `jit` field is always empty for this tool (no guidance needed).
    Use doc IDs from this list to filter search_clauses results if needed.
    """
    docs = get_document_list()
    return {
        "documents": [d.model_dump() for d in docs],
        "jit": "",
    }


@mcp.tool()
def compare_clauses(clause_id_a: str, clause_id_b: str) -> dict:
    """
    Retrieve two clauses side-by-side for comparison.

    Returns RAW TEXT ONLY -- no analysis. The LLM performs the comparison.
    Check the `jit` field: if the two clauses are different types, the jit
    field will instruct you to declare the type mismatch before comparing.

    Parameters
    ----------
    clause_id_a : First clause ID (from search_clauses results).
    clause_id_b : Second clause ID (from search_clauses results).
    """
    detail_a = get_clause_by_id(clause_id_a)
    detail_b = get_clause_by_id(clause_id_b)

    errors: list[str] = []
    if detail_a is None:
        errors.append(f"Clause not found: '{clause_id_a}'")
    if detail_b is None:
        errors.append(f"Clause not found: '{clause_id_b}'")
    if errors:
        return {"error": "; ".join(errors)}

    # Strip surrounding_context and per-clause jit -- only raw text returned
    def _to_raw(d: "ClauseDetail") -> dict:  # type: ignore[name-defined]
        return {
            "clause_id": d.clause_id,
            "clause_type": d.clause_type.value,
            "text": d.text,
            "page": d.page,
        }

    return {
        "clause_a": _to_raw(detail_a),
        "clause_b": _to_raw(detail_b),
        "jit": jit_for_compare(
            detail_a.clause_type.value,
            detail_b.clause_type.value,
        ),
    }


# ---------------------------------------------------------------------------
# Custom HTTP routes
# ---------------------------------------------------------------------------


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Liveness probe for Railway / Docker."""
    return JSONResponse({"status": "ok"})


@mcp.custom_route("/ingest", methods=["POST"])
async def ingest_endpoint(request: Request) -> JSONResponse:
    """
    Upload a PDF contract for indexing.

    Expects multipart/form-data with a field named "file".
    Idempotent: re-uploading the same file (same name + size) returns
    cached stats without re-embedding.
    """
    try:
        form = await request.form()
    except Exception as exc:
        return JSONResponse({"error": f"Could not parse form data: {exc}"}, status_code=400)

    file = form.get("file")
    if file is None:
        return JSONResponse({"error": "No file field in form data."}, status_code=400)

    filename: str = getattr(file, "filename", "") or ""
    if not filename.lower().endswith(".pdf"):
        return JSONResponse({"error": "Only PDF files are accepted."}, status_code=400)

    content: bytes = await file.read()
    file_size = len(content)
    doc_id = hashlib.sha256(f"{filename}:{file_size}".encode()).hexdigest()[:16]

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = ingest_document(tmp_path, doc_id=doc_id, original_filename=filename)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        tmp_path.unlink(missing_ok=True)

    return JSONResponse(result)


# ---------------------------------------------------------------------------
# ASGI app export (for uvicorn / Railway)
# ---------------------------------------------------------------------------

# Wrap with CORSMiddleware so the Next.js client can call from any origin.
# Starlette's CORSMiddleware is ASGI-native and wraps cleanly around FastMCP.
_mcp_app = mcp.http_app(transport="http", stateless_http=True)
app = CORSMiddleware(
    _mcp_app,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
