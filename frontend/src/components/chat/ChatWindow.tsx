"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { EmptyState } from "./EmptyState";
import { ApiModelPicker, type ApiModelSelection } from "./ApiModelPicker";
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
    setConversationProvider,
  } = useChatStore();

  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Pending text to fill into the MessageInput
  const [pendingInput, setPendingInput] = useState<string>("");

  // Whether to show the API model picker in the chat area
  const [showApiModelPicker, setShowApiModelPicker] = useState(false);

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

  const handleFillInput = useCallback((text: string) => {
    setPendingInput(text);
    setShowApiModelPicker(false);
  }, []);

  const handleSelectApiModel = useCallback(() => {
    setShowApiModelPicker(true);
  }, []);

  const handleApiModelSelected = useCallback(async (selection: ApiModelSelection) => {
    // Persist provider + model to backend so all future messages use this provider
    await setConversationProvider(selection.provider, selection.model);
    setShowApiModelPicker(false);
    // Brief feedback in input
    setPendingInput(`[${selection.provider} · ${selection.model}] `);
  }, [setConversationProvider]);

  const isEmptyState =
    (!activeConversationId && messages.length === 0) || messages.length === 0;

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

      {/* Messages area */}
      <div
        className="flex-1 overflow-y-auto scrollbar-thin min-h-0"
        ref={scrollRef}
      >
        {showApiModelPicker ? (
          <ApiModelPicker
            onSelect={handleApiModelSelected}
            onCancel={() => setShowApiModelPicker(false)}
          />
        ) : isEmptyState && !isLoadingMessages ? (
          <EmptyState
            onFillInput={handleFillInput}
            onSelectApiModel={handleSelectApiModel}
          />
        ) : isLoadingMessages ? (
          <div className="flex items-center justify-start px-6 py-8">
            <div className="flex items-center gap-2 text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-foreground/30 animate-pulse" />
              <span className="text-xs text-muted-foreground">Carregando...</span>
            </div>
          </div>
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
          externalValue={pendingInput}
          onExternalValueConsumed={() => setPendingInput("")}
        />
      </div>
    </div>
  );
}
