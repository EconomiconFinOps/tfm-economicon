import { useId } from "react";
import { CostEvidence } from "./CostEvidence";

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
  const cost = metadata.cost_evidence;
  const costId = typeof cost === "object" && cost !== null && "id" in cost
    && typeof cost.id === "string" && /^cost:[a-f0-9]{64}$/.test(cost.id) ? cost.id : null;
  const evidenceIds = citations.length ? citations.map((citation) => citation.evidence_id) : costId ? [costId] : [];

  return <>
    {metadata.generation === "mock" && <p className="text-xs text-muted-foreground">Modo de demostración: respuesta de plantilla, sin modelo generativo.</p>}
    {metadata.answer_status === "insufficient_data" && <p className="text-sm font-medium" role="status">Evidencia insuficiente</p>}
    <div className="mt-1 whitespace-pre-wrap break-words text-sm text-foreground">
      {content.split("\n").map((line, index) => {
        const claim = Array.isArray(metadata.claims) ? metadata.claims[index] as unknown : null;
        if (metadata.generation === "litellm" && typeof claim === "object" && claim !== null) {
          const record = claim as Record<string, unknown>;
          const ids = record.evidence_ids;
          const valid = typeof record.text === "string" && Array.isArray(ids) && ids.length > 0
            && ids.every((id: unknown) => evidenceIds.some((evidenceId) => evidenceId === id));
          const numbers = valid ? ids.map((id: unknown) => evidenceIds.findIndex((evidenceId) => evidenceId === id) + 1) : [];
          if (valid && line === `${record.text} ${numbers.map((n: number) => `[${n}]`).join(" ")}`) {
            return <p key={index}>{record.text as string}{" "}{numbers.map((number: number) =>
              <a key={number} href={`#${prefix}-source-${number}`} aria-label={`Ver fuente ${number}`}
                className="mr-1 text-info-foreground underline" onClick={(event) => {
                  const target = event.currentTarget.ownerDocument.getElementById(`${prefix}-source-${number}`);
                  const details = target instanceof HTMLDetailsElement ? target : target?.querySelector("details");
                  if (details instanceof HTMLDetailsElement) {
                    event.preventDefault(); details.open = true; details.querySelector("summary")?.focus();
                  }
                }}>[{number}]</a>)}</p>;
          }
        }
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
    {citations.length > 0 ? <section className="mt-3 space-y-2 text-sm text-subtle-foreground" aria-label="Fuentes utilizadas">
      <h3 className="font-semibold text-foreground">Fuentes utilizadas</h3>
      {citations.map((citation, index) => <details key={citation.evidence_id} id={`${prefix}-source-${index + 1}`} className="rounded border border-border p-2">
        <summary className="cursor-pointer">[{index + 1}] {citation.title} — {citation.source}</summary>
        <p>Documento: {citation.document_id}</p>
        {citation.section && <p>Sección: {citation.section}</p>}
        {citation.page !== null && <p>Página: {citation.page}</p>}
        <p className="break-all">Referencia: {citation.reference}</p>
        <blockquote className="mt-2 whitespace-pre-wrap border-l-2 border-info pl-3">{citation.excerpt}</blockquote>
        {metadata.generation === "litellm" && Array.isArray(metadata.claims) && metadata.claims.flatMap((claim: unknown, claimIndex: number) => {
          if (typeof claim !== "object" || claim === null || !("support" in claim) || !Array.isArray(claim.support)) return [];
          return claim.support.flatMap((support: unknown, supportIndex: number) => {
            if (typeof support !== "object" || support === null || !("id" in support) || support.id !== citation.evidence_id
              || !("quote" in support) || typeof support.quote !== "string") return [];
            return <blockquote key={`${citation.evidence_id}-${claimIndex}-${supportIndex}`} className="mt-2 whitespace-pre-wrap break-words border-l-2 border-info pl-3">{support.quote}</blockquote>;
          });
        })}
      </details>)}
    </section> : "cost_evidence" in metadata ? <div id={`${prefix}-source-1`}><CostEvidence evidence={metadata.cost_evidence} /></div> : <p className="mt-2 text-xs text-muted-foreground">
      {Array.isArray(references) && references.length > 0
        ? "La evidencia de esta respuesta no está disponible."
        : "Sin fuentes documentales utilizadas."}
    </p>}
  </>;
}
