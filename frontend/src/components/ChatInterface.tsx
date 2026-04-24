import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import type { ChatMessage, ThinkingStep, DiscrepancyReport } from "../lib/types";
import { streamMessage } from "../lib/api";
import { ReportCard } from "./ReportCard";

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
  "Show me top specialty drugs with highest spread",
  "Monitor Humira pricing weekly",
  "Research pass-through PBMs near Cost Plus Drugs",
];

// ── ThinkingBubble ─────────────────────────────────────────────────────────

function ThinkingBubble({
  steps,
  currentStep,
  isActive,
}: {
  steps: ThinkingStep[];
  currentStep?: string;
  isActive: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    if (!isActive && steps.length > 0) {
      const t = setTimeout(() => setFading(true), 800);
      return () => clearTimeout(t);
    }
  }, [isActive, steps.length]);

  if (fading && !isActive) return null;

  const displayStep =
    currentStep ?? (steps.length > 0 ? steps[steps.length - 1].step : "Thinking…");

  return (
    <div className={fading ? "thinking-bubble-done" : ""} style={{ marginBottom: 6 }}>
      <button
        onClick={() => steps.length > 0 && setExpanded((v) => !v)}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          background: "#2a2a2a",
          border: "1px solid #3a3a3a",
          borderRadius: 20,
          padding: "6px 14px",
          cursor: steps.length > 0 ? "pointer" : "default",
          color: "#8e8ea0",
          fontSize: 13,
          textAlign: "left",
          maxWidth: "100%",
        }}
      >
        {isActive && (
          <span style={{ display: "inline-flex", gap: 3, alignItems: "center", flexShrink: 0 }}>
            <span className="thinking-dot" style={{ width: 5, height: 5, borderRadius: "50%", background: "#8e8ea0", display: "inline-block" }} />
            <span className="thinking-dot" style={{ width: 5, height: 5, borderRadius: "50%", background: "#8e8ea0", display: "inline-block" }} />
            <span className="thinking-dot" style={{ width: 5, height: 5, borderRadius: "50%", background: "#8e8ea0", display: "inline-block" }} />
          </span>
        )}
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {displayStep}
        </span>
        {steps.length > 0 && (
          <span style={{ fontSize: 10, opacity: 0.5, flexShrink: 0 }}>
            {expanded ? "▲" : "▼"}
          </span>
        )}
      </button>

      {expanded && steps.length > 0 && (
        <div
          className="thinking-steps-panel"
          style={{
            marginTop: 6,
            background: "#1a1a1a",
            border: "1px solid #2f2f2f",
            borderRadius: 10,
            padding: "12px 14px",
            display: "flex",
            flexDirection: "column",
            gap: 10,
            maxWidth: 420,
          }}
        >
          <div style={{ fontSize: 11, color: "#6b6b6b", marginBottom: 2, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Agent Roadmap
          </div>
          {steps.map((s, i) => (
            <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
              <div
                style={{
                  width: 20,
                  height: 20,
                  borderRadius: "50%",
                  background: "#2f2f2f",
                  border: "1px solid #3f3f3f",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  marginTop: 1,
                }}
              >
                <span style={{ fontSize: 9, color: "#8e8ea0", fontWeight: 700 }}>{i + 1}</span>
              </div>
              <div>
                <div style={{ fontSize: 13, color: "#ececec", lineHeight: 1.4 }}>{s.step}</div>
                <div style={{ fontSize: 11, color: "#6b6b6b", marginTop: 1 }}>{s.tool}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── InputBar ───────────────────────────────────────────────────────────────

function InputBar({
  input,
  setInput,
  loading,
  onSubmit,
}: {
  input: string;
  setInput: (v: string) => void;
  loading: boolean;
  onSubmit: (text: string) => void;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(input);
    }
  };

  const canSend = !loading && input.trim().length > 0;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        gap: 8,
        background: "#2f2f2f",
        borderRadius: 16,
        padding: "10px 10px 10px 16px",
        border: "1px solid #3a3a3a",
      }}
    >
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about drug pricing, PBM spreads, or set up monitoring…"
        disabled={loading}
        rows={1}
        style={{
          flex: 1,
          background: "transparent",
          border: "none",
          outline: "none",
          color: "#ececec",
          fontSize: 15,
          lineHeight: 1.55,
          resize: "none",
          fontFamily: "inherit",
          maxHeight: 180,
          overflowY: "auto",
          padding: "2px 0",
        }}
      />
      <button
        onClick={() => onSubmit(input)}
        disabled={!canSend}
        style={{
          width: 34,
          height: 34,
          borderRadius: "50%",
          flexShrink: 0,
          background: canSend ? "#ececec" : "#3a3a3a",
          border: "none",
          cursor: canSend ? "pointer" : "not-allowed",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#212121",
          fontSize: 17,
          fontWeight: 700,
          transition: "background 0.15s",
          lineHeight: 1,
        }}
      >
        ↑
      </button>
    </div>
  );
}

// ── MessageRow ─────────────────────────────────────────────────────────────

function MessageRow({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div
        className="msg-enter"
        style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20 }}
      >
        <div
          style={{
            maxWidth: "72%",
            background: "#2f2f2f",
            color: "#ececec",
            borderRadius: "18px 18px 4px 18px",
            padding: "10px 16px",
            fontSize: 15,
            lineHeight: 1.6,
            wordBreak: "break-word",
          }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  const showThinking =
    message.isStreaming ||
    ((message.thinkingSteps?.length ?? 0) > 0 && !message.content);

  return (
    <div className="msg-enter" style={{ marginBottom: 24 }}>
      {showThinking && (
        <ThinkingBubble
          steps={message.thinkingSteps ?? []}
          currentStep={message.currentThinkingStep}
          isActive={message.isStreaming ?? false}
        />
      )}

      {message.content && (
        <div
          className={`prose-dark${message.isStreaming ? " streaming-cursor" : ""}`}
          style={{ fontSize: 15, lineHeight: 1.7 }}
        >
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      )}

      {!message.isStreaming && message.report && (
        <ReportCard report={message.report} />
      )}
    </div>
  );
}

// ── ChatInterface ──────────────────────────────────────────────────────────

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

      const assistantId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          timestamp: new Date().toISOString(),
          isStreaming: true,
          thinkingSteps: [],
          currentThinkingStep: undefined,
        },
      ]);

      try {
        await streamMessage(
          text,
          sessionId.current,
          // onThinking
          (step, tool) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id !== assistantId
                  ? m
                  : {
                      ...m,
                      currentThinkingStep: step,
                      thinkingSteps: [
                        ...(m.thinkingSteps ?? []),
                        { tool, step, timestamp: new Date().toISOString() },
                      ],
                    }
              )
            );
          },
          // onDelta
          (delta) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id !== assistantId ? m : { ...m, content: m.content + delta }
              )
            );
          },
          // onDone
          (event) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id !== assistantId
                  ? m
                  : {
                      ...m,
                      content: event.reply,
                      isStreaming: false,
                      report: event.report,
                      task_id: event.task_id,
                      task_status: event.task_status,
                      currentThinkingStep: undefined,
                    }
              )
            );
          },
          // onError
          (err) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id !== assistantId
                  ? m
                  : { ...m, content: `Error: ${err}`, isStreaming: false }
              )
            );
          }
        );
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id !== assistantId
              ? m
              : {
                  ...m,
                  content: "Error: Could not reach the agent. Is the backend running?",
                  isStreaming: false,
                }
          )
        );
      } finally {
        setLoading(false);
      }
    },
    [loading]
  );

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        background: "#212121",
        overflow: "hidden",
      }}
    >
      {/* Sidebar */}
      <aside
        style={{
          width: 56,
          background: "#171717",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: "12px 0",
          gap: 4,
          flexShrink: 0,
          borderRight: "1px solid #2a2a2a",
        }}
      >
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: 8,
            background: "#2a2a2a",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 16,
            marginBottom: 8,
          }}
        >
          💊
        </div>
        <SidebarBtn title="New chat" onClick={() => {
          localStorage.removeItem(SESSION_KEY);
          sessionId.current = getOrCreateSession();
          setMessages([{
            id: "welcome",
            role: "assistant",
            content: "Hello! I'm your PBM Pass-Through Intelligence agent. Ask me to research drug pricing, identify spread pricing discrepancies, or set up monitoring for specific medications.\n\nTry: *\"What's the spread on Eliquis 5mg 60 tablets?\"*",
            timestamp: new Date().toISOString(),
          }]);
        }}>
          ✏️
        </SidebarBtn>
      </aside>

      {/* Main */}
      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          overflow: "hidden",
          minWidth: 0,
        }}
      >
        {/* Top bar */}
        <div
          style={{
            width: "100%",
            maxWidth: 768,
            padding: "12px 20px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: 13, color: "#6b6b6b" }}>
            PBM Intelligence · claude-opus-4-6
          </span>
        </div>

        {/* Messages */}
        <div
          className="no-scrollbar"
          style={{
            flex: 1,
            width: "100%",
            maxWidth: 768,
            overflowY: "auto",
            padding: "8px 20px 0",
          }}
        >
          {messages.map((msg) => (
            <MessageRow key={msg.id} message={msg} />
          ))}
          <div ref={bottomRef} style={{ height: 16 }} />
        </div>

        {/* Quick prompts */}
        {messages.length <= 1 && (
          <div
            style={{
              width: "100%",
              maxWidth: 768,
              padding: "0 20px 12px",
              display: "flex",
              flexWrap: "wrap",
              gap: 8,
            }}
          >
            {QUICK_PROMPTS.map((p) => (
              <button
                key={p}
                onClick={() => submit(p)}
                style={{
                  padding: "6px 12px",
                  border: "1px solid #3a3a3a",
                  borderRadius: 999,
                  background: "#2a2a2a",
                  fontSize: 12,
                  color: "#8e8ea0",
                  cursor: "pointer",
                  transition: "border-color 0.15s",
                }}
              >
                {p}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div style={{ width: "100%", maxWidth: 768, padding: "8px 20px 6px" }}>
          <InputBar
            input={input}
            setInput={setInput}
            loading={loading}
            onSubmit={submit}
          />
          <p
            style={{
              textAlign: "center",
              fontSize: 11,
              color: "#4a4a4a",
              marginTop: 6,
              paddingBottom: 8,
            }}
          >
            PBM Intelligence can make mistakes. Verify critical pricing data.
          </p>
        </div>
      </main>
    </div>
  );
}

function SidebarBtn({
  title,
  onClick,
  children,
}: {
  title: string;
  onClick?: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      title={title}
      onClick={onClick}
      style={{
        width: 36,
        height: 36,
        borderRadius: 8,
        background: "none",
        border: "none",
        cursor: "pointer",
        color: "#6b6b6b",
        fontSize: 16,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "#2a2a2a")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
    >
      {children}
    </button>
  );
}
