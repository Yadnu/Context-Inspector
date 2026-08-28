// Next.js API route: POST /api/tool
// Proxies a single MCP tool call to the FastMCP server.
// Runs server-side only — the MCP server URL stays in env vars.

import { NextRequest, NextResponse } from "next/server";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const MCP_SERVER_URL =
  process.env.MCP_SERVER_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  let body: { tool?: string; args?: Record<string, unknown> };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { tool, args = {} } = body;
  if (!tool) {
    return NextResponse.json({ error: "Missing `tool` field" }, { status: 400 });
  }

  const client = new Client(
    { name: "clause-lens-web", version: "0.1.0" },
    { capabilities: {} }
  );

  const transport = new StreamableHTTPClientTransport(
    new URL(`${MCP_SERVER_URL}/mcp/`)
  );

  try {
    await client.connect(transport);
    const result = await client.callTool({ name: tool, arguments: args });
    return NextResponse.json(result);
  } catch (err) {
    console.error("[api/tool] error:", err);
    return NextResponse.json(
      { error: String(err) },
      { status: 502 }
    );
  } finally {
    await client.close().catch(() => {});
  }
}
