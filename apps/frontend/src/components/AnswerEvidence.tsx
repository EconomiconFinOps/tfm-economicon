import { useId } from "react";
import { FileText } from "lucide-react";
import { AnomalyEvidence } from "./AnomalyEvidence";
import { CostEvidence } from "./CostEvidence";
import * as Dialog from "@radix-ui/react-dialog";

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
  content?: string;
}

function isCitation(value: unknown): value is Citation {
  if (typeof value !== "object" || value === null) return false;
  const item = value as Record<string, unknown>;
  return item.kind === "corpus"
    && ["evidence_id", "document_id", "title", "source", "reference"].every(
      (key) => typeof item[key] === "string" && (item[key] as string).trim().length > 0)
    && typeof item.excerpt === "string"
    && (item.content === undefined || typeof item.content === "string")
    && (item.section === null || typeof item.section === "string")
    && (item.page === null || (typeof item.page === "number" && Number.isInteger(item.page) && item.page > 0));
}

export function AnswerEvidence({ content, metadata }: {
  content: string; metadata: Record<string, unknown>;
}) {
  const prefix = useId();
  const raw = metadata.source_citations;
  const references = metadata.citations;
  const response = metadata.response;
  const body = response && typeof response === "object" && !Array.isArray(response) ? response as Record<string, unknown> : undefined;
  const rawActions = body?.next_actions;
  const rawLimitations = body?.limitations;
  const actions = Array.isArray(rawActions) && rawActions.length <= 10
    && rawActions.every(item => typeof item === "string" && item.trim().length > 0 && item.length <= 500)
    ? rawActions as string[] : [];
  // Server-added notices (for example an omitted, unverified figure) live only in metadata: show them with the answer.
  const limitations = Array.isArray(rawLimitations) && rawLimitations.length <= 10
    && rawLimitations.every(item => typeof item === "string" && item.trim().length > 0 && item.length <= 500)
    ? rawLimitations as string[] : [];
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
    {limitations.length > 0 && <section className="mt-3 text-sm text-muted-foreground" aria-label="Limitaciones">
      <h4 className="font-medium">Limitaciones</h4>
      <ul className="list-disc space-y-1 pl-5">{limitations.map((limitation, index) => <li key={index}>{limitation}</li>)}</ul>
    </section>}
    {actions.length > 0 && <section className="mt-3 text-sm" aria-label="Siguientes pasos">
      <h4 className="font-medium">Siguientes pasos</h4>
      <ul className="list-disc space-y-1 pl-5">{actions.map((action, index) => <li key={index}>{action}</li>)}</ul>
    </section>}
    {citations.length > 0 ? <section className="mt-3 text-muted-foreground" aria-label="Fuentes utilizadas">
      <ul className="m-0 grid list-none gap-1.5 p-0">
        {citations.map((citation, index) => <li key={citation.evidence_id} id={`${prefix}-source-${index + 1}`} tabIndex={-1}
          className="flex min-h-6 items-center gap-2 text-[0.8125rem] focus-visible:outline-2 focus-visible:outline-highlight">
          <FileText size={15} strokeWidth={1.6} className="shrink-0" aria-hidden="true" />
          <Dialog.Root>
            <Dialog.Trigger asChild><button type="button" className="min-w-0 text-left underline [overflow-wrap:anywhere]"
              aria-label={`Abrir fuente ${index + 1}: ${citation.title}`}>
              {citation.title}{citation.source.trim().toLocaleLowerCase() !== citation.title.trim().toLocaleLowerCase() && ` · ${citation.source}`}
            </button></Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 z-50 bg-background/60" />
            <Dialog.Content onEscapeKeyDown={event => event.stopPropagation()}
              className="fixed left-1/2 top-1/2 z-50 grid max-h-[85dvh] w-[calc(100%-2rem)] max-w-2xl -translate-x-1/2 -translate-y-1/2 gap-3 overflow-y-auto rounded-lg border bg-background p-6 shadow-lg">
              <Dialog.Title className="text-lg font-semibold">{citation.title}</Dialog.Title>
              <Dialog.Description className="text-sm text-muted-foreground">{citation.content?.trim()
                ? "Fragmento documental conservado con esta respuesta; no es el documento completo."
                : "Sólo se conserva el extracto de esta respuesta; el fragmento completo no está disponible."}</Dialog.Description>
              <p className="text-sm text-muted-foreground">{citation.source}</p>
              {citation.page !== null && <p className="text-sm">Página: {citation.page}</p>}
              {citation.section !== null && <p className="text-sm">Sección: {citation.section}</p>}
              <blockquote className="whitespace-pre-wrap break-words border-l-2 pl-3 text-sm">
                {citation.content?.trim() ? citation.content : citation.excerpt || "El extracto no está disponible."}
              </blockquote>
              <Dialog.Close className="justify-self-end rounded border px-3 py-2 text-sm">Cerrar fuente</Dialog.Close>
            </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
        </li>)}
      </ul>
    </section> : "cost_evidence" in metadata ? <CostEvidence evidence={metadata.cost_evidence} />
      : "anomaly_evidence" in metadata ? <AnomalyEvidence evidence={metadata.anomaly_evidence} />
      : Array.isArray(references) && references.length > 0 &&
      <p className="mt-2 text-xs text-muted-foreground">La evidencia de esta respuesta no está disponible.</p>}
  </>;
}
