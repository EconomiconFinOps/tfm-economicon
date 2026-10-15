import { useCallback, useEffect, useRef, useState } from "react";
import { SectionCard } from "./SectionCard";

import type { DocumentTransport, UploadStatus } from "../services/document-contracts";
export type { DocumentTransport, UploadTicket, UploadStatus } from "../services/document-contracts";
type Item = { id: number; file: File; state: string; progress: number; error?: string; uploadId?: string; jobId?: string; duplicate?: boolean; forceRetry?: boolean };
const MAX_BYTES = 20_000_000;
const POLLING_ERROR = "No se ha podido actualizar el estado. Se volverá a consultar.";
const allowed = /\.(md|txt|pdf|docx|doc)$/i;
const labels: Record<string, string> = {
  selected: "Pendiente de subida", hashing: "Comprobando archivo", uploading: "Subiendo",
  confirming: "Subido · pendiente de confirmación", publish_pending: "Pendiente de publicación",
  queued: "Encolado", running: "Procesando", completed: "Completado", failed: "Fallido",
  retry_pending: "Pendiente de reintento de procesamiento",
  expired: "Subida caducada", cancelled: "Subida cancelada"
};
const terminal = new Set(["completed", "failed", "expired", "cancelled"]);

export function DocumentUploadPanel({ transport }: { transport: DocumentTransport }) {
  const [items, setItems] = useState<Item[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const nextId = useRef(0);
  const lifetime = useRef(new AbortController());
  const outstanding = useRef(new Set<string>());
  const active = useRef(false);
  const currentTransport = useRef(transport);
  currentTransport.current = transport;
  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    const api = currentTransport.current;
    const uploads = outstanding.current;
    return () => {
      controller.abort();
      uploads.forEach((id) => { void api.cancel(id).catch(() => {}); });
    };
  }, []);

  const patch = useCallback((id: number, update: Partial<Item>) => {
    if (!lifetime.current.signal.aborted) setItems((previous) => previous.map((item) => item.id === id ? { ...item, ...update } : item));
  }, []);
  function select(files: File[]) {
    if (active.current) return;
    if (files.length !== 1) {
      setError("Selecciona un solo archivo por envío.");
      return;
    }
    if (items.some((item) => item.uploadId && !item.jobId && !terminal.has(item.state))) return;
    setError("");
    setItems(files.map((file) => ({
      id: ++nextId.current, file, state: "selected", progress: 0,
      error: !allowed.test(file.name) ? "Formato no admitido. Usa MD, TXT, PDF, DOCX o DOC."
        : file.size === 0 ? "El archivo está vacío." : file.size > MAX_BYTES ? "El archivo supera los 20 MB (20.000.000 bytes)." : undefined
    })));
  }
  const applyStatus = useCallback((id: number, result: UploadStatus) => {
    patch(id, { state: result.retry_pending ? "retry_pending" : result.job_status ?? result.status, jobId: result.job_id ?? undefined, duplicate: result.duplicate });
  }, [patch]);

  useEffect(() => {
    const pending = items.filter((item) => item.uploadId && item.jobId && !terminal.has(item.state));
    if (!pending.length) return;
    const controller = new AbortController();
    let pendingPoll = false;
    const timer = window.setInterval(() => {
      if (pendingPoll) return;
      pendingPoll = true;
      void Promise.all(pending.map(async (item) => {
        try {
          const result = await currentTransport.current.status(item.uploadId!, controller.signal);
          if (!controller.signal.aborted) {
            applyStatus(item.id, result);
            setError((previous) => previous === POLLING_ERROR ? "" : previous);
          }
        } catch {
          if (!controller.signal.aborted) setError(POLLING_ERROR);
        }
      })).finally(() => { pendingPoll = false; });
    }, 2000);
    return () => { controller.abort(); window.clearInterval(timer); };
  }, [items, applyStatus]);

  async function upload() {
    if (active.current) return;
    active.current = true;
    setBusy(true);
    setError("");
    const signal = lifetime.current.signal;
    for (const item of items.filter((candidate) => candidate.state === "selected" && !candidate.error)) {
      if (signal.aborted) break;
      let uploadId: string | undefined;
      try {
        patch(item.id, { state: "hashing" });
        const bytes = await item.file.arrayBuffer();
        const hash = await crypto.subtle.digest("SHA-256", bytes);
        if (signal.aborted) break;
        const digest = Array.from(new Uint8Array(hash), (value) => value.toString(16).padStart(2, "0")).join("");
        const ticket = await currentTransport.current.begin({ filename: item.file.name, file_size: item.file.size,
          content_hash: digest, force_reprocess: item.forceRetry === true }, signal);
        uploadId = ticket.upload_id;
        if (signal.aborted) {
          void currentTransport.current.cancel(uploadId).catch(() => {});
          break;
        }
        outstanding.current.add(uploadId);
        patch(item.id, { uploadId, state: "uploading" });
        await currentTransport.current.transfer(ticket, item.file, (progress) => patch(item.id, { progress }), signal);
        patch(item.id, { state: "confirming", progress: 100 });
        const result = await currentTransport.current.confirm(uploadId, signal);
        outstanding.current.delete(uploadId);
        applyStatus(item.id, result);
      } catch {
        if (uploadId) {
          outstanding.current.delete(uploadId);
          void currentTransport.current.cancel(uploadId).catch(() => {});
        }
        patch(item.id, { state: "failed", error: "No se ha podido completar la subida. Comprueba la conexión o si tienes otra subida activa." });
      }
    }
    active.current = false;
    if (!signal.aborted) setBusy(false);
  }

  return <SectionCard title="Subir un documento" subtitle="Selecciona o arrastra un archivo. Máximo 20 MB. Una subida a la vez por usuario.">
    <div className="flex flex-col gap-4">
      <div className="rounded-md border border-dashed border-input bg-background p-4"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => { event.preventDefault(); select(Array.from(event.dataTransfer.files)); }}>
        <label className="mb-2 block text-sm text-muted-foreground" htmlFor="document-files">Selecciona o arrastra un archivo aquí</label>
        <input id="document-files" className="block min-w-0 w-full text-sm text-foreground file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-2 file:text-primary-foreground"
          type="file" accept=".md,.txt,.pdf,.docx,.doc" disabled={busy}
          onChange={(event) => { select(Array.from(event.target.files ?? [])); event.target.value = ""; }} />
      </div>
      <p className="text-sm text-muted-foreground">Formatos admitidos: MD, TXT UTF-8, PDF, DOCX y DOC. El documento se procesa en segundo plano después de la transferencia.</p>
      {items.length ? <ul className="flex flex-col gap-3" aria-label="Documentos seleccionados">
        {items.map((item) => <li key={item.id} className="rounded-md border border-border bg-background p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="min-w-0 break-all text-sm font-medium text-foreground">{item.file.name}</span>
            <span className="text-xs text-muted-foreground">{new Intl.NumberFormat("es").format(item.file.size)} bytes</span>
            {!busy && item.state === "selected" ? <button type="button" className="text-sm text-muted-foreground hover:text-foreground"
              aria-label={`Quitar ${item.file.name}`} onClick={() => setItems((previous) => previous.filter((entry) => entry.id !== item.id))}>Quitar</button> : null}
          </div>
          <p className="mt-2 text-sm text-muted-foreground" role="status">{labels[item.state] ?? "Pendiente"}{item.duplicate ? " · Documento ya existente" : ""}</p>
          {item.state === "uploading" ? <progress className="mt-2 h-2 w-full accent-foreground" max={100} value={item.progress} aria-label={`Progreso de ${item.file.name}`} /> : null}
          {item.jobId ? <p className="mt-1 break-all text-xs text-muted-foreground">Trabajo: {item.jobId}</p> : null}
          {item.error ? <p className="mt-2 text-sm text-danger">{item.error}</p> : null}
          {!busy && item.state === "failed" ? <button type="button" className="mt-2 text-sm text-foreground underline"
            onClick={() => patch(item.id, { state: "selected", error: undefined, forceRetry: Boolean(item.jobId), uploadId: undefined, jobId: undefined, progress: 0 })}>{item.jobId ? "Reintentar procesamiento de" : "Reintentar"} {item.file.name}</button> : null}
        </li>)}
      </ul> : null}
      {error ? <p className="text-sm text-danger" role="alert">{error}</p> : null}
      <button type="button" className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
        disabled={busy || !items.some((item) => item.state === "selected" && !item.error)} onClick={() => { void upload(); }}>
        {busy ? "Subiendo documento..." : "Subir archivo"}
      </button>
    </div>
  </SectionCard>;
}
