"use client";

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Key,
  Plus,
  Trash2,
  Check,
  ChevronDown,
  Loader2,
  AlertCircle,
  ShieldCheck,
} from "lucide-react";
import {
  listApiKeys,
  upsertApiKey,
  deleteApiKey,
  type ProviderKeyInfo,
} from "@/lib/api";

// ── Types ────────────────────────────────────

const PROVIDER_OPTIONS = [
  { id: "openai", label: "OpenAI", icon: "⬡" },
  { id: "anthropic", label: "Anthropic", icon: "◈" },
  { id: "google", label: "Google AI", icon: "◎" },
  { id: "groq", label: "Groq", icon: "⚡" },
  { id: "mistral", label: "Mistral", icon: "◆" },
  { id: "openrouter", label: "OpenRouter", icon: "○" },
  { id: "gemini", label: "Gemini", icon: "✦" },
];

// ── Sub-components ───────────────────────────

function ProviderSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const selected = PROVIDER_OPTIONS.find((p) => p.id === value);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg bg-foreground/4 border border-foreground/10 text-sm hover:border-foreground/20 transition-colors focus:outline-none"
      >
        <span className="flex items-center gap-2 text-foreground/60">
          {selected ? (
            <>
              <span className="text-base leading-none">{selected.icon}</span>
              {selected.label}
            </>
          ) : (
            "Selecione o provedor"
          )}
        </span>
        <ChevronDown
          size={13}
          className={`text-foreground/30 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute z-50 top-full mt-1 left-0 right-0 rounded-lg border border-foreground/12 bg-[var(--gatha-surface)] shadow-xl overflow-hidden">
            {PROVIDER_OPTIONS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => { onChange(p.id); setOpen(false); }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm text-left transition-colors ${
                  p.id === value
                    ? "bg-foreground/8 text-foreground/80"
                    : "text-foreground/50 hover:bg-foreground/5 hover:text-foreground/75"
                }`}
              >
                <span className="text-base leading-none">{p.icon}</span>
                {p.label}
                {p.id === value && (
                  <Check size={11} className="ml-auto text-foreground/50" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function KeyForm({
  initial,
  isSaving,
  onSave,
  onCancel,
}: {
  initial?: { provider: string };
  isSaving: boolean;
  onSave: (provider: string, key: string) => void;
  onCancel: () => void;
}) {
  const [provider, setProvider] = useState(initial?.provider || "");
  const [key, setKey] = useState("");
  const [showKey, setShowKey] = useState(false);

  const isEditing = !!initial?.provider;
  const canSave = provider && key.trim().length >= 8;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      className="rounded-xl border border-foreground/10 bg-foreground/2 p-4 flex flex-col gap-3"
    >
      <p className="text-xs font-medium text-foreground/40 uppercase tracking-widest">
        {isEditing ? "Atualizar chave" : "Nova chave de API"}
      </p>

      {/* Provider */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[11px] text-foreground/35">Provedor</label>
        <ProviderSelect
          value={provider}
          onChange={isEditing ? () => {} : setProvider}
        />
      </div>

      {/* Key */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[11px] text-foreground/35">
          {isEditing ? "Nova chave de API" : "Chave de API"}
        </label>
        <div className="relative flex items-center">
          <input
            type={showKey ? "text" : "password"}
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="sk-... / gsk_... / AIza..."
            className="flex-1 px-3 py-2.5 pr-10 rounded-lg bg-foreground/4 border border-foreground/10 text-sm text-foreground/70 placeholder:text-foreground/20 focus:outline-none focus:border-foreground/25 transition-colors font-mono"
          />
          <button
            type="button"
            onClick={() => setShowKey((v) => !v)}
            className="absolute right-3 text-foreground/25 hover:text-foreground/55 transition-colors text-[11px]"
          >
            {showKey ? "ocultar" : "mostrar"}
          </button>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-foreground/25">
          <ShieldCheck size={10} />
          Criptografada com AES antes de salvar no servidor.
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-2 rounded-lg text-sm text-foreground/35 hover:text-foreground/60 hover:bg-foreground/5 transition-colors"
        >
          Cancelar
        </button>
        <button
          type="button"
          disabled={!canSave || isSaving}
          onClick={() => canSave && onSave(provider, key.trim())}
          className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            canSave && !isSaving
              ? "bg-foreground/10 text-foreground/70 hover:bg-foreground/15 hover:text-foreground/90"
              : "bg-foreground/4 text-foreground/20 cursor-not-allowed"
          }`}
        >
          {isSaving ? (
            <Loader2 size={13} className="animate-spin" />
          ) : (
            <Check size={13} />
          )}
          {isEditing ? "Atualizar chave" : "Adicionar chave"}
        </button>
      </div>
    </motion.div>
  );
}

function KeyCard({
  keyInfo,
  isDeleting,
  onUpdate,
  onDelete,
}: {
  keyInfo: ProviderKeyInfo;
  isDeleting: boolean;
  onUpdate: () => void;
  onDelete: () => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const provider = PROVIDER_OPTIONS.find((p) => p.id === keyInfo.provider);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      className="flex flex-col gap-2 rounded-xl border border-foreground/8 bg-foreground/2 p-4 group"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span className="text-lg leading-none text-foreground/35">
            {provider?.icon ?? "✦"}
          </span>
          <div>
            <p className="text-sm font-medium text-foreground/65">
              {provider?.label ?? keyInfo.provider}
            </p>
            <p className="text-[11px] text-foreground/30">{keyInfo.provider}</p>
          </div>
        </div>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={onUpdate}
            className="w-7 h-7 rounded-lg flex items-center justify-center text-foreground/25 hover:text-foreground/60 hover:bg-foreground/8 transition-colors text-[11px]"
            title="Atualizar chave"
          >
            ↻
          </button>
          {confirmDelete ? (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-2 py-1 text-[11px] text-foreground/30 hover:text-foreground/55 transition-colors"
              >
                Não
              </button>
              <button
                onClick={onDelete}
                disabled={isDeleting}
                className="px-2 py-1 text-[11px] rounded bg-destructive/15 text-destructive/70 hover:bg-destructive/25 transition-colors flex items-center gap-1"
              >
                {isDeleting && <Loader2 size={9} className="animate-spin" />}
                Sim, remover
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(true)}
              className="w-7 h-7 rounded-lg flex items-center justify-center text-foreground/25 hover:text-destructive/60 hover:bg-destructive/8 transition-colors"
              title="Remover"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Key preview — always masked, key never leaves backend */}
      <div className="flex items-center gap-2 mt-0.5">
        <code className="flex-1 text-[11px] font-mono text-foreground/20 truncate">
          ••••••••••••••••••••
        </code>
        <span className="flex items-center gap-1 text-[10px] text-green-400/60">
          <ShieldCheck size={9} />
          configurada
        </span>
      </div>

      <p className="text-[10px] text-foreground/18">
        Atualizada em {new Date(keyInfo.updated_at).toLocaleDateString("pt-BR")}
      </p>
    </motion.div>
  );
}

// ── Main Panel ───────────────────────────────

interface ApiKeysPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ApiKeysPanel({ isOpen, onClose }: ApiKeysPanelProps) {
  const [keys, setKeys] = useState<ProviderKeyInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingProvider, setDeletingProvider] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchKeys = useCallback(async () => {
    setIsLoading(true);
    try {
      const fetched = await listApiKeys();
      setKeys(fetched);
    } catch {
      setError("Não foi possível carregar as chaves do servidor.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load when panel opens
  useEffect(() => {
    if (isOpen) {
      fetchKeys();
      setShowForm(false);
      setEditingProvider(null);
      setError(null);
    }
  }, [isOpen, fetchKeys]);

  const handleSave = async (provider: string, key: string) => {
    setIsSaving(true);
    setError(null);
    try {
      await upsertApiKey(provider, key);
      await fetchKeys();
      setShowForm(false);
      setEditingProvider(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao salvar chave.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (provider: string) => {
    setDeletingProvider(provider);
    setError(null);
    try {
      await deleteApiKey(provider);
      await fetchKeys();
    } catch {
      setError("Erro ao remover chave.");
    } finally {
      setDeletingProvider(null);
    }
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingProvider(null);
    setError(null);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 z-40"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
            className="fixed right-0 top-0 h-full w-[380px] z-50 flex flex-col bg-sidebar border-l border-sidebar-border shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-foreground/8 flex items-center justify-center">
                  <Key size={13} className="text-foreground/45" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-foreground">
                    Chaves de API
                  </h2>
                  <p className="text-[11px] text-muted-foreground">
                    {isLoading
                      ? "Carregando..."
                      : keys.length === 0
                      ? "Nenhuma chave configurada"
                      : `${keys.length} chave${keys.length !== 1 ? "s" : ""} configurada${keys.length !== 1 ? "s" : ""}`}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto scrollbar-thin p-4 flex flex-col gap-3">
              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-destructive/8 border border-destructive/15 text-destructive/80 text-xs"
                >
                  <AlertCircle size={13} className="flex-shrink-0 mt-0.5" />
                  {error}
                </motion.div>
              )}

              {/* Add / Update form */}
              <AnimatePresence mode="wait">
                {(showForm || editingProvider) && (
                  <KeyForm
                    key={editingProvider ?? "new"}
                    initial={
                      editingProvider ? { provider: editingProvider } : undefined
                    }
                    isSaving={isSaving}
                    onSave={handleSave}
                    onCancel={handleCancelForm}
                  />
                )}
              </AnimatePresence>

              {/* Loading skeleton */}
              {isLoading && (
                <div className="flex flex-col gap-2">
                  {[1, 2].map((i) => (
                    <div
                      key={i}
                      className="h-20 rounded-xl border border-foreground/5 bg-foreground/2 animate-pulse"
                    />
                  ))}
                </div>
              )}

              {/* Keys list */}
              {!isLoading && (
                <AnimatePresence>
                  {keys.map((k) => (
                    <KeyCard
                      key={k.provider}
                      keyInfo={k}
                      isDeleting={deletingProvider === k.provider}
                      onUpdate={() => {
                        setEditingProvider(k.provider);
                        setShowForm(false);
                      }}
                      onDelete={() => handleDelete(k.provider)}
                    />
                  ))}
                </AnimatePresence>
              )}

              {/* Empty state */}
              {!isLoading && keys.length === 0 && !showForm && !editingProvider && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex flex-col items-center justify-center py-12 gap-3 text-center"
                >
                  <div className="w-12 h-12 rounded-2xl bg-foreground/4 border border-foreground/8 flex items-center justify-center">
                    <Key size={20} className="text-foreground/20" />
                  </div>
                  <div>
                    <p className="text-sm text-foreground/35 font-medium">
                      Sem chaves configuradas
                    </p>
                    <p className="text-xs text-foreground/20 mt-0.5">
                      Adicione uma chave para usar modelos externos
                    </p>
                  </div>
                </motion.div>
              )}

              <p className="text-[10px] text-foreground/18 text-center px-4 pb-2">
                As chaves são criptografadas com AES-128 (Fernet) antes de serem
                salvas. A chave bruta nunca é retornada pelo servidor.
              </p>
            </div>

            {/* Footer — Add button */}
            {!showForm && !editingProvider && (
              <div className="p-4 border-t border-sidebar-border">
                <button
                  onClick={() => setShowForm(true)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-dashed border-foreground/15 text-sm text-foreground/40 hover:text-foreground/65 hover:border-foreground/25 hover:bg-foreground/3 transition-all"
                >
                  <Plus size={14} />
                  Adicionar chave de API
                </button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
