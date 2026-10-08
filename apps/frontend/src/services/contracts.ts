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
