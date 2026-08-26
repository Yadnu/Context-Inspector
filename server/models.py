"""
Pydantic schemas shared across the server.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ClauseType(str, Enum):
    indemnification = "indemnification"
    termination = "termination"
    liability = "liability"
    confidentiality = "confidentiality"
    payment = "payment"
    governing_law = "governing_law"
    other = "other"


class ClauseResult(BaseModel):
    clause_id: str = Field(description="Stable identifier: '<doc_id>:<chunk_index>'")
    clause_type: ClauseType
    text: str
    page: int = Field(description="1-indexed page number from the source PDF")
    score: float = Field(description="Cross-encoder relevance score (higher = more relevant)")
    # Added in Stage 2 so JIT multi-doc hint is actionable
    filename: str = Field(default="", description="Original PDF filename")
    doc_id: str = Field(default="", description="Document identifier")


class ClauseDetail(BaseModel):
    """Extended clause view returned by get_clause()."""

    clause_id: str
    clause_type: ClauseType
    text: str
    page: int
    surrounding_context: str = Field(
        description=(
            "Text of the chunks immediately before and after this clause, "
            "labelled with their page numbers. Empty if this is the first or last chunk."
        )
    )
    jit: str = Field(default="")


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    page_count: int
    clause_count: int


class SearchResponse(BaseModel):
    results: list[ClauseResult]
    jit: str = Field(
        default="",
        description="Deterministic instruction for the LLM. Empty string = no special guidance.",
    )


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    jit: str = Field(default="")


class CompareResponse(BaseModel):
    clause_a: ClauseResult
    clause_b: ClauseResult
    jit: str = Field(default="")


class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    page_count: int
    clause_count: int
    cached: bool = Field(
        default=False,
        description="True when an existing index was reused; False when freshly indexed.",
    )
