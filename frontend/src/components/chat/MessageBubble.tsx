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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={`flex gap-0 px-6 py-4 transition-colors ${
        isUser
          ? "bg-transparent"
          : "bg-[var(--gatha-user-bg)]/0"
      }`}
    >
      {/* Left gutter with avatar */}
      <div className="w-9 flex-shrink-0 pt-0.5">
        <div
          className={`w-6 h-6 rounded-md flex items-center justify-center ${
            isUser
              ? "bg-foreground/10 text-foreground/60"
              : "bg-foreground/6 text-foreground/50"
          }`}
        >
          {isUser ? <User size={13} /> : <Bot size={13} />}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1 pt-0.5">
        {/* Name + model badge */}
        <div className="flex items-center gap-2 mb-2">
          <span className={`text-xs font-medium ${
            isUser ? "text-foreground/50" : "text-foreground/60"
          }`}>
            {isUser ? "Você" : "GathaAI"}
          </span>
          {model && !isUser && (
            <span className="text-[10px] px-1.5 py-px rounded bg-foreground/6 text-foreground/35 font-mono tracking-tight border border-foreground/8">
              {model}
            </span>
          )}
        </div>

        {/* Thinking block */}
        {thinking && (
          <div className="mb-3">
            {isStreaming && !content ? (
              <div className="bg-foreground/4 border border-foreground/8 rounded-lg p-3 space-y-2 animate-fade-in-up">
                <div className="flex items-center gap-2 text-foreground/50 text-xs font-medium">
                  <BrainCircuit size={13} className="animate-pulse" />
                  Raciocinando...
                </div>
                <div className="text-xs text-foreground/35 whitespace-pre-wrap font-mono max-h-[180px] overflow-y-auto scrollbar-thin leading-relaxed">
                  {thinking}
                </div>
                <div className="h-px w-full bg-foreground/8 overflow-hidden rounded-full relative">
                  <div className="absolute top-0 left-0 h-full w-[30%] bg-foreground/20 rounded-full animate-progress" />
                </div>
              </div>
            ) : (
              <details className="group border border-foreground/8 rounded-lg bg-foreground/3 overflow-hidden [&_summary::-webkit-details-marker]:hidden animate-fade-in-up">
                <summary className="flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-foreground/5 transition-colors select-none text-xs text-foreground/40">
                  <BrainCircuit size={12} />
                  Processo de raciocínio
                  <ChevronRight size={12} className="ml-auto transition-transform group-open:rotate-90 opacity-50" />
                </summary>
                <div className="p-3 pt-2 text-xs text-foreground/30 whitespace-pre-wrap font-mono border-t border-foreground/6 leading-relaxed">
                  {thinking}
                </div>
              </details>
            )}
          </div>
        )}

        {/* Message content */}
        <div className={`prose prose-sm max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 ${
          isUser
            ? "prose-invert text-foreground/80"
            : "prose-invert text-foreground/90"
        }`}>
          {content ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  const codeString = String(children).replace(/\n$/, "");

                  if (match) {
                    return <CodeBlock language={match[1]} code={codeString} />;
                  }

                  return (
                    <code
                      className="bg-foreground/8 px-1.5 py-0.5 rounded text-[12px] font-mono text-foreground/80 border border-foreground/8"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
                p({ children }) {
                  return <p className="leading-7 text-[14px]">{children}</p>;
                },
                ul({ children }) {
                  return <ul className="list-disc pl-4 space-y-1 text-[14px]">{children}</ul>;
                },
                ol({ children }) {
                  return <ol className="list-decimal pl-4 space-y-1 text-[14px]">{children}</ol>;
                },
                a({ href, children }) {
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-foreground/70 underline underline-offset-2 hover:text-foreground transition-colors decoration-foreground/30"
                    >
                      {children}
                    </a>
                  );
                },
                h1({ children }) {
                  return <h1 className="text-lg font-semibold text-foreground mt-4 mb-2">{children}</h1>;
                },
                h2({ children }) {
                  return <h2 className="text-base font-semibold text-foreground mt-3 mb-1.5">{children}</h2>;
                },
                h3({ children }) {
                  return <h3 className="text-sm font-semibold text-foreground mt-2 mb-1">{children}</h3>;
                },
                blockquote({ children }) {
                  return (
                    <blockquote className="border-l-2 border-foreground/15 pl-3 text-foreground/50 italic my-2">
                      {children}
                    </blockquote>
                  );
                },
              }}
            >
              {content}
            </ReactMarkdown>
          ) : isStreaming ? (
            <span className="inline-block w-1.5 h-4 bg-foreground/40 rounded-sm cursor-blink" />
          ) : null}

          {isStreaming && content && (
            <span className="inline-block w-1.5 h-4 bg-foreground/40 rounded-sm cursor-blink ml-0.5 align-middle" />
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
    <div className="not-prose relative group rounded-lg overflow-hidden my-3 border border-foreground/10 bg-[oklch(0.07_0_0)]">
      <div className="flex items-center justify-between px-3 py-1.5 bg-foreground/4 border-b border-foreground/8">
        <span className="text-[11px] font-mono text-foreground/35 tracking-wide">
          {language}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[11px] text-foreground/35 hover:text-foreground/70 transition-colors"
        >
          {copied ? <Check size={11} /> : <Copy size={11} />}
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
          background: "oklch(0.07 0 0)",
          fontSize: "12.5px",
          lineHeight: "1.6",
        }}
        codeTagProps={{
          style: { backgroundColor: "transparent" }
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
