import { severityLabels, statusLabels } from "../lib/anomalyPanel";
import { isAnomalyEvidence } from "../services/contracts";

// Mismo texto que usa el resto de bloques de evidencia cuando el contrato no se entiende.
const NOT_AVAILABLE = "La evidencia de esta explicación no está disponible.";

export function AnomalyEvidence({ evidence }: { evidence: unknown }) {
  // Los metadatos del mensaje no son fiables: si el validador no entiende el contrato (versión, formato,
  // coherencia con el episodio...) no se pinta ninguna cifra, igual que CostEvidence. Preferimos avisar a
  // mostrar una foto que pueda mezclar datos de dos momentos.
  if (!isAnomalyEvidence(evidence)) {
    return <p className="mt-2 text-xs text-muted-foreground">{NOT_AVAILABLE}</p>;
  }
  const { episode, opening, impact, operands, source } = evidence;
  const currency = episode.currency;
  const severity = severityLabels[episode.severity];
  // Aquí NO se calcula nada (ni sumas, restas, redondeos ni conversiones a Number): las cifras ya vienen
  // calculadas por el backend con Decimal y se muestran como la cadena guardada. Recalcular en el cliente
  // duplicaría la regla y, con importes grandes, perdería dígitos.
  // Solo el 1 es singular; el 0 se escribe en plural («0 días»).
  const days = `${impact.day_count} ${impact.day_count === 1 ? "día" : "días"}`;
  // El servicio y las limitaciones salen de datos del cliente: se pintan siempre como texto de React
  // (nunca como HTML en bruto) para que un nombre hostil no cree elementos.
  const service = episode.service ?? "sin servicio informado";
  return <details className="mt-3 rounded border border-border p-2 text-sm text-subtle-foreground">
    <summary className="cursor-pointer font-semibold text-foreground">{`Evidencia de la anomalía — ${severity}`}</summary>
    <p className="mt-2 break-all">{`Identificador: ${evidence.id}`}</p>
    {/* La hora se muestra tal como llega: el backend escribe +00:00 y otras APIs escriben Z; ambas valen. */}
    <p>{`Fotografía tomada el ${evidence.explained_at} (UTC).`}</p>
    <p className="break-words">{`Servicio: ${service} · Moneda: ${currency}`}</p>
    <p>{`Estado: ${statusLabels[episode.status]}`}</p>
    <p>{`Regla ${source.rules_version}: más de ${opening.absolute_threshold} ${currency} y más de un ${opening.relative_threshold_percent} % sobre la referencia, las dos a la vez.`}</p>
    <p>{`Día de apertura ${episode.start_date}: observado ${opening.observed_cost} ${currency}, referencia diaria ${opening.reference_daily_cost} ${currency}. Subida ${opening.absolute_increase} ${currency} (${opening.relative_increase_percent} %).`}</p>
    <p>{`Impacto acumulado: ${impact.accumulated_impact} ${currency} en ${days}, hasta ${impact.through_date}.`}</p>
    <p>{`Criticidad: ${severity} (tramo ${impact.severity_band}).`}</p>
    <p>Candidata: causa no establecida.</p>
    {evidence.rounding_notes.length > 0 && <p className="mt-2">
      Algunas cifras se muestran redondeadas a dos decimales; los valores exactos cumplen la regla y están en los operandos.
    </p>}
    {evidence.includes_synthetic_data && <p className="mt-2">Los datos de este cliente incluyen datos sintéticos de demostración.</p>}
    <details className="mt-2 rounded border border-border p-2">
      <summary className="cursor-pointer">Operandos exactos</summary>
      <p>{`Referencia de 7 días: ${operands.reference_seven_day_total}`}</p>
      <p>{`Observado el día de apertura: ${operands.opening_observed_cost}`}</p>
      <p>{`Impacto acumulado × 7: ${operands.accumulated_impact_times_seven}`}</p>
    </details>
    {/* Se leen las limitaciones de la evidencia, no las del episodio embebido: cada fuente trae su texto. */}
    {evidence.limitations.length > 0 && <ul className="mt-2 list-inside list-disc" aria-label="Limitaciones">
      {evidence.limitations.map((limitation, index) => <li key={index}>{limitation}</li>)}
    </ul>}
  </details>;
}
