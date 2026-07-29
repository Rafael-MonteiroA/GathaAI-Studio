"use client";

import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { listModels, type ModelInfo } from "@/lib/api";

interface ModelSelectorProps {
  value: string | null;
  onChange: (model: string | null) => void;
  placeholder?: string;
}

export function ModelSelector({
  value,
  onChange,
  placeholder = "Modelo padrão",
}: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    listModels()
      .then(setModels)
      .finally(() => setLoading(false));
  }, []);

  const selected = models.find((m) => m.name === value);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-xl bg-card/50 border border-border/60 text-sm hover:border-primary/40 transition-colors focus:outline-none focus:border-primary/60"
      >
        <span className={selected ? "text-foreground" : "text-muted-foreground"}>
          {loading
            ? "Carregando modelos..."
            : selected?.name ?? placeholder}
        </span>
        <ChevronDown
          size={14}
          className={`text-muted-foreground flex-shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
          />
          <div className="absolute z-50 top-full mt-1 left-0 right-0 max-h-48 overflow-y-auto rounded-xl border border-border/60 bg-popover shadow-xl">
            {/* Clear option */}
            <button
              type="button"
              onClick={() => { onChange(null); setOpen(false); }}
              className="w-full px-3 py-2 text-left text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            >
              {placeholder}
            </button>
            {models.length === 0 && !loading && (
              <div className="px-3 py-2 text-sm text-muted-foreground/60">
                Nenhum modelo encontrado
              </div>
            )}
            {models.map((model) => (
              <button
                key={model.name}
                type="button"
                onClick={() => { onChange(model.name); setOpen(false); }}
                className={`w-full px-3 py-2 text-left text-sm transition-colors ${
                  model.name === value
                    ? "bg-primary/15 text-primary"
                    : "hover:bg-accent hover:text-foreground text-foreground/80"
                }`}
              >
                <span className="font-medium">{model.name}</span>
                {model.size && (
                  <span className="ml-2 text-xs text-muted-foreground">
                    {(model.size / 1e9).toFixed(1)} GB
                  </span>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
