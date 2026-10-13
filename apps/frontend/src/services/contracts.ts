// Response shapes and request fields from apps/backend/app/schemas.
// Datetimes are serialized as ISO strings; open metadata remains untrusted.
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export function isNonemptyString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

export function isUserProfile(value: unknown): value is UserProfile {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    && "id" in value && isNonemptyString(value.id)
    && "email" in value && isNonemptyString(value.email)
    && "role" in value && isNonemptyString(value.role)
    && "full_name" in value && typeof value.full_name === "string";
}

export function isLoginResponse(value: unknown): value is LoginResponse {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    && "access_token" in value && isNonemptyString(value.access_token)
    && "token_type" in value && value.token_type === "bearer"
    && "user" in value && isUserProfile(value.user);
}

export interface TenantRecord {
  id: string;
  name: string;
  slug: string;
  plan: string;
}

export interface TenantCollection {
  items: TenantRecord[];
}

export type BillingGrouping = "subscription" | "resource_group" | "service" | "project" | "tag";

export interface BillingSelection {
  start_date?: string;
  end_date?: string;
  group_by?: BillingGrouping;
  tag_key?: string;
}

export interface BillingTotal {
  currency: string;
  cost: string;
  record_count: number;
}

export interface BillingGroup extends BillingTotal {
  subscription_id: string | null;
  value: string | null;
}

export interface BillingSummary {
  contract_version: 2;
  period: { start_date: string; end_date: string; timezone: "UTC" };
  group_by: BillingGrouping;
  tag_key: string | null;
  data_status: "available" | "partial" | "empty";
  totals: BillingTotal[];
  groups: BillingGroup[];
  missing_dimension_count: number;
  excluded_undated_count: number;
  monthly_spend: string | null;
  savings_identified: null;
  open_ingestions: number;
  currency: string | null;
}

export function isBillingSummary(value: unknown): value is BillingSummary {
  const object = (item: unknown): item is Record<string, unknown> =>
    typeof item === "object" && item !== null && !Array.isArray(item);
  const nullableString = (item: unknown) => item === null || typeof item === "string";
  const count = (item: unknown) => typeof item === "number" && Number.isSafeInteger(item) && item >= 0;
  const money = (item: unknown) => typeof item === "string" && /^-?(0|[1-9][0-9]*)\.[0-9]{2}$/.test(item) && item !== "-0.00";
  const total = (item: unknown) => object(item) && isNonemptyString(item.currency) && money(item.cost) && count(item.record_count);
  const isoDate = (item: unknown) => typeof item === "string" && /^\d{4}-\d{2}-\d{2}$/.test(item)
    && !Number.isNaN(Date.parse(item)) && new Date(item).toISOString().slice(0, 10) === item;
  return object(value) && value.contract_version === 2
    && object(value.period) && isoDate(value.period.start_date) && isoDate(value.period.end_date)
    && String(value.period.start_date) < String(value.period.end_date) && value.period.timezone === "UTC"
    && ["subscription", "resource_group", "service", "project", "tag"].includes(String(value.group_by))
    && (value.group_by === "tag" ? typeof value.tag_key === "string" && value.tag_key.trim().length > 0 : value.tag_key === null)
    && ["available", "partial", "empty"].includes(String(value.data_status))
    && Array.isArray(value.totals) && value.totals.every(total)
    && Array.isArray(value.groups) && value.groups.every((item) => total(item) && object(item)
      && nullableString(item.subscription_id) && nullableString(item.value))
    && count(value.missing_dimension_count) && count(value.excluded_undated_count)
    && (value.monthly_spend === null || money(value.monthly_spend))
    && nullableString(value.currency) && value.savings_identified === null && count(value.open_ingestions);
}

export interface CurrencyTagCoverage {
  currency: string;
  record_count: number;
  compliant_record_count: number;
  noncompliant_record_count: number;
  positive_cost: string;
  compliant_cost: string;
  noncompliant_cost: string;
  negative_adjustments: string;
  compliant_negative_adjustments: string;
  noncompliant_negative_adjustments: string;
  net_cost: string;
  compliant_net_cost: string;
  noncompliant_net_cost: string;
  compliant_percent: string | null;
  noncompliant_percent: string | null;
  no_positive_cost_reason: "zero_cost_only" | "negative_adjustments_only" | null;
  missing_or_invalid_tag_counts: Record<string, number>;
}

export interface TagCoverage {
  contract_version: 1;
  policy_version: "economicon-minimum-v1";
  required_tags: string[];
  period: BillingSummary["period"];
  data_status: "available" | "partial" | "empty";
  excluded_undated_count: number;
  currencies: CurrencyTagCoverage[];
}

export function isTagCoverage(value: unknown): value is TagCoverage {
  const object = (v: unknown): v is Record<string, unknown> =>
    typeof v === "object" && v !== null && !Array.isArray(v);
  const count = (v: unknown) => typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
  const money = (v: unknown) => typeof v === "string" && /^-?(0|[1-9][0-9]*)\.[0-9]{2}$/.test(v) && v !== "-0.00";
  const percent = (v: unknown) => typeof v === "string" && /^(100\.00|(0|[1-9][0-9]?)\.[0-9]{2})$/.test(v);
  const required = ["owner", "environment", "application", "cost_center", "project"];
  const isoDate = (v: unknown) => typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v)
    && !Number.isNaN(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v;
  return object(value) && value.contract_version === 1 && value.policy_version === "economicon-minimum-v1"
    && Array.isArray(value.required_tags) && JSON.stringify(value.required_tags) === JSON.stringify(required)
    && object(value.period) && isoDate(value.period.start_date) && isoDate(value.period.end_date)
    && String(value.period.start_date) < String(value.period.end_date) && value.period.timezone === "UTC"
    && ["available", "partial", "empty"].includes(String(value.data_status))
    && count(value.excluded_undated_count) && Array.isArray(value.currencies)
    && value.currencies.every((c) => object(c) && isNonemptyString(c.currency)
      && ["record_count", "compliant_record_count", "noncompliant_record_count"].every((key) => count(c[key]))
      && ["positive_cost", "compliant_cost", "noncompliant_cost", "negative_adjustments",
        "compliant_negative_adjustments", "noncompliant_negative_adjustments", "net_cost",
        "compliant_net_cost", "noncompliant_net_cost"].every((key) => money(c[key]))
      && (c.no_positive_cost_reason === null
        ? percent(c.compliant_percent) && percent(c.noncompliant_percent)
        : ["zero_cost_only", "negative_adjustments_only"].includes(String(c.no_positive_cost_reason))
          && c.compliant_percent === null && c.noncompliant_percent === null)
      && object(c.missing_or_invalid_tag_counts)
      && required.every((key) => object(c.missing_or_invalid_tag_counts) && count(c.missing_or_invalid_tag_counts[key])));
}

export interface IngestJobRequest {
  tenant_id: string;
  source: string;
  text_content: string;
  artifact_uri?: string | null;
  metadata?: Record<string, unknown>;
}

export interface IngestJobResponse {
  job_id: string;
  status: string;
  queue: string;
}

export interface ConversationCreateRequest {
  title: string;
}

export interface MessageCreateRequest {
  content: string;
  ownership_query?: OwnershipQuery;
}

export interface OwnershipQuery {
  group_by: "project" | "application" | "owner" | "cost_center" | "tag";
  tag_key?: string;
  value?: string;
  currency?: string;
  start_date?: string;
  end_date?: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  source: string;
  content: string;
  distance: number;
}

export interface MessageRecord {
  id: string;
  role: string;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ConversationRecord {
  id: string;
  tenant_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationCollection {
  items: ConversationRecord[];
}

export interface ConversationDetail {
  conversation: ConversationRecord;
  messages: MessageRecord[];
}

export interface AssistantReply {
  conversation: ConversationRecord;
  user_message: MessageRecord;
  assistant_message: MessageRecord;
  retrieved_context: RetrievedChunk[];
}

export interface HealthResponse {
  status: string;
  services: Record<string, string>;
  checked_at: string;
}

// Operational health has a closed vocabulary and never carries free upstream text.
export const healthComponentIds = ["backend", "database", "rabbitmq", "processor", "vector_store", "azure_cost_api", "litellm", "openrouter"] as const;
export type HealthComponentId = typeof healthComponentIds[number];
export type HealthState = "ok" | "degraded" | "failed" | "unknown";
export const healthReasons = ["none", "connection", "upstream_error", "authentication", "timeout", "invalid_response", "not_configured", "not_initialized", "not_verified", "busy", "cooldown", "budget_unavailable", "stale"] as const;
export type HealthReason = typeof healthReasons[number];
export interface HealthComponent {
  id: HealthComponentId;
  status: HealthState;
  reason_code: HealthReason;
  source_kind: "live" | "simulated" | "mock" | "unverified";
  checked_at: string;
  latency_ms: number | null;
  worker_status?: "unknown" | null;
  verified_at?: string | null;
  last_attempt_at?: string | null;
  expires_at?: string | null;
  check_id?: string | null;
  reported_model?: string | null;
  model_identity?: "unconfirmed";
  reported_cost_usd?: string | null;
  cost_status?: "gateway_reported" | "unavailable" | "invalid";
  cost_confirmation?: "unconfirmed";
}
export interface HealthActivitySummary {
  data_status: "available" | "empty" | "unavailable";
  counts: Record<string, number> | null;
  failed_last_24h: number | null;
  last_updated_at?: string | null;
  last_completed_at?: string | null;
}
export interface SystemHealth {
  status: HealthState;
  tenant_id: string;
  checked_at: string;
  window: { start: string; end: string };
  components: HealthComponent[];
  jobs: HealthActivitySummary;
  ingestion: HealthActivitySummary;
}

function healthObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
export function isHealthUTC(value: unknown): value is string {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$/.test(value)
    && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 19) === value.slice(0, 19);
}
export const HEALTH_FUTURE_TOLERANCE_MS = 1000;
export function isHealthObservationTime(value: unknown, observedNow: number): value is string {
  return isHealthUTC(value) && Number.isFinite(observedNow)
    && Date.parse(value) <= observedNow + HEALTH_FUTURE_TOLERANCE_MS;
}
const nullableHealthDate = (value: unknown) => value === null || isHealthUTC(value);
const healthCount = (value: unknown) => typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
export function isHealthComponent(value: unknown): value is HealthComponent {
  return healthObject(value) && healthComponentIds.includes(value.id as HealthComponentId)
    && ["ok", "degraded", "failed", "unknown"].includes(String(value.status))
    && healthReasons.includes(value.reason_code as HealthReason)
    && ["live", "simulated", "mock", "unverified"].includes(String(value.source_kind))
    && isHealthUTC(value.checked_at)
    && (value.latency_ms === null || (typeof value.latency_ms === "number" && Number.isFinite(value.latency_ms) && value.latency_ms >= 0))
    && (value.id !== "openrouter" || (nullableHealthDate(value.verified_at) && nullableHealthDate(value.last_attempt_at)
      && nullableHealthDate(value.expires_at) && (value.check_id === null || typeof value.check_id === "string")
      && (value.status !== "ok" || (value.source_kind === "live" && isHealthUTC(value.verified_at) && typeof value.check_id === "string" && value.check_id.length > 0))));
}
// The fetch boundary returns its parsed object after validation. Normalize
// only informational fields on that same object, never functional validity.
function normalizeProviderInformation(value: HealthComponent) {
  const model = value.reported_model;
  value.reported_model = typeof model === "string" && /^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$/.test(model) ? model : null;
  value.model_identity = "unconfirmed";
  const cost = value.reported_cost_usd;
  // Exact bounded decimal text, never a charge calculated with JS floats.
  const usable = typeof cost === "string" && /^(?:0|[1-9]\d{0,12})(?:\.\d{1,18})?$/.test(cost)
    && cost.replace(".", "").replace(/^0+/, "").length <= 40;
  if (usable) {
    value.cost_status = "gateway_reported";
  } else {
    value.reported_cost_usd = null;
    value.cost_status = cost === null || cost === undefined
      ? (value.cost_status === "invalid" ? "invalid" : "unavailable") : "invalid";
  }
  value.cost_confirmation = "unconfirmed";
}
export function isProviderObservation(value: unknown): value is HealthComponent {
  if (!isHealthComponent(value) || value.id !== "openrouter") return false;
  normalizeProviderInformation(value);
  return true;
}

function isHealthSummary(value: unknown, states: string[], latest: string): boolean {
  if (!healthObject(value) || !["available", "empty", "unavailable"].includes(String(value.data_status)) || !nullableHealthDate(value[latest])) return false;
  if (value.data_status === "unavailable") return value.counts === null && value.failed_last_24h === null;
  if (!healthObject(value.counts) || Object.keys(value.counts).length !== states.length || !states.every((key) => key in (value.counts as object) && healthCount((value.counts as Record<string, unknown>)[key])) || !healthCount(value.failed_last_24h)) return false;
  return value.data_status !== "empty" || (Object.values(value.counts).every((count) => count === 0) && value.failed_last_24h === 0 && value[latest] === null);
}
export function isSystemHealth(value: unknown): value is SystemHealth {
  const valid = healthObject(value) && isNonemptyString(value.tenant_id)
    && ["ok", "degraded", "failed", "unknown"].includes(String(value.status))
    && isHealthUTC(value.checked_at) && healthObject(value.window) && isHealthUTC(value.window.start) && isHealthUTC(value.window.end)
    && Date.parse(value.window.end) === Date.parse(value.checked_at) && Date.parse(value.window.end) - Date.parse(value.window.start) === 86_400_000
    && Array.isArray(value.components) && value.components.length === healthComponentIds.length && value.components.every(isHealthComponent)
    && new Set(value.components.map((component) => component.id)).size === healthComponentIds.length
    && isHealthSummary(value.jobs, ["publish_pending", "publish_failed", "publish_unknown", "queued", "running", "completed", "failed", "other"], "last_updated_at")
    && isHealthSummary(value.ingestion, ["running", "completed", "failed", "other"], "last_completed_at");
  if (!valid) return false;
  const components = value.components as HealthComponent[];
  components.filter((component) => component.id === "openrouter").forEach(normalizeProviderInformation);
  return true;
}

export type AnomalySeverity = "P1" | "P2" | "P3";
export type AnomalyStatus = "new" | "investigating" | "resolved" | "false_positive";
export type AnomalyObservation = "observed" | "no_longer_observed";

export interface AnomalyEpisode {
  id: string;
  kind: "cost_anomaly_candidate";
  currency: string;
  service: string | null;
  start_date: string;
  last_seen_date: string;
  observation: AnomalyObservation;
  no_longer_observed_on: string | null;
  reference_daily_cost: string;
  opening_observed_cost: string;
  accumulated_impact: string;
  impact_day_count: number;
  impact_through_date: string;
  severity: AnomalySeverity;
  status: AnomalyStatus;
  status_changed_by: string | null;
  status_changed_at: string | null;
  first_reviewed_at: string | null;
  first_reviewed_by: string | null;
  closed_at: string | null;
  closure_reason: string | null;
  previous_episode_id: string | null;
  rules_version: string;
  rules: Record<string, unknown>;
  cause_status: "not_established";
  limitations: string[];
  created_at: string;
  updated_at: string;
}

export interface CurrencyAmount {
  currency: string;
  amount: string;
}

export interface AnomalyEpisodeList {
  contract_version: 1;
  scope: "open" | "all";
  episodes: AnomalyEpisode[];
  last_evaluated_date: string | null;
  includes_synthetic_data: boolean;
  open_impact_by_currency: CurrencyAmount[];
}

export interface AnomalyDetectionRun {
  status: "completed" | "up_to_date" | "insufficient_data";
  rules_version: string;
  last_complete_day: string | null;
  evaluated_days: string[];
  skipped_days: { date: string; reason: "not_observed" | "reference_incomplete" }[];
  unsupported_currencies: string[];
  opened: number;
  continued: number;
  no_longer_observed: number;
}

export interface AnomalyStatusChange {
  status: AnomalyStatus;
  reason?: string;
}

const anomalyObject = (item: unknown): item is Record<string, unknown> =>
  typeof item === "object" && item !== null && !Array.isArray(item);
const anomalyMoney = (item: unknown) => typeof item === "string" && /^-?(0|[1-9][0-9]*)\.[0-9]{2}$/.test(item) && item !== "-0.00";
const anomalyDate = (item: unknown) => typeof item === "string" && /^\d{4}-\d{2}-\d{2}$/.test(item)
  && !Number.isNaN(Date.parse(item)) && new Date(item).toISOString().slice(0, 10) === item;
const anomalyInstant = (item: unknown) => typeof item === "string" && /^\d{4}-\d{2}-\d{2}T[\d:.]+(Z|[+-]\d{2}:\d{2})$/.test(item)
  && !Number.isNaN(Date.parse(item));
const anomalyCount = (item: unknown) => typeof item === "number" && Number.isSafeInteger(item) && item >= 0;
const orNull = (check: (item: unknown) => boolean) => (item: unknown) => item === null || check(item);
const nullableText = orNull((item) => typeof item === "string");

export function isAnomalyEpisode(value: unknown): value is AnomalyEpisode {
  return anomalyObject(value) && isNonemptyString(value.id) && value.kind === "cost_anomaly_candidate"
    && isNonemptyString(value.currency) && nullableText(value.service)
    && anomalyDate(value.start_date) && anomalyDate(value.last_seen_date)
    && ["observed", "no_longer_observed"].includes(String(value.observation)) && orNull(anomalyDate)(value.no_longer_observed_on)
    && anomalyMoney(value.reference_daily_cost) && anomalyMoney(value.opening_observed_cost) && anomalyMoney(value.accumulated_impact)
    && anomalyCount(value.impact_day_count) && anomalyDate(value.impact_through_date)
    && ["P1", "P2", "P3"].includes(String(value.severity))
    && ["new", "investigating", "resolved", "false_positive"].includes(String(value.status))
    && nullableText(value.status_changed_by) && orNull(anomalyInstant)(value.status_changed_at)
    && orNull(anomalyInstant)(value.first_reviewed_at) && nullableText(value.first_reviewed_by)
    && orNull(anomalyInstant)(value.closed_at) && nullableText(value.closure_reason) && nullableText(value.previous_episode_id)
    && isNonemptyString(value.rules_version) && anomalyObject(value.rules) && value.cause_status === "not_established"
    && Array.isArray(value.limitations) && value.limitations.every((item) => typeof item === "string")
    && anomalyInstant(value.created_at) && anomalyInstant(value.updated_at);
}

export function isAnomalyEpisodeList(value: unknown): value is AnomalyEpisodeList {
  if (!anomalyObject(value) || value.contract_version !== 1 || !["open", "all"].includes(String(value.scope))) return false;
  const totals = value.open_impact_by_currency;
  return Array.isArray(value.episodes) && value.episodes.every(isAnomalyEpisode)
    && orNull(anomalyDate)(value.last_evaluated_date) && typeof value.includes_synthetic_data === "boolean"
    && Array.isArray(totals) && totals.every((item) => anomalyObject(item) && isNonemptyString(item.currency) && anomalyMoney(item.amount))
    && new Set(totals.map((item) => (item as CurrencyAmount).currency)).size === totals.length;
}

export function isAnomalyDetectionRun(value: unknown): value is AnomalyDetectionRun {
  return anomalyObject(value) && ["completed", "up_to_date", "insufficient_data"].includes(String(value.status))
    && isNonemptyString(value.rules_version) && orNull(anomalyDate)(value.last_complete_day)
    && Array.isArray(value.evaluated_days) && value.evaluated_days.every(anomalyDate)
    && Array.isArray(value.skipped_days) && value.skipped_days.every((item) => anomalyObject(item) && anomalyDate(item.date)
      && ["not_observed", "reference_incomplete"].includes(String(item.reason)))
    && Array.isArray(value.unsupported_currencies) && value.unsupported_currencies.every(isNonemptyString)
    && anomalyCount(value.opened) && anomalyCount(value.continued) && anomalyCount(value.no_longer_observed);
}

// JUP-038: evidencia guardada de la explicación de una anomalía (metadata.anomaly_evidence de un mensaje).
// Es la fotografía de un solo episodio que genera el backend; los metadatos del mensaje no son fiables,
// así que este validador es la frontera de confianza antes de pintar ninguna cifra.
export type AnomalyRoundingNote = "absolute_increase" | "relative_increase" | "accumulated_impact";

export interface AnomalyEvidence {
  schema_version: "1.0";
  adapter_version: "anomaly-explanation-1.0";
  id: string;
  status: "ok";
  source: { kind: "anomaly_episodes"; rules_version: string; data_as_of: string };
  episode: AnomalyEpisode;
  // Operandos exactos con la escala de la base de datos (p. ej. 12 decimales): se muestran, nunca se recalculan.
  operands: { reference_seven_day_total: string; opening_observed_cost: string; accumulated_impact_times_seven: string };
  opening: {
    reference_daily_cost: string; observed_cost: string; absolute_increase: string; relative_increase_percent: string;
    absolute_threshold: string; relative_threshold_percent: string; conditions_met: true;
  };
  impact: { accumulated_impact: string; day_count: number; through_date: string; severity: AnomalySeverity; severity_band: string };
  rounding_notes: AnomalyRoundingNote[];
  includes_synthetic_data: boolean;
  cause_status: "not_established";
  assumptions: unknown[];
  limitations: string[];
  explained_at: string;
}

// Operandos y umbrales: números decimales exactos de cualquier escala, validados como TEXTO. Nunca se
// convierten a Number (perdería dígitos en importes enormes). Sin bandera `m`, `$` no admite un salto de
// línea final, así que "2800.00\n" se rechaza.
const anomalyExact = (item: unknown) => typeof item === "string" && /^-?\d+(\.\d+)?$/.test(item);
const anomalyThreshold = (item: unknown) => typeof item === "string" && /^\d+(\.\d+)?$/.test(item);
const anomalyRoundingNotes = ["absolute_increase", "relative_increase", "accumulated_impact"];

export function isAnomalyEvidence(value: unknown): value is AnomalyEvidence {
  if (!anomalyObject(value)) return false;
  const { source, episode, operands, opening, impact } = value;
  if (value.schema_version !== "1.0" || value.adapter_version !== "anomaly-explanation-1.0"
    || typeof value.id !== "string" || !/^anomaly-explanation:[0-9a-f]{64}$/.test(value.id) || value.status !== "ok") return false;
  // La fuente no se acepta si falta su versión de reglas: sin ella la regla mostrada no sería trazable.
  if (!anomalyObject(source) || source.kind !== "anomaly_episodes"
    || typeof source.rules_version !== "string" || source.rules_version.trim().length === 0
    || !anomalyDate(source.data_as_of)) return false;
  if (!isAnomalyEpisode(episode)) return false;
  if (!anomalyObject(operands) || !anomalyExact(operands.reference_seven_day_total)
    || !anomalyExact(operands.opening_observed_cost) || !anomalyExact(operands.accumulated_impact_times_seven)) return false;
  // Solo se guarda evidencia de aperturas que cumplieron la regla: conditions_met distinto de true se rechaza.
  if (!anomalyObject(opening) || opening.conditions_met !== true
    || !anomalyMoney(opening.reference_daily_cost) || !anomalyMoney(opening.observed_cost)
    || !anomalyMoney(opening.absolute_increase) || !anomalyMoney(opening.relative_increase_percent)
    || !anomalyThreshold(opening.absolute_threshold) || !anomalyThreshold(opening.relative_threshold_percent)) return false;
  if (!anomalyObject(impact) || !anomalyMoney(impact.accumulated_impact) || !anomalyCount(impact.day_count)
    || !anomalyDate(impact.through_date) || !["P1", "P2", "P3"].includes(String(impact.severity))
    || typeof impact.severity_band !== "string" || impact.severity_band.trim().length === 0) return false;
  // Coherencia interna: la evidencia es la foto de UN episodio. Si el bloque de apertura o de impacto no
  // coincide con el episodio embebido, mezcla datos de dos momentos y no se debe mostrar. Se comparan las
  // cadenas exactas (sin Number), así que una diferencia de un céntimo ya la rechaza.
  if (impact.severity !== episode.severity || impact.accumulated_impact !== episode.accumulated_impact
    || opening.reference_daily_cost !== episode.reference_daily_cost
    || opening.observed_cost !== episode.opening_observed_cost) return false;
  // La hora acepta tanto +00:00 (la escribe el backend) como Z (la escribe la API de episodios). Además de
  // anomalyInstant se valida la parte de fecha por separado: Date.parse de V8 admite "2026-02-30T..." y lo
  // desplaza a marzo, mientras que anomalyDate comprueba el ida y vuelta y rechaza el día imposible.
  return Array.isArray(value.rounding_notes) && value.rounding_notes.every((note) => typeof note === "string" && anomalyRoundingNotes.includes(note))
    && typeof value.includes_synthetic_data === "boolean" && value.cause_status === "not_established"
    && Array.isArray(value.assumptions)
    && Array.isArray(value.limitations) && value.limitations.every((item) => typeof item === "string")
    && anomalyInstant(value.explained_at) && anomalyDate((value.explained_at as string).slice(0, 10));
}
