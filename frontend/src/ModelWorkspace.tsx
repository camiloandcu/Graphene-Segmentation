import { useCallback, useEffect, useRef, useState } from "react";
import { LocalModel, ModelDetails, Registry, modelRequest } from "./api";

function ModelInfo({ model }: { model: LocalModel }) {
  const [detail, setDetail] = useState<ModelDetails | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const load = async () => {
    setLoading(true);
    setError("");
    try { setDetail(await modelRequest<ModelDetails>(`/${model.model_id}`)); }
    catch (failure) { setError((failure as Error).message); }
    finally { setLoading(false); }
  };
  const evidence = detail?.evaluation.evidence;
  return (
    <details className="model-details" onToggle={(event) => {
      if (event.currentTarget.open && !detail && !loading && !error) void load();
    }}>
      <summary>Model details for {model.name}</summary>
      {loading && <p role="status">Loading model details…</p>}
      {error && <div><p role="alert">{error}</p><button onClick={() => void load()}>Retry details</button></div>}
      {detail && <>
        <dl className="model-facts">
          <div><dt>Model ID</dt><dd>{model.model_id}</dd></div>
          <div><dt>Classes</dt><dd>Background · Few-layer graphene · Bulk graphene</dd></div>
          <div><dt>Operating setting</dt><dd>{detail.manifest.decision.kind === "argmax" ? "Highest-scoring class" : `Few-layer threshold: ${detail.manifest.decision.threshold}`}</dd></div>
          <div><dt>Image geometry</dt><dd>{detail.manifest.geometry.mode === "letterbox" ? "Aspect-preserving letterbox" : "Native-resolution tiles"}</dd></div>
          <div><dt>Compatibility</dt><dd>CPU compatibility checked at import. Selection checks the current runtime again.</dd></div>
          <div><dt>Package SHA-256</dt><dd>{model.bundle_sha256}</dd></div>
          <div><dt>Model SHA-256</dt><dd>{model.model_sha256}</dd></div>
        </dl>
        <h3>Evaluation</h3>
        {evidence?.kind === "unmeasured" ? <p>Unmeasured: {evidence.reason}</p> : <>
          <p>Reported results from {evidence?.source}. These results have not been independently verified by this workspace.</p>
          <ul className="metric-list">{evidence?.metrics?.map((metric, index) => <li key={index}>
            <strong>{metric.name}</strong>: {metric.value === null ? `Unavailable — ${metric.unavailable_reason}` : `${metric.value} ${metric.unit}`}.
            <p>{metric.definition} Support: {metric.support === null ? "unknown" : metric.support}.</p>
          </li>)}</ul>
        </>}
        <details><summary>Training provenance supplied by the exporter</summary><pre>{JSON.stringify(detail.manifest.provenance, null, 2)}</pre></details>
      </>}
    </details>
  );
}

export default function ModelWorkspace({ view }: { view: "workspace" | "models" }) {
  const [registry, setRegistry] = useState<Registry | null>(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState("");
  const [stale, setStale] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const mounted = useRef(true);
  const generation = useRef(0);
  const locked = useRef(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const feedback = useRef<HTMLParagraphElement>(null);

  const refresh = useCallback(async () => {
    const request = ++generation.current;
    setLoading(true);
    try {
      const data = await modelRequest<Registry>("");
      if (mounted.current && request === generation.current) {
        setRegistry(data); setStale(false); setError("");
      }
      return data;
    } catch (failure) {
      if (mounted.current && request === generation.current) {
        setError((failure as Error).message); setStale(true);
      }
      return null;
    } finally {
      if (mounted.current && request === generation.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void refresh();
    const onFocus = () => { if (!locked.current) void refresh(); };
    window.addEventListener("focus", onFocus);
    return () => { mounted.current = false; generation.current++; window.removeEventListener("focus", onFocus); };
  }, [refresh]);

  const mutate = async (kind: "import" | "select", model?: LocalModel) => {
    if (locked.current) return;
    if (kind === "import" && (!file || file.size > 256 * 1024 * 1024)) {
      setError("Choose a compatible model ZIP no larger than 256 MiB.");
      return;
    }
    locked.current = true;
    generation.current++; // Ignore list responses that started before this mutation.
    setPending(kind === "import" ? "Importing and checking the model…" : `Checking and selecting ${model?.name}…`);
    setStatus(""); setError("");
    let failureMessage = "";
    try {
      if (kind === "import") {
        const response = await modelRequest<{ model: LocalModel; created: boolean }>("/import", {
          method: "POST", headers: { "Content-Type": "application/zip" }, body: file,
        });
        setStatus(`${response.model.name} ${response.created ? "saved locally" : "is already imported"}. Selection unchanged. Choose Select model when ready.`);
        setFile(null);
        if (fileInput.current) fileInput.current.value = "";
      } else {
        await modelRequest<Registry>("/selection", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model_id: model?.model_id }) });
        setStatus(`${model?.name} selected and saved locally. Prediction is not available in this build yet.`);
      }
    } catch (failure) { failureMessage = (failure as Error).message; }
    // A response may be lost after commit. Reconcile before asserting the old choice.
    const updated = await refresh();
    if (failureMessage) { setError(failureMessage); setStatus(""); }
    if (!updated) setStatus("");
    setPending(""); locked.current = false;
    feedback.current?.focus();
  };

  const selected = registry?.models.find((model) => model.model_id === registry.selected_model_id);
  const blocked = Boolean(pending) || loading || stale || !registry?.validation_available;
  return (
    <section id={view === "models" ? "models" : "workspace-model"} className="models-section" aria-labelledby="model-heading">
      <div className="models-title"><h2 id="model-heading">{view === "models" ? "Local models" : "Selected model"}</h2>
        <button disabled={Boolean(pending) || loading} onClick={() => void refresh()}>{loading ? "Refreshing…" : "Refresh Models"}</button></div>
      <p role="status" aria-live="polite" tabIndex={-1} ref={feedback} className="model-feedback">{pending || status || (loading ? "Loading local models…" : "")}</p>
      {error && <p role="alert" id="model-error" className="model-error">{error}</p>}
      {stale && registry && <p className="model-error">Showing last confirmed model data. Refresh Models to check the current selection.</p>}
      {!loading && !selected && <p>No model selected. Import a compatible ZIP in Models, then select it.</p>}
      {selected && <div className="selection-summary"><strong>{selected.name}</strong><span>Version {selected.version} · {stale ? "Last confirmed selection" : "Selected"}</span>
        {!selected.available && <p className="model-error">Selected file is missing or damaged. Choose another intact model, or restore a workspace backup. No replacement was selected automatically.</p>}
      </div>}
      <p className="model-note">Models stay on this computer. Prediction is not available in this build yet.</p>
      {view === "models" && <>
        {registry && !registry.validation_available && <div className="runtime-guidance"><h3>Model support needs installation</h3><p>{registry.installation_action}</p><p>Restart the local server, then refresh Models. Stored model details remain available.</p></div>}
        <form className="model-import" onSubmit={(event) => { event.preventDefault(); void mutate("import"); }}>
          <h3>Import a model</h3>
          <label htmlFor="model-file">Model package ZIP</label>
          <p id="package-help">Use a v1 ZIP containing model.onnx, manifest.json and evaluation.json. Maximum 256 MiB. Importing keeps your current selection.</p>
          <input id="model-file" ref={fileInput} type="file" accept=".zip,application/zip" disabled={Boolean(pending)} aria-describedby={error ? "package-help model-error" : "package-help"} onChange={(event) => { setFile(event.target.files?.[0] ?? null); setError(""); }} />
          <button type="submit" disabled={blocked || !file}>Import model</button>
        </form>
        <h3 className="registry-heading">Imported models{registry ? ` (${registry.models.length})` : ""}</h3>
        {!loading && registry?.models.length === 0 && <p>No models imported yet. Choose a compatible ZIP above to get started.</p>}
        <ul className="model-list">{registry?.models.map((model) => <li key={model.model_id}>
          <div className="model-row"><div><h4>{model.name}</h4><p>Version {model.version} · {model.selected ? "Selected" : "Not selected"} · {model.available ? "File available" : "File unavailable"}</p>
            <p>{model.evidence_kind === "unmeasured" ? "Lab performance unmeasured" : "Reported evaluation; not independently verified"}</p></div>
            <button disabled={blocked || !model.available || model.selected} onClick={() => void mutate("select", model)} aria-label={`Select model ${model.name}`}>{model.selected ? "Selected" : "Select model"}</button>
          </div>
          <ModelInfo model={model} />
        </li>)}</ul>
      </>}
    </section>
  );
}
