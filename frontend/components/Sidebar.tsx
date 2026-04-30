"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createPortal } from "react-dom";
import type { SessionMeta } from "@/lib/storage";

interface SidebarProps {
  open: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  onLogout: () => void;
  onClearHistory: () => void;
  sessions: SessionMeta[];
  currentSessionId: string;
  onSelectSession: (sessionId: string) => void;
}

function timeLabel(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function Sidebar({
  open,
  onToggle,
  onNewChat,
  onLogout,
  onClearHistory,
  sessions,
  currentSessionId,
  onSelectSession,
}: SidebarProps) {
  const router = useRouter();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [popupStyle, setPopupStyle] = useState<React.CSSProperties>({});
  const settingsBtnRef = useRef<HTMLButtonElement>(null);

  const width = open ? "220px" : "60px";

  useEffect(() => {
    if (!settingsOpen || !settingsBtnRef.current) return;
    const r = settingsBtnRef.current.getBoundingClientRect();
    setPopupStyle({
      position: "fixed",
      bottom: window.innerHeight - r.top + 4,
      left: r.left,
      width: open ? r.width : 176,
      zIndex: 9999,
    });
  }, [settingsOpen, open]);

  useEffect(() => {
    if (!settingsOpen) return;
    const handler = (e: MouseEvent) => {
      if (settingsBtnRef.current && !settingsBtnRef.current.contains(e.target as Node)) {
        setSettingsOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [settingsOpen]);

  return (
    <aside
      style={{ width, minWidth: width }}
      className="relative flex flex-col bg-[#171717] h-full transition-all duration-200 overflow-hidden flex-shrink-0"
    >
      {/* New chat */}
      <div className="flex items-center h-14 px-3 flex-shrink-0">
        <button
          onClick={onNewChat}
          title="New chat"
          className="flex items-center gap-3 w-full rounded-lg px-2 py-2 text-[#8e8ea0] hover:text-[#ececec] hover:bg-[#2f2f2f] transition-colors"
        >
          <span className="text-lg flex-shrink-0">✏</span>
          {open && <span className="text-sm whitespace-nowrap">New chat</span>}
        </button>
      </div>

      {/* Prospects nav */}
      <div className="px-3 flex-shrink-0">
        <button
          onClick={() => router.push("/prospects")}
          title="Prospect pipeline"
          className="flex items-center gap-3 w-full rounded-lg px-2 py-2 text-[#8e8ea0] hover:text-[#ececec] hover:bg-[#2f2f2f] transition-colors"
        >
          <span className="text-lg flex-shrink-0">◉</span>
          {open && <span className="text-sm whitespace-nowrap">Prospects</span>}
        </button>
      </div>

      {/* History */}
      <div className="flex-1 overflow-y-auto no-scrollbar px-2 mt-2">
        {!open ? (
          <button
            onClick={onToggle}
            title="Show history"
            className="flex items-center justify-center w-full rounded-lg px-2 py-2 text-[#8e8ea0] hover:text-[#ececec] hover:bg-[#2f2f2f] transition-colors"
          >
            <span className="text-lg">◷</span>
          </button>
        ) : (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-[#4b4b4b] px-2 py-1">
              History
            </p>
            {sessions.length === 0 ? (
              <p className="text-xs text-[#4b4b4b] px-2 py-2">No past chats yet.</p>
            ) : (
              <div className="space-y-0.5">
                {sessions.map((s) => (
                  <button
                    key={s.sessionId}
                    onClick={() => onSelectSession(s.sessionId)}
                    title={s.title}
                    className={`w-full text-left rounded-lg px-2 py-2 transition-colors group ${
                      s.sessionId === currentSessionId
                        ? "bg-[#2f2f2f] text-[#ececec]"
                        : "text-[#8e8ea0] hover:bg-[#232323] hover:text-[#ececec]"
                    }`}
                  >
                    <p className="text-xs truncate leading-snug">{s.title}</p>
                    <p className="text-[10px] text-[#4b4b4b] group-hover:text-[#6b6b6b] mt-0.5">
                      {timeLabel(s.timestamp)}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Settings + collapse */}
      <div className="px-3 pb-4 space-y-1 flex-shrink-0">
        <button
          ref={settingsBtnRef}
          onClick={() => setSettingsOpen((v) => !v)}
          title="Settings"
          className={`flex items-center gap-3 w-full rounded-lg px-2 py-2 transition-colors ${
            settingsOpen
              ? "bg-[#2f2f2f] text-[#ececec]"
              : "text-[#8e8ea0] hover:text-[#ececec] hover:bg-[#2f2f2f]"
          }`}
        >
          <span className="text-lg flex-shrink-0">⚙</span>
          {open && <span className="text-sm whitespace-nowrap">Settings</span>}
        </button>
        <button
          onClick={onToggle}
          title={open ? "Collapse sidebar" : "Expand sidebar"}
          className="flex items-center gap-3 w-full rounded-lg px-2 py-2 text-[#8e8ea0] hover:text-[#ececec] hover:bg-[#2f2f2f] transition-colors"
        >
          <span className="text-lg flex-shrink-0">{open ? "◂" : "▸"}</span>
          {open && <span className="text-sm whitespace-nowrap">Collapse</span>}
        </button>
      </div>

      {settingsOpen && typeof document !== "undefined" &&
        createPortal(
          <div
            style={popupStyle}
            className="bg-[#1a1a1a] border border-[#3f3f3f] rounded-xl shadow-xl py-1"
          >
            <div className="px-3 py-2 border-b border-[#2f2f2f]">
              <p className="text-[10px] uppercase tracking-wider text-[#4b4b4b]">Account</p>
            </div>
            <button
              onMouseDown={(e) => e.stopPropagation()}
              onClick={() => {
                setSettingsOpen(false);
                onClearHistory();
              }}
              className="w-full text-left px-3 py-2 text-sm text-[#8e8ea0] hover:bg-[#2f2f2f] hover:text-[#ececec] transition-colors"
            >
              Clear history
            </button>
            <button
              onMouseDown={(e) => e.stopPropagation()}
              onClick={() => {
                setSettingsOpen(false);
                onLogout();
              }}
              className="w-full text-left px-3 py-2 text-sm text-[#f87171] hover:bg-[#2f2f2f] transition-colors"
            >
              Sign out
            </button>
          </div>,
          document.body
        )}
    </aside>
  );
}
