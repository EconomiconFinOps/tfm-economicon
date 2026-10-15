import type { AnomalyDetectionRun, AnomalyEpisode, AnomalyObservation, AnomalySeverity, AnomalyStatus } from "../services/contracts";
import { ApiError } from "../services/api";

export const severityLabels: Record<AnomalySeverity, string> = { P1: "Alta (P1)", P2: "Media (P2)", P3: "Baja (P3)" };
export const statusLabels: Record<AnomalyStatus, string> = {
  new: "Nueva", investigating: "Investigando", resolved: "Resuelta", false_positive: "Falso positivo",
};
export const openStatuses: AnomalyStatus[] = ["new", "investigating"];

export type SeverityFilter = "all" | AnomalySeverity;
export type StatusFilter = "open" | "all" | AnomalyStatus;
export type ObservationFilter = "all" | AnomalyObservation;

export function isOpen(episode: AnomalyEpisode): boolean {
  return openStatuses.includes(episode.status);
}

export function filterEpisodes(episodes: AnomalyEpisode[], severity: SeverityFilter, status: StatusFilter,
  observation: ObservationFilter): AnomalyEpisode[] {
  return episodes.filter((episode) =>
    (severity === "all" || episode.severity === severity)
    && (status === "all" || (status === "open" ? isOpen(episode) : episode.status === status))
    && (observation === "all" || episode.observation === observation));
}

export function dayLabel(isoDate: string): string {
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

export function money(amount: string, currency: string): string {
  return `${amount} ${currency}`;
}

// Amounts arrive as exact two-decimal strings; BigInt keeps cents that Number would lose.
function cents(amount: string): bigint {
  return BigInt(amount.replace(".", ""));
}

function centsText(value: bigint): string {
  const sign = value < 0n ? "-" : "";
  const magnitude = value < 0n ? -value : value;
  return `${sign}${magnitude / 100n}.${String(magnitude % 100n).padStart(2, "0")}`;
}

export function openingExcess(episode: AnomalyEpisode): string {
  return centsText(cents(episode.opening_observed_cost) - cents(episode.reference_daily_cost));
}

export function observationText(episode: AnomalyEpisode): string {
  return episode.observation === "observed" || !episode.no_longer_observed_on
    ? "Se sigue observando" : `Ya no se observa desde ${dayLabel(episode.no_longer_observed_on)}`;
}

// Python's str.strip also removes U+001C-U+001F and U+0085, which String.prototype.trim keeps.
export function trimLikeBackend(reason: string): string {
  const blank = (char: string) => char.trim() === "" || (char >= "\u001c" && char <= "\u001f") || char === "\u0085";
  const chars = [...reason];
  let start = 0;
  let end = chars.length;
  while (start < end && blank(chars[start])) start += 1;
  while (end > start && blank(chars[end - 1])) end -= 1;
  return chars.slice(start, end).join("");
}

// Same rule as the backend: at least one visible character and no control, format or separator characters.
export function validClosingReason(reason: string): boolean {
  const text = trimLikeBackend(reason);
  if (text.length < 1 || text.length > 500) return false;
  if (/[\p{C}\p{Zl}\p{Zp}]/u.test(text)) return false;
  return [...text].some((char) => /[\p{L}\p{N}\p{P}\p{S}]/u.test(char) && !"\u115f\u1160\u3164\uffa0\u2800".includes(char));
}

export function apiErrorCode(error: unknown): string | null {
  if (!(error instanceof ApiError)) return null;
  const match = error.message.match(/"code"\s*:\s*"([a-z_]+)"/);
  return match ? match[1] : null;
}

export function detectionMessage(error: unknown): string {
  const code = apiErrorCode(error);
  if (code === "ambiguous_cost_source") return "Hay fuentes de coste solapadas en esas fechas; no se ha guardado nada.";
  if (code === "detection_conflict") {
    return "Otra detección se estaba ejecutando a la vez; no se ha guardado nada. Vuelve a intentarlo.";
  }
  return "No se ha podido completar la detección.";
}

export function runHeadline(run: AnomalyDetectionRun): string {
  if (run.status === "up_to_date") {
    return `Ya estaba al día: no hay días completos nuevos desde el ${run.last_complete_day ? dayLabel(run.last_complete_day) : "último día revisado"}.`;
  }
  if (run.status === "insufficient_data") return "Aún no hay datos suficientes: hacen falta 8 días seguidos con datos del cliente.";
  return `Detección hecha hasta el ${dayLabel(run.last_complete_day ?? "")} · ${run.evaluated_days.length} días evaluados`;
}

export function runCounts(run: AnomalyDetectionRun): string {
  const plural = (count: number, one: string, many: string) => `${count} ${count === 1 ? one : many}`;
  return `${plural(run.opened, "anomalía nueva", "anomalías nuevas")} · ${plural(run.continued, "sigue activa", "siguen activas")} · `
    + `${run.no_longer_observed} ya no se ${run.no_longer_observed === 1 ? "observa" : "observan"}`;
}

export const skipReasons: Record<"not_observed" | "reference_incomplete", string> = {
  not_observed: "sin datos del cliente ese día",
  reference_incomplete: "sin 7 días previos con datos",
};

export function statusChangeMessage(error: unknown): string {
  const code = apiErrorCode(error);
  if (code === "status_change_conflict") return "Otra persona cambió esta anomalía a la vez. Recárgala para ver su estado actual.";
  if (code === "invalid_status_transition") return "Este cambio de estado ya no es posible. Recarga la anomalía para ver su estado actual.";
  if (code === "anomaly_episode_not_found") return "Esta anomalía ya no está disponible.";
  if (error instanceof ApiError && error.status === 422) return "El motivo no es válido: escribe un texto visible de hasta 500 caracteres.";
  return "No se ha podido cambiar el estado.";
}

export function exportRows(episodes: AnomalyEpisode[], context: { tenantName: string; synthetic: boolean; lastEvaluated: string | null }) {
  return episodes.map((episode) => ({
    Cliente: context.tenantName,
    Origen: context.synthetic ? "Sintéticos" : "Ingesta de costes",
    Criticidad: severityLabels[episode.severity],
    Servicio: episode.service ?? "(sin servicio)",
    Moneda: episode.currency,
    "Impacto acumulado": episode.accumulated_impact,
    "Días con impacto": episode.impact_day_count,
    Inicio: episode.start_date,
    "Última vez vista": episode.last_seen_date,
    Observación: observationText(episode),
    Estado: statusLabels[episode.status],
    "Motivo de cierre": episode.closure_reason ?? "",
    "Revisado hasta": context.lastEvaluated ?? "",
    Reglas: episode.rules_version,
    Naturaleza: "Candidata: causa no establecida",
  }));
}
