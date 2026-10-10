import type { ImpactReport, Recommendation, RecommendationDifficulty, RecommendationEvidence, RecommendationImpact, RecommendationReport } from "@/services/recommendations";

export const categoryLabels = { tagging: "Etiquetado", investigation: "Investigación" } as const;
export const difficultyLabels = { low: "Baja", medium: "Media", high: "Alta", unknown: "Por evaluar" } as const;
export type SavingsPeriod = "monthly" | "annual";
export type RecommendationOrder = "savings" | "difficulty";
export interface RecommendationRow extends Recommendation { evidence: RecommendationEvidence[]; impact: RecommendationImpact | null }
export interface RecommendationFilters {
  category: "all" | Recommendation["category"];
  difficulty: "all" | RecommendationDifficulty;
  order: RecommendationOrder;
  period: SavingsPeriod;
}
export const defaultRecommendationFilters: RecommendationFilters = { category: "all", difficulty: "all", order: "savings", period: "monthly" };

// Match scenarios by id AND tenant/month. Do not derive difficulty from risk.
export function recommendationRows(report: RecommendationReport, impact?: ImpactReport, tenantId?: string): RecommendationRow[] {
  if (impact && (impact.tenant_id !== tenantId || impact.baseline_month !== report.period.start_date
    || report.period.start_date.slice(8) !== "01" || report.period.end_date !== nextMonth(report.period.start_date))) {
    throw new Error("El informe de impacto no corresponde al cliente y mes consultados.");
  }
  const impacts = new Map(impact?.recommendations.map(item => [item.scenario.recommendation_id, item]));
  if (impact && impacts.size !== impact.recommendations.length) throw new Error("Informe de impacto con identificadores duplicados.");
  return report.recommendations.map(item => ({ ...item,
    evidence: report.evidence.filter(source => item.evidence_ids.includes(source.id)),
    impact: impacts.get(item.id) ?? null,
  }));
}
function nextMonth(start: string) {
  const value = new Date(start + "T00:00:00Z");
  value.setUTCMonth(value.getUTCMonth() + 1);
  return value.toISOString().slice(0, 10);
}
// Decimal formatting/comparison stays exact beyond Number.MAX_SAFE_INTEGER.
// This does not calculate potential savings or perform currency conversion.
export function compareDecimal(a: string, b: string): number {
  const [ai, af = ""] = a.split("."), [bi, bf = ""] = b.split(".");
  if (BigInt(ai) !== BigInt(bi)) return BigInt(ai) < BigInt(bi) ? -1 : 1;
  const width = Math.max(af.length, bf.length);
  const ax = af.padEnd(width, "0"), bx = bf.padEnd(width, "0");
  return ax === bx ? 0 : ax < bx ? -1 : 1;
}
export function formatDecimal(value: string): string {
  const [whole, fraction] = value.split(".");
  return `${whole.replace(/\B(?=(\d{3})+(?!\d))/g, ".")}${fraction === undefined ? "" : "," + fraction}`;
}
export function savingsAmount(row: RecommendationRow, period: SavingsPeriod): string | null {
  return (period === "monthly" ? row.impact?.potential_monthly_savings : row.impact?.potential_annual_savings) ?? null;
}
const difficultyRank = { low: 0, medium: 1, high: 2, unknown: 3 };
export function filterRecommendations(rows: RecommendationRow[], filters: RecommendationFilters): RecommendationRow[] {
  return rows.filter(row => (filters.category === "all" || row.category === filters.category)
    && (filters.difficulty === "all" || row.difficulty === filters.difficulty))
    .sort((a, b) => {
      if (filters.order === "difficulty") {
        const difficulty = difficultyRank[a.difficulty] - difficultyRank[b.difficulty];
        if (difficulty) return difficulty;
      }
      const av = savingsAmount(a, filters.period), bv = savingsAmount(b, filters.period);
      if (av === null && bv !== null) return 1;
      if (av !== null && bv === null) return -1;
      if (av !== null && bv !== null) {
        const group = (a.impact?.scenario.currency ?? "").localeCompare(b.impact?.scenario.currency ?? "");
        if (group) return group;
        const amount = compareDecimal(bv, av);
        if (amount) return amount;
      }
      return difficultyRank[a.difficulty] - difficultyRank[b.difficulty] || a.id.localeCompare(b.id);
    });
}
function csvCell(value: string) {
  // RFC 4180 quoting plus spreadsheet formula neutralisation; no HTML export.
  const first = Array.from(value).find(character => character.charCodeAt(0) > 31 && !/\s/.test(character));
  const safe = (first !== undefined && "=+-@".includes(first)) || /^[\t\r\n]/.test(value) ? "'" + value : value;
  return '"' + safe.replace(/"/g, '""') + '"';
}
export function recommendationsCsv(rows: RecommendationRow[], report: RecommendationReport, period: SavingsPeriod, source: string, impact?: ImpactReport): string {
  const headers = ["Origen", "Inicio UTC", "Fin exclusivo UTC", "ID", "Tipo", "Acción propuesta", "Justificación", "Dificultad", "Ahorro potencial", "Moneda", "Periodicidad", "Riesgo", "Confianza", "Evidencias", "Requiere aprobación humana", "Incluida en total del informe", "Excluida por", "Supuestos", "Limitaciones", "Base del escenario", "Mes base", "Coste observado", "Moneda del coste observado"];
  const values = rows.map(row => [source, report.period.start_date, report.period.end_date, row.id, categoryLabels[row.category], row.action, row.rationale,
    difficultyLabels[row.difficulty], savingsAmount(row, period) ?? "No estimado", row.impact?.scenario.currency ?? "No disponible", period === "monthly" ? "Mensual" : "Anual",
    difficultyLabels[row.risk], difficultyLabels[row.confidence], row.evidence_ids.join("; "), "Sí", row.impact ? row.impact.included_in_total ? "Sí" : "No" : "No disponible",
    row.impact?.excluded_by.join("; ") ?? "", [...report.assumptions, ...(row.impact?.scenario.assumptions ?? []), ...(impact?.assumptions ?? [])].join("; "), [...report.limitations, ...(impact?.limitations ?? [])].join("; "), impact?.basis ?? "No disponible", impact?.baseline_month ?? "No disponible", row.observed_cost.amount, row.observed_cost.currency]);
  return "\uFEFF" + [headers, ...values].map(row => row.map(csvCell).join(",")).join("\r\n");
}
export function downloadRecommendations(csv: string) {
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "recomendaciones-vista-actual.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
