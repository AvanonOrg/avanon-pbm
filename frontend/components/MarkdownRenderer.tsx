"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  if (!content) return null;
  return (
    <div className="prose prose-invert max-w-none
      prose-p:my-1.5 prose-p:leading-relaxed prose-p:text-[#ececec]
      prose-headings:text-[#ececec] prose-headings:font-semibold
      prose-h1:text-xl prose-h2:text-lg prose-h3:text-base
      prose-strong:text-[#ececec] prose-strong:font-semibold
      prose-em:text-[#ececec]
      prose-code:text-[#e879f9] prose-code:bg-[#1e1e1e] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none
      prose-pre:bg-[#1e1e1e] prose-pre:border prose-pre:border-[#3f3f3f] prose-pre:rounded-xl prose-pre:my-3
      prose-pre:text-[#ececec] prose-pre:text-sm
      prose-ul:my-2 prose-ul:pl-5 prose-li:my-0.5 prose-li:text-[#ececec]
      prose-ol:my-2 prose-ol:pl-5
      prose-table:text-sm prose-table:border-collapse
      prose-th:bg-[#2a2a2a] prose-th:text-[#ececec] prose-th:px-3 prose-th:py-2 prose-th:border prose-th:border-[#3f3f3f]
      prose-td:text-[#ececec] prose-td:px-3 prose-td:py-2 prose-td:border prose-td:border-[#3f3f3f]
      prose-blockquote:border-l-[#3f3f3f] prose-blockquote:text-[#8e8ea0]
      prose-hr:border-[#3f3f3f]
      prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
