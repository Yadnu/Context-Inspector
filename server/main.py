"""
Clause Lens — MCP server entry point.

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
from server.jit import jit_for_search
from server.search import search_clauses as _search_clauses

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "clause-lens",
    instructions=(
        "You are a contract analysis assistant powered by Clause Lens. "
        "ALWAYS use the search_clauses tool to find relevant text before answering. "
        "ALWAYS cite the page number from each result you reference. "
        "If the tool returns no results or the jit field warns of low confidence, "
        "tell the user that no strongly matching clause was found. "
        "NEVER answer from your own training knowledge."
    ),
)

# CORS — allow the Next.js client (any origin in dev; tighten in prod)
mcp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    Check the `jit` field for guidance on how to present results to the user.
    """
    results = _search_clauses(query, clause_type=clause_type, top_k=top_k)
    top_score = results[0].score if results else 0.0
    return {
        "results": [r.model_dump() for r in results],
        "jit": jit_for_search(results, top_score),
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

    # Stable doc_id from original filename + size
    doc_id = hashlib.sha256(f"{filename}:{file_size}".encode()).hexdigest()[:16]

    # Write to temp file so pypdf can open it
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

app = mcp.http_app(transport="http")

# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
