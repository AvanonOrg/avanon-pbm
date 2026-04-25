import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const auth = request.headers.get("authorization") ?? "";

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: auth },
      body,
    });
  } catch (err) {
    return new Response(
      `data: ${JSON.stringify({ type: "error", message: String(err) })}\n\ndata: [DONE]\n\n`,
      { status: 502, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  if (!upstream.ok || !upstream.body) {
    return new Response(
      `data: ${JSON.stringify({ type: "error", message: `Backend ${upstream.status}` })}\n\ndata: [DONE]\n\n`,
      { status: upstream.status, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  // Pipe upstream ReadableStream directly — zero buffering
  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
      Connection: "keep-alive",
    },
  });
}
