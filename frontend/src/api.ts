/** Built deployment uses the same local origin; Vite can set an explicit API URL. */
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

/** Local workspace requests do not carry legacy account tokens. */
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, options);
}
