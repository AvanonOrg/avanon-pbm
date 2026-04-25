import type { ChatMessage } from "./types";

const SESSION_ID_KEY = "avanon_session_id";
const SESSIONS_KEY = "avanon_sessions";

export interface SessionMeta {
  sessionId: string;
  title: string;
  timestamp: string;
}

export function getSessionId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(SESSION_ID_KEY);
}

export function setSessionId(id: string): void {
  localStorage.setItem(SESSION_ID_KEY, id);
}

export function getSessions(): SessionMeta[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(SESSIONS_KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function upsertSessionMeta(sessionId: string, title: string): void {
  const sessions = getSessions();
  const idx = sessions.findIndex((s) => s.sessionId === sessionId);
  const meta: SessionMeta = { sessionId, title, timestamp: new Date().toISOString() };
  if (idx >= 0) {
    sessions[idx] = meta;
  } else {
    sessions.unshift(meta);
  }
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions.slice(0, 50)));
}

export function getStoredMessages(sessionId: string): ChatMessage[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(`avanon_msgs_${sessionId}`);
    if (!raw) return [];
    const msgs = JSON.parse(raw) as ChatMessage[];
    return msgs.map((m) => ({ ...m, isStreaming: false, currentThinkingStep: undefined }));
  } catch {
    return [];
  }
}

export function storeMessages(sessionId: string, messages: ChatMessage[]): void {
  if (!sessionId) return;
  const completed = messages.filter((m) => !m.isStreaming);
  try {
    localStorage.setItem(`avanon_msgs_${sessionId}`, JSON.stringify(completed));
  } catch {
    // Storage quota exceeded — ignore
  }
}

export function clearAllHistory(): void {
  Object.keys(localStorage)
    .filter((k) => k.startsWith("avanon"))
    .forEach((k) => localStorage.removeItem(k));
}
