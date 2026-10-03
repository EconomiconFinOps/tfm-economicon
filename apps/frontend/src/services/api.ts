import type { QueryClient } from "@tanstack/react-query";
import type {
  AssistantReply,
  BillingSelection,
  BillingSummary,
  TagCoverage,
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
import { isBillingSummary, isTagCoverage, isLoginResponse, isUserProfile } from "./contracts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Union cerrada de motivos de invalidacion (tarea 2.1). Solo dos valores:
// "expired" (401 recibido fuera de /me) y "manual" (logout explicito u otro
// origen sin motivo especifico). Se modela como tipo, no como enum, porque
// los consumidores actuales (SessionGate, LoginPage) solo necesitan el
// literal en tiempo de ejecucion, no un objeto enum en el bundle.
export type SessionInvalidationReason = "expired" | "manual";

let sessionGeneration = 0;
const invalidationListeners = new Set<(reason: SessionInvalidationReason) => void>();

export function getSessionGeneration() {
  return sessionGeneration;
}

export function advanceSessionGeneration() {
  return ++sessionGeneration;
}

export function subscribeSessionInvalidation(listener: (reason: SessionInvalidationReason) => void) {
  invalidationListeners.add(listener);
  return () => { invalidationListeners.delete(listener); };
}

export function invalidateSession(generation: number, reason: SessionInvalidationReason = "manual") {
  // El guard se queda intacto: una generacion abandonada no debe notificar
  // ningun motivo (tarea 2.2), y ese comportamiento ya lo garantiza este
  // return temprano evaluado antes de tocar los listeners.
  if (generation !== sessionGeneration) return;
  advanceSessionGeneration();
  invalidationListeners.forEach((listener) => listener(reason));
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
      // Un 401 fuera de /me solo puede significar que el token dejo de ser
      // valido para el backend (expiro o fue revocado), no un logout manual:
      // por eso el motivo aqui es siempre "expired" (tarea 3.3).
      invalidateSession(generation, "expired");
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

export function fetchBillingSummary(token: string, tenantId: string, selection: BillingSelection = {}, signal?: AbortSignal) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(selection)) {
    if (value !== undefined) params.set(key, value);
  }
  const query = params.toString();
  return fetchJson<BillingSummary>(`/billing/summary${query ? `?${query}` : ""}`, {
    token, tenantId, signal, validate: isBillingSummary
  });
}

export function fetchTagCoverage(token: string, tenantId: string,
  period: Pick<BillingSelection, "start_date" | "end_date">, signal?: AbortSignal) {
  const params = new URLSearchParams();
  if (period.start_date) params.set("start_date", period.start_date);
  if (period.end_date) params.set("end_date", period.end_date);
  const query = params.toString();
  return fetchJson<TagCoverage>(`/billing/tag-coverage${query ? `?${query}` : ""}`, {
    token, tenantId, signal, validate: isTagCoverage
  });
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
