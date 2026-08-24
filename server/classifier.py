"""
Keyword-rule clause classifier.

RULES maps each clause type to a list of lowercase substrings. A chunk
matches the first type whose any keyword appears in the lowercased text.
Priority is defined by PRIORITY_ORDER (most-specific types first).

To tune: edit RULES or PRIORITY_ORDER. No re-indexing is needed — the
classifier runs at ingest time, so re-ingest after changes.
"""
from __future__ import annotations

from server.models import ClauseType

# ---------------------------------------------------------------------------
# Tunable rules — edit freely
# ---------------------------------------------------------------------------

RULES: dict[str, list[str]] = {
    "indemnification": [
        "indemnif",
        "hold harmless",
        "defend and indemnify",
        "indemnitor",
        "indemnitee",
    ],
    "termination": [
        "terminat",
        "end of term",
        "expir",
        "cancel",
        "notice of termination",
        "right to terminate",
    ],
    "liability": [
        "liabilit",
        "liable",
        "consequential damages",
        "incidental damages",
        "limitation of liability",
        "cap on liability",
        "in no event",
    ],
    "confidentiality": [
        "confidential",
        "non-disclosure",
        "nda",
        "proprietary information",
        "trade secret",
        "keep secret",
        "disclose",
    ],
    "payment": [
        "payment",
        "invoice",
        "remittance",
        "compensation",
        "fee",
        "pricing",
        "net 30",
        "net 60",
        "overdue",
        "late payment",
    ],
    "governing_law": [
        "governing law",
        "choice of law",
        "jurisdiction",
        "venue",
        "courts of",
        "laws of the state",
        "laws of the commonwealth",
    ],
}

# First match wins — order from most-specific to least-specific
PRIORITY_ORDER: list[str] = [
    "indemnification",
    "governing_law",
    "confidentiality",
    "termination",
    "liability",
    "payment",
]


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


def classify_chunk(text: str) -> ClauseType:
    """
    Classify a chunk of contract text into one of the named clause types,
    or "other" if no keyword matches.

    Runs in O(n_rules × n_keywords_per_rule) — fast enough for ingest.
    """
    lower = text.lower()
    for clause_type in PRIORITY_ORDER:
        if any(kw in lower for kw in RULES[clause_type]):
            return ClauseType(clause_type)
    return ClauseType.other
