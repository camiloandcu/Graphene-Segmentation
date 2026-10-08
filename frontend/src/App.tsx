import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "./api";

interface Health {
  status: "ok";
  runtime: "local";
  storage_ready: boolean;
  model_loaded: boolean;
}

type Connection = "checking" | "ready" | "error";

export default function App() {
  const [connection, setConnection] = useState<Connection>("checking");
  const request = useRef<AbortController | null>(null);

  const checkConnection = useCallback(async () => {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setConnection("checking");
    const timeout = window.setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        signal: controller.signal,
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Workspace unavailable");
      const health: Health = await response.json();
      if (health.status !== "ok" || health.runtime !== "local" || !health.storage_ready || health.model_loaded !== false) {
        throw new Error("Workspace not ready");
      }
      if (request.current === controller) setConnection("ready");
    } catch {
      if (request.current === controller) setConnection("error");
    } finally {
      window.clearTimeout(timeout);
    }
  }, []);

  useEffect(() => {
    void checkConnection();
    return () => {
      request.current?.abort();
      request.current = null;
    };
  }, [checkConnection]);

  const label = connection === "ready" ? "Workspace connected" : connection === "error" ? "Connection unavailable" : "Connecting to workspace";

  return (
    <div className="workspace-shell">
      <a className="skip-link" href="#main">Skip to workspace</a>
      <header className="workspace-header">
        <a className="wordmark" href="#main" aria-label="Graphene workspace">
          <svg viewBox="0 0 28 28" width="28" height="28" aria-hidden="true">
            <path d="M14 3 24 8.5v11L14 25 4 19.5v-11Z M4 8.5 14 14l10-5.5 M14 14v11" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
          </svg>
          Graphene
        </a>
        <span className="local-label">Local workspace</span>
      </header>
      <div className="workspace-layout">
        <nav className="workspace-nav" aria-label="Workspace navigation">
          <a href="#main" aria-current="page">Workspace</a>
          <p>On this computer</p>
        </nav>
        <main id="main" className="workspace-main" tabIndex={-1}>
          <div className="page-heading">
            <h1>Workspace</h1>
            <p>Graphene screening for your microscopy images.</p>
          </div>
          <section className="connection-section" aria-labelledby="connection-heading">
            <div>
              <h2 id="connection-heading">Workspace status</h2>
              <p role="status" aria-live="polite" className={`connection-state ${connection}`}>
                <span className="status-dot" aria-hidden="true" />{label}
              </p>
              <p className="status-description">
                {connection === "ready"
                  ? "Local storage is ready. No account is needed."
                  : connection === "error"
                    ? "Start the local server, then check the connection again."
                    : "Checking the connection and local storage…"}
              </p>
            </div>
            <button onClick={() => void checkConnection()} disabled={connection === "checking"}>
              {connection === "checking" ? "Checking…" : "Check connection"}
            </button>
          </section>
          <section className="empty-workspace" aria-labelledby="model-heading">
            <svg viewBox="0 0 48 48" width="48" height="48" aria-hidden="true">
              <path d="M8 12h32v24H8z M8 20h32 M18 12v24 M24 27h10 M24 31h6" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
            </svg>
            <h2 id="model-heading">No model available</h2>
            <p>Model import and prediction are not available in this build yet.</p>
            <p className="future-work">Once a validated model is available, you’ll be able to inspect graphene masks and rank images by few-layer coverage.</p>
          </section>
          <footer className="workspace-footer">Workspace files stay on this computer.</footer>
        </main>
      </div>
    </div>
  );
}
