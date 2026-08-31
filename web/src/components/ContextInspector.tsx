"use client";

import { ContextStats } from "@/types";
import { useState } from "react";
import { ChevronUp, ChevronDown, Zap } from "lucide-react";

interface Props {
  stats: ContextStats;
}

function fmt(n: number) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

export default function ContextInspector({ stats }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (stats.turns.length === 0) return null;

  const last = stats.turns[stats.turns.length - 1];

  return (
    <div
      className="glass border-t"
      style={{ borderColor: "var(--border)", fontSize: "12px" }}
    >
      {/* Summary strip */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5" style={{ color: "var(--accent-1)" }}>
            <Zap size={12} />
            <span className="font-semibold" style={{ color: "var(--text-secondary)" }}>Context</span>
          </div>
          <span style={{ color: "var(--text-muted)" }}>Turn {last.index}</span>
          <span style={{ color: "var(--text-secondary)" }}>
            ↑{fmt(last.inputTokens)} ↓{fmt(last.outputTokens)} tokens
          </span>
          <span style={{ color: "var(--text-muted)" }}>·</span>
          <span style={{ color: "var(--text-secondary)" }}>
            Total ↑{fmt(stats.totalInput)} ↓{fmt(stats.totalOutput)}
          </span>
        </div>
        <div style={{ color: "var(--text-muted)" }}>
          {expanded ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
        </div>
      </button>

      {/* Expanded per-turn table */}
      {expanded && (
        <div className="px-4 pb-3 fade-in">
          <table className="w-full" style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ color: "var(--text-muted)" }}>
                <th className="text-left py-1 pr-4 font-medium">Turn</th>
                <th className="text-right py-1 pr-4 font-medium">Input tokens</th>
                <th className="text-right py-1 font-medium">Output tokens</th>
              </tr>
            </thead>
            <tbody>
              {stats.turns.map((t) => (
                <tr key={t.index} style={{ color: "var(--text-secondary)", borderTop: "1px solid var(--border)" }}>
                  <td className="py-1 pr-4">{t.index}</td>
                  <td className="py-1 pr-4 text-right">{t.inputTokens.toLocaleString()}</td>
                  <td className="py-1 text-right">{t.outputTokens.toLocaleString()}</td>
                </tr>
              ))}
              <tr style={{ color: "var(--text-primary)", borderTop: "1px solid var(--border-hover)", fontWeight: 600 }}>
                <td className="py-1.5 pr-4">Total</td>
                <td className="py-1.5 pr-4 text-right">{stats.totalInput.toLocaleString()}</td>
                <td className="py-1.5 text-right">{stats.totalOutput.toLocaleString()}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
