"use client";

import { useEffect, useState } from "react";
import { X, Save, RotateCcw, Settings, Thermometer, Bot, MessageSquare } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useChatStore } from "@/store/chat";
import { ModelSelector } from "./ModelSelector";

interface SettingsPanelProps {
  conversationId: string;
}

export function SettingsPanel({ conversationId }: SettingsPanelProps) {
  const { settingsPanelOpen, activeSettings, isLoadingSettings, closeSettings, saveSettings } =
    useChatStore();

  const [model, setModel] = useState<string | null>(null);
  const [temperature, setTemperature] = useState<number | null>(null);
  const [systemPrompt, setSystemPrompt] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Populate form from loaded settings
  useEffect(() => {
    if (activeSettings) {
      setModel(activeSettings.model);
      setTemperature(activeSettings.temperature);
      setSystemPrompt(activeSettings.system_prompt);
    }
  }, [activeSettings]);

  const handleSave = async () => {
    setSaving(true);
    await saveSettings(conversationId, {
      model: model || null,
      temperature: temperature ?? null,
      system_prompt: systemPrompt || null,
    });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setModel(null);
    setTemperature(null);
    setSystemPrompt(null);
  };

  return (
    <AnimatePresence>
      {settingsPanelOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 z-40"
            onClick={closeSettings}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
            className="fixed right-0 top-0 h-full w-[360px] z-50 flex flex-col bg-sidebar border-l border-sidebar-border shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-primary/15 flex items-center justify-center">
                  <Settings size={14} className="text-primary" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-foreground">Configurações</h2>
                  <p className="text-[11px] text-muted-foreground">Personalize esta conversa</p>
                </div>
              </div>
              <button
                onClick={closeSettings}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* Content */}
            {isLoadingSettings ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin">

                {/* Model */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    <Bot size={12} />
                    Modelo
                  </label>
                  <ModelSelector value={model} onChange={setModel} />
                  <p className="text-[11px] text-muted-foreground/60">
                    Deixe em branco para usar o modelo padrão da instância Ollama.
                  </p>
                </div>

                {/* Temperature */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    <Thermometer size={12} />
                    Temperatura
                    <span className="ml-auto font-mono text-primary">
                      {temperature !== null ? temperature.toFixed(1) : "0.7 (padrão)"}
                    </span>
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={2}
                    step={0.1}
                    value={temperature ?? 0.7}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full accent-primary cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground/50">
                    <span>0.0 — Preciso</span>
                    <span>1.0 — Balanceado</span>
                    <span>2.0 — Criativo</span>
                  </div>
                  {temperature !== null && (
                    <button
                      type="button"
                      onClick={() => setTemperature(null)}
                      className="text-[11px] text-muted-foreground/60 hover:text-muted-foreground transition-colors"
                    >
                      Resetar para padrão
                    </button>
                  )}
                </div>

                {/* System Prompt */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    <MessageSquare size={12} />
                    System Prompt
                  </label>
                  <textarea
                    value={systemPrompt ?? ""}
                    onChange={(e) => setSystemPrompt(e.target.value || null)}
                    placeholder={"Você é GathaAI, uma assistente... (deixe vazio para usar o padrão)"}
                    rows={8}
                    className="w-full px-3 py-2.5 rounded-xl bg-card/50 border border-border/60 text-sm text-foreground placeholder:text-muted-foreground/40 resize-none focus:outline-none focus:border-primary/60 transition-colors scrollbar-thin font-mono"
                  />
                  <p className="text-[11px] text-muted-foreground/60">
                    Define a personalidade e as regras da IA para esta conversa.
                  </p>
                </div>
              </div>
            )}

            {/* Footer actions */}
            <div className="p-4 border-t border-sidebar-border flex gap-2">
              <button
                type="button"
                onClick={handleReset}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-colors"
                title="Resetar para padrões"
              >
                <RotateCcw size={13} />
                Resetar
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  saved
                    ? "bg-green-500/20 text-green-400 border border-green-500/30"
                    : "bg-primary/15 text-primary hover:bg-primary/25 border border-primary/30"
                } disabled:opacity-50`}
              >
                <Save size={13} />
                {saving ? "Salvando..." : saved ? "Salvo!" : "Salvar"}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
