import type { StreamEvent } from "./types";

export async function downloadReport(report: object, token: string): Promise<void> {
  const res = await fetch("/api/pdf", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(report),
  });
  if (!res.ok) throw new Error(`PDF generation failed: HTTP ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const reportId = (report as { report_id?: string }).report_id ?? "report";
  a.download = `pbm-report-${reportId}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function login(email: string, password: string): Promise<string> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Invalid credentials");
  }
  return (await res.json()).access_token;
}

export async function streamMessage(
  message: string,
  sessionId: string,
  token: string,
  callbacks: {
    onThinking: (step: string, tool: string) => void;
    onDelta: (delta: string) => void;
    onDone: (event: Extract<StreamEvent, { type: "done" }>) => void;
    onError: (msg: string) => void;
  },
  history: { role: string; content: string }[] = []
): Promise<void> {
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, session_id: sessionId, history }),
  });

  if (!res.ok || !res.body) {
    callbacks.onError(`HTTP ${res.status}`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (raw === "[DONE]") return;
      try {
        const event = JSON.parse(raw) as StreamEvent;
        if (event.type === "thinking") callbacks.onThinking(event.step, event.tool);
        else if (event.type === "text_delta") callbacks.onDelta(event.delta);
        else if (event.type === "done") callbacks.onDone(event);
        else if (event.type === "error") callbacks.onError(event.message);
      } catch {
        // malformed SSE line — skip
      }
    }
  }
}
