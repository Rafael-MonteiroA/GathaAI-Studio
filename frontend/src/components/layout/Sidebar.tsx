"use client";

import { useEffect, useRef, useState } from "react";
import {
  Plus,
  MessageSquare,
  Bot,
  PanelLeftClose,
  PanelLeft,
  MoreHorizontal,
  Upload,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useChatStore } from "@/store/chat";
import { ConversationMenu } from "@/components/ui/ConversationMenu";
import { SettingsPanel } from "@/components/settings/SettingsPanel";

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
    exportConversation,
    importConversation,
    openSettings,
  } = useChatStore();

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const handleNewChat = async () => {
    await createConversation();
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await importConversation(file);
      e.target.value = "";
    }
  };

  return (
    <>
      {/* Hidden file input for import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Settings panel (renders over all content) */}
      {activeConversationId && (
        <SettingsPanel conversationId={activeConversationId} />
      )}

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
            className="fixed lg:relative z-50 flex flex-col w-[260px] h-full bg-sidebar border-r border-sidebar-border"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-sidebar-border">
              <div className="flex items-center gap-2.5">
                <div className="w-6 h-6 rounded-md bg-foreground/8 flex items-center justify-center">
                  <Bot size={13} className="text-foreground/50" />
                </div>
                <span className="text-sm font-medium text-sidebar-foreground/80 tracking-tight">
                  GathaAI
                </span>
              </div>
              <div className="flex items-center gap-0.5">
                <button
                  onClick={handleImportClick}
                  className="w-7 h-7 rounded-md flex items-center justify-center text-sidebar-foreground/30 hover:text-sidebar-foreground/70 hover:bg-sidebar-accent transition-colors"
                  title="Importar conversa (.json)"
                >
                  <Upload size={13} />
                </button>
                <button
                  onClick={onToggle}
                  className="w-7 h-7 rounded-md flex items-center justify-center text-sidebar-foreground/30 hover:text-sidebar-foreground/70 hover:bg-sidebar-accent transition-colors"
                >
                  <PanelLeftClose size={14} />
                </button>
              </div>
            </div>

            {/* New chat button */}
            <div className="px-3 py-2.5">
              <button
                onClick={handleNewChat}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed border-sidebar-border/60 text-[13px] text-sidebar-foreground/40 hover:text-sidebar-foreground/80 hover:border-sidebar-border hover:bg-sidebar-accent transition-all"
              >
                <Plus size={14} />
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
                      onExportJson={() => exportConversation(conv.id, "json")}
                      onExportMarkdown={() =>
                        exportConversation(conv.id, "markdown")
                      }
                      onOpenSettings={() => openSettings(conv.id)}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-sidebar-border">
              <div className="flex items-center gap-2 text-[11px] text-sidebar-foreground/25">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500/50" />
                Ollama · Memory Engine
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
  onExportJson,
  onExportMarkdown,
  onOpenSettings,
}: {
  id: string;
  title: string;
  isActive: boolean;
  messageCount: number;
  onSelect: () => void;
  onDelete: () => void;
  onExportJson: () => void;
  onExportMarkdown: () => void;
  onOpenSettings: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div
      className={`group relative flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-all ${
        isActive
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/45 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground/80"
      }`}
      onClick={onSelect}
    >
      <MessageSquare size={12} className="flex-shrink-0 opacity-40" />
      <span className="flex-1 text-[13px] truncate">{title}</span>

      {/* More options button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          setMenuOpen((v) => !v);
        }}
        className="flex-shrink-0 opacity-0 group-hover:opacity-100 w-5 h-5 rounded flex items-center justify-center text-sidebar-foreground/30 hover:text-sidebar-foreground/70 hover:bg-sidebar-accent transition-all"
        title="Opções"
      >
        <MoreHorizontal size={11} />
      </button>

      {/* Context menu */}
      <ConversationMenu
        conversationId={id}
        isOpen={menuOpen}
        onClose={() => setMenuOpen(false)}
        onOpenSettings={() => { onOpenSettings(); setMenuOpen(false); }}
        onExportJson={() => { onExportJson(); setMenuOpen(false); }}
        onExportMarkdown={() => { onExportMarkdown(); setMenuOpen(false); }}
        onDelete={() => { onDelete(); setMenuOpen(false); }}
      />
    </div>
  );
}
