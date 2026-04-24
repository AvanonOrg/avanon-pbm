import type { ChatResponse, StreamEvent, DiscrepancyReport } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export function getToken(): string | null {
  return localStorage.getItem("pbm_token");
}

export function setToken(token: string, tenantId: string) {
  localStorage.setItem("pbm_token", token);
  localStorage.setItem("pbm_tenant_id", tenantId);
}

export function getTenantId(): string | null {
  return localStorage.getItem("pbm_tenant_id");
}

export function clearAuth() {
  localStorage.removeItem("pbm_token");
  localStorage.removeItem("pbm_tenant_id");
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return response.json();
}

export async function login(email: string, password: string): Promise<void> {
  const data = await apiFetch<{ access_token: string; tenant_id: string }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token, data.tenant_id);
}

export async function sendMessage(
  message: string,
  sessionId: string
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId }),
  });
}

export async function streamMessage(
  message: string,
  sessionId: string,
  onThinking: (step: string, tool: string) => void,
  onDelta: (delta: string) => void,
  onDone: (event: { reply: string; report?: DiscrepancyReport; task_id?: string; task_status: string }) => void,
  onError: (err: string) => void,
): Promise<void> {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || "Stream request failed");
  }

  const reader = response.body!.getReader();
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
        if (event.type === "thinking") {
          onThinking(event.step, event.tool);
        } else if (event.type === "text_delta") {
          onDelta(event.delta);
        } else if (event.type === "done") {
          onDone(event);
        } else if (event.type === "error") {
          onError(event.message);
        }
      } catch {
        // malformed line — skip
      }
    }
  }
}

export async function getTasks(): Promise<unknown[]> {
  return apiFetch<unknown[]>("/api/tasks");
}

export async function getTaskStatus(taskId: string): Promise<unknown> {
  return apiFetch<unknown>(`/api/tasks/${taskId}`);
}
