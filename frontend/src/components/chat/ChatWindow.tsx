"use client";

import { useRef, useEffect } from "react";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { EmptyState } from "./EmptyState";
import { useChatStore } from "@/store/chat";
import { ScrollArea } from "@/components/ui/scroll-area";

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
      // Create a new conversation first
      const id = await useChatStore.getState().createConversation();
      if (id) {
        // Wait for state to update, then send
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
        <div className="px-4 py-2 bg-destructive/10 border-b border-destructive/20 text-destructive text-sm flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={clearError}
            className="text-xs underline hover:no-underline"
          >
            Fechar
          </button>
        </div>
      )}

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin" ref={scrollRef}>
        {!activeConversationId && messages.length === 0 ? (
          <EmptyState onSuggestion={handleSend} />
        ) : isLoadingMessages ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-sm">Carregando...</span>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <EmptyState onSuggestion={handleSend} />
        ) : (
          <div className="max-w-3xl mx-auto py-4">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                role={msg.role}
                content={msg.content}
                isStreaming={msg.isStreaming}
                model={msg.model}
              />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-border bg-background/80 backdrop-blur-sm">
        <MessageInput
          onSend={handleSend}
          onCancel={cancelStream}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  );
}
