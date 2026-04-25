"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { flushSync } from "react-dom";
import { useRouter } from "next/navigation";
import type { ChatMessage, ThinkingStep } from "@/lib/types";
import { getToken, clearToken } from "@/lib/auth";
import { streamMessage } from "@/lib/api";
import {
  getSessionId,
  setSessionId,
  getSessions,
  upsertSessionMeta,
  getStoredMessages,
  storeMessages,
  clearAllHistory,
  type SessionMeta,
} from "@/lib/storage";
import Sidebar from "./Sidebar";
import MessageRow from "./MessageRow";
import InputBar from "./InputBar";

const QUICK_PROMPTS = [
  "Analyze spread on Eliquis 5mg for 30-day supply",
  "Compare NADAC vs GoodRx pricing for Lipitor",
  "What is pass-through pricing vs spread pricing?",
  "Set up weekly price monitoring for metformin",
];

export default function ChatInterface() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessions, setSessions] = useState<SessionMeta[]>([]);
  const sessionId = useRef<string>("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const metaSavedRef = useRef(false);

  // Init: restore session ID + messages from localStorage
  useEffect(() => {
    if (!getToken()) {
      router.replace("/");
      return;
    }

    let sid = getSessionId();
    if (!sid) {
      sid = crypto.randomUUID();
      setSessionId(sid);
    }
    sessionId.current = sid;
    metaSavedRef.current = false;

    const stored = getStoredMessages(sid);
    if (stored.length > 0) {
      setMessages(stored);
      metaSavedRef.current = true;
    }

    setSessions(getSessions());
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Persist completed messages to localStorage after each update
  useEffect(() => {
    if (!sessionId.current || messages.length === 0) return;
    const hasStreaming = messages.some((m) => m.isStreaming);
    if (!hasStreaming) {
      storeMessages(sessionId.current, messages);
    }
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const submit = useCallback(
    async (text: string) => {
      const token = getToken();
      if (!token || loading) return;

      // Save session meta on first message of a conversation
      if (!metaSavedRef.current) {
        upsertSessionMeta(sessionId.current, text.slice(0, 60));
        metaSavedRef.current = true;
        setSessions(getSessions());
      }

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
      };

      const assistantId = crypto.randomUUID();
      const assistantPlaceholder: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
        thinkingSteps: [],
      };

      setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);
      setLoading(true);

      function updateAssistant(update: Partial<ChatMessage>) {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, ...update } : m))
        );
      }

      // Build history from completed messages (exclude streaming placeholders)
      const history = messages
        .filter((m) => !m.isStreaming && m.content.length > 0)
        .map((m) => ({ role: m.role, content: m.content }));

      try {
        await streamMessage(text, sessionId.current, token, {
          onThinking(step, tool) {
            const ts: ThinkingStep = { step, tool, timestamp: new Date().toISOString() };
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, thinkingSteps: [...(m.thinkingSteps ?? []), ts], currentThinkingStep: step }
                  : m
              )
            );
          },
          onDelta(delta) {
            flushSync(() => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: m.content + delta } : m
                )
              );
            });
          },
          onDone(event) {
            updateAssistant({
              isStreaming: false,
              currentThinkingStep: undefined,
              report: event.report,
              taskId: event.task_id,
            });
          },
          onError(msg) {
            updateAssistant({
              isStreaming: false,
              content: `Error: ${msg}`,
              currentThinkingStep: undefined,
            });
          },
        }, history);
      } catch {
        updateAssistant({
          isStreaming: false,
          content: "An unexpected error occurred. Please try again.",
        });
      } finally {
        setLoading(false);
      }
    },
    [loading]
  );

  function handleNewChat() {
    // Save current session before clearing
    if (messages.length > 0) {
      storeMessages(sessionId.current, messages);
      const firstUser = messages.find((m) => m.role === "user");
      if (firstUser) {
        upsertSessionMeta(sessionId.current, firstUser.content.slice(0, 60));
      }
    }

    const newId = crypto.randomUUID();
    setSessionId(newId);
    sessionId.current = newId;
    metaSavedRef.current = false;
    setMessages([]);
    setSessions(getSessions());
  }

  function handleSelectSession(sid: string) {
    if (sid === sessionId.current) return;

    // Persist current session
    if (messages.length > 0) {
      storeMessages(sessionId.current, messages);
    }

    setSessionId(sid);
    sessionId.current = sid;
    metaSavedRef.current = true;
    const stored = getStoredMessages(sid);
    setMessages(stored);
    setSessions(getSessions());
  }

  function handleClearHistory() {
    clearAllHistory();
    const newId = crypto.randomUUID();
    setSessionId(newId);
    sessionId.current = newId;
    metaSavedRef.current = false;
    setMessages([]);
    setSessions([]);
  }

  function handleLogout() {
    clearToken();
    router.push("/");
  }

  return (
    <div className="flex bg-[#212121] overflow-hidden" style={{ height: "100vh" }}>
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen((o) => !o)}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
        onClearHistory={handleClearHistory}
        sessions={sessions}
        currentSessionId={sessionId.current}
        onSelectSession={handleSelectSession}
      />

      <main className="flex flex-col flex-1 min-w-0 overflow-hidden" style={{ alignItems: "center" }}>
        {/* Top bar */}
        <div
          className="flex items-center justify-between w-full px-4 flex-shrink-0 border-b border-[#2f2f2f]"
          style={{ height: "56px" }}
        >
          <div className="flex-1" />
          <div className="text-center">
            <span className="text-sm font-medium text-[#ececec]">Avanon PBM</span>
            <span className="text-xs text-[#8e8ea0] ml-2">Intelligence</span>
          </div>
          <div className="flex-1 flex justify-end">
            <button
              onClick={handleLogout}
              className="text-xs text-[#6b6b6b] hover:text-[#8e8ea0] transition-colors px-2 py-1"
            >
              Sign out
            </button>
          </div>
        </div>

        {/* Empty state — vertically centred between top bar and input */}
        {messages.length === 0 && (
          <div className="flex-1 w-full flex flex-col items-center justify-center px-4 gap-6">
            <div className="text-center">
              <h2 className="text-2xl font-semibold text-[#ececec] mb-2">
                PBM Spread Analysis
              </h2>
              <p className="text-sm text-[#8e8ea0]">
                Ask me to analyze drug pricing, calculate spreads, or set up monitoring.
              </p>
            </div>
            <div className="w-full max-w-3xl flex flex-wrap gap-2 justify-center">
              {QUICK_PROMPTS.map((p) => (
                <button
                  key={p}
                  disabled={loading}
                  onClick={() => submit(p)}
                  className="text-xs bg-[#2f2f2f] border border-[#3f3f3f] text-[#8e8ea0] rounded-full px-3 py-1.5 hover:text-[#ececec] hover:border-[#6b6b6b] transition-colors disabled:opacity-50"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages area */}
        {messages.length > 0 && (
          <div className="flex-1 w-full overflow-y-auto no-scrollbar">
            <div className="max-w-3xl mx-auto px-4 py-6">
              {messages.map((m) => (
                <MessageRow key={m.id} message={m} />
              ))}
              <div ref={bottomRef} />
            </div>
          </div>
        )}

        <InputBar onSubmit={submit} disabled={loading} />

        <p className="text-xs text-[#6b6b6b] pb-3 px-4 text-center">
          Avanon can make mistakes. Verify drug pricing with official sources before making formulary decisions.
        </p>
      </main>
    </div>
  );
}
