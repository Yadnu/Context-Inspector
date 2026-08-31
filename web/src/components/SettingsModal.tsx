"use client";

import { Settings, DEFAULT_SETTINGS } from "@/types";
import { saveSettings } from "@/lib/storage";
import { useState } from "react";
import { X, Eye, EyeOff } from "lucide-react";

const ANTHROPIC_MODELS = [
  { value: "claude-sonnet-4-5", label: "Claude Sonnet 4.5" },
  { value: "claude-opus-4-5", label: "Claude Opus 4.5" },
  { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
];
const OPENAI_MODELS = [
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o mini" },
  { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
];

interface Props {
  settings: Settings;
  onClose: () => void;
  onSave: (s: Settings) => void;
}

export default function SettingsModal({ settings, onClose, onSave }: Props) {
  const [local, setLocal] = useState<Settings>({ ...settings });
  const [showKey, setShowKey] = useState(false);

  const models = local.provider === "anthropic" ? ANTHROPIC_MODELS : OPENAI_MODELS;

  function handleProviderChange(p: Settings["provider"]) {
    const defaultModel = p === "anthropic" ? ANTHROPIC_MODELS[0].value : OPENAI_MODELS[0].value;
    setLocal((s) => ({ ...s, provider: p, model: defaultModel, apiKey: "" }));
  }

  function handleSave() {
    saveSettings(local);
    onSave(local);
    onClose();
  }

  function handleReset() {
    const fresh = { ...DEFAULT_SETTINGS };
    setLocal(fresh);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="glass rounded-xl w-full max-w-md mx-4 fade-in"
        style={{ border: "1px solid var(--border-accent)" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b" style={{ borderColor: "var(--border)" }}>
          <div>
            <h2 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>Settings</h2>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>API keys are stored locally and never sent to our servers.</p>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5" style={{ padding: "6px" }}>
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-5">
          {/* Provider */}
          <div>
            <label className="text-xs font-medium mb-2 block" style={{ color: "var(--text-secondary)" }}>AI Provider</label>
            <div className="grid grid-cols-2 gap-2">
              {(["anthropic", "openai"] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => handleProviderChange(p)}
                  className="py-2.5 rounded-lg text-sm font-medium transition-all duration-150"
                  style={{
                    background: local.provider === p ? "linear-gradient(135deg, var(--accent-1), var(--accent-2))" : "var(--bg-elevated)",
                    color: local.provider === p ? "#fff" : "var(--text-secondary)",
                    border: `1px solid ${local.provider === p ? "transparent" : "var(--border)"}`,
                  }}
                >
                  {p === "anthropic" ? "Anthropic" : "OpenAI"}
                </button>
              ))}
            </div>
          </div>

          {/* API Key */}
          <div>
            <label className="text-xs font-medium mb-2 block" style={{ color: "var(--text-secondary)" }}>
              {local.provider === "anthropic" ? "Anthropic" : "OpenAI"} API Key
            </label>
            <div className="relative">
              <input
                type={showKey ? "text" : "password"}
                value={local.apiKey}
                onChange={(e) => setLocal((s) => ({ ...s, apiKey: e.target.value }))}
                placeholder={local.provider === "anthropic" ? "sk-ant-..." : "sk-..."}
                className="input-base pr-10"
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2"
                style={{ color: "var(--text-muted)" }}
              >
                {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          {/* Model */}
          <div>
            <label className="text-xs font-medium mb-2 block" style={{ color: "var(--text-secondary)" }}>Model</label>
            <select
              value={local.model}
              onChange={(e) => setLocal((s) => ({ ...s, model: e.target.value }))}
              className="input-base"
              style={{ cursor: "pointer" }}
            >
              {models.map((m) => (
                <option key={m.value} value={m.value} style={{ background: "var(--bg-elevated)" }}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          {/* Server URL */}
          <div>
            <label className="text-xs font-medium mb-2 block" style={{ color: "var(--text-secondary)" }}>MCP Server URL</label>
            <input
              type="url"
              value={local.serverUrl}
              onChange={(e) => setLocal((s) => ({ ...s, serverUrl: e.target.value }))}
              placeholder="http://localhost:8000"
              className="input-base"
            />
            <p className="text-xs mt-1.5" style={{ color: "var(--text-muted)" }}>
              For local dev use http://localhost:8000. For production, paste your Railway URL.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-5 border-t" style={{ borderColor: "var(--border)" }}>
          <button onClick={handleReset} className="btn-ghost text-xs">Reset to defaults</button>
          <div className="flex gap-2">
            <button onClick={onClose} className="btn-ghost">Cancel</button>
            <button onClick={handleSave} className="btn-accent" disabled={!local.apiKey}>Save</button>
          </div>
        </div>
      </div>
    </div>
  );
}
