import type { ChatResponse } from "./types";

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

export async function getTasks(): Promise<unknown[]> {
  return apiFetch<unknown[]>("/api/tasks");
}

export async function getTaskStatus(taskId: string): Promise<unknown> {
  return apiFetch<unknown>(`/api/tasks/${taskId}`);
}
