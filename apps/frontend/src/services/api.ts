import type { QueryClient } from "@tanstack/react-query";
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
import { isLoginResponse, isUserProfile } from "./contracts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

let sessionGeneration = 0;
const invalidationListeners = new Set<() => void>();

export function getSessionGeneration() {
  return sessionGeneration;
}

export function advanceSessionGeneration() {
  return ++sessionGeneration;
}

export function subscribeSessionInvalidation(listener: () => void) {
  invalidationListeners.add(listener);
  return () => { invalidationListeners.delete(listener); };
}

export function invalidateSession(generation: number) {
  if (generation !== sessionGeneration) return;
  advanceSessionGeneration();
  invalidationListeners.forEach((listener) => listener());
}

export function clearSessionMutations(queryClient: QueryClient) {
  const cache = queryClient.getMutationCache();
  const removed = cache.getAll();
  cache.clear();
  for (const mutation of removed) {
    // Only removed mutations lose GC scheduling. Infinity survives later
    // observer option updates; destroy also cancels any existing timer.
    mutation.setOptions({ ...mutation.options, gcTime: Infinity });
    mutation.destroy();
  }
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

function discardResponse(): Promise<never> {
  // Cleared mutations cannot be cancelled by QueryClient. Do not settle their
  // abandoned HTTP work: settling would run callbacks or schedule retries.
  return new Promise(() => {});
}

type FetchJsonOptions = Omit<RequestInit, "headers"> & {
  token?: string;
  tenantId?: string;
  headers?: Record<string, string>;
  validate?: (value: unknown) => boolean;
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
  const generation = getSessionGeneration();
  const { token, tenantId, headers, validate, ...requestInit } = options;
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: buildHeaders(token, tenantId, headers),
      ...requestInit
    });
    if (generation !== getSessionGeneration()) return discardResponse();

    if (token && path !== "/me" && response.status === 401) {
      invalidateSession(generation);
      return discardResponse();
    }

    if (!response.ok) {
      const body = await response.text();
      if (generation !== getSessionGeneration()) return discardResponse();
      const message = token ? body.split(token).join("[redacted]") : body;
      throw new ApiError(response.status, message.slice(0, 512) || `Request failed for ${path}`);
    }

    const data: unknown = await response.json();
    if (generation !== getSessionGeneration()) return discardResponse();
    if (validate && !validate(data)) {
      throw new ApiError(response.status, `Invalid response for ${path}`);
    }
    return data as T;
  } catch (error) {
    if (generation !== getSessionGeneration()) return discardResponse();
    throw error;
  }
}

export function fetchHealth() {
  return fetchJson<HealthResponse>("/health");
}

export function fetchProfile(token: string) {
  return fetchJson<UserProfile>("/me", { token, validate: isUserProfile });
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
    validate: isLoginResponse,
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
