"use client";

import { useEffect } from "react";
import {
  Plus,
  MessageSquare,
  Trash2,
  Bot,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useChatStore } from "@/store/chat";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

export function Sidebar({ isOpen, onToggle }: SidebarProps) {
  const {
    conversations,
    activeConversationId,
    isLoadingConversations,
    loadConversations,
    createConversation,
    selectConversation,
    deleteConversation,
  } = useChatStore();

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const handleNewChat = async () => {
    await createConversation();
  };

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={onToggle}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <AnimatePresence>
        {isOpen && (
          <motion.aside
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed lg:relative z-50 flex flex-col w-[280px] h-full bg-sidebar border-r border-sidebar-border"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-sidebar-border">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-primary/15 flex items-center justify-center">
                  <Bot size={14} className="text-primary" />
                </div>
                <span className="text-sm font-semibold text-sidebar-foreground">
                  GathaAI
                </span>
              </div>
              <button
                onClick={onToggle}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent transition-colors"
              >
                <PanelLeftClose size={16} />
              </button>
            </div>

            {/* New chat button */}
            <div className="p-3">
              <button
                onClick={handleNewChat}
                className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl border border-dashed border-sidebar-border text-sm text-sidebar-foreground/70 hover:text-sidebar-foreground hover:border-primary/40 hover:bg-sidebar-accent transition-all"
              >
                <Plus size={16} />
                Nova conversa
              </button>
            </div>

            {/* Conversations list */}
            <div className="flex-1 overflow-y-auto scrollbar-thin px-2">
              {isLoadingConversations ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-xs text-sidebar-foreground/40">
                    Nenhuma conversa ainda
                  </p>
                </div>
              ) : (
                <div className="space-y-0.5 pb-2">
                  {conversations.map((conv) => (
                    <ConversationItem
                      key={conv.id}
                      id={conv.id}
                      title={conv.title}
                      isActive={conv.id === activeConversationId}
                      messageCount={conv.message_count}
                      onSelect={() => selectConversation(conv.id)}
                      onDelete={() => deleteConversation(conv.id)}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-sidebar-border">
              <div className="flex items-center gap-2 text-[11px] text-sidebar-foreground/40">
                <div className="w-2 h-2 rounded-full bg-green-500/60" />
                Ollama local
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Toggle button when sidebar is closed */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed top-3 left-3 z-30 w-9 h-9 rounded-lg glass flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
        >
          <PanelLeft size={18} />
        </button>
      )}
    </>
  );
}

// ── Conversation Item ────────────────────────

function ConversationItem({
  id,
  title,
  isActive,
  messageCount,
  onSelect,
  onDelete,
}: {
  id: string;
  title: string;
  isActive: boolean;
  messageCount: number;
  onSelect: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all ${
        isActive
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
      }`}
      onClick={onSelect}
    >
      <MessageSquare size={14} className="flex-shrink-0 opacity-50" />
      <span className="flex-1 text-sm truncate">{title}</span>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="flex-shrink-0 opacity-0 group-hover:opacity-100 w-6 h-6 rounded flex items-center justify-center text-sidebar-foreground/40 hover:text-destructive hover:bg-destructive/10 transition-all"
        title="Deletar conversa"
      >
        <Trash2 size={12} />
      </button>
    </div>
  );
}
