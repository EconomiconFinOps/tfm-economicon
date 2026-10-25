// IngestPage: en la nueva arquitectura de rutas (JUP-095, grupo 6, sub-ronda
// c -- ver Addendum de design.md) deja de recibir `token`/`activeTenant` como
// props desde `App.jsx` y pasa a leerlos via
// `useOutletContext<SessionOutletContext>()`, igual que ya hace `LoginPage`
// para su propia migracion. La logica del formulario (estado, mutacion,
// handleSubmit, guarda de tenant requerido) se conserva verbatim del origen
// (`IngestPage.jsx`); solo cambian el origen de `token`/`activeTenant` y la
// presentacion (Tailwind + SectionCard reconstruido).
import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useOutletContext } from "react-router";
import { DocumentUploadPanel } from "../components/DocumentUploadPanel";
import { SectionCard } from "../components/SectionCard";
import { createDocumentTransport, createIngestJob } from "../services/api";
import type { IngestJobRequest } from "../services/contracts";
import type { SessionOutletContext } from "../layouts/SessionGate";

// Estado del formulario, verbatim de IngestPage.jsx: mismos tres campos y
// mismos valores por defecto.
interface IngestFormState {
  source: string;
  artifact_uri: string;
  text_content: string;
}

export function IngestPage() {
  const { token, activeTenant } = useOutletContext<SessionOutletContext>();

  const tenantId = activeTenant?.id;
  const documentTransport = useMemo(() => tenantId ? createDocumentTransport(token, tenantId) : null, [token, tenantId]);

  const [form, setForm] = useState<IngestFormState>({
    source: "aws-cur",
    artifact_uri: "",
    text_content: ""
  });

  const mutation = useMutation({
    mutationFn: (payload: IngestJobRequest) => {
      if (!activeTenant) {
        throw new Error("Tenant required");
      }
      return createIngestJob(token, activeTenant.id, payload);
    }
  });

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeTenant) {
      return;
    }
    mutation.mutate({
      tenant_id: activeTenant.id,
      source: form.source,
      artifact_uri: form.artifact_uri || null,
      text_content: form.text_content,
      metadata: {}
    });
  }

  if (!activeTenant) {
    return (
      <SectionCard
        title="Cliente requerido"
        subtitle="Elige un cliente antes de encolar trabajos de ingesta."
      >
        <p className="text-sm text-muted-foreground">No hay ningún cliente activo.</p>
      </SectionCard>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <DocumentUploadPanel key={`${token}:${activeTenant.id}`} transport={documentTransport!} />
      <SectionCard
        title="Crear trabajo de ingesta"
        subtitle="El backend crea el trabajo en CockroachDB y lo publica en RabbitMQ."
      >
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted-foreground" htmlFor="ingest-source">
              Origen
            </label>
            <input
              id="ingest-source"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-highlight"
              value={form.source}
              onChange={(event) =>
                setForm((current) => ({ ...current, source: event.target.value }))
              }
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted-foreground" htmlFor="ingest-artifact-uri">
              URI del artefacto
            </label>
            <input
              id="ingest-artifact-uri"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-highlight"
              placeholder="s3://billing/report.csv"
              value={form.artifact_uri}
              onChange={(event) =>
                setForm((current) => ({ ...current, artifact_uri: event.target.value }))
              }
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted-foreground" htmlFor="ingest-text-content">
              Contenido del texto
            </label>
            <textarea
              id="ingest-text-content"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-highlight"
              rows={10}
              placeholder="Pega el contenido del documento que se dividirá en fragmentos y se vectorizará."
              value={form.text_content}
              onChange={(event) =>
                setForm((current) => ({ ...current, text_content: event.target.value }))
              }
            />
          </div>

          {mutation.error ? (
            <p className="text-sm text-danger">{mutation.error.message}</p>
          ) : null}

          <button
            className="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
            type="submit"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Encolando trabajo..." : "Encolar ingesta"}
          </button>
        </form>
      </SectionCard>

      {mutation.data ? (
        <SectionCard
          title="Trabajo aceptado"
          subtitle="El procesador tratará el documento, generará los embeddings y actualizará el estado del trabajo."
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">ID del trabajo</p>
              <strong className="text-foreground">{mutation.data.job_id}</strong>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Estado</p>
              <strong className="text-foreground">{mutation.data.status}</strong>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Cola</p>
              <strong className="text-foreground">{mutation.data.queue}</strong>
            </div>
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}
