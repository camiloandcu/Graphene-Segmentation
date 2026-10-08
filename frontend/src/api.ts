/** Built deployment uses the same local origin; Vite can set an explicit API URL. */
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

/** Local workspace requests do not carry legacy account tokens. */
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, options);
}

export interface LocalModel {
  model_id: string;
  name: string;
  version: string;
  bundle_sha256: string;
  model_sha256: string;
  imported_at: string;
  available: boolean;
  selected: boolean;
  evidence_kind: "unmeasured" | "reported";
}

export interface Registry {
  models: LocalModel[];
  selected_model_id: string | null;
  validation_available: boolean;
  installation_action: string;
}

export interface ModelDetails extends LocalModel {
  manifest: {
    classes: { id: number; name: string }[];
    decision: { kind: string; threshold?: number };
    geometry: { mode: string };
    provenance: Record<string, unknown>;
  };
  evaluation: {
    evidence: {
      kind: "reported" | "unmeasured";
      reason?: string;
      source?: string;
      metrics?: {
        name: string; value: number | null; unit: string;
        definition: string; support: number | null; unavailable_reason: string | null;
      }[];
    };
  };
}

export async function modelRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), options.method ? 100000 : 15000);
  try {
    const response = await apiFetch(`/api/models${path}`, { ...options, signal: controller.signal, cache: "no-store" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Model request failed. Refresh Models and retry.");
    return data as T;
  } catch (error) {
    if (error instanceof Error && error.name !== "AbortError" && error.name !== "TypeError" && error.name !== "SyntaxError") throw error;
    throw new Error("Connection unavailable or response lost. Check the local server, then refresh Models before retrying.");
  } finally {
    window.clearTimeout(timeout);
  }
}
