"use client";

import { useRef, useEffect } from "react";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { EmptyState } from "./EmptyState";
import { useChatStore } from "@/store/chat";

export function ChatWindow() {
  const {
    messages,
    isStreaming,
    isLoadingMessages,
    activeConversationId,
    error,
    sendMessage,
    cancelStream,
    clearError,
  } = useChatStore();

  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (content: string) => {
    if (!activeConversationId) {
      const id = await useChatStore.getState().createConversation();
      if (id) {
        setTimeout(() => {
          useChatStore.getState().sendMessage(content);
        }, 50);
      }
      return;
    }
    sendMessage(content);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Error banner */}
      {error && (
        <div className="px-6 py-2.5 bg-destructive/8 border-b border-destructive/15 text-destructive text-xs flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={clearError}
            className="text-xs underline hover:no-underline opacity-70 hover:opacity-100 transition-opacity"
          >
            Fechar
          </button>
        </div>
      )}

      {/* Messages area — left-aligned, no centering */}
      <div
        className="flex-1 overflow-y-auto scrollbar-thin min-h-0"
        ref={scrollRef}
      >
        {!activeConversationId && messages.length === 0 ? (
          <EmptyState onSuggestion={handleSend} />
        ) : isLoadingMessages ? (
          <div className="flex items-center justify-start px-6 py-8">
            <div className="flex items-center gap-2 text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-foreground/30 animate-pulse" />
              <span className="text-xs text-muted-foreground">Carregando...</span>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <EmptyState onSuggestion={handleSend} />
        ) : (
          <div className="py-2">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                role={msg.role}
                content={msg.content}
                isStreaming={msg.isStreaming}
                thinking={msg.thinking}
                model={msg.model}
              />
            ))}
            <div ref={bottomRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="separator bg-background/95 backdrop-blur-sm">
        <MessageInput
          onSend={handleSend}
          onCancel={cancelStream}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  );
}
