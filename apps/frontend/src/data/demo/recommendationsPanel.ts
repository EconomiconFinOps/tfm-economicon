import type { ImpactReport, Recommendation, RecommendationReport } from "@/services/recommendations";

// Serialized-contract doubles, NOT output observed from a deployed engine.
// Scenarios and difficulty are authored solely to exercise the JUP-058 UI.
// JUP-033 currently emits unknown difficulty and null estimated savings.
const id = (prefix: string, digit: string) => `${prefix}:sha256:${digit.repeat(64)}`;
const period = { start_date: "2026-09-01", end_date: "2026-10-01", timezone: "UTC" } as const;
export const demoRecommendationTenant = "demo-jup058";
const rows: Recommendation[] = [
  { id: id("recommendation", "1"), rule_id: "missing_project", rule_version: 1, category: "tagging", qualification: "supported", action: "Completar la atribución de costes por proyecto", rationale: "Hay costes de Azure sin proyecto asignado. Confirmar su propietario permite mejorar la atribución; etiquetar por sí solo no reduce el consumo.", scope: { dimension: "project", value: null }, observed_cost: { amount: "1840.00", currency: "EUR", record_count: 16 }, estimated_savings: null, currency: null, confidence: "high", risk: "low", difficulty: "low", evidence_ids: [id("evidence", "1")], requires_human_approval: true },
  { id: id("recommendation", "2"), rule_id: "largest_project_cost", rule_version: 1, category: "investigation", qualification: "investigation_candidate", action: "Revisar el consumo de Atlas · producción", rationale: "Atlas concentra el mayor coste de su grupo en la muestra. El coste observado justifica investigar; no demuestra que los recursos estén sobredimensionados.", scope: { dimension: "project", value: "Atlas · producción" }, observed_cost: { amount: "6200.00", currency: "EUR", record_count: 42 }, estimated_savings: null, currency: null, confidence: "medium", risk: "medium", difficulty: "medium", evidence_ids: [id("evidence", "2")], requires_human_approval: true },
  { id: id("recommendation", "3"), rule_id: "largest_project_cost", rule_version: 1, category: "investigation", qualification: "investigation_candidate", action: "Contrastar una alternativa para Atlas", rationale: "El escenario comparte alcance de costes con la revisión de Atlas. Son alternativas: no deben sumarse como oportunidades independientes.", scope: { dimension: "project", value: "Atlas · producción" }, observed_cost: { amount: "6200.00", currency: "EUR", record_count: 42 }, estimated_savings: null, currency: null, confidence: "low", risk: "high", difficulty: "high", evidence_ids: [id("evidence", "3")], requires_human_approval: true },
  { id: id("recommendation", "4"), rule_id: "largest_project_cost", rule_version: 1, category: "investigation", qualification: "investigation_candidate", action: "Investigar el consumo de Boreal", rationale: "El conjunto de muestra incluye un proyecto facturado en USD. Cualquier escenario se mantiene separado de las estimaciones en EUR.", scope: { dimension: "project", value: "Boreal" }, observed_cost: { amount: "2400.00", currency: "USD", record_count: 21 }, estimated_savings: null, currency: null, confidence: "medium", risk: "low", difficulty: "low", evidence_ids: [id("evidence", "4")], requires_human_approval: true },
  { id: id("recommendation", "5"), rule_id: "largest_project_cost", rule_version: 1, category: "investigation", qualification: "investigation_candidate", action: "Recopilar métricas del proyecto Nébula", rationale: "Faltan métricas de uso y un escenario objetivo verificable para estimar el ahorro o la dificultad. No se presupone una reducción de costes.", scope: { dimension: "project", value: "Nébula" }, observed_cost: { amount: "960.00", currency: "EUR", record_count: 8 }, estimated_savings: null, currency: null, confidence: "low", risk: "medium", difficulty: "unknown", evidence_ids: [id("evidence", "5")], requires_human_approval: true },
];
export const demoRecommendationReport: RecommendationReport = {
  contract_version: 1, period, source: "azure_cost_records", cloud: "azure", data_environment: "simulated", data_status: "partial", status: "available",
  recommendations: rows,
  evidence: rows.map(row => ({ id: row.evidence_ids[0], kind: "cost_query", source: "azure_cost_records", query: { period, group_by: "project", tag_key: null }, rule_id: row.rule_id, rule_version: row.rule_version, scope: row.scope, observed_cost: row.observed_cost })),
  total_candidates: rows.length, truncated: false,
  assumptions: ["Muestra estática de interfaz: acciones y dificultad redactadas para demostrar la priorización.", "El coste observado no equivale a un ahorro alcanzable."],
  limitations: ["Los ejemplos son independientes del cliente seleccionado y no provienen de una ejecución real.", "La evaluación de recursos requiere telemetría y revisión de su propietario."],
  not_evaluated: [{ action: "rightsizing", missing_inputs: ["Métricas de utilización", "Validación del propietario"] }],
  missing_dimension_count: 16, excluded_undated_count: 0,
};
const scenarios = [
  { index: 0, baseline: "1840.00", target: "1840.00", monthly: "0.00", annual: "0.00", included: true },
  { index: 1, baseline: "6200.00", target: "5300.00", monthly: "900.00", annual: "10800.00", included: true },
  { index: 2, baseline: "6200.00", target: "5550.00", monthly: "650.00", annual: "7800.00", included: false },
  { index: 3, baseline: "2400.00", target: "2000.00", monthly: "400.00", annual: "4800.00", included: true },
  { index: 4, baseline: null, target: null, monthly: null, annual: null, included: false },
];
export const demoImpactReport: ImpactReport = {
  schema_version: "1.0", tenant_id: demoRecommendationTenant, baseline_month: period.start_date, basis: "caller_supplied_scenario", aggregation_method: "descending_savings_disjoint_scopes",
  recommendations: scenarios.map(item => ({
    scenario: { recommendation_id: rows[item.index].id, cost_scope_ids: [item.index === 2 ? "demo/atlas" : ["demo/untagged", "demo/atlas", "", "demo/boreal", "demo/nebula"][item.index]], currency: rows[item.index].observed_cost.currency, baseline_monthly_cost: item.baseline, target_monthly_cost: item.target, evidence_ids: rows[item.index].evidence_ids, assumptions: ["Escenario hipotético de demostración; costes objetivo facilitados como ejemplo, pendientes de validación."] },
    status: item.monthly === null ? "insufficient_data" : item.monthly === "0.00" ? "no_savings" : "estimated",
    potential_monthly_savings: item.monthly, potential_annual_savings: item.annual, observed_savings: null, included_in_total: item.included, excluded_by: item.index === 2 ? [rows[1].id] : [],
  })),
  totals: [
    { currency: "EUR", potential_monthly_savings: "900.00", potential_annual_savings: "10800.00", included_recommendation_ids: [rows[1].id, rows[0].id], unestimated_recommendation_ids: [rows[4].id], observed_savings: null },
    { currency: "USD", potential_monthly_savings: "400.00", potential_annual_savings: "4800.00", included_recommendation_ids: [rows[3].id], unestimated_recommendation_ids: [], observed_savings: null },
  ],
  assumptions: ["La proyección anual del escenario mantiene las condiciones mensuales durante doce meses."],
  limitations: ["Ninguna estimación es un ahorro realizado o garantizado.", "Los escenarios que comparten alcance no son aditivos; la interfaz conserva las exclusiones del informe."],
};
