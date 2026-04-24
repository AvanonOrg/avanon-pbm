import type { StreamEvent } from "./types";

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
  }
): Promise<void> {
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, session_id: sessionId }),
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
