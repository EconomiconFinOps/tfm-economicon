import { Database } from "lucide-react";

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isoDate(value: unknown): value is string {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)
    && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
}

interface CostRecord {
  id: string;
  kind: "cost_query";
  title: string;
  source: "billing-summary-v2";
  data_status: "available" | "partial" | "empty";
  period: { start_date: string; end_date: string; timezone: "UTC" };
  metrics: { name: "total_cost"; value: string; unit: string }[];
}

function isRecord(value: unknown): value is CostRecord {
  return object(value) && typeof value.id === "string" && value.id.startsWith("cost:")
    && value.kind === "cost_query" && value.source === "billing-summary-v2"
    && typeof value.title === "string" && ["available", "partial", "empty"].includes(String(value.data_status))
    && object(value.period) && isoDate(value.period.start_date) && isoDate(value.period.end_date)
    && value.period.start_date < value.period.end_date && value.period.timezone === "UTC"
    && Array.isArray(value.metrics) && value.metrics.every(metric => object(metric)
      && metric.name === "total_cost" && typeof metric.value === "string"
      && /^-?(0|[1-9][0-9]*)\.\d+$/.test(metric.value)
      && typeof metric.unit === "string" && /^[A-Z]{3}$/.test(metric.unit));
}

export function ChatCostEvidence({ records }: { records: unknown }) {
  if (!Array.isArray(records) || records.length === 0) return null;
  if (records.length > 20 || !records.every(isRecord)
    || new Set(records.map(item => item.id)).size !== records.length) {
    return <p className="mt-2 text-xs text-muted-foreground">La evidencia de costes de esta respuesta no está disponible.</p>;
  }
  return <section aria-label="Evidencia de costes" className="mt-2 text-xs text-muted-foreground">
    {records.map(record => <details key={record.id} className="mt-1">
      <summary className="cursor-pointer"><Database size={15} aria-hidden="true" className="mr-2 inline-block align-middle" />
        Evidencia de costes contrastada</summary>
      <p className="mt-1">{record.period.start_date} a {record.period.end_date} UTC (fin excluido).</p>
      {record.metrics.map(metric => <p key={metric.unit}>{metric.value} {metric.unit}</p>)}
      <p>{record.data_status === "empty" ? "Sin registros; no equivale a gasto cero."
        : record.data_status === "partial" ? "Datos parciales." : "Ingestas Azure completadas."}</p>
      <p className="break-all">{record.id}</p>
    </details>)}
  </section>;
}
