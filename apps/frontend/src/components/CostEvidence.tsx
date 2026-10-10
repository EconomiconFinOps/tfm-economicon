import { isBillingSummary } from "../services/contracts";

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isoDate(value: unknown): value is string {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)
    && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
}

function isProvenance(value: unknown): value is {
  ingestion_ids: string[]; observed_day_count: number; first_usage_date: string | null; last_usage_date: string | null;
} {
  return object(value) && Array.isArray(value.ingestion_ids)
    && value.ingestion_ids.every((id) => typeof id === "string" && id.trim().length > 0 && id.length <= 256)
    && typeof value.observed_day_count === "number" && Number.isSafeInteger(value.observed_day_count) && value.observed_day_count >= 0
    && (value.first_usage_date === null || isoDate(value.first_usage_date))
    && (value.last_usage_date === null || isoDate(value.last_usage_date));
}

const statusLabels = {
  ok: "Datos disponibles",
  partial: "Datos parciales",
  no_data: "Sin datos para la selección",
  insufficient_data: "Datos insuficientes para esta dimensión"
};

interface EvidenceGroup {
  value: string | null;
  currency: string;
  cost: string;
  record_count: number;
}

function isGroup(value: unknown): value is EvidenceGroup {
  return object(value) && (value.value === null || typeof value.value === "string")
    && typeof value.currency === "string" && value.currency.trim().length > 0
    && typeof value.cost === "string" && /^-?(0|[1-9][0-9]*)\.[0-9]{2}$/.test(value.cost) && value.cost !== "-0.00"
    && typeof value.record_count === "number" && Number.isSafeInteger(value.record_count) && value.record_count >= 0;
}

export function CostEvidence({ evidence }: { evidence: unknown }) {
  // Display only fields whose contract is understood, never calculate totals
  // here or reinterpret a missing selection as zero cost.
  if (!object(evidence) || evidence.schema_version !== "1.0"
    || evidence.adapter_version !== "ownership-1.0"
    || evidence.source !== "azure_cost_records/completed"
    || typeof evidence.id !== "string" || !/^cost:[a-f0-9]{64}$/.test(evidence.id)
    || typeof evidence.status !== "string" || !Object.hasOwn(statusLabels, evidence.status)
    || !isBillingSummary(evidence.summary)) {
    return <p className="mt-2 text-xs text-muted-foreground">La evidencia de costes de esta respuesta no está disponible.</p>;
  }
  const summary = evidence.summary;
  const provenance = isProvenance(evidence.provenance) ? evidence.provenance : null;
  const groups = Array.isArray(evidence.selected_groups) && evidence.selected_groups.length <= 1000
    && evidence.selected_groups.every(isGroup) ? evidence.selected_groups : null;
  return <details className="mt-3 rounded border border-border p-2 text-sm text-subtle-foreground">
    <summary className="cursor-pointer font-semibold text-foreground">Evidencia de costes — {statusLabels[evidence.status as keyof typeof statusLabels]}</summary>
    <p className="mt-2 break-all">Identificador: {evidence.id}</p>
    <p>Fuente registrada: ingestas Azure completadas.</p>
    <p>Periodo UTC: {summary.period.start_date} a {summary.period.end_date} (fin excluido).</p>
    <p>Registros sin dimensión en el periodo: {summary.missing_dimension_count}.</p>
    <p>Registros sin fecha excluidos del tenant, todas las fechas: {summary.excluded_undated_count}.</p>
    {groups ? <details className="mt-2 rounded border border-border p-2">
      <summary className="cursor-pointer">Todos los grupos seleccionados ({groups.length})</summary>
      {groups.length > 0 ? <div className="mt-2 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <caption className="text-left text-xs text-muted-foreground">Importes de la selección, separados por moneda y sin conversión.</caption>
          <thead><tr><th scope="col">Valor</th><th scope="col">Coste</th><th scope="col">Moneda</th><th scope="col">Registros</th></tr></thead>
          <tbody>{groups.map((group, index) => <tr key={index}>
            <td className="break-words pr-3">{group.value ?? "Sin dimensión"}</td>
            <td className="pr-3">{group.cost}</td><td className="pr-3">{group.currency}</td><td>{group.record_count}</td>
          </tr>)}</tbody>
        </table>
      </div> : <p>Sin grupos en la selección; no equivale a gasto cero.</p>}
    </details> : <p className="mt-2">El desglose guardado no está disponible.</p>}
    {provenance ? <div className="mt-2">
      <p className="font-medium">Procedencia del periodo del tenant (todos los valores y monedas)</p>
      <p>Días con registros observados: {provenance.observed_day_count}.</p>
      <p>Primera fecha de uso: {provenance.first_usage_date ?? "Sin fecha observada"}.</p>
      <p>Última fecha de uso: {provenance.last_usage_date ?? "Sin fecha observada"}.</p>
      <p>Ingestas: {provenance.ingestion_ids.length}.</p>
      {provenance.ingestion_ids.length > 0 && <ul className="list-inside list-disc break-all" aria-label="Identificadores de ingesta">
        {provenance.ingestion_ids.map((id, index) => <li key={`${index}:${id}`}>{id}</li>)}
      </ul>}
    </div> : <p className="mt-2">La procedencia detallada no está disponible.</p>}
    <p className="mt-2">La fuente no confirma cobertura completa, actualidad ni validez de las etiquetas. Entorno de datos no confirmado. Los importes se muestran por moneda, sin conversión.</p>
  </details>;
}
