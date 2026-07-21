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
    // Reset textarea height
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
    <div className="p-4">
      <div className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2 glass rounded-2xl px-4 py-3 transition-all focus-within:ring-2 focus-within:ring-primary/30 focus-within:glow-purple">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="flex-1 bg-transparent resize-none text-sm text-foreground placeholder:text-muted-foreground focus:outline-none min-h-[24px] max-h-[200px] py-0.5 scrollbar-thin"
          />

          {isStreaming ? (
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              onClick={onCancel}
              className="flex-shrink-0 w-8 h-8 rounded-lg bg-destructive/20 text-destructive flex items-center justify-center hover:bg-destructive/30 transition-colors"
              title="Parar geração"
            >
              <Square size={14} fill="currentColor" />
            </motion.button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!canSend}
              className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                canSend
                  ? "bg-primary text-primary-foreground hover:brightness-110 glow-purple"
                  : "bg-muted text-muted-foreground cursor-not-allowed"
              }`}
              title="Enviar mensagem (Enter)"
            >
              <Send size={14} />
            </button>
          )}
        </div>

        <p className="text-[11px] text-muted-foreground text-center mt-2">
          GathaAI pode cometer erros. Verifique informações importantes.
        </p>
      </div>
    </div>
  );
}
