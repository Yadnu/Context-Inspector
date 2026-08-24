"""
JIT (Just-In-Time) instruction generator.

Rules are deterministic if/else — never an LLM.
Stage 1: stub returns empty string for all inputs.
Stage 2: full rules are implemented here.

Keep rule logic in this module only; callers just pass results through.
"""
from __future__ import annotations

from server.models import ClauseResult


def jit_for_search(results: list[ClauseResult], top_score: float) -> str:
    """
    Return a guidance string for the LLM based on retrieval outcomes.
    Empty string means "no special guidance needed".

    Stage 1 stub — always returns "".
    """
    # Stage 2 will add:
    #   - low-confidence warning (top_score < 0.4)
    #   - multi-document citation reminder
    return ""


def jit_for_get_clause(text: str, page: int) -> str:
    """Stage 1 stub."""
    return ""


def jit_for_compare(clause_type_a: str, clause_type_b: str) -> str:
    """Stage 1 stub."""
    return ""
