"""
JIT (Just-In-Time) instruction generator.

All rules are deterministic if/else — never an LLM.
Rules live only in this module; callers pass data in and get a string back.
An empty string means "no special guidance needed".

Rules
-----
search_clauses
  - top_score < 0.4      : warn about low confidence
  - multiple doc_ids     : remind the LLM to name source documents

get_clause
  - touches page boundary: warn about possible truncation

compare_clauses
  - clause_types differ  : instruct the LLM to state the type mismatch first
"""
from __future__ import annotations

from server.models import ClauseResult

# Cross-encoder score below which retrieval is considered low-confidence.
# Scores are not probability; anything below this is a weak lexical overlap.
LOW_CONFIDENCE_THRESHOLD = 0.4


def jit_for_search(results: list[ClauseResult], top_score: float) -> str:
    """
    Return guidance for the LLM based on search result characteristics.

    Combines multiple applicable rules; rules are checked in priority order.
    """
    if not results:
        return ""

    messages: list[str] = []

    # Rule 1: low-confidence match
    if top_score < LOW_CONFIDENCE_THRESHOLD:
        messages.append(
            "Low confidence match. Tell the user no strongly matching clause was found "
            "rather than summarizing weak results."
        )

    # Rule 2: results span multiple documents
    doc_ids = {r.clause_id.split(":")[0] for r in results}
    if len(doc_ids) > 1:
        messages.append(
            "Results come from more than one document. "
            "Name the source document for each clause cited."
        )

    return " ".join(messages)


def jit_for_get_clause(touches_boundary: bool) -> str:
    """
    Return guidance when a clause sits at a page boundary.

    'touches_boundary' is True when the chunk is the last on its page
    (next chunk has a different page number) — the clause text may continue
    on the following page and the chunk may be truncated.
    """
    if touches_boundary:
        return (
            "This clause may continue past the page break. "
            "Flag possible truncation to the user."
        )
    return ""


def jit_for_compare(clause_type_a: str, clause_type_b: str) -> str:
    """
    Return guidance when comparing clauses of different types.

    RAW TEXT ONLY is returned to the LLM — no analysis from the server.
    This JIT rule ensures the LLM acknowledges the type mismatch.
    """
    if clause_type_a != clause_type_b:
        return (
            "These are different clause types "
            f"({clause_type_a} vs {clause_type_b}). "
            "State that before comparing."
        )
    return ""
