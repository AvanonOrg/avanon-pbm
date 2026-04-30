import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  const auth = request.headers.get("authorization") ?? "";
  const url = new URL(request.url);
  const path = url.searchParams.get("path") ?? "list";
  const qs = new URLSearchParams();
  ["pbm", "state", "plan_type", "min_employees", "limit"].forEach((k) => {
    const v = url.searchParams.get(k);
    if (v) qs.set(k, v);
  });
  const target = `${BACKEND}/api/prospects/${path}${qs.toString() ? `?${qs}` : ""}`;
  try {
    const upstream = await fetch(target, {
      method: "GET",
      headers: { Authorization: auth },
      cache: "no-store",
    });
    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: String(err) }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }
}
