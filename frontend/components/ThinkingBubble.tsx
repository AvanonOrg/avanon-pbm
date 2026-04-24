"use client";

import { useState, useEffect } from "react";
import type { ThinkingStep } from "@/lib/types";

interface ThinkingBubbleProps {
  steps: ThinkingStep[];
  currentStep?: string;
  isActive: boolean;
}

export default function ThinkingBubble({ steps, currentStep, isActive }: ThinkingBubbleProps) {
  const [expanded, setExpanded] = useState(false);
  const [gone, setGone] = useState(false);

  useEffect(() => {
    if (!isActive && steps.length > 0) {
      const t = setTimeout(() => setGone(true), 1600);
      return () => clearTimeout(t);
    }
  }, [isActive, steps.length]);

  if (gone) return null;

  const isDone = !isActive && steps.length > 0;

  return (
    <div className={`mb-3 ${isDone ? "thinking-bubble-done" : ""}`}>
      <button
        onClick={() => setExpanded((e) => !e)}
        className="flex items-center gap-2 bg-[#2f2f2f] border border-[#3f3f3f] rounded-full px-3 py-1.5 text-sm text-[#8e8ea0] hover:text-[#ececec] transition-colors"
      >
        <span className="thinking-dot inline-block w-1.5 h-1.5 rounded-full bg-[#8e8ea0]" />
        <span className="thinking-dot inline-block w-1.5 h-1.5 rounded-full bg-[#8e8ea0]" />
        <span className="thinking-dot inline-block w-1.5 h-1.5 rounded-full bg-[#8e8ea0]" />
        <span className="ml-1 text-xs max-w-xs truncate">
          {currentStep || (isDone ? "Done thinking" : "Thinking…")}
        </span>
        {steps.length > 0 && (
          <span className="text-xs ml-1 transition-transform inline-block" style={{ transform: expanded ? "rotate(180deg)" : "rotate(0deg)" }}>
            ▾
          </span>
        )}
      </button>

      {expanded && steps.length > 0 && (
        <div className="mt-2 ml-3 border-l border-[#3f3f3f] pl-3 space-y-1.5">
          {steps.map((s, i) => (
            <div key={i} className="text-xs text-[#8e8ea0] flex gap-2">
              <span className="text-[#6b6b6b] flex-shrink-0">{i + 1}.</span>
              <span>{s.step}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
