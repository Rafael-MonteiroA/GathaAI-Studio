/**
 * API client for GathaAI Studio backend.
 *
 * All HTTP communication with the FastAPI backend goes through here.
 * SSE streaming is handled separately in streaming.ts.
 *
 * v0.3: Added Settings, Models list, Export, and Import endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ────────────────────────────────────

export interface Conversation {
  id: string;
  title: string;
  provider: string;
  model: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  model: string | null;
  tokens_prompt: number | null;
  tokens_completion: number | null;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface ConversationSettings {
  conversation_id: string;
  provider: string | null;
  model: string | null;
  temperature: number | null;
  system_prompt: string | null;
  updated_at: string | null;
}

export interface ModelInfo {
  name: string;
  size: number | null;
  modified_at: string | null;
}

/** A stored provider key — raw key is NEVER returned by the backend. */
export interface ProviderKeyInfo {
  id: string;
  provider: string;
  configured: true;
  updated_at: string;
}

// ── Conversations ─────────────────────────────

export async function createConversation(
  title: string = "Nova conversa"
): Promise<Conversation> {
  const res = await fetch(`${API_BASE}/api/v1/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(`Failed to create conversation: ${res.status}`);
  return res.json();
}

export async function listConversations(): Promise<Conversation[]> {
  const res = await fetch(`${API_BASE}/api/v1/conversations`);
  if (!res.ok) throw new Error(`Failed to list conversations: ${res.status}`);
  return res.json();
}

export async function getConversation(
  id: string
): Promise<ConversationDetail> {
  const res = await fetch(`${API_BASE}/api/v1/conversations/${id}`);
  if (!res.ok) throw new Error(`Failed to get conversation: ${res.status}`);
  return res.json();
}

export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/conversations/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete conversation: ${res.status}`);
}

// ── Settings ──────────────────────────────────

export async function getConversationSettings(
  id: string
): Promise<ConversationSettings> {
  const res = await fetch(`${API_BASE}/api/v1/conversations/${id}/settings`);
  if (!res.ok) throw new Error(`Failed to get settings: ${res.status}`);
  return res.json();
}

export async function updateConversationSettings(
  id: string,
  settings: Partial<Pick<ConversationSettings, "provider" | "model" | "temperature" | "system_prompt">>
): Promise<ConversationSettings> {
  const res = await fetch(`${API_BASE}/api/v1/conversations/${id}/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error(`Failed to update settings: ${res.status}`);
  return res.json();
}

/**
 * Shortcut to update only provider + model for a conversation.
 * This makes the provider selector in the UI persist its choice.
 */
export async function updateConversationProvider(
  id: string,
  provider: string,
  model: string
): Promise<ConversationSettings> {
  return updateConversationSettings(id, { provider, model });
}

export async function listModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${API_BASE}/api/v1/models`);
  if (!res.ok) return [];
  return res.json();
}

// ── Export / Import ───────────────────────────

export async function exportConversation(
  id: string,
  format: "json" | "markdown" = "json"
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/api/v1/conversations/${id}/export?format=${format}`
  );
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);

  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^";]+)"?/);
  const filename =
    match?.[1] ?? `gathaai_export.${format === "markdown" ? "md" : "json"}`;

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function importConversation(
  file: File
): Promise<{ id: string; title: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/v1/conversations/import`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Import failed: ${res.status}`);
  }
  return res.json();
}

// ── Health ────────────────────────────────────

export async function checkHealth(): Promise<{
  status: string;
  ollama: string;
}> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json();
}

// ── Provider Keys ─────────────────────────────

/** Returns all providers that have a key stored on the backend. */
export async function listApiKeys(): Promise<ProviderKeyInfo[]> {
  const res = await fetch(`${API_BASE}/api/v1/keys`);
  if (!res.ok) return [];
  return res.json();
}

/**
 * Store (or replace) a key for the given provider.
 * The raw key is encrypted on the backend before storage.
 */
export async function upsertApiKey(
  provider: string,
  key: string
): Promise<ProviderKeyInfo> {
  const res = await fetch(`${API_BASE}/api/v1/keys`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, key }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Failed to save key: ${res.status}`);
  }
  return res.json();
}

/** Delete the stored key for the given provider. */
export async function deleteApiKey(provider: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/keys/${provider}`, {
    method: "DELETE",
  });
  if (!res.ok && res.status !== 404) {
    throw new Error(`Failed to delete key: ${res.status}`);
  }
}
