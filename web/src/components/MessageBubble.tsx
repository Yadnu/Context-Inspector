"use client";

import { UIMessage } from "@/types";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Search, FileText, List, GitCompare, ChevronDown, ChevronRight,
  AlertTriangle, Zap, Bot, User
} from "lucide-react";

const TOOL_ICONS: Record<string, React.ReactNode> = {
  search_clauses:  <Search size={13} />,
  get_clause:      <FileText size={13} />,
  list_documents:  <List size={13} />,
  compare_clauses: <GitCompare size={13} />,
};

interface Props {
  message: UIMessage;
}

export default function MessageBubble({ message }: Props) {
  const [expanded, setExpanded] = useState(false);

  /* ── User ─────────────────────────────────────────────────── */
  if (message.type === "user") {
    return (
      <div className="flex justify-end fade-in">
        <div className="flex items-end gap-2 max-w-[75%]">
          <div
            className="rounded-2xl rounded-br-sm px-4 py-3 text-sm leading-relaxed"
            style={{
              background: "linear-gradient(135deg, var(--accent-1), var(--accent-2))",
              color: "#fff",
            }}
          >
            {message.content}
          </div>
          <div
            className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center"
            style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }}
          >
            <User size={14} style={{ color: "var(--text-muted)" }} />
          </div>
        </div>
      </div>
    );
  }

  /* ── Tool call ────────────────────────────────────────────── */
  if (message.type === "tool_call") {
    const icon = TOOL_ICONS[message.toolName ?? ""] ?? <Search size={13} />;
    return (
      <div className="flex justify-start fade-in">
        <div
          className="glass rounded-xl px-3 py-2 max-w-[80%] cursor-pointer select-none"
          style={{ borderColor: "var(--border-accent)" }}
          onClick={() => setExpanded((v) => !v)}
        >
          <div className="flex items-center gap-2">
            <span style={{ color: "var(--accent-1)" }}>{icon}</span>
            <span className="text-xs font-semibold" style={{ color: "var(--accent-1)", fontFamily: "'JetBrains Mono', monospace" }}>
              {message.toolName}
            </span>
            <span style={{ color: "var(--text-muted)", marginLeft: "auto" }}>
              {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            </span>
          </div>
          {expanded && message.toolArgs && (
            <pre
              className="mt-2 text-xs overflow-auto"
              style={{
                color: "var(--text-secondary)",
                fontFamily: "'JetBrains Mono', monospace",
                maxHeight: "120px",
              }}
            >
              {JSON.stringify(message.toolArgs, null, 2)}
            </pre>
          )}
        </div>
      </div>
    );
  }

  /* ── Tool result ──────────────────────────────────────────── */
  if (message.type === "tool_result") {
    return (
      <div className="flex justify-start fade-in">
        <div className="glass rounded-xl px-3 py-2 max-w-[80%]" style={{ borderColor: "rgba(34,197,94,0.25)" }}>
          <div className="flex items-center gap-2 mb-1.5">
            <span style={{ color: "#22c55e", fontSize: "11px", fontWeight: 600 }}>Result</span>
            {message.jit && (
              <span className="jit-badge">
                <Zap size={10} />
                JIT
              </span>
            )}
          </div>
          {message.jit && (
            <p
              className="text-xs mb-2 leading-relaxed"
              style={{
                color: "var(--jit)",
                background: "rgba(14,165,233,0.08)",
                borderRadius: "var(--radius-sm)",
                padding: "6px 8px",
                borderLeft: "2px solid var(--jit)",
              }}
            >
              {message.jit}
            </p>
          )}
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-xs w-full text-left"
            style={{ color: "var(--text-muted)" }}
          >
            {expanded ? "Hide raw JSON ▲" : "Show raw JSON ▼"}
          </button>
          {expanded && (
            <pre
              className="mt-2 text-xs overflow-auto fade-in"
              style={{
                color: "var(--text-secondary)",
                fontFamily: "'JetBrains Mono', monospace",
                maxHeight: "200px",
              }}
            >
              {message.content}
            </pre>
          )}
        </div>
      </div>
    );
  }

  /* ── Error ────────────────────────────────────────────────── */
  if (message.type === "error") {
    return (
      <div className="flex justify-start fade-in">
        <div
          className="glass rounded-xl px-4 py-3 max-w-[80%] flex items-start gap-2"
          style={{ borderColor: "rgba(239,68,68,0.35)" }}
        >
          <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" style={{ color: "var(--error)" }} />
          <p className="text-sm" style={{ color: "#fca5a5" }}>{message.content}</p>
        </div>
      </div>
    );
  }

  /* ── Assistant ────────────────────────────────────────────── */
  return (
    <div className="flex justify-start fade-in">
      <div className="flex items-end gap-2 max-w-[82%]">
        <div
          className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, var(--accent-1), var(--accent-2))",
            boxShadow: "0 0 12px var(--accent-glow)",
          }}
        >
          <Bot size={14} color="#fff" />
        </div>
        <div
          className="glass rounded-2xl rounded-bl-sm px-4 py-3 text-sm leading-relaxed"
          style={{ borderLeft: "2px solid var(--accent-1)" }}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0" style={{ color: "var(--text-primary)" }}>{children}</p>,
              code: ({ inline, children, ...props }: { inline?: boolean; children?: React.ReactNode }) =>
                inline ? (
                  <code
                    {...props}
                    className="px-1.5 py-0.5 rounded text-xs"
                    style={{ background: "var(--bg-elevated)", color: "#a5b4fc", fontFamily: "'JetBrains Mono', monospace" }}
                  >
                    {children}
                  </code>
                ) : (
                  <pre className="overflow-auto rounded-lg p-3 my-2" style={{ background: "var(--bg-elevated)" }}>
                    <code {...props} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", color: "var(--text-secondary)" }}>
                      {children}
                    </code>
                  </pre>
                ),
              strong: ({ children }) => <strong style={{ color: "var(--text-primary)", fontWeight: 600 }}>{children}</strong>,
              ul: ({ children }) => <ul className="list-disc pl-4 my-1 space-y-0.5">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-4 my-1 space-y-0.5">{children}</ol>,
              li: ({ children }) => <li style={{ color: "var(--text-primary)" }}>{children}</li>,
              h1: ({ children }) => <h1 className="text-base font-bold mb-1 mt-2" style={{ color: "var(--text-primary)" }}>{children}</h1>,
              h2: ({ children }) => <h2 className="text-sm font-semibold mb-1 mt-2" style={{ color: "var(--text-primary)" }}>{children}</h2>,
              h3: ({ children }) => <h3 className="text-sm font-medium mb-1 mt-2" style={{ color: "var(--text-secondary)" }}>{children}</h3>,
              blockquote: ({ children }) => (
                <blockquote className="border-l-2 pl-3 my-2 italic" style={{ borderColor: "var(--accent-1)", color: "var(--text-secondary)" }}>
                  {children}
                </blockquote>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
