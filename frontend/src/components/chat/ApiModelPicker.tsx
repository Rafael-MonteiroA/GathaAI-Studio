"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Cloud, ChevronLeft, Check, Key, AlertCircle, Loader2 } from "lucide-react";
import { listApiKeys, type ProviderKeyInfo } from "@/lib/api";

export interface ApiModelSelection {
  provider: string;
  model: string;
}

interface Provider {
  id: string;
  label: string;
  icon: string;
  models: { id: string; label: string; description: string }[];
}

const PROVIDERS: Provider[] = [
  {
    id: "openai",
    label: "OpenAI",
    icon: "⬡",
    models: [
      { id: "gpt-4o", label: "GPT-4o", description: "Mais capaz, multimodal" },
      { id: "gpt-4o-mini", label: "GPT-4o mini", description: "Rápido e econômico" },
      { id: "gpt-4-turbo", label: "GPT-4 Turbo", description: "Alta performance" },
      { id: "o1-mini", label: "o1 mini", description: "Raciocínio avançado" },
    ],
  },
  {
    id: "anthropic",
    label: "Anthropic",
    icon: "◈",
    models: [
      { id: "claude-opus-4-5", label: "Claude Opus 4.5", description: "Mais capaz" },
      { id: "claude-sonnet-4-5", label: "Claude Sonnet 4.5", description: "Equilibrado e potente" },
      { id: "claude-haiku-4-5", label: "Claude Haiku 4.5", description: "Ultra-rápido" },
    ],
  },
  {
    id: "gemini",
    label: "Google Gemini",
    icon: "◎",
    models: [
      { id: "gemini-2.5-pro", label: "Gemini 2.5 Pro", description: "Máxima capacidade" },
      { id: "gemini-2.0-flash", label: "Gemini 2.0 Flash", description: "Rápido e eficiente" },
      { id: "gemini-1.5-flash", label: "Gemini 1.5 Flash", description: "Leve e ágil" },
    ],
  },
  {
    id: "groq",
    label: "Groq",
    icon: "⚡",
    models: [
      { id: "llama-3.3-70b-versatile", label: "LLaMA 3.3 70B", description: "Open source, veloz" },
      { id: "llama-3.1-70b-versatile", label: "LLaMA 3.1 70B", description: "Alta qualidade" },
      { id: "mixtral-8x7b-32768", label: "Mixtral 8x7B", description: "Eficiente" },
    ],
  },
  {
    id: "openrouter",
    label: "OpenRouter",
    icon: "○",
    models: [
      { id: "openai/gpt-4o", label: "GPT-4o via OR", description: "Multi-provider" },
      { id: "anthropic/claude-3-5-sonnet", label: "Claude 3.5 Sonnet via OR", description: "Alta qualidade" },
      { id: "google/gemini-2.0-flash-001", label: "Gemini 2.0 Flash via OR", description: "Google via OR" },
    ],
  },
];

interface ApiModelPickerProps {
  onSelect: (selection: ApiModelSelection) => void;
  onCancel: () => void;
}

export function ApiModelPicker({ onSelect, onCancel }: ApiModelPickerProps) {
  const [step, setStep] = useState<"provider" | "model">("provider");
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [configuredKeys, setConfiguredKeys] = useState<ProviderKeyInfo[]>([]);
  const [isLoadingKeys, setIsLoadingKeys] = useState(true);

  // Fetch configured keys from backend on mount
  useEffect(() => {
    setIsLoadingKeys(true);
    listApiKeys()
      .then(setConfiguredKeys)
      .catch(() => setConfiguredKeys([]))
      .finally(() => setIsLoadingKeys(false));
  }, []);

  const isConfigured = (providerId: string) =>
    configuredKeys.some((k) => k.provider === providerId);

  const handleProviderSelect = (provider: Provider) => {
    setSelectedProvider(provider);
    setStep("model");
  };

  const handleModelSelect = (modelId: string) => {
    if (!selectedProvider) return;
    onSelect({ provider: selectedProvider.id, model: modelId });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="flex flex-col h-full w-full"
    >
      {/* Header */}
      <div className="px-6 pt-8 pb-5 border-b border-foreground/5">
        <motion.div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-foreground/6 border border-foreground/8 flex items-center justify-center">
            <Cloud size={15} className="text-foreground/45" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground/80">
              Usar modelo de API
            </h2>
            <p className="text-xs text-foreground/30">
              {step === "provider"
                ? "Escolha o provedor"
                : `Escolha o modelo · ${selectedProvider?.label}`}
            </p>
          </div>
          <button
            onClick={onCancel}
            className="ml-auto text-xs text-foreground/25 hover:text-foreground/50 transition-colors px-2 py-1 rounded border border-foreground/8 hover:border-foreground/15"
          >
            Cancelar
          </button>
        </motion.div>
      </div>

      {/* Content */}
      <div className="flex-1 px-6 py-5 overflow-y-auto scrollbar-thin">
        <AnimatePresence mode="wait">
          {step === "provider" ? (
            <motion.div
              key="provider"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }}
              transition={{ duration: 0.2 }}
              className="grid grid-cols-2 gap-2"
            >
              {isLoadingKeys ? (
                // Loading skeleton
                Array.from({ length: 6 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-24 rounded-xl border border-foreground/5 bg-foreground/2 animate-pulse"
                  />
                ))
              ) : (
                PROVIDERS.map((provider, i) => {
                  const configured = isConfigured(provider.id);
                  return (
                    <motion.button
                      key={provider.id}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.04 }}
                      onClick={() =>
                        configured ? handleProviderSelect(provider) : undefined
                      }
                      disabled={!configured}
                      className={`relative flex flex-col gap-1.5 p-4 rounded-xl border text-left transition-all group ${
                        configured
                          ? "border-foreground/8 bg-foreground/2 hover:bg-foreground/5 hover:border-foreground/15 cursor-pointer"
                          : "border-foreground/5 bg-foreground/1 opacity-40 cursor-not-allowed"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-lg leading-none text-foreground/40 group-hover:text-foreground/70 transition-colors">
                          {provider.icon}
                        </span>
                        {configured ? (
                          <span className="text-[9px] text-green-400/70 flex items-center gap-1">
                            <Key size={8} />
                            ativa
                          </span>
                        ) : (
                          <span className="text-[9px] text-foreground/20 flex items-center gap-1">
                            <AlertCircle size={8} />
                            sem chave
                          </span>
                        )}
                      </div>
                      <span className="text-sm font-medium text-foreground/55 group-hover:text-foreground/80 transition-colors">
                        {provider.label}
                      </span>
                      <span className="text-[11px] text-foreground/25">
                        {provider.models.length} modelo
                        {provider.models.length !== 1 ? "s" : ""}
                      </span>
                    </motion.button>
                  );
                })
              )}
            </motion.div>
          ) : (
            <motion.div
              key="model"
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 12 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col gap-1.5"
            >
              <button
                onClick={() => {
                  setStep("provider");
                  setSelectedModel(null);
                }}
                className="flex items-center gap-1.5 text-xs text-foreground/30 hover:text-foreground/55 transition-colors mb-3 group"
              >
                <ChevronLeft
                  size={12}
                  className="group-hover:-translate-x-0.5 transition-transform"
                />
                Voltar
              </button>

              {selectedProvider?.models.map((model, i) => (
                <motion.button
                  key={model.id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => {
                    setSelectedModel(model.id);
                    handleModelSelect(model.id);
                  }}
                  className={`flex items-center gap-4 w-full px-4 py-3.5 rounded-lg border text-left transition-all group ${
                    selectedModel === model.id
                      ? "border-foreground/25 bg-foreground/6"
                      : "border-foreground/8 bg-foreground/2 hover:bg-foreground/5 hover:border-foreground/15"
                  }`}
                >
                  <div className="flex flex-col flex-1 min-w-0">
                    <span className="text-sm font-medium text-foreground/65 group-hover:text-foreground/85 transition-colors">
                      {model.label}
                    </span>
                    <span className="text-xs text-foreground/25">
                      {model.description}
                    </span>
                  </div>
                  {selectedModel === model.id && (
                    <Check size={13} className="text-foreground/50 flex-shrink-0" />
                  )}
                </motion.button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* No keys notice */}
        {step === "provider" && !isLoadingKeys && configuredKeys.length === 0 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-4 text-xs text-foreground/25 text-center leading-relaxed"
          >
            Nenhuma chave de API configurada ainda.
            <br />
            Clique em{" "}
            <span className="text-foreground/40 font-medium">Chaves de API</span>{" "}
            na sidebar para adicionar.
          </motion.p>
        )}
      </div>
    </motion.div>
  );
}
