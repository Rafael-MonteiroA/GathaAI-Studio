/**
 * Chat store — Zustand state management for GathaAI Studio.
 *
 * Manages:
 * - List of conversations (sidebar)
 * - Active conversation + messages
 * - Streaming state (isStreaming, partial response)
 * - CRUD operations that sync with the backend
 */

import { create } from "zustand";
import {
  createConversation as apiCreateConversation,
  listConversations as apiListConversations,
  getConversation as apiGetConversation,
  deleteConversation as apiDeleteConversation,
  type Conversation,
  type Message,
} from "@/lib/api";
import { streamMessage } from "@/lib/streaming";

// ── Types ────────────────────────────────────

interface ChatMessage extends Message {
  isStreaming?: boolean;
  thinking?: string;
}

interface ChatState {
  // Conversations list
  conversations: Conversation[];
  isLoadingConversations: boolean;

  // Active conversation
  activeConversationId: string | null;
  messages: ChatMessage[];
  isLoadingMessages: boolean;

  // Streaming
  isStreaming: boolean;
  streamController: AbortController | null;

  // Error
  error: string | null;

  // Actions
  loadConversations: () => Promise<void>;
  createConversation: () => Promise<string | null>;
  selectConversation: (id: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  cancelStream: () => void;
  clearError: () => void;
}

// ── Store ────────────────────────────────────

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  isLoadingConversations: false,
  activeConversationId: null,
  messages: [],
  isLoadingMessages: false,
  isStreaming: false,
  streamController: null,
  error: null,

  loadConversations: async () => {
    set({ isLoadingConversations: true, error: null });
    try {
      const conversations = await apiListConversations();
      set({ conversations, isLoadingConversations: false });
    } catch (err) {
      set({
        error: "Não foi possível carregar as conversas",
        isLoadingConversations: false,
      });
    }
  },

  createConversation: async () => {
    try {
      const conv = await apiCreateConversation("Nova conversa");
      set((state) => ({
        conversations: [conv, ...state.conversations],
        activeConversationId: conv.id,
        messages: [],
        error: null,
      }));
      return conv.id;
    } catch (err) {
      set({ error: "Não foi possível criar a conversa" });
      return null;
    }
  },

  selectConversation: async (id: string) => {
    if (id === get().activeConversationId) return;

    // Cancel any active stream
    get().cancelStream();

    set({ activeConversationId: id, isLoadingMessages: true, error: null });
    try {
      const detail = await apiGetConversation(id);
      set({
        messages: detail.messages,
        isLoadingMessages: false,
      });
    } catch (err) {
      set({
        error: "Não foi possível carregar a conversa",
        isLoadingMessages: false,
      });
    }
  },

  deleteConversation: async (id: string) => {
    try {
      await apiDeleteConversation(id);
      set((state) => {
        const conversations = state.conversations.filter((c) => c.id !== id);
        const isActive = state.activeConversationId === id;
        return {
          conversations,
          activeConversationId: isActive ? null : state.activeConversationId,
          messages: isActive ? [] : state.messages,
        };
      });
    } catch (err) {
      set({ error: "Não foi possível deletar a conversa" });
    }
  },

  sendMessage: async (content: string) => {
    const { activeConversationId, isStreaming } = get();

    if (!activeConversationId || isStreaming) return;

    // Add user message immediately (optimistic)
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      model: null,
      tokens_prompt: null,
      tokens_completion: null,
      created_at: new Date().toISOString(),
    };

    // Add placeholder for assistant response
    const assistantPlaceholder: ChatMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      model: null,
      tokens_prompt: null,
      tokens_completion: null,
      created_at: new Date().toISOString(),
      isStreaming: true,
    };

    set((state) => ({
      messages: [...state.messages, userMessage, assistantPlaceholder],
      isStreaming: true,
      error: null,
    }));

    // Start streaming
    const controller = streamMessage(activeConversationId, content, {
      onToken: (data) => {
        set((state) => {
          const messages = [...state.messages];
          const last = messages[messages.length - 1];
          if (last && last.role === "assistant") {
            messages[messages.length - 1] = {
              ...last,
              content: last.content + (data.content || ""),
              thinking: (last.thinking || "") + (data.thinking || ""),
            };
          }
          return { messages };
        });
      },
      onDone: (data) => {
        set((state) => {
          const messages = [...state.messages];
          const last = messages[messages.length - 1];
          if (last && last.role === "assistant") {
            messages[messages.length - 1] = {
              ...last,
              model: data.model,
              tokens_prompt: data.tokens_prompt,
              tokens_completion: data.tokens_completion,
              isStreaming: false,
            };
          }
          return {
            messages,
            isStreaming: false,
            streamController: null,
          };
        });
      },
      onTitle: (title) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === activeConversationId ? { ...c, title } : c
          ),
        }));
      },
      onError: (error) => {
        set((state) => {
          // Remove the empty assistant placeholder on error
          const messages = state.messages.filter(
            (m) => !(m.role === "assistant" && m.isStreaming && !m.content)
          );
          return {
            messages,
            isStreaming: false,
            streamController: null,
            error,
          };
        });
      },
    });

    set({ streamController: controller });
  },

  cancelStream: () => {
    const { streamController } = get();
    if (streamController) {
      streamController.abort();
      set((state) => {
        const messages = state.messages.map((m) =>
          m.isStreaming ? { ...m, isStreaming: false } : m
        );
        return {
          messages,
          isStreaming: false,
          streamController: null,
        };
      });
    }
  },

  clearError: () => set({ error: null }),
}));
