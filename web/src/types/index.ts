// Shared TypeScript types for Clause Lens web client

export type Provider = "anthropic" | "openai";

export interface Settings {
  provider: Provider;
  apiKey: string;
  model: string;
  serverUrl: string;
}

export const DEFAULT_SETTINGS: Settings = {
  provider: "anthropic",
  apiKey: "",
  model: "claude-sonnet-4-5",
  serverUrl: "http://localhost:8000",
};

// ── Document ────────────────────────────────────────────────────────────────

export interface Document {
  doc_id: string;
  filename: string;
  page_count: number;
  clause_count: number;
}

// ── Messages (UI layer) ──────────────────────────────────────────────────────

export type MessageType =
  | "user"
  | "assistant"
  | "tool_call"
  | "tool_result"
  | "error";

export interface TurnUsage {
  inputTokens: number;
  outputTokens: number;
}

export interface UIMessage {
  id: string;
  type: MessageType;
  content: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  toolResult?: unknown;
  jit?: string;
  timestamp: Date;
  usage?: TurnUsage;
}

// ── Token counters ───────────────────────────────────────────────────────────

export interface ContextStats {
  turns: Array<{
    index: number;
    inputTokens: number;
    outputTokens: number;
  }>;
  totalInput: number;
  totalOutput: number;
}

// ── LLM raw types ────────────────────────────────────────────────────────────

// Anthropic
export interface AnthropicContentBlock {
  type: "text" | "tool_use";
  text?: string;
  id?: string;
  name?: string;
  input?: Record<string, unknown>;
}

export interface AnthropicResponse {
  id: string;
  type: string;
  role: string;
  content: AnthropicContentBlock[];
  stop_reason: string;
  usage: { input_tokens: number; output_tokens: number };
}

// OpenAI
export interface OpenAIToolCall {
  id: string;
  type: "function";
  function: { name: string; arguments: string };
}

export interface OpenAIMessage {
  role: string;
  content: string | null;
  tool_calls?: OpenAIToolCall[];
  tool_call_id?: string;
}

export interface OpenAIResponse {
  id: string;
  choices: Array<{
    message: OpenAIMessage;
    finish_reason: string;
  }>;
  usage: { prompt_tokens: number; completion_tokens: number };
}
