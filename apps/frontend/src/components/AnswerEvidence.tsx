import { useId } from "react";

interface Citation {
  evidence_id: string;
  kind: "corpus";
  document_id: string;
  title: string;
  source: string;
  reference: string;
  section: string | null;
  page: number | null;
  excerpt: string;
}

function isCitation(value: unknown): value is Citation {
  if (typeof value !== "object" || value === null) return false;
  const item = value as Record<string, unknown>;
  return item.kind === "corpus"
    && ["evidence_id", "document_id", "title", "source", "reference"].every(
      (key) => typeof item[key] === "string" && (item[key] as string).trim().length > 0)
    && typeof item.excerpt === "string"
    && (item.section === null || typeof item.section === "string")
    && (item.page === null || (typeof item.page === "number" && Number.isInteger(item.page) && item.page > 0));
}

export function AnswerEvidence({ content, metadata }: {
  content: string; metadata: Record<string, unknown>;
}) {
  const prefix = useId();
  const raw = metadata.source_citations;
  const references = metadata.citations;
  // Metadata is untrusted; never render partial or ambiguous citation sets.
  const citations = Array.isArray(raw) && raw.every(isCitation)
    && new Set(raw.map((item) => item.evidence_id)).size === raw.length
    && Array.isArray(references) && references.length === raw.length
    && raw.every((item, index) => references[index] === item.evidence_id) ? raw : [];

  return <>
    <div className="mt-1 whitespace-pre-wrap break-words text-sm text-foreground">
      {content.split("\n").map((line, index) => {
        const match = /^- \[(\d+)\] /.exec(line);
        const number = match ? Number(match[1]) : 0;
        const citation = citations[number - 1];
        const supported = citation && line === `- [${number}] ${citation.source}: ${citation.excerpt}`;
        return <p key={index}>{supported ? <>
          <a className="text-info-foreground underline" href={`#${prefix}-source-${number}`} aria-label={`Ver fuente ${number}`}
            onClick={(event) => {
              const target = event.currentTarget.ownerDocument.getElementById(`${prefix}-source-${number}`);
              if (target instanceof HTMLDetailsElement) {
                event.preventDefault();
                target.open = true;
                target.querySelector("summary")?.focus();
              }
            }}>
            [{number}]
          </a>{" "}{line.slice(match![0].length)}
        </> : line}</p>;
      })}
    </div>
    {citations.length > 0 ? <section className="mt-3 space-y-2 break-words text-sm text-subtle-foreground" aria-label="Fuentes utilizadas">
      <h3 className="font-semibold text-brand">Fuentes utilizadas</h3>
      {citations.map((citation, index) => <details key={citation.evidence_id} id={`${prefix}-source-${index + 1}`} className="rounded border border-border p-2">
        <summary className="cursor-pointer">[{index + 1}] {citation.title} — {citation.source}</summary>
        <p>Documento: {citation.document_id}</p>
        {citation.section && <p>Sección: {citation.section}</p>}
        {citation.page !== null && <p>Página: {citation.page}</p>}
        <p className="break-all">Referencia: {citation.reference}</p>
        <blockquote className="mt-2 whitespace-pre-wrap border-l-2 border-info pl-3">{citation.excerpt}</blockquote>
      </details>)}
    </section> : <p className="mt-2 text-xs text-muted-foreground">
      {Array.isArray(references) && references.length > 0
        ? "La evidencia de esta respuesta no está disponible."
        : "Sin fuentes documentales utilizadas."}
    </p>}
  </>;
}
