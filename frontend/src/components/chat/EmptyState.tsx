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
    <div className="flex flex-col items-center justify-center h-full px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="flex flex-col items-center gap-6 max-w-lg"
      >
        {/* Logo / Icon */}
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center glow-purple">
            <Bot size={32} className="text-primary" />
          </div>
          <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-green-500" />
          </div>
        </div>

        {/* Title */}
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-semibold text-foreground">
            GathaAI Studio
          </h1>
          <p className="text-sm text-muted-foreground max-w-sm">
            Assistente de IA local e gratuita. Converse, programe, aprenda — 
            tudo rodando na sua máquina.
          </p>
        </div>

        {/* Suggestion cards */}
        <div className="grid grid-cols-2 gap-3 w-full mt-2">
          {suggestions.map((s, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.05 }}
              onClick={() => onSuggestion(s.prompt)}
              className="flex items-start gap-3 p-3 rounded-xl border border-border bg-card/50 hover:bg-card hover:border-primary/30 transition-all text-left group"
            >
              <s.icon
                size={16}
                className="text-muted-foreground group-hover:text-primary transition-colors mt-0.5 flex-shrink-0"
              />
              <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors">
                {s.label}
              </span>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
