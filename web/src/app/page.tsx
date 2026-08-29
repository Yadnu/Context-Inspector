"use client";

import { ContextStats, Document, Settings, DEFAULT_SETTINGS, UIMessage } from "@/types";
import { loadSettings } from "@/lib/storage";
import { callTool } from "@/lib/mcp";
import { chat } from "@/lib/llm";
import { useCallback, useEffect, useState } from "react";
import DocumentPanel from "@/components/DocumentPanel";
import ChatPanel from "@/components/ChatPanel";
import SettingsModal from "@/components/SettingsModal";

export default function Home() {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const [stats, setStats] = useState<ContextStats>({
    turns: [],
    totalInput: 0,
    totalOutput: 0,
  });

  // Load settings from localStorage on mount
  useEffect(() => {
    const loaded = loadSettings();
    setSettings(loaded);
  }, []);

  // Fetch document list from MCP server
  const fetchDocuments = useCallback(async () => {
    try {
      const res = await callTool("list_documents", {});
      if (Array.isArray(res.documents)) {
        setDocuments(res.documents as Document[]);
      }
    } catch (err) {
      console.warn("Failed to fetch document list:", err);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Handle user send message
  async function handleSendMessage(userText: string) {
    const userMsg: UIMessage = {
      id: Math.random().toString(36).slice(2, 10),
      type: "user",
      content: userText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsProcessing(true);

    // Convert existing message history to format for LLM helper
    // Filter out tool_call/tool_result/error for history array if needed or map them
    const historyObj = messages
      .filter((m) => m.type === "user" || m.type === "assistant")
      .map((m) => ({
        role: m.type === "user" ? "user" : "assistant",
        content: m.content,
      }));

    try {
      const generator = chat(userText, historyObj, settings);
      let turnTokens: { inputTokens: number; outputTokens: number } | null = null;

      for await (const chunkMsg of generator) {
        setMessages((prev) => [...prev, chunkMsg]);

        if (chunkMsg.usage) {
          turnTokens = chunkMsg.usage;
        }
      }

      if (turnTokens) {
        setStats((prev) => {
          const turnIndex = prev.turns.length + 1;
          const newTurn = {
            index: turnIndex,
            inputTokens: turnTokens!.inputTokens,
            outputTokens: turnTokens!.outputTokens,
          };
          return {
            turns: [...prev.turns, newTurn],
            totalInput: prev.totalInput + turnTokens!.inputTokens,
            totalOutput: prev.totalOutput + turnTokens!.outputTokens,
          };
        });
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2, 10),
          type: "error",
          content: `Error running turn: ${String(err)}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  }

  return (
    <main className="flex h-screen w-screen overflow-hidden">
      {/* Sidebar / Document Panel */}
      <DocumentPanel
        documents={documents}
        settings={settings}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onRefreshDocs={fetchDocuments}
      />

      {/* Main Chat Interface */}
      <ChatPanel
        messages={messages}
        stats={stats}
        settings={settings}
        isProcessing={isProcessing}
        onSendMessage={handleSendMessage}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Settings Modal */}
      {isSettingsOpen && (
        <SettingsModal
          settings={settings}
          onClose={() => setIsSettingsOpen(false)}
          onSave={(newSettings) => {
            setSettings(newSettings);
            fetchDocuments();
          }}
        />
      )}
    </main>
  );
}
