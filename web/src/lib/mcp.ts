// Client-side MCP tool caller.
// Calls /api/tool (Next.js server route) which proxies to the MCP server.
// The MCP server URL and protocol details stay on the server side.

export async function callTool(
  name: string,
  args: Record<string, unknown> = {}
): Promise<Record<string, unknown>> {
  const res = await fetch("/api/tool", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool: name, args }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Tool proxy error ${res.status}: ${text}`);
  }

  const sdkResult = await res.json();

  if (sdkResult.error) throw new Error(sdkResult.error);
  if (sdkResult.isError) {
    const errText = sdkResult.content?.[0]?.text ?? "Tool returned an error";
    throw new Error(errText);
  }

  // FastMCP returns content as a list of content blocks.
  // For JSON-returning tools the first block is type="text" with JSON.
  const textBlock = (sdkResult.content ?? []).find(
    (b: { type: string }) => b.type === "text"
  ) as { text?: string } | undefined;

  if (!textBlock?.text) return {};

  try {
    return JSON.parse(textBlock.text) as Record<string, unknown>;
  } catch {
    return { text: textBlock.text };
  }
}

// Convenience: upload a PDF to the ingest endpoint
export async function ingestPDF(file: File): Promise<Record<string, unknown>> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch("/api/ingest", { method: "POST", body: form });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Ingest error ${res.status}: ${text}`);
  }
  return res.json();
}
