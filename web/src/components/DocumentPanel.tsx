"use client";

import { Document, Settings } from "@/types";
import { ingestPDF } from "@/lib/mcp";
import { useCallback, useRef, useState } from "react";
import {
  Upload, FileText, Settings as SettingsIcon, Loader2,
  CheckCircle2, FileSearch, ChevronRight
} from "lucide-react";

interface Props {
  documents: Document[];
  settings: Settings;
  onOpenSettings: () => void;
  onRefreshDocs: () => void;
}

export default function DocumentPanel({
  documents,
  settings,
  onOpenSettings,
  onRefreshDocs,
}: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [statusType, setStatusType] = useState<"ok" | "err">("ok");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setStatusType("err");
        setUploadStatus("Only PDF files are supported.");
        return;
      }
      setUploading(true);
      setUploadStatus(null);
      try {
        const result = await ingestPDF(file);
        const cached = result.cached as boolean;
        setStatusType("ok");
        setUploadStatus(cached ? `${file.name} — already indexed` : `${file.name} — indexed successfully`);
        onRefreshDocs();
      } catch (err) {
        setStatusType("err");
        setUploadStatus(`Upload failed: ${String(err)}`);
      } finally {
        setUploading(false);
      }
    },
    [onRefreshDocs]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      className="flex flex-col h-full"
      style={{
        width: "var(--sidebar-width)",
        minWidth: "var(--sidebar-width)",
        borderRight: "1px solid var(--border)",
        background: "var(--bg-surface)",
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-4"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, var(--accent-1), var(--accent-2))", boxShadow: "0 0 10px var(--accent-glow)" }}
          >
            <FileSearch size={14} color="#fff" />
          </div>
          <div>
            <span className="text-sm font-bold gradient-text">Clause Lens</span>
            <p className="text-xs" style={{ color: "var(--text-muted)", lineHeight: 1.2 }}>Contract Intelligence</p>
          </div>
        </div>
        <button
          onClick={onOpenSettings}
          className="btn-ghost p-1.5"
          style={{ padding: "6px" }}
          title="Settings"
        >
          <SettingsIcon size={15} />
        </button>
      </div>

      {/* Upload zone */}
      <div className="p-3">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => !uploading && inputRef.current?.click()}
          className="rounded-xl flex flex-col items-center justify-center py-6 gap-2 cursor-pointer transition-all duration-200"
          style={{
            border: `2px dashed ${dragging ? "var(--accent-1)" : "var(--border)"}`,
            background: dragging ? "var(--accent-glow)" : "var(--bg-glass)",
            boxShadow: dragging ? "0 0 20px var(--accent-glow)" : "none",
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); e.target.value = ""; }}
          />
          {uploading ? (
            <Loader2 size={20} className="animate-spin" style={{ color: "var(--accent-1)" }} />
          ) : (
            <Upload size={20} style={{ color: dragging ? "var(--accent-1)" : "var(--text-muted)" }} />
          )}
          <span className="text-xs font-medium" style={{ color: uploading ? "var(--accent-1)" : "var(--text-secondary)" }}>
            {uploading ? "Indexing…" : "Drop PDF or click to upload"}
          </span>
          {!uploading && (
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>PDF contracts only</span>
          )}
        </div>

        {uploadStatus && (
          <div
            className="mt-2 rounded-lg px-3 py-2 flex items-center gap-2 text-xs fade-in"
            style={{
              background: statusType === "ok" ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)",
              border: `1px solid ${statusType === "ok" ? "rgba(34,197,94,0.25)" : "rgba(239,68,68,0.25)"}`,
              color: statusType === "ok" ? "#86efac" : "#fca5a5",
            }}
          >
            {statusType === "ok" ? <CheckCircle2 size={12} /> : null}
            <span className="truncate">{uploadStatus}</span>
          </div>
        )}
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto px-3 pb-3">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Documents ({documents.length})
          </span>
          {documents.length > 0 && (
            <button onClick={onRefreshDocs} className="text-xs" style={{ color: "var(--text-muted)" }}>
              refresh
            </button>
          )}
        </div>

        {documents.length === 0 ? (
          <div className="rounded-xl p-4 text-center" style={{ background: "var(--bg-glass)", border: "1px solid var(--border)" }}>
            <FileText size={28} className="mx-auto mb-2" style={{ color: "var(--text-muted)" }} />
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Upload a contract PDF to begin</p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {documents.map((doc) => (
              <div
                key={doc.doc_id}
                className="glass glass-hover rounded-xl px-3 py-3 transition-all duration-150"
              >
                <div className="flex items-start gap-2">
                  <FileText size={14} className="flex-shrink-0 mt-0.5" style={{ color: "var(--accent-1)" }} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate" style={{ color: "var(--text-primary)" }}>
                      {doc.filename}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className="text-xs rounded-full px-2 py-0.5"
                        style={{ background: "var(--accent-glow)", color: "var(--accent-1)", fontSize: "10px" }}
                      >
                        {doc.page_count}p
                      </span>
                      <span
                        className="text-xs rounded-full px-2 py-0.5"
                        style={{ background: "rgba(139,92,246,0.12)", color: "#c4b5fd", fontSize: "10px" }}
                      >
                        {doc.clause_count} clauses
                      </span>
                    </div>
                  </div>
                  <ChevronRight size={12} style={{ color: "var(--text-muted)", flexShrink: 0, marginTop: "2px" }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer: model indicator */}
      <div
        className="px-4 py-3 flex items-center gap-2"
        style={{ borderTop: "1px solid var(--border)" }}
      >
        <div className="w-1.5 h-1.5 rounded-full" style={{ background: settings.apiKey ? "var(--success)" : "var(--error)" }} />
        <span className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
          {settings.apiKey ? `${settings.provider} · ${settings.model}` : "No API key — open Settings"}
        </span>
      </div>
    </div>
  );
}
