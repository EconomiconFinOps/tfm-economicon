// JUP-033 contract v1 and JUP-034 proposed schema 1.0. The contracts are
// dependencies, not implementations of either recommendation/impact engine.
export type RecommendationLevel = "low" | "medium" | "high";
export type RecommendationDifficulty = RecommendationLevel | "unknown";
export type RecommendationCategory = "tagging" | "investigation";
export interface RecommendationPeriod { start_date: string; end_date: string; timezone: "UTC" }
export interface RecommendationScope { dimension: "project"; value: string | null }
export interface ObservedCost { amount: string; currency: string; record_count: number }
export interface Recommendation {
  id: string;
  rule_id: "missing_project" | "largest_project_cost";
  rule_version: 1;
  category: RecommendationCategory;
  qualification: "supported" | "investigation_candidate";
  action: string;
  rationale: string;
  scope: RecommendationScope;
  observed_cost: ObservedCost;
  estimated_savings: null;
  currency: null;
  confidence: RecommendationLevel;
  risk: RecommendationLevel;
  difficulty: RecommendationDifficulty;
  evidence_ids: string[];
  requires_human_approval: true;
}
export interface RecommendationEvidence {
  id: string;
  kind: "cost_query";
  source: "azure_cost_records";
  query: { period: RecommendationPeriod; group_by: "project"; tag_key: null };
  rule_id: Recommendation["rule_id"];
  rule_version: 1;
  scope: RecommendationScope;
  observed_cost: ObservedCost;
}
export interface RecommendationReport {
  contract_version: 1;
  period: RecommendationPeriod;
  source: "azure_cost_records";
  cloud: "azure";
  data_environment: "simulated";
  data_status: "available" | "partial" | "empty";
  status: "available" | "insufficient_data";
  recommendations: Recommendation[];
  evidence: RecommendationEvidence[];
  total_candidates: number;
  truncated: boolean;
  assumptions: string[];
  limitations: string[];
  not_evaluated: { action: "rightsizing" | "scheduling" | "orphan_cleanup" | "rate_optimization" | "savings_impact"; missing_inputs: string[] }[];
  missing_dimension_count: number;
  excluded_undated_count: number;
}
export interface ImpactScenario {
  recommendation_id: string;
  cost_scope_ids: string[];
  currency: string;
  baseline_monthly_cost: string | null;
  target_monthly_cost: string | null;
  evidence_ids: string[];
  assumptions: string[];
}
export interface RecommendationImpact {
  scenario: ImpactScenario;
  status: "estimated" | "no_savings" | "insufficient_data";
  potential_monthly_savings: string | null;
  potential_annual_savings: string | null;
  observed_savings: null;
  included_in_total: boolean;
  excluded_by: string[];
}
export interface ImpactReport {
  schema_version: "1.0";
  tenant_id: string;
  baseline_month: string;
  basis: "caller_supplied_scenario";
  aggregation_method: "descending_savings_disjoint_scopes";
  recommendations: RecommendationImpact[];
  totals: {
    currency: string;
    potential_monthly_savings: string | null;
    potential_annual_savings: string | null;
    included_recommendation_ids: string[];
    unestimated_recommendation_ids: string[];
    observed_savings: null;
  }[];
  assumptions: string[];
  limitations: string[];
}

const object = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const count = (v: unknown): v is number => typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
const text = (v: unknown): v is string => typeof v === "string" && v.length > 0;
const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every(text);
const identifier = (v: unknown): v is string => typeof v === "string" && /^[a-z-]+:sha256:[0-9a-f]{64}$/.test(v);
const level = (v: unknown) => v === "low" || v === "medium" || v === "high";
const currency = (v: unknown) => typeof v === "string" && /^[A-Z]{3}$/.test(v);
const date = (v: unknown): v is string => typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v) && !Number.isNaN(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v;
const period = (v: unknown): v is RecommendationPeriod => object(v) && date(v.start_date) && date(v.end_date) && v.start_date < v.end_date && v.timezone === "UTC";
const scope = (v: unknown): v is RecommendationScope => object(v) && v.dimension === "project" && (v.value === null || typeof v.value === "string");
const cost = (v: unknown): v is ObservedCost => object(v) && typeof v.amount === "string" && /^-?(0|[1-9][0-9]*)\.[0-9]{2}$/.test(v.amount) && v.amount !== "-0.00" && currency(v.currency) && count(v.record_count) && v.record_count > 0;
const samePeriod = (a: RecommendationPeriod, b: RecommendationPeriod) => a.start_date === b.start_date && a.end_date === b.end_date && a.timezone === b.timezone;
const sameCost = (a: ObservedCost, b: ObservedCost) => a.amount === b.amount && a.currency === b.currency && a.record_count === b.record_count;

function recommendation(v: unknown): v is Recommendation {
  return object(v) && identifier(v.id) && v.rule_version === 1 && scope(v.scope) && cost(v.observed_cost)
    && ((v.rule_id === "missing_project" && v.category === "tagging" && v.qualification === "supported" && v.scope.value === null)
      || (v.rule_id === "largest_project_cost" && v.category === "investigation" && v.qualification === "investigation_candidate" && v.scope.value !== null))
    && text(v.action) && v.action.length <= 500 && text(v.rationale) && v.rationale.length <= 1000
    && v.estimated_savings === null && v.currency === null && level(v.confidence) && level(v.risk)
    && (level(v.difficulty) || v.difficulty === "unknown") && v.requires_human_approval === true
    && Array.isArray(v.evidence_ids) && v.evidence_ids.length === 1 && v.evidence_ids.every(identifier);
}
function evidence(v: unknown): v is RecommendationEvidence {
  return object(v) && identifier(v.id) && v.kind === "cost_query" && v.source === "azure_cost_records"
    && object(v.query) && period(v.query.period) && v.query.group_by === "project" && v.query.tag_key === null
    && (v.rule_id === "missing_project" || v.rule_id === "largest_project_cost") && v.rule_version === 1
    && scope(v.scope) && cost(v.observed_cost);
}

// Validate the HTTP boundary, including evidence linkage. Invalid/foreign
// periods must fail visibly rather than being presented as the current view.
export function isRecommendationReport(v: unknown): v is RecommendationReport {
  if (!(object(v) && v.contract_version === 1 && period(v.period) && v.source === "azure_cost_records"
    && v.cloud === "azure" && v.data_environment === "simulated" && ["available", "partial", "empty"].includes(String(v.data_status))
    && ["available", "insufficient_data"].includes(String(v.status)) && Array.isArray(v.recommendations)
    && v.recommendations.length <= 50 && v.recommendations.every(recommendation)
    && Array.isArray(v.evidence) && v.evidence.length <= 50 && v.evidence.every(evidence)
    && count(v.total_candidates) && typeof v.truncated === "boolean" && strings(v.assumptions) && strings(v.limitations)
    && count(v.missing_dimension_count) && count(v.excluded_undated_count) && Array.isArray(v.not_evaluated)
    && v.not_evaluated.every(item => object(item) && ["rightsizing", "scheduling", "orphan_cleanup", "rate_optimization", "savings_impact"].includes(String(item.action)) && strings(item.missing_inputs) && item.missing_inputs.length > 0))) return false;
  const reportPeriod = v.period;
  const byEvidence = new Map(v.evidence.map(item => [item.id, item]));
  if (byEvidence.size !== v.evidence.length || new Set(v.recommendations.map(item => item.id)).size !== v.recommendations.length
    || v.total_candidates < v.recommendations.length || v.truncated !== (v.total_candidates > v.recommendations.length)
    || (v.status === "insufficient_data" && (v.total_candidates !== 0 || v.evidence.length !== 0))) return false;
  const referenced = new Set<string>();
  return v.recommendations.every(item => item.evidence_ids.every(id => {
    const source = byEvidence.get(id);
    referenced.add(id);
    return source && source.rule_id === item.rule_id && source.rule_version === item.rule_version
      && source.scope.dimension === item.scope.dimension && source.scope.value === item.scope.value
      && sameCost(source.observed_cost, item.observed_cost) && samePeriod(source.query.period, reportPeriod);
  })) && referenced.size === byEvidence.size;
}
