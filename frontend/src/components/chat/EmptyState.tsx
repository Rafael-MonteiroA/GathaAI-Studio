"use client";

import { Bot, Sparkles, Code, FileText, Lightbulb } from "lucide-react";
import { motion } from "framer-motion";

interface EmptyStateProps {
  onSuggestion: (content: string) => void;
}

const suggestions = [
  {
    icon: Code,
    label: "Ajuda com código",
    prompt: "Me ajude a criar uma função Python que...",
  },
  {
    icon: Lightbulb,
    label: "Explicar conceito",
    prompt: "Explique de forma simples o que é...",
  },
  {
    icon: FileText,
    label: "Resumir texto",
    prompt: "Resuma o seguinte texto para mim:",
  },
  {
    icon: Sparkles,
    label: "Ideia criativa",
    prompt: "Me dê ideias criativas para...",
  },
];

export function EmptyState({ onSuggestion }: EmptyStateProps) {
  return (
    <div className="flex flex-col h-full w-full">
      {/* Top section — header */}
      <div className="px-6 pt-10 pb-6 border-b border-foreground/5">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="flex items-center gap-3"
        >
          <div className="w-8 h-8 rounded-lg bg-foreground/6 border border-foreground/8 flex items-center justify-center">
            <Bot size={16} className="text-foreground/45" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-foreground/80 leading-tight">
              GathaAI Studio
            </h1>
            <p className="text-xs text-foreground/30 leading-tight">
              IA local · rodando na sua máquina
            </p>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500/60 animate-pulse" />
            <span className="text-[11px] text-foreground/25">online</span>
          </div>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="mt-4 text-sm text-foreground/35 leading-relaxed"
        >
          Converse, programe, aprenda. Nenhum dado sai da sua máquina.
        </motion.p>
      </div>

      {/* Suggestions section — fills remaining space */}
      <div className="flex-1 px-6 py-6 flex flex-col gap-1.5">
        <span className="text-[10px] text-foreground/20 uppercase tracking-widest font-medium mb-2">
          Comece com uma sugestão
        </span>

        {suggestions.map((s, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 + i * 0.06 }}
            onClick={() => onSuggestion(s.prompt)}
            className="flex items-center gap-4 w-full px-4 py-3.5 rounded-lg border border-foreground/6 bg-foreground/2 hover:bg-foreground/5 hover:border-foreground/12 transition-all text-left group"
          >
            <s.icon
              size={14}
              className="text-foreground/25 group-hover:text-foreground/50 transition-colors flex-shrink-0"
            />
            <span className="text-sm text-foreground/50 group-hover:text-foreground/75 transition-colors font-medium">
              {s.label}
            </span>
            <span className="ml-auto text-xs text-foreground/20 group-hover:text-foreground/35 transition-colors font-mono truncate max-w-[260px]">
              {s.prompt}
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
