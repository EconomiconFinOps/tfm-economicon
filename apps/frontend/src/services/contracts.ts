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
