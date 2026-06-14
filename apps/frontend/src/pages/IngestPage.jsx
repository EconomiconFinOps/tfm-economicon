import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { SectionCard } from "../components/SectionCard";
import { createIngestJob } from "../services/api";

export function IngestPage({ token, activeTenant }) {
  const [form, setForm] = useState({
    source: "aws-cur",
    artifact_uri: "",
    text_content: ""
  });

  const mutation = useMutation({
    mutationFn: (payload) => createIngestJob(token, activeTenant.id, payload)
  });

  function handleSubmit(event) {
    event.preventDefault();
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
        title="Tenant required"
        subtitle="Choose a tenant before enqueuing ingestion jobs."
      >
        <p>No active tenant selected.</p>
      </SectionCard>
    );
  }

  return (
    <div className="page-stack">
      <SectionCard
        title="Create ingestion job"
        subtitle="The backend creates the job in CockroachDB and publishes it to RabbitMQ."
      >
        <form className="form-stack" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="ingest-source">Source</label>
          <input
            id="ingest-source"
            className="text-input"
            value={form.source}
            onChange={(event) => setForm((current) => ({ ...current, source: event.target.value }))}
          />

          <label className="field-label" htmlFor="ingest-artifact-uri">Artifact URI</label>
          <input
            id="ingest-artifact-uri"
            className="text-input"
            placeholder="s3://billing/report.csv"
            value={form.artifact_uri}
            onChange={(event) => setForm((current) => ({ ...current, artifact_uri: event.target.value }))}
          />

          <label className="field-label" htmlFor="ingest-text-content">Text content</label>
          <textarea
            id="ingest-text-content"
            className="text-area"
            rows={10}
            placeholder="Paste the document content to be chunked and embedded."
            value={form.text_content}
            onChange={(event) => setForm((current) => ({ ...current, text_content: event.target.value }))}
          />

          {mutation.error ? <p className="error-copy">{mutation.error.message}</p> : null}

          <button className="primary-button" type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Queueing job..." : "Queue ingestion"}
          </button>
        </form>
      </SectionCard>

      {mutation.data ? (
        <SectionCard
          title="Job accepted"
          subtitle="The worker will process the document, generate embeddings and update the job status."
        >
          <div className="result-grid">
            <div>
              <p className="result-label">Job ID</p>
              <strong>{mutation.data.job_id}</strong>
            </div>
            <div>
              <p className="result-label">Status</p>
              <strong>{mutation.data.status}</strong>
            </div>
            <div>
              <p className="result-label">Queue</p>
              <strong>{mutation.data.queue}</strong>
            </div>
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}
