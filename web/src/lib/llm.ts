// LLM client — runs entirely in the browser.
// API key comes from localStorage (via settings), never touches the Next.js server.
// Supports Anthropic (claude-*) and OpenAI (gpt-4o, etc.)
//
// Per-turn flow (single tool call):
//  1. POST conversation + tool schemas to LLM
//  2. If LLM requests a tool → execute it, append result (including jit field)
//  3. POST again → get final text response
//  4. Yield UIMessages for each step (tool_call, tool_result, assistant)

import { callTool } from "@/lib/mcp";
import { TOOLS_ANTHROPIC, TOOLS_OPENAI } from "@/lib/tools";
import {
  AnthropicContentBlock,
  AnthropicResponse,
  OpenAIMessage,
  OpenAIResponse,
  Settings,
  TurnUsage,
  UIMessage,
} from "@/types";

// System prompt — forces the model to use tools and cite pages
const SYSTEM_PROMPT = `You are Clause Lens, a contract analysis assistant.
RULES:
1. ALWAYS use a tool to retrieve clause text before answering. Never answer from memory.
2. ALWAYS cite the page number and source document filename for every clause you reference.
3. If retrieval returns no results, say so clearly. Do not invent content.
4. If the tool result contains a non-empty "jit" field, follow its instructions exactly — it takes priority over these general rules.
5. Keep answers concise and grounded in the retrieved text.`;

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

// ── Anthropic ─────────────────────────────────────────────────────────────────

async function anthropicRound(
  messages: object[],
  settings: Settings
): Promise<AnthropicResponse> {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": settings.apiKey,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: settings.model,
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      messages,
      tools: TOOLS_ANTHROPIC,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${err}`);
  }
  return res.json() as Promise<AnthropicResponse>;
}

async function* runAnthropic(
  userText: string,
  history: object[],
  settings: Settings
): AsyncGenerator<UIMessage> {
  // Build conversation
  const messages: object[] = [
    ...history,
    { role: "user", content: userText },
  ];

  // --- Turn 1: initial LLM call ---
  const resp1 = await anthropicRound(messages, settings);
  const usage1: TurnUsage = {
    inputTokens: resp1.usage.input_tokens,
    outputTokens: resp1.usage.output_tokens,
  };

  if (resp1.stop_reason !== "tool_use") {
    // No tool call — yield assistant message directly
    const text = resp1.content
      .filter((b) => b.type === "text")
      .map((b) => b.text ?? "")
      .join("");
    yield { id: uid(), type: "assistant", content: text, timestamp: new Date(), usage: usage1 };
    return;
  }

  // Find the first tool_use block (single tool call per turn)
  const toolBlock = resp1.content.find(
    (b): b is AnthropicContentBlock & { type: "tool_use" } =>
      b.type === "tool_use"
  )!;

  // Emit any assistant text before the tool call
  const preText = resp1.content
    .filter((b) => b.type === "text")
    .map((b) => b.text ?? "")
    .join("")
    .trim();
  if (preText) {
    yield { id: uid(), type: "assistant", content: preText, timestamp: new Date(), usage: usage1 };
  }

  // Yield tool_call bubble
  yield {
    id: uid(),
    type: "tool_call",
    content: toolBlock.name ?? "",
    toolName: toolBlock.name,
    toolArgs: toolBlock.input,
    timestamp: new Date(),
  };

  // --- Execute the tool ---
  let toolResult: Record<string, unknown>;
  try {
    toolResult = await callTool(toolBlock.name!, toolBlock.input ?? {});
  } catch (err) {
    yield { id: uid(), type: "error", content: String(err), timestamp: new Date() };
    return;
  }

  const jit = typeof toolResult.jit === "string" ? toolResult.jit : "";

  // Yield tool_result bubble
  yield {
    id: uid(),
    type: "tool_result",
    content: JSON.stringify(toolResult, null, 2),
    toolName: toolBlock.name,
    toolResult,
    jit,
    timestamp: new Date(),
  };

  // --- Turn 2: feed tool result back ---
  const messages2 = [
    ...messages,
    { role: "assistant", content: resp1.content },
    {
      role: "user",
      content: [
        {
          type: "tool_result",
          tool_use_id: toolBlock.id,
          // Pass full JSON so jit reaches the model
          content: JSON.stringify(toolResult),
        },
      ],
    },
  ];

  const resp2 = await anthropicRound(messages2, settings);
  const usage2: TurnUsage = {
    inputTokens: resp2.usage.input_tokens,
    outputTokens: resp2.usage.output_tokens,
  };

  const finalText = resp2.content
    .filter((b) => b.type === "text")
    .map((b) => b.text ?? "")
    .join("");

  yield {
    id: uid(),
    type: "assistant",
    content: finalText,
    timestamp: new Date(),
    usage: { inputTokens: usage1.inputTokens + usage2.inputTokens, outputTokens: usage1.outputTokens + usage2.outputTokens },
  };
}

// ── OpenAI ────────────────────────────────────────────────────────────────────

async function openaiRound(
  messages: OpenAIMessage[],
  settings: Settings
): Promise<OpenAIResponse> {
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${settings.apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: settings.model,
      messages,
      tools: TOOLS_OPENAI,
      tool_choice: "auto",
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`OpenAI API error ${res.status}: ${err}`);
  }
  return res.json() as Promise<OpenAIResponse>;
}

async function* runOpenAI(
  userText: string,
  history: OpenAIMessage[],
  settings: Settings
): AsyncGenerator<UIMessage> {
  const messages: OpenAIMessage[] = [
    { role: "system", content: SYSTEM_PROMPT },
    ...history,
    { role: "user", content: userText },
  ];

  const resp1 = await openaiRound(messages, settings);
  const msg1 = resp1.choices[0].message;
  const usage1: TurnUsage = {
    inputTokens: resp1.usage.prompt_tokens,
    outputTokens: resp1.usage.completion_tokens,
  };

  if (resp1.choices[0].finish_reason !== "tool_calls" || !msg1.tool_calls?.length) {
    yield { id: uid(), type: "assistant", content: msg1.content ?? "", timestamp: new Date(), usage: usage1 };
    return;
  }

  const toolCall = msg1.tool_calls[0];

  if (msg1.content?.trim()) {
    yield { id: uid(), type: "assistant", content: msg1.content, timestamp: new Date(), usage: usage1 };
  }

  let parsedArgs: Record<string, unknown> = {};
  try { parsedArgs = JSON.parse(toolCall.function.arguments); } catch { /* ignore */ }

  yield {
    id: uid(), type: "tool_call", content: toolCall.function.name,
    toolName: toolCall.function.name, toolArgs: parsedArgs, timestamp: new Date(),
  };

  let toolResult: Record<string, unknown>;
  try {
    toolResult = await callTool(toolCall.function.name, parsedArgs);
  } catch (err) {
    yield { id: uid(), type: "error", content: String(err), timestamp: new Date() };
    return;
  }

  const jit = typeof toolResult.jit === "string" ? toolResult.jit : "";

  yield {
    id: uid(), type: "tool_result", content: JSON.stringify(toolResult, null, 2),
    toolName: toolCall.function.name, toolResult, jit, timestamp: new Date(),
  };

  const messages2: OpenAIMessage[] = [
    ...messages,
    msg1,
    { role: "tool", tool_call_id: toolCall.id, content: JSON.stringify(toolResult) },
  ];

  const resp2 = await openaiRound(messages2, settings);
  const usage2: TurnUsage = {
    inputTokens: resp2.usage.prompt_tokens,
    outputTokens: resp2.usage.completion_tokens,
  };

  yield {
    id: uid(), type: "assistant",
    content: resp2.choices[0].message.content ?? "",
    timestamp: new Date(),
    usage: { inputTokens: usage1.inputTokens + usage2.inputTokens, outputTokens: usage1.outputTokens + usage2.outputTokens },
  };
}

// ── Public API ────────────────────────────────────────────────────────────────

export async function* chat(
  userText: string,
  history: object[],
  settings: Settings
): AsyncGenerator<UIMessage> {
  if (!settings.apiKey) {
    yield { id: uid(), type: "error", content: "No API key configured. Open Settings to add one.", timestamp: new Date() };
    return;
  }
  if (settings.provider === "anthropic") {
    yield* runAnthropic(userText, history, settings);
  } else {
    yield* runOpenAI(userText, history as OpenAIMessage[], settings);
  }
}
