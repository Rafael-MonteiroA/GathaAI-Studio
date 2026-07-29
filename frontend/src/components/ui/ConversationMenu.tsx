"use client";

import { useRef, useEffect } from "react";
import { Settings, Download, FileJson, FileText, Upload, Trash2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ConversationMenuProps {
  conversationId: string;
  isOpen: boolean;
  onClose: () => void;
  onOpenSettings: () => void;
  onExportJson: () => void;
  onExportMarkdown: () => void;
  onDelete: () => void;
}

export function ConversationMenu({
  isOpen,
  onClose,
  onOpenSettings,
  onExportJson,
  onExportMarkdown,
  onDelete,
}: ConversationMenuProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    if (isOpen) document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [isOpen, onClose]);

  const items = [
    {
      icon: Settings,
      label: "Configurações",
      onClick: onOpenSettings,
      className: "text-foreground/80",
    },
    {
      icon: FileJson,
      label: "Exportar JSON",
      onClick: onExportJson,
      className: "text-foreground/80",
    },
    {
      icon: FileText,
      label: "Exportar Markdown",
      onClick: onExportMarkdown,
      className: "text-foreground/80",
    },
    {
      icon: Trash2,
      label: "Deletar",
      onClick: onDelete,
      className: "text-destructive",
      separator: true,
    },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={ref}
          initial={{ opacity: 0, scale: 0.92, y: -4 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92, y: -4 }}
          transition={{ duration: 0.12 }}
          className="absolute right-0 top-8 z-50 w-44 rounded-xl border border-border/60 bg-popover shadow-xl py-1"
        >
          {items.map((item, i) => (
            <div key={i}>
              {item.separator && (
                <div className="my-1 border-t border-border/40" />
              )}
              <button
                onClick={() => { item.onClick(); onClose(); }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm hover:bg-accent transition-colors ${item.className}`}
              >
                <item.icon size={13} className="flex-shrink-0 opacity-70" />
                {item.label}
              </button>
            </div>
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
