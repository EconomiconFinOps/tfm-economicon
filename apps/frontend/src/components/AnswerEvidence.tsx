import { useId } from "react";
import { FileText } from "lucide-react";
import { AnomalyEvidence } from "./AnomalyEvidence";
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
              if (target instanceof HTMLElement) {
                event.preventDefault();
                target.focus();
              }
            }}>
            [{number}]
          </a>{" "}{line.slice(match![0].length)}
        </> : line}</p>;
      })}
    </div>
    {citations.length > 0 ? <section className="mt-3 text-muted-foreground" aria-label="Fuentes utilizadas">
      <ul className="m-0 grid list-none gap-1.5 p-0">
        {citations.map((citation, index) => <li key={citation.evidence_id} id={`${prefix}-source-${index + 1}`} tabIndex={-1}
          className="flex min-h-6 items-center gap-2 text-[0.8125rem] focus-visible:outline-2 focus-visible:outline-highlight">
          <FileText size={15} strokeWidth={1.6} className="shrink-0" aria-hidden="true" />
          <span className="min-w-0 [overflow-wrap:anywhere]">{citation.title}
            {citation.source.trim().toLocaleLowerCase() !== citation.title.trim().toLocaleLowerCase() && ` · ${citation.source}`}</span>
        </li>)}
      </ul>
    </section> : "cost_evidence" in metadata ? <CostEvidence evidence={metadata.cost_evidence} />
      : "anomaly_evidence" in metadata ? <AnomalyEvidence evidence={metadata.anomaly_evidence} />
      : Array.isArray(references) && references.length > 0 &&
      <p className="mt-2 text-xs text-muted-foreground">La evidencia de esta respuesta no está disponible.</p>}
  </>;
}
