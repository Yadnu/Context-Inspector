// Next.js API route: POST /api/ingest
// Forwards a PDF file upload to the MCP server's /ingest endpoint.

import { NextRequest, NextResponse } from "next/server";

const MCP_SERVER_URL =
  process.env.MCP_SERVER_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  try {
    const form = await req.formData();
    const file = form.get("file");
    if (!file || !(file instanceof Blob)) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Forward to MCP server's custom ingest route
    const upstream = new FormData();
    const filename =
      file instanceof File ? file.name : "upload.pdf";
    upstream.append("file", file, filename);

    const res = await fetch(`${MCP_SERVER_URL}/ingest`, {
      method: "POST",
      body: upstream,
    });

    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error("[api/ingest] error:", err);
    return NextResponse.json({ error: String(err) }, { status: 502 });
  }
}
