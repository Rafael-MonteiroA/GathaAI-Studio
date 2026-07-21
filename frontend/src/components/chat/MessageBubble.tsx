"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { motion } from "framer-motion";
import { Bot, User, Copy, Check, BrainCircuit, ChevronRight } from "lucide-react";
import { useState } from "react";

interface MessageBubbleProps {
  role: "user" | "assistant" | "system";
  content: string;
  isStreaming?: boolean;
  thinking?: string;
  model?: string | null;
}

export function MessageBubble({
  role,
  content,
  isStreaming,
  thinking,
  model,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`flex gap-3 px-4 py-5 ${
        isUser ? "" : "bg-card/50"
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
          isUser
            ? "bg-primary/20 text-primary"
            : "bg-accent/20 text-accent"
        }`}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">
            {isUser ? "Você" : "GathaAI"}
          </span>
          {model && !isUser && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono">
              {model}
            </span>
          )}
        </div>

        {thinking && (
          <div className="mb-4 mt-2">
            {isStreaming && !content ? (
              <div className="bg-muted/30 border border-primary/20 rounded-lg p-4 space-y-3 shadow-lg shadow-primary/5 animate-fade-in-up">
                <div className="flex items-center gap-2 text-primary font-medium text-sm">
                  <BrainCircuit size={16} className="animate-pulse" />
                  Raciocinando...
                </div>
                <div className="text-sm text-muted-foreground whitespace-pre-wrap font-mono opacity-80 max-h-[200px] overflow-y-auto scrollbar-thin">
                  {thinking}
                </div>
                <div className="h-1 w-full bg-muted overflow-hidden rounded-full mt-2 relative">
                  <div className="absolute top-0 left-0 h-full w-[30%] bg-primary/50 rounded-full animate-progress" />
                </div>
              </div>
            ) : (
              <details className="group border border-border rounded-lg bg-card/50 overflow-hidden [&_summary::-webkit-details-marker]:hidden animate-fade-in-up">
                <summary className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-muted/50 transition-colors select-none text-xs font-medium text-muted-foreground">
                  <BrainCircuit size={14} />
                  Processo de raciocínio
                  <ChevronRight size={14} className="ml-auto transition-transform group-open:rotate-90" />
                </summary>
                <div className="p-3 pt-1 text-xs text-muted-foreground/80 whitespace-pre-wrap font-mono border-t border-border/50 bg-muted/20">
                  {thinking}
                </div>
              </details>
            )}
          </div>
        )}

        <div className="prose prose-invert prose-sm max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 mt-2">
          {content ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  const codeString = String(children).replace(/\n$/, "");

                  if (match) {
                    return (
                      <CodeBlock language={match[1]} code={codeString} />
                    );
                  }

                  return (
                    <code
                      className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-primary"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
                p({ children }) {
                  return <p className="leading-relaxed">{children}</p>;
                },
                ul({ children }) {
                  return <ul className="list-disc pl-4 space-y-1">{children}</ul>;
                },
                ol({ children }) {
                  return <ol className="list-decimal pl-4 space-y-1">{children}</ol>;
                },
                a({ href, children }) {
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      {children}
                    </a>
                  );
                },
              }}
            >
              {content}
            </ReactMarkdown>
          ) : isStreaming ? (
            <span className="inline-block w-2 h-4 bg-primary rounded-sm cursor-blink" />
          ) : null}

          {isStreaming && content && (
            <span className="inline-block w-2 h-4 bg-primary rounded-sm cursor-blink ml-0.5 align-middle" />
          )}
        </div>
      </div>
    </motion.div>
  );
}

// ── Code Block with copy button ──────────────

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="not-prose relative group rounded-lg overflow-hidden my-3 border border-border">
      <div className="flex items-center justify-between px-3 py-1.5 bg-muted/80 border-b border-border">
        <span className="text-[11px] font-mono text-muted-foreground">
          {language}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? "Copiado" : "Copiar"}
        </button>
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={language}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: 0,
          background: "oklch(0.14 0.01 260)",
          fontSize: "13px",
        }}
        codeTagProps={{
          style: { backgroundColor: "transparent", inherit: "background" }
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
