// Response fields follow apps/backend/app/schemas/{auth,tenant,health,billing,
// jobs,assistant}.py. IDs, timestamps and credentials are synthetic test data.
import type {
  AssistantReply,
  ConversationRecord,
  HealthResponse,
  IngestJobResponse,
  LoginResponse,
  MessageRecord,
  TenantRecord,
  UserProfile
} from "../src/services/contracts";

export const operator = {
  id: "user-operator",
  email: "operator@example.com",
  full_name: "Test Operator",
  role: "operator"
} satisfies UserProfile;

export const loginResponse = {
  access_token: "test-access-token",
  token_type: "bearer",
  user: operator
} satisfies LoginResponse;

export const session = {
  accessToken: loginResponse.access_token,
  user: operator
};

export const tenants = [
  { id: "tenant-north", name: "North Operations", slug: "north", plan: "enterprise" },
  { id: "tenant-south", name: "South Operations", slug: "south", plan: "starter" }
] satisfies TenantRecord[];

export const health = {
  status: "ok",
  services: { database: "ok", rabbitmq: "ok", vector_store: "ok" },
  checked_at: "2026-09-08T10:00:00Z"
} satisfies HealthResponse;

export const billing = {
  contract_version: 2,
  period: { start_date: "2024-06-01", end_date: "2024-07-01", timezone: "UTC" },
  group_by: "service",
  tag_key: null,
  data_status: "available",
  totals: [{ currency: "USD", cost: "12345.67", record_count: 2 }],
  groups: [{ currency: "USD", subscription_id: null, value: "Compute", cost: "12345.67", record_count: 2 }],
  missing_dimension_count: 0,
  excluded_undated_count: 0,
  monthly_spend: "12345.67",
  savings_identified: null,
  open_ingestions: 2,
  currency: "USD"
};

export function billingWithCost(cost: string) {
  return { ...billing, monthly_spend: cost,
    totals: [{ ...billing.totals[0], cost }], groups: [{ ...billing.groups[0], cost }] };
}

export const ingestJob = {
  job_id: "job-billing-document",
  status: "queued",
  queue: "ingest.jobs"
} satisfies IngestJobResponse;

export const conversation = {
  id: "conversation-cost-review",
  tenant_id: tenants[0].id,
  user_id: operator.id,
  title: "September costs",
  created_at: "2026-09-08T10:00:00Z",
  updated_at: "2026-09-08T10:05:00Z"
} satisfies ConversationRecord;

export const userMessage = {
  id: "message-question",
  role: "user",
  content: "Where can we reduce compute costs?",
  metadata: {},
  created_at: "2026-09-08T10:05:00Z"
} satisfies MessageRecord;

export const assistantMessage = {
  id: "message-answer",
  role: "assistant",
  content: "The billing document identifies idle compute instances.",
  metadata: { citations: ["chunk-compute"] },
  created_at: "2026-09-08T10:05:01Z"
} satisfies MessageRecord;

export const assistantReply = {
  conversation,
  user_message: userMessage,
  assistant_message: assistantMessage,
  retrieved_context: [{
    chunk_id: "chunk-compute",
    source: "aws-cur",
    content: "Idle compute instances cost 678 USD this month.",
    distance: 0.12
  }]
} satisfies AssistantReply;
