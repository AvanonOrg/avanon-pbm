import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

// ── Copy button for code blocks ────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <button
      onClick={copy}
      style={{
        background: "none",
        border: "none",
        color: copied ? "#4ade80" : "#8e8ea0",
        fontSize: 11,
        cursor: "pointer",
        padding: "2px 6px",
        borderRadius: 4,
        transition: "color 0.15s",
        fontFamily: "inherit",
      }}
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

// ── Custom component map ───────────────────────────────────────────────────

const makeComponents = (): Components => ({
  // Inline code
  code({ node, className, children, ...props }) {
    const isInline = !className;
    const language = (className ?? "").replace("language-", "");
    const codeText = String(children).replace(/\n$/, "");

    if (isInline) {
      return (
        <code
          {...props}
          style={{
            background: "#2d2d2d",
            border: "1px solid #3a3a3a",
            borderRadius: 4,
            padding: "1px 6px",
            fontSize: "0.875em",
            fontFamily: "'Fira Code', 'Cascadia Code', Consolas, monospace",
            color: "#e2c08d",
          }}
        >
          {children}
        </code>
      );
    }

    return (
      <div
        style={{
          background: "#1a1a1a",
          border: "1px solid #2f2f2f",
          borderRadius: 8,
          margin: "12px 0",
          overflow: "hidden",
        }}
      >
        {/* Code block header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "6px 14px",
            background: "#222",
            borderBottom: "1px solid #2f2f2f",
          }}
        >
          <span style={{ fontSize: 11, color: "#6b6b6b", fontFamily: "monospace" }}>
            {language || "code"}
          </span>
          <CopyButton text={codeText} />
        </div>
        <pre
          style={{
            margin: 0,
            padding: "14px 16px",
            overflowX: "auto",
            fontSize: 13,
            lineHeight: 1.65,
            fontFamily: "'Fira Code', 'Cascadia Code', Consolas, monospace",
            color: "#ececec",
          }}
        >
          <code style={{ fontFamily: "inherit", color: "inherit" }}>{children}</code>
        </pre>
      </div>
    );
  },

  // Paragraphs
  p({ children }) {
    return (
      <p
        style={{
          margin: "0 0 12px",
          lineHeight: 1.7,
          color: "#ececec",
        }}
      >
        {children}
      </p>
    );
  },

  // Headers
  h1({ children }) {
    return <h1 style={{ fontSize: "1.5em", fontWeight: 700, color: "#fff", margin: "20px 0 10px", lineHeight: 1.3 }}>{children}</h1>;
  },
  h2({ children }) {
    return <h2 style={{ fontSize: "1.25em", fontWeight: 600, color: "#fff", margin: "18px 0 8px", lineHeight: 1.35 }}>{children}</h2>;
  },
  h3({ children }) {
    return <h3 style={{ fontSize: "1.1em", fontWeight: 600, color: "#ececec", margin: "14px 0 6px", lineHeight: 1.4 }}>{children}</h3>;
  },
  h4({ children }) {
    return <h4 style={{ fontSize: "1em", fontWeight: 600, color: "#ececec", margin: "12px 0 4px" }}>{children}</h4>;
  },

  // Lists
  ul({ children }) {
    return <ul style={{ margin: "0 0 12px", paddingLeft: 22, color: "#ececec" }}>{children}</ul>;
  },
  ol({ children }) {
    return <ol style={{ margin: "0 0 12px", paddingLeft: 22, color: "#ececec" }}>{children}</ol>;
  },
  li({ children }) {
    return <li style={{ marginBottom: 4, lineHeight: 1.65 }}>{children}</li>;
  },

  // Links — open in new tab
  a({ href, children }) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: "#60a5fa", textDecoration: "underline", textUnderlineOffset: 3 }}
      >
        {children}
      </a>
    );
  },

  // Blockquote
  blockquote({ children }) {
    return (
      <blockquote
        style={{
          borderLeft: "3px solid #3f3f3f",
          margin: "12px 0",
          padding: "4px 0 4px 16px",
          color: "#8e8ea0",
        }}
      >
        {children}
      </blockquote>
    );
  },

  // Horizontal rule
  hr() {
    return <hr style={{ border: "none", borderTop: "1px solid #2f2f2f", margin: "16px 0" }} />;
  },

  // Tables (GFM)
  table({ children }) {
    return (
      <div style={{ overflowX: "auto", margin: "12px 0" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: 14,
            color: "#ececec",
          }}
        >
          {children}
        </table>
      </div>
    );
  },
  thead({ children }) {
    return <thead style={{ background: "#2a2a2a" }}>{children}</thead>;
  },
  th({ children }) {
    return (
      <th
        style={{
          padding: "8px 12px",
          textAlign: "left",
          fontWeight: 600,
          color: "#8e8ea0",
          fontSize: 12,
          borderBottom: "1px solid #3f3f3f",
          whiteSpace: "nowrap",
        }}
      >
        {children}
      </th>
    );
  },
  td({ children }) {
    return (
      <td
        style={{
          padding: "8px 12px",
          borderBottom: "1px solid #2a2a2a",
          verticalAlign: "top",
        }}
      >
        {children}
      </td>
    );
  },

  // Strong / em
  strong({ children }) {
    return <strong style={{ color: "#fff", fontWeight: 600 }}>{children}</strong>;
  },
  em({ children }) {
    return <em style={{ color: "#c8c8c8", fontStyle: "italic" }}>{children}</em>;
  },

  // Strikethrough (GFM)
  del({ children }) {
    return <del style={{ color: "#6b6b6b" }}>{children}</del>;
  },
});

// ── MarkdownRenderer ───────────────────────────────────────────────────────

interface Props {
  content: string;
  isStreaming?: boolean;
}

export function MarkdownRenderer({ content, isStreaming }: Props) {
  const components = makeComponents();

  return (
    <div
      className={isStreaming ? "md-streaming" : ""}
      style={{ fontSize: 15, lineHeight: 1.7, color: "#ececec" }}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
