// IngestPage: en la nueva arquitectura de rutas (JUP-095, grupo 6, sub-ronda
// c -- ver Addendum de design.md) deja de recibir `token`/`activeTenant` como
// props desde `App.jsx` y pasa a leerlos via
// `useOutletContext<SessionOutletContext>()`, igual que ya hace `LoginPage`
// para su propia migracion. La logica del formulario (estado, mutacion,
// handleSubmit, guarda de tenant requerido) se conserva verbatim del origen
// (`IngestPage.jsx`); solo cambian el origen de `token`/`activeTenant` y la
// presentacion (Tailwind + SectionCard reconstruido).
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useOutletContext } from "react-router";
import { SectionCard } from "../components/SectionCard";
import { createIngestJob } from "../services/api";
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
      <div className="page-content">
        <SectionCard
          headingLevel={1}
          title="Tenant required"
          subtitle="Choose a tenant before enqueuing ingestion jobs."
        >
          <p className="text-sm text-muted-foreground">No active tenant selected.</p>
        </SectionCard>
      </div>
    );
  }

  return (
    <div className="page-content flex flex-col gap-6">
      <SectionCard
        headingLevel={1}
        title="Create ingestion job"
        subtitle="The backend creates the job in CockroachDB and publishes it to RabbitMQ."
      >
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted-foreground" htmlFor="ingest-source">
              Source
            </label>
            <input
              id="ingest-source"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary"
              value={form.source}
              onChange={(event) =>
                setForm((current) => ({ ...current, source: event.target.value }))
              }
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted-foreground" htmlFor="ingest-artifact-uri">
              Artifact URI
            </label>
            <input
              id="ingest-artifact-uri"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary"
              placeholder="s3://billing/report.csv"
              value={form.artifact_uri}
              onChange={(event) =>
                setForm((current) => ({ ...current, artifact_uri: event.target.value }))
              }
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted-foreground" htmlFor="ingest-text-content">
              Text content
            </label>
            <textarea
              id="ingest-text-content"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary"
              rows={10}
              placeholder="Paste the document content to be chunked and embedded."
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
            {mutation.isPending ? "Queueing job..." : "Queue ingestion"}
          </button>
        </form>
      </SectionCard>

      {mutation.data ? (
        <SectionCard
          title="Job accepted"
          subtitle="The worker will process the document, generate embeddings and update the job status."
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Job ID</p>
              <strong className="break-all text-foreground">{mutation.data.job_id}</strong>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Status</p>
              <strong className="break-all text-foreground">{mutation.data.status}</strong>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Queue</p>
              <strong className="break-all text-foreground">{mutation.data.queue}</strong>
            </div>
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}
