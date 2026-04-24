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
  const [gone, setGone] = useState(false);

  // Fade out 1.2s after streaming stops, then fully remove
  useEffect(() => {
    if (!isActive) {
      const fadeTimer = setTimeout(() => setGone(true), 1600);
      return () => clearTimeout(fadeTimer);
    }
  }, [isActive]);

  if (gone) return null;

  const displayStep =
    currentStep ?? (steps.length > 0 ? steps[steps.length - 1].step : "Thinking…");

  return (
    <div
      className={!isActive ? "thinking-bubble-done" : ""}
      style={{ marginBottom: 8 }}
    >
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
        {!isActive && (
          <span style={{ fontSize: 12 }}>✓</span>
        )}
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {isActive ? displayStep : `${steps.length} step${steps.length !== 1 ? "s" : ""} completed`}
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

  // Show thinking bubble whenever there are steps OR still streaming
  // Keep rendering until ThinkingBubble self-removes after fade
  const showThinking = message.isStreaming || (message.thinkingSteps?.length ?? 0) > 0;

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

// ── Sidebar ────────────────────────────────────────────────────────────────

function Sidebar({
  open,
  onToggle,
  onNewChat,
}: {
  open: boolean;
  onToggle: () => void;
  onNewChat: () => void;
}) {
  return (
    <aside
      style={{
        width: open ? 240 : 56,
        background: "#171717",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
        borderRight: "1px solid #2a2a2a",
        transition: "width 0.22s ease",
        overflow: "hidden",
      }}
    >
      {/* Top controls */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "10px 10px",
          gap: 8,
          flexShrink: 0,
        }}
      >
        {/* Toggle button */}
        <SidebarBtn title={open ? "Close sidebar" : "Open sidebar"} onClick={onToggle}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </SidebarBtn>
        {open && (
          <span
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: "#ececec",
              whiteSpace: "nowrap",
              opacity: open ? 1 : 0,
              transition: "opacity 0.15s ease 0.08s",
            }}
          >
            PBM Intelligence
          </span>
        )}
      </div>

      {/* New chat */}
      <div style={{ padding: "0 8px 8px" }}>
        <button
          onClick={onNewChat}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            gap: 10,
            background: "none",
            border: "1px solid #2f2f2f",
            borderRadius: 8,
            padding: open ? "8px 10px" : "8px",
            cursor: "pointer",
            color: "#8e8ea0",
            fontSize: 13,
            textAlign: "left",
            justifyContent: open ? "flex-start" : "center",
            transition: "background 0.15s",
            whiteSpace: "nowrap",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#2a2a2a")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
          title="New chat"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <path d="M12 5v14M5 12h14" />
          </svg>
          {open && <span>New chat</span>}
        </button>
      </div>

      {/* Section label */}
      {open && (
        <div style={{ padding: "8px 14px 4px", fontSize: 11, color: "#4a4a4a", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>
          Recent
        </div>
      )}

      {/* Placeholder recent chats */}
      {open && (
        <div style={{ flex: 1, overflowY: "auto", padding: "4px 8px" }}>
          {["Eliquis spread analysis", "Ozempic PBM pricing", "Humira monitoring setup"].map((label) => (
            <button
              key={label}
              style={{
                width: "100%",
                display: "block",
                background: "none",
                border: "none",
                borderRadius: 6,
                padding: "7px 8px",
                cursor: "pointer",
                color: "#8e8ea0",
                fontSize: 13,
                textAlign: "left",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                transition: "background 0.12s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#2a2a2a")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Logo / brand at bottom */}
      <div
        style={{
          padding: open ? "12px 14px" : "12px 10px",
          borderTop: "1px solid #2a2a2a",
          display: "flex",
          alignItems: "center",
          gap: 8,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 6,
            background: "#2a2a2a",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 14,
            flexShrink: 0,
          }}
        >
          💊
        </div>
        {open && (
          <div style={{ overflow: "hidden" }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "#ececec", whiteSpace: "nowrap" }}>Avanon</div>
            <div style={{ fontSize: 11, color: "#4a4a4a", whiteSpace: "nowrap" }}>Pass-Through Intelligence</div>
          </div>
        )}
      </div>
    </aside>
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
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        transition: "background 0.15s, color 0.15s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "#2a2a2a";
        e.currentTarget.style.color = "#ececec";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "none";
        e.currentTarget.style.color = "#6b6b6b";
      }}
    >
      {children}
    </button>
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sessionId = useRef(getOrCreateSession());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewChat = useCallback(() => {
    localStorage.removeItem(SESSION_KEY);
    sessionId.current = getOrCreateSession();
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content:
          "Hello! I'm your PBM Pass-Through Intelligence agent. Ask me to research drug pricing, identify spread pricing discrepancies, or set up monitoring for specific medications.\n\nTry: *\"What's the spread on Eliquis 5mg 60 tablets?\"*",
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

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
          (delta) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id !== assistantId ? m : { ...m, content: m.content + delta }
              )
            );
          },
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
    <div style={{ display: "flex", height: "100vh", background: "#212121", overflow: "hidden" }}>
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen((v) => !v)}
        onNewChat={handleNewChat}
      />

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

        {/* Quick prompts — disabled while loading */}
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
                disabled={loading}
                style={{
                  padding: "6px 12px",
                  border: "1px solid #3a3a3a",
                  borderRadius: 999,
                  background: "#2a2a2a",
                  fontSize: 12,
                  color: loading ? "#4a4a4a" : "#8e8ea0",
                  cursor: loading ? "not-allowed" : "pointer",
                  transition: "color 0.15s",
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
