import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const BACKEND = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const auth = request.headers.get("authorization") ?? "";
    const sp = request.nextUrl.searchParams;
    const path = sp.get("path") ?? "list";
    const qs = new URLSearchParams();
    for (const k of ["pbm", "state", "plan_type", "min_employees", "limit"]) {
      const v = sp.get(k);
      if (v) qs.set(k, v);
    }
    const target = `${BACKEND}/api/prospects/${path}${qs.toString() ? `?${qs.toString()}` : ""}`;
    const upstream = await fetch(target, {
      method: "GET",
      headers: { Authorization: auth },
      cache: "no-store",
    });
    const body = await upstream.text();
    return new NextResponse(body, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      { error: String(err), backend: BACKEND ? "set" : "missing" },
      { status: 502 }
    );
  }
}
