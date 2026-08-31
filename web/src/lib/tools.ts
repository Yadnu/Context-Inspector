// Tool schemas in both Anthropic and OpenAI formats.
// These mirror the FastMCP tool definitions in server/main.py exactly.

const CLAUSE_TYPE_ENUM = [
  "indemnification",
  "termination",
  "liability",
  "confidentiality",
  "payment",
  "governing_law",
  "other",
];

// ── Anthropic format ─────────────────────────────────────────────────────────

export const TOOLS_ANTHROPIC = [
  {
    name: "search_clauses",
    description:
      "Search contract clauses by natural-language query. Returns ranked results with page numbers and clause types. ALWAYS check the `jit` field — when non-empty it contains mandatory guidance for how to present results.",
    input_schema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Natural-language question or keyword phrase to search for.",
        },
        clause_type: {
          type: "string",
          enum: CLAUSE_TYPE_ENUM,
          description: "Optional: restrict results to this clause type only.",
        },
        top_k: {
          type: "integer",
          description: "Maximum number of results to return (default: 5).",
          default: 5,
        },
      },
      required: ["query"],
    },
  },
  {
    name: "get_clause",
    description:
      "Retrieve the full text and surrounding context for a single clause by its stable ID. Use when the user wants to read a clause in full. Check `jit` for page-boundary truncation warnings.",
    input_schema: {
      type: "object",
      properties: {
        clause_id: {
          type: "string",
          description:
            "Stable clause identifier returned by search_clauses (format: '<doc_id>:<chunk_index>').",
        },
      },
      required: ["clause_id"],
    },
  },
  {
    name: "list_documents",
    description:
      "List all ingested contract documents with their filename, page count, and clause count.",
    input_schema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "compare_clauses",
    description:
      "Retrieve two clauses side-by-side for comparison. Returns raw text only — you perform the comparison. ALWAYS check `jit`: if clause types differ, declare the mismatch first.",
    input_schema: {
      type: "object",
      properties: {
        clause_id_a: {
          type: "string",
          description: "First clause ID (from search_clauses).",
        },
        clause_id_b: {
          type: "string",
          description: "Second clause ID (from search_clauses).",
        },
      },
      required: ["clause_id_a", "clause_id_b"],
    },
  },
];

// ── OpenAI function-calling format ───────────────────────────────────────────

export const TOOLS_OPENAI = TOOLS_ANTHROPIC.map((t) => ({
  type: "function" as const,
  function: {
    name: t.name,
    description: t.description,
    parameters: t.input_schema,
  },
}));
