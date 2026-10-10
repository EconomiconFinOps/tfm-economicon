import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ApiError, fetchTagCoverage, getSessionGeneration } from "@/services/api";

interface Props {
  token: string;
  tenantId?: string;
  period: { start_date: string; end_date: string };
}

export function TagCoveragePanel({ token, tenantId, period }: Props) {
  const [open, setOpen] = useState(false);
  const valid = Boolean(token && tenantId && period.start_date && period.end_date
    && period.start_date < period.end_date);
  const query = useQuery({
    queryKey: ["tag-coverage", tenantId, 1, getSessionGeneration(), period.start_date, period.end_date],
    queryFn: ({ signal }) => {
      if (!tenantId) throw new Error("Tenant required");
      return fetchTagCoverage(token, tenantId, period, signal);
    },
    enabled: open && valid,
    retry: (count, error) => !(error instanceof ApiError && [400, 401, 403, 409, 422].includes(error.status))
      && count < 2
  });
  const coverage = valid && !query.isFetching && !query.isError ? query.data : undefined;
  const overlap = query.error instanceof ApiError && query.error.status === 409;
  return <details className="rounded-lg border border-border bg-card p-4"
    onToggle={(event) => setOpen(event.currentTarget.open)}>
    <summary className="cursor-pointer font-semibold text-foreground">Cobertura de etiquetas FinOps</summary>
    {open && <section aria-label="Cobertura de etiquetas" className="mt-4 space-y-4 text-sm text-subtle-foreground">
      <p>Se requieren owner, environment, application, cost_center y project.
        Una etiqueta incompleta hace que todo el coste del registro no cumpla.</p>
      <p>Cobertura del coste positivo observado antes de impuestos. Los ajustes negativos se muestran aparte.
        Se validan identificadores y entornos; la pertenencia a catálogos de la organización no se verifica.</p>
      <p>Importes redondeados a dos decimales; los subtotales pueden diferir por redondeo.</p>
      {!valid ? <p role="status">Selecciona un cliente y un periodo válido.</p>
        : query.isError ? <p role="alert">{overlap
          ? "Posible solapamiento de fuentes: cobertura no disponible."
          : "Error al cargar la cobertura. Datos no disponibles."}</p>
          : !coverage ? <p role="status">Cargando cobertura...</p> : <>
            <p>{coverage.period.start_date} a {coverage.period.end_date} (fin exclusivo), UTC</p>
            {coverage.excluded_undated_count > 0 && <p role="status">
              Datos parciales: {coverage.excluded_undated_count} registros sin fecha excluidos.</p>}
            {coverage.currencies.length === 0 && <p role="status">Sin datos de costes para este periodo. Cobertura: N/D.</p>}
            <div className="grid gap-4 lg:grid-cols-2">
              {coverage.currencies.map((c) => <article key={c.currency} className="min-w-0 space-y-2 rounded-md border border-border p-4 [overflow-wrap:anywhere]">
                <h3 className="font-semibold text-foreground">{c.currency}</h3>
                <p>Cumple: <strong>{c.compliant_percent === null ? "N/D" : `${c.compliant_percent}%`}</strong>
                  {" · "}No cumple: <strong>{c.noncompliant_percent === null ? "N/D" : `${c.noncompliant_percent}%`}</strong></p>
                {c.no_positive_cost_reason && <p role="status">{c.no_positive_cost_reason === "zero_cost_only"
                  ? "Solo costes cero; no hay cargos positivos."
                  : "Solo ajustes negativos y posibles costes cero; no hay cargos positivos."}</p>}
                <dl className="space-y-1 tabular-nums">
                  <div><dt className="inline">Coste positivo: </dt><dd className="inline">{c.positive_cost} {c.currency}</dd></div>
                  <div><dt className="inline">Coste que cumple: </dt><dd className="inline">{c.compliant_cost} {c.currency}</dd></div>
                  <div><dt className="inline">Coste que no cumple: </dt><dd className="inline">{c.noncompliant_cost} {c.currency}</dd></div>
                  <div><dt className="inline">Ajustes negativos: </dt><dd className="inline">{c.negative_adjustments} {c.currency}</dd></div>
                  <div><dt className="inline">Neto: </dt><dd className="inline">{c.net_cost} {c.currency}</dd></div>
                  <div><dt className="inline">Neto que cumple: </dt><dd className="inline">{c.compliant_net_cost} {c.currency}</dd></div>
                  <div><dt className="inline">Neto que no cumple: </dt><dd className="inline">{c.noncompliant_net_cost} {c.currency}</dd></div>
                </dl>
                <p>{c.compliant_record_count} de {c.record_count} registros cumplen.</p>
                <p>Etiquetas ausentes o inválidas (los recuentos pueden solaparse):</p>
                <ul className="list-inside list-disc">{coverage.required_tags.map((tag) =>
                  <li key={tag}>{tag}: {c.missing_or_invalid_tag_counts[tag]}</li>)}</ul>
              </article>)}
            </div>
          </>}
    </section>}
  </details>;
}
