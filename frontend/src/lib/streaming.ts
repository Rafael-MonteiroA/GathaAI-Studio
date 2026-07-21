/**
 * SSE streaming client for GathaAI Studio.
 *
 * Handles the Server-Sent Events connection to the chat endpoint,
 * parsing token/done/error/title events in real-time.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StreamCallbacks {
  onToken: (content: string) => void;
  onDone: (data: {
    model: string;
    tokens_prompt: number | null;
    tokens_completion: number | null;
  }) => void;
  onTitle?: (title: string) => void;
  onError?: (error: string) => void;
}

/**
 * Send a message and stream the response via SSE.
 *
 * Returns an AbortController so the caller can cancel the stream.
 */
export function streamMessage(
  conversationId: string,
  content: string,
  callbacks: StreamCallbacks,
  options: { temperature?: number } = {}
): AbortController {
  const controller = new AbortController();

  const url = `${API_BASE}/api/v1/conversations/${conversationId}/messages`;

  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      content,
      temperature: options.temperature ?? 0.7,
    }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const text = await response.text();
        callbacks.onError?.(`Erro ${response.status}: ${text}`);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError?.("Streaming não suportado neste navegador");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const dataStr = line.slice(6);
            try {
              const data = JSON.parse(dataStr);

              switch (currentEvent) {
                case "token":
                  if (data.content) {
                    callbacks.onToken(data.content);
                  }
                  break;
                case "done":
                  callbacks.onDone(data);
                  break;
                case "title":
                  callbacks.onTitle?.(data.title);
                  break;
                case "error":
                  callbacks.onError?.(data.detail || "Erro desconhecido");
                  break;
              }
            } catch {
              // Skip non-JSON data lines (e.g., ping comments)
            }
            currentEvent = "";
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        callbacks.onError?.(err.message || "Erro de conexão");
      }
    });

  return controller;
}
