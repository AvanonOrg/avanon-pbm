import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "../lib/types";
import { sendMessage } from "../lib/api";
import { ReportCard } from "./ReportCard";
import { TaskStatusBadge } from "./TaskStatusBadge";

const SESSION_KEY = "pbm_session_id";

function getOrCreateSession(): string {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

const QUICK_PROMPTS = [
  "What's the spread on Ozempic 0.5mg?",
  "Compare Eliquis 5mg prices across PBMs",
  "Show me the top 5 specialty drugs with highest spread",
  "Monitor Humira pricing weekly",
  "Research pass-through PBMs that partner with Cost Plus Drugs",
];

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hello! I'm your PBM Pass-Through Intelligence agent. Ask me to research drug pricing, identify spread pricing discrepancies, or set up monitoring for specific medications.\n\nTry: *\"What's the spread on Eliquis 5mg 60 tablets?\"*",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useRef(getOrCreateSession());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const submit = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);

      // Thinking placeholder
      const thinkingId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        {
          id: thinkingId,
          role: "assistant",
          content: "",
          timestamp: new Date().toISOString(),
          task_status: "running",
        },
      ]);

      try {
        const res = await sendMessage(text, sessionId.current);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === thinkingId
              ? {
                  ...m,
                  content: res.reply,
                  report: res.report,
                  task_id: res.task_id,
                  task_status: res.task_status,
                }
              : m
          )
        );
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === thinkingId
              ? { ...m, content: "Error: Could not reach the agent. Is the backend running?" }
              : m
          )
        );
      } finally {
        setLoading(false);
      }
    },
    [loading]
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", maxWidth: 900, margin: "0 auto", fontFamily: "Inter, system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ padding: "16px 20px", borderBottom: "1px solid #e2e8f0", background: "#fff" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: "#0f172a", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 16 }}>
            💊
          </div>
          <div>
            <div style={{ fontWeight: 700, color: "#0f172a", fontSize: 15 }}>PBM Intelligence Agent</div>
            <div style={{ fontSize: 12, color: "#64748b" }}>Powered by Avanon · Pass-Through Pricing Analysis</div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="no-scrollbar" style={{ flex: 1, overflowY: "auto", padding: "20px", display: "flex", flexDirection: "column", gap: 16 }}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Quick prompts */}
      {messages.length <= 1 && (
        <div style={{ padding: "0 20px 12px", display: "flex", flexWrap: "wrap", gap: 8 }}>
          {QUICK_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => submit(p)}
              style={{
                padding: "6px 12px",
                border: "1px solid #e2e8f0",
                borderRadius: 999,
                background: "#fff",
                fontSize: 12,
                color: "#475569",
                cursor: "pointer",
              }}
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{ padding: "12px 20px", borderTop: "1px solid #e2e8f0", background: "#fff" }}>
        <form
          onSubmit={(e) => { e.preventDefault(); submit(input); }}
          style={{ display: "flex", gap: 10 }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about drug pricing, PBM spreads, or set up monitoring..."
            disabled={loading}
            style={{
              flex: 1,
              padding: "10px 14px",
              border: "1px solid #e2e8f0",
              borderRadius: 8,
              fontSize: 14,
              outline: "none",
              background: loading ? "#f8fafc" : "#fff",
            }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            style={{
              padding: "10px 20px",
              background: loading || !input.trim() ? "#94a3b8" : "#0f172a",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: loading || !input.trim() ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Researching..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isThinking = message.role === "assistant" && !message.content && message.task_status === "running";

  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <div
        style={{
          maxWidth: isUser ? "70%" : "100%",
          background: isUser ? "#0f172a" : "#fff",
          color: isUser ? "#fff" : "#1e293b",
          border: isUser ? "none" : "1px solid #e2e8f0",
          borderRadius: isUser ? "16px 16px 4px 16px" : "4px 16px 16px 16px",
          padding: "12px 16px",
          fontSize: 14,
          lineHeight: 1.6,
        }}
      >
        {isThinking ? (
          <span style={{ color: "#94a3b8", fontStyle: "italic" }}>Researching pricing data...</span>
        ) : (
          <>
            {message.content && (
              <ReactMarkdown>{message.content}</ReactMarkdown>
            )}
            {message.task_status && message.task_status !== "complete" && (
              <TaskStatusBadge status={message.task_status} />
            )}
            {message.report && <ReportCard report={message.report} />}
          </>
        )}
      </div>
    </div>
  );
}
