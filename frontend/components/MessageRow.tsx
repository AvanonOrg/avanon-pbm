"use client";

import type { ChatMessage } from "@/lib/types";
import MarkdownRenderer from "./MarkdownRenderer";
import ThinkingBubble from "./ThinkingBubble";
import ReportCard from "./ReportCard";

interface MessageRowProps {
  message: ChatMessage;
}

export default function MessageRow({ message }: MessageRowProps) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end mb-4 msg-enter">
        <div className="bg-[#2f2f2f] text-[#ececec] rounded-3xl px-4 py-3 max-w-xl text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  const hasThinking = message.isStreaming || (message.thinkingSteps?.length ?? 0) > 0;

  return (
    <div className="flex flex-col mb-6 msg-enter max-w-3xl">
      {hasThinking && (
        <ThinkingBubble
          steps={message.thinkingSteps ?? []}
          currentStep={message.currentThinkingStep}
          isActive={message.isStreaming ?? false}
        />
      )}

      <div className={hasThinking && !message.content ? "" : ""}>
        {message.content && <MarkdownRenderer content={message.content} />}
        {message.isStreaming && <span className="streaming-cursor" />}
      </div>

      {message.report && <ReportCard report={message.report} />}
    </div>
  );
}
