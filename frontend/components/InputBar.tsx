"use client";

import { useRef, useEffect, useState } from "react";

interface InputBarProps {
  onSubmit: (text: string) => void;
  disabled: boolean;
}

export default function InputBar({ onSubmit, disabled }: InputBarProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  }, [value]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleSubmit() {
    const text = value.trim();
    if (!text || disabled) return;
    setValue("");
    onSubmit(text);
  }

  const canSubmit = value.trim().length > 0 && !disabled;

  return (
    <div className="w-full max-w-3xl px-4 pb-2">
      <div className="flex items-end gap-2 bg-[#2f2f2f] border border-[#3f3f3f] rounded-2xl px-4 py-3">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask about drug pricing…"
          className="flex-1 bg-transparent text-[#ececec] resize-none outline-none text-sm leading-6 placeholder-[#6b6b6b] overflow-y-auto"
          style={{ maxHeight: "200px" }}
        />
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors"
          style={{
            background: canSubmit ? "#ececec" : "#3f3f3f",
            color: canSubmit ? "#212121" : "#6b6b6b",
          }}
          title="Send"
        >
          ↑
        </button>
      </div>
    </div>
  );
}
