"use client";

import { useRef, useState, useCallback, type KeyboardEvent } from "react";
import { Send, Square } from "lucide-react";
import { motion } from "framer-motion";

interface MessageInputProps {
  onSend: (content: string) => void;
  onCancel?: () => void;
  isStreaming?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({
  onSend,
  onCancel,
  isStreaming = false,
  disabled = false,
  placeholder = "Envie uma mensagem...",
}: MessageInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled || isStreaming) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, disabled, isStreaming, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  const canSend = value.trim().length > 0 && !disabled && !isStreaming;

  return (
    <div className="px-6 py-4">
      {/* Input container — left-aligned, no centering */}
      <div
        className={`relative flex items-end gap-3 bg-[var(--gatha-surface)] border rounded-xl px-4 py-3 transition-all ${
          value.trim()
            ? "border-foreground/20 shadow-lg shadow-black/30"
            : "border-foreground/10"
        } focus-within:border-foreground/25 focus-within:shadow-lg focus-within:shadow-black/30`}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent resize-none text-sm text-foreground/85 placeholder:text-foreground/25 focus:outline-none min-h-[22px] max-h-[200px] py-0 scrollbar-thin leading-6"
        />

        {isStreaming ? (
          <motion.button
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            onClick={onCancel}
            className="flex-shrink-0 w-7 h-7 rounded-lg bg-destructive/15 text-destructive/80 flex items-center justify-center hover:bg-destructive/25 transition-colors"
            title="Parar geração"
          >
            <Square size={12} fill="currentColor" />
          </motion.button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!canSend}
            className={`flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
              canSend
                ? "bg-foreground/90 text-background hover:bg-foreground"
                : "bg-foreground/8 text-foreground/25 cursor-not-allowed"
            }`}
            title="Enviar mensagem (Enter)"
          >
            <Send size={12} />
          </button>
        )}
      </div>

      <p className="text-[11px] text-foreground/20 mt-2 ml-0.5">
        Enter para enviar · Shift+Enter para nova linha
      </p>
    </div>
  );
}
