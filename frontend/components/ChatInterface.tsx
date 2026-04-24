"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import type { ChatMessage, ThinkingStep } from "@/lib/types";
import { getToken, clearToken } from "@/lib/auth";
import { streamMessage } from "@/lib/api";
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
  const sessionId = useRef<string>("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Generate session ID client-side only
    sessionId.current = crypto.randomUUID();

    // Auth guard
    if (!getToken()) {
      router.replace("/");
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const submit = useCallback(
    async (text: string) => {
      const token = getToken();
      if (!token || loading) return;

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
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: m.content + delta } : m
              )
            );
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
        });
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
    setMessages([]);
    sessionId.current = crypto.randomUUID();
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

        {/* Messages area */}
        <div className="flex-1 w-full overflow-y-auto no-scrollbar">
          <div className="max-w-3xl mx-auto px-4 py-6">
            {messages.length === 0 && (
              <div className="text-center mt-16 mb-8">
                <h2 className="text-2xl font-semibold text-[#ececec] mb-2">
                  PBM Spread Analysis
                </h2>
                <p className="text-sm text-[#8e8ea0]">
                  Ask me to analyze drug pricing, calculate spreads, or set up monitoring.
                </p>
              </div>
            )}

            {messages.map((m) => (
              <MessageRow key={m.id} message={m} />
            ))}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Quick prompts */}
        {messages.length === 0 && (
          <div className="w-full max-w-3xl px-4 pb-3 flex flex-wrap gap-2 justify-center">
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
        )}

        {/* Input bar */}
        <InputBar onSubmit={submit} disabled={loading} />

        {/* Footer */}
        <p className="text-xs text-[#6b6b6b] pb-3 px-4 text-center">
          Avanon can make mistakes. Verify drug pricing with official sources before making formulary decisions.
        </p>
      </main>
    </div>
  );
}
