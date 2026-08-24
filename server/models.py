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


class SearchResponse(BaseModel):
    results: list[ClauseResult]
    jit: str = Field(
        default="",
        description="Deterministic instruction for the LLM. Empty string = no special guidance.",
    )


class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    page_count: int
    clause_count: int
    cached: bool = Field(
        default=False,
        description="True when an existing index was reused; False when freshly indexed.",
    )
