"use client";

import { Bot, Sparkles, Code, FileText, Lightbulb, Cloud } from "lucide-react";
import { motion } from "framer-motion";

interface EmptyStateProps {
  onFillInput: (text: string) => void;
  onSelectApiModel: () => void;
}

const suggestions = [
  {
    icon: Code,
    label: "Ajuda com código",
    placeholder: "Me ajude a criar ",
    hint: "ex: uma função Python que ordena uma lista...",
  },
  {
    icon: Lightbulb,
    label: "Explicar conceito",
    placeholder: "Explique de forma simples o que é ",
    hint: "ex: machine learning, recursão...",
  },
  {
    icon: FileText,
    label: "Resumir texto",
    placeholder: "Resuma o seguinte texto: ",
    hint: "cole o texto após os dois pontos...",
  },
  {
    icon: Sparkles,
    label: "Ideia criativa",
    placeholder: "Me dê ideias criativas para ",
    hint: "ex: um app, um projeto, uma campanha...",
  },
];

export function EmptyState({ onFillInput, onSelectApiModel }: EmptyStateProps) {
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

      {/* Suggestions section */}
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
            onClick={() => onFillInput(s.placeholder)}
            className="flex items-center gap-4 w-full px-4 py-3.5 rounded-lg border border-foreground/6 bg-foreground/2 hover:bg-foreground/5 hover:border-foreground/12 transition-all text-left group"
          >
            <s.icon
              size={14}
              className="text-foreground/25 group-hover:text-foreground/50 transition-colors flex-shrink-0"
            />
            <div className="flex flex-col min-w-0">
              <span className="text-sm text-foreground/50 group-hover:text-foreground/75 transition-colors font-medium">
                {s.label}
              </span>
              <span className="text-xs text-foreground/20 group-hover:text-foreground/35 transition-colors font-mono truncate">
                {s.hint}
              </span>
            </div>
            <span className="ml-auto text-xs text-foreground/15 group-hover:text-foreground/30 transition-colors font-mono truncate max-w-[160px] flex-shrink-0">
              {s.placeholder}…
            </span>
          </motion.button>
        ))}

        {/* Divider */}
        <div className="flex items-center gap-3 my-2">
          <div className="flex-1 h-px bg-foreground/6" />
          <span className="text-[10px] text-foreground/20 uppercase tracking-widest">ou</span>
          <div className="flex-1 h-px bg-foreground/6" />
        </div>

        {/* API model button */}
        <motion.button
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12 + suggestions.length * 0.06 }}
          onClick={onSelectApiModel}
          className="flex items-center gap-4 w-full px-4 py-3.5 rounded-lg border border-dashed border-foreground/10 bg-transparent hover:bg-foreground/3 hover:border-foreground/20 transition-all text-left group"
        >
          <Cloud
            size={14}
            className="text-foreground/20 group-hover:text-foreground/45 transition-colors flex-shrink-0"
          />
          <div className="flex flex-col min-w-0">
            <span className="text-sm text-foreground/40 group-hover:text-foreground/65 transition-colors font-medium">
              Usar modelo de API
            </span>
            <span className="text-xs text-foreground/18 group-hover:text-foreground/30 transition-colors">
              OpenAI, Anthropic, Google AI, Groq e outros
            </span>
          </div>
          <span className="ml-auto text-[10px] text-foreground/15 group-hover:text-foreground/30 transition-colors px-2 py-0.5 rounded border border-foreground/8 font-medium">
            API
          </span>
        </motion.button>
      </div>
    </div>
  );
}
