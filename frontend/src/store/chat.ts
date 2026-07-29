/**
 * Chat store — Zustand state management for GathaAI Studio.
 *
 * Manages:
 * - List of conversations (sidebar)
 * - Active conversation + messages
 * - Streaming state (isStreaming, partial response)
 * - CRUD operations that sync with the backend
 * - Per-conversation settings (v0.3)
 * - Export / Import (v0.3)
 */

import { create } from "zustand";
import {
  createConversation as apiCreateConversation,
  listConversations as apiListConversations,
  getConversation as apiGetConversation,
  deleteConversation as apiDeleteConversation,
  getConversationSettings as apiGetSettings,
  updateConversationSettings as apiUpdateSettings,
  exportConversation as apiExport,
  importConversation as apiImport,
  type Conversation,
  type Message,
  type ConversationSettings,
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

  // Settings panel
  settingsPanelOpen: boolean;
  activeSettings: ConversationSettings | null;
  isLoadingSettings: boolean;

  // Error
  error: string | null;

  // Actions — conversations
  loadConversations: () => Promise<void>;
  createConversation: () => Promise<string | null>;
  selectConversation: (id: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  cancelStream: () => void;

  // Actions — settings
  openSettings: (conversationId: string) => Promise<void>;
  closeSettings: () => void;
  saveSettings: (
    conversationId: string,
    settings: Partial<Pick<ConversationSettings, "model" | "temperature" | "system_prompt">>
  ) => Promise<void>;

  // Actions — export / import
  exportConversation: (id: string, format: "json" | "markdown") => Promise<void>;
  importConversation: (file: File) => Promise<void>;

  // Utility
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
  settingsPanelOpen: false,
  activeSettings: null,
  isLoadingSettings: false,
  error: null,

  // ── Conversations ──────────────────────────

  loadConversations: async () => {
    set({ isLoadingConversations: true, error: null });
    try {
      const conversations = await apiListConversations();
      set({ conversations, isLoadingConversations: false });
    } catch {
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
    } catch {
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
    } catch {
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
          settingsPanelOpen: isActive ? false : state.settingsPanelOpen,
        };
      });
    } catch {
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

  // ── Settings ───────────────────────────────

  openSettings: async (conversationId: string) => {
    set({ settingsPanelOpen: true, isLoadingSettings: true, activeSettings: null });
    try {
      const settings = await apiGetSettings(conversationId);
      set({ activeSettings: settings, isLoadingSettings: false });
    } catch {
      set({ isLoadingSettings: false });
    }
  },

  closeSettings: () => {
    set({ settingsPanelOpen: false, activeSettings: null });
  },

  saveSettings: async (conversationId, settings) => {
    try {
      const updated = await apiUpdateSettings(conversationId, settings);
      set({ activeSettings: updated });
    } catch {
      set({ error: "Não foi possível salvar as configurações" });
    }
  },

  // ── Export / Import ────────────────────────

  exportConversation: async (id, format) => {
    try {
      await apiExport(id, format);
    } catch {
      set({ error: "Erro ao exportar conversa" });
    }
  },

  importConversation: async (file) => {
    try {
      const result = await apiImport(file);
      // Reload conversations so the imported one appears in the sidebar
      await get().loadConversations();
      // Auto-select the imported conversation
      await get().selectConversation(result.id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao importar conversa";
      set({ error: msg });
    }
  },

  // ── Utility ────────────────────────────────

  clearError: () => set({ error: null }),
}));
