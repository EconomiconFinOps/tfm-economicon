import type {
  AssistantReply,
  BillingSummary,
  ConversationCollection,
  ConversationCreateRequest,
  ConversationDetail,
  ConversationRecord,
  HealthResponse,
  IngestJobRequest,
  IngestJobResponse,
  LoginRequest,
  LoginResponse,
  MessageCreateRequest,
  TenantCollection,
  UserProfile
} from "./contracts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type FetchJsonOptions = Omit<RequestInit, "headers"> & {
  token?: string;
  tenantId?: string;
  headers?: Record<string, string>;
};

function buildHeaders(token?: string, tenantId?: string, headers: Record<string, string> = {}) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(tenantId ? { "X-Tenant-Id": tenantId } : {}),
    ...headers
  };
}

async function fetchJson<T>(path: string, options: FetchJsonOptions = {}): Promise<T> {
  const { token, tenantId, headers, ...requestInit } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: buildHeaders(token, tenantId, headers),
    ...requestInit
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed for ${path}`);
  }

  // This is the HTTP boundary. Callers supply the backend's response contract.
  return response.json() as Promise<T>;
}

export function fetchHealth() {
  return fetchJson<HealthResponse>("/health");
}

export function fetchProfile(token: string) {
  return fetchJson<UserProfile>("/me", { token });
}

export function fetchTenants(token: string) {
  return fetchJson<TenantCollection>("/tenants", { token });
}

export function fetchBillingSummary(token: string, tenantId: string) {
  return fetchJson<BillingSummary>("/billing/summary", { token, tenantId });
}

export function login(payload: LoginRequest) {
  return fetchJson<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function createIngestJob(token: string, tenantId: string, payload: IngestJobRequest) {
  return fetchJson<IngestJobResponse>("/jobs/ingest", {
    method: "POST",
    token,
    tenantId,
    body: JSON.stringify(payload)
  });
}

export function listConversations(token: string, tenantId: string) {
  return fetchJson<ConversationCollection>("/assistant/conversations", { token, tenantId });
}

export function createConversation(token: string, tenantId: string, payload: ConversationCreateRequest) {
  return fetchJson<ConversationRecord>("/assistant/conversations", {
    method: "POST",
    token,
    tenantId,
    body: JSON.stringify(payload)
  });
}

export function getConversation(token: string, tenantId: string, conversationId: string) {
  return fetchJson<ConversationDetail>(`/assistant/conversations/${conversationId}`, {
    token,
    tenantId
  });
}

export function sendConversationMessage(
  token: string,
  tenantId: string,
  conversationId: string,
  payload: MessageCreateRequest
) {
  return fetchJson<AssistantReply>(`/assistant/conversations/${conversationId}/messages`, {
    method: "POST",
    token,
    tenantId,
    body: JSON.stringify(payload)
  });
}
