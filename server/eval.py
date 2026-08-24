"""
CLI evaluation script — validate retrieval quality before building the client.

Usage
-----
# Single query
python -m server.eval --pdf path/to/contract.pdf --query "indemnification"

# Multiple queries + clause-type filter
python -m server.eval \\
    --pdf path/to/contract.pdf \\
    --query "what are the payment terms" \\
    --query "notice period for termination" \\
    --query "governing jurisdiction" \\
    --top-k 3

# With clause-type filter (only searches that clause type)
python -m server.eval \\
    --pdf path/to/contract.pdf \\
    --query "liability cap" \\
    --clause-type liability

Output
------
Per query: top_k results with score, page, clause_type, and a 300-char
text preview. A summary table is printed at the end.

Score guidance
--------------
Cross-encoder scores have no fixed scale. Roughly:
  > 5    : very high confidence match
  2 – 5  : confident match
  0 – 2  : moderate match
  < 0    : weak / tangential match
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path


def _separator(char: str = "-", width: int = 70) -> str:
    return char * width


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m server.eval",
        description="Evaluate retrieval quality on a contract PDF.",
    )
    parser.add_argument("--pdf", required=True, help="Path to PDF contract file.")
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        required=True,
        metavar="QUERY",
        help="Test query. Repeat to run multiple queries.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Results per query (default: 5).",
    )
    parser.add_argument(
        "--clause-type",
        choices=[
            "indemnification",
            "termination",
            "liability",
            "confidentiality",
            "payment",
            "governing_law",
            "other",
        ],
        default=None,
        help="Optional: restrict results to this clause type.",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # ── Ingest (or load cache) ───────────────────────────────────────────────
    print(_separator("="))
    print(f"  Clause Lens - eval")
    print(_separator("="))
    print(f"  PDF      : {pdf_path.resolve()}")
    print(f"  Queries  : {len(args.queries)}")
    print(f"  top_k    : {args.top_k}")
    if args.clause_type:
        print(f"  Filter   : clause_type = {args.clause_type}")
    print()

    from server.ingest import ingest_document

    result = ingest_document(pdf_path)
    status = "CACHED" if result.get("cached") else "INDEXED"
    print(
        f"[{status}] {result['filename']} - "
        f"{result['page_count']} pages, {result['clause_count']} chunks"
    )
    print()

    # ── Run queries ──────────────────────────────────────────────────────────
    from server.search import search_clauses

    summary_rows: list[tuple[str, float, str, int]] = []  # query, top_score, type, page

    for q_idx, query in enumerate(args.queries, start=1):
        print(_separator())
        print(f"  Query {q_idx}/{len(args.queries)}: {query!r}")
        print(_separator())

        results = search_clauses(query, clause_type=args.clause_type, top_k=args.top_k)

        if not results:
            print("  [!]  No results returned.\n")
            summary_rows.append((query, 0.0, "-", 0))
            continue

        for rank, r in enumerate(results, start=1):
            print(
                f"\n  [{rank}] score={r.score:+.4f}  page={r.page}  "
                f"type={r.clause_type.value}  id={r.clause_id}"
            )
            preview = textwrap.fill(
                r.text[:300].replace("\n", " "),
                width=66,
                initial_indent="       ",
                subsequent_indent="       ",
            )
            print(preview)
            if len(r.text) > 300:
                print("       [...]")

        top = results[0]
        summary_rows.append((query, top.score, top.clause_type.value, top.page))
        print()

    # ── Summary table ────────────────────────────────────────────────────────
    print(_separator("="))
    print("  SUMMARY")
    print(_separator("="))
    print(f"  {'#':<3}  {'Score':>8}  {'Type':<18}  {'Pg':>4}  Query")
    print(f"  {'-'*3}  {'-'*8}  {'-'*18}  {'-'*4}  {'-'*30}")
    for i, (q, score, ctype, pg) in enumerate(summary_rows, start=1):
        q_short = q[:40] + "..." if len(q) > 40 else q
        print(f"  {i:<3}  {score:>+8.4f}  {ctype:<18}  {pg:>4}  {q_short}")
    print(_separator("="))


if __name__ == "__main__":
    main()
