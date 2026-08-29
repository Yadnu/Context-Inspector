"use client";

import { ContextStats, Settings, UIMessage } from "@/types";
import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import ContextInspector from "./ContextInspector";
import { Send, Sparkles, Loader2, Key } from "lucide-react";

interface Props {
  messages: UIMessage[];
  stats: ContextStats;
  settings: Settings;
  isProcessing: boolean;
  onSendMessage: (text: string) => void;
  onOpenSettings: () => void;
}

const SUGGESTIONS = [
  "What are the termination notice requirements?",
  "Summarize indemnification obligations in the contract.",
  "What is the limitation of liability cap?",
  "What are the payment terms and invoice due dates?",
];

export default function ChatPanel({
  messages,
  stats,
  settings,
  isProcessing,
  onSendMessage,
  onOpenSettings,
}: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;
    const text = input.trim();
    setInput("");
    onSendMessage(text);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden" style={{ background: "var(--bg-base)" }}>
      {/* Header / Banner if API Key missing */}
      {!settings.apiKey && (
        <div
          className="flex items-center justify-between px-4 py-2.5 text-xs font-medium"
          style={{
            background: "rgba(245, 158, 11, 0.12)",
            borderBottom: "1px solid rgba(245, 158, 11, 0.3)",
            color: "var(--warning)",
          }}
        >
          <div className="flex items-center gap-2">
            <Key size={14} />
            <span>API Key required to run questions.</span>
          </div>
          <button
            onClick={onOpenSettings}
            className="underline hover:opacity-80 transition-opacity font-semibold"
          >
            Configure Settings
          </button>
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto py-12">
            <div
              className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4"
              style={{
                background: "linear-gradient(135deg, var(--accent-1), var(--accent-2))",
                boxShadow: "0 0 25px var(--accent-glow)",
              }}
            >
              <Sparkles size={24} color="#fff" />
            </div>
            <h1 className="text-xl font-bold mb-2 gradient-text">Ask Clause Lens</h1>
            <p className="text-sm mb-6 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              Query contract terms, inspect citations with exact page numbers, or compare clauses across documents.
            </p>

            {/* Suggestions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 w-full">
              {SUGGESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(s)}
                  disabled={isProcessing}
                  className="glass glass-hover text-left p-3 rounded-xl text-xs font-medium transition-all duration-150"
                  style={{ color: "var(--text-secondary)" }}
                >
                  &ldquo;{s}&rdquo;
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="flex items-center gap-3 glass rounded-xl px-4 py-3 max-w-[200px] fade-in" style={{ borderColor: "var(--border-accent)" }}>
            <Loader2 size={15} className="animate-spin" style={{ color: "var(--accent-1)" }} />
            <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
              Analyzing clause...
            </span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Context Inspector Strip */}
      <ContextInspector stats={stats} />

      {/* Input Form */}
      <div className="p-4 border-t" style={{ borderColor: "var(--border)", background: "var(--bg-surface)" }}>
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder={settings.apiKey ? "Ask a question about your contract... (Shift+Enter for new line)" : "Please add an API key in Settings first"}
            disabled={!settings.apiKey || isProcessing}
            className="input-base pr-12 py-3 resize-none"
            style={{
              minHeight: "48px",
              maxHeight: "160px",
              borderRadius: "var(--radius-lg)",
            }}
          />
          <button
            type="submit"
            disabled={!input.trim() || !settings.apiKey || isProcessing}
            className="absolute right-2.5 p-2 rounded-xl btn-accent flex items-center justify-center"
            style={{ width: "34px", height: "34px", padding: 0 }}
          >
            {isProcessing ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={15} />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
