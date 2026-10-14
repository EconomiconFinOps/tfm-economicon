import { fetchChatResponse } from "./api";
import { readChatEvents, type ChatFrame } from "./chatStream";
import type { ScreenCapture } from "./screenCapture";
export interface ChatScope { token: string; tenantId: string; userId: string }
export interface ChatCapabilities { chat_enabled: boolean }
export function isChatCapabilities(value: unknown): value is ChatCapabilities {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const item = value as Record<string, unknown>;
  return Object.keys(item).length === 1 && typeof item.chat_enabled === 'boolean';
}
export async function fetchChatCapabilities(scope: ChatScope, signal: AbortSignal): Promise<ChatCapabilities> {
  const value: unknown = await chatJson(scope, '/assistant/capabilities', signal);
  if (!isChatCapabilities(value)) throw new Error('capabilities_invalid');
  return value;
}
export interface GenerationPayload { request_id: string; content: string; screen_context: ScreenCapture; retry_of_operation_id?: string }
export interface SavedChatRequest { tenant_id: string; user_id: string; conversation_id: string; question: string; operation: ChatOperation }
export function isSavedChatRequest(value: unknown, scope: ChatScope): value is SavedChatRequest {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const item = value as Record<string, unknown>;
  return item.tenant_id === scope.tenantId && item.user_id === scope.userId
    && typeof item.conversation_id === "string" && !!item.conversation_id
    && typeof item.question === "string" && isChatOperation(item.operation);
}
export type OperationState = "reserved" | "active" | "waiting" | "paused" | "completed" | "failed" | "cancelled";
export interface ChatOperation {
  v: 2; operation_id: string; question_id: string; request_id: string; state: OperationState;
  attempt_count: number; current_attempt_id: string | null; attempt_deadline: string | null;
  retry_at: string | null; result_url: string | null;
  wait_info: { reason: string | null; local_remaining_ms: number; provider_remaining_ms: number;
    automatic_until: string | null; retry_at: string | null; pause_reason: string | null };
}
const states: readonly string[] = ["reserved", "active", "waiting", "paused", "completed", "failed", "cancelled"];
export function isChatOperation(value: unknown): value is ChatOperation {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const item = value as Record<string, unknown>;
  return item.v === 2 && typeof item.operation_id === "string" && !!item.operation_id
    && typeof item.question_id === "string" && typeof item.request_id === "string"
    && states.includes(String(item.state)) && Number.isSafeInteger(item.attempt_count)
    && Number(item.attempt_count) >= 0 && Number(item.attempt_count) <= 4
    && (item.current_attempt_id === null || typeof item.current_attempt_id === "string")
    && typeof item.wait_info === "object" && item.wait_info !== null;
}
export function chatPath(conversationId: string, operationId?: string, action?: string) {
  return `/assistant/conversations/${encodeURIComponent(conversationId)}/generations`
    + (operationId ? `/${encodeURIComponent(operationId)}` : "") + (action ? `/${action}` : "");
}
export async function chatJson<T>(scope: ChatScope, path: string, signal: AbortSignal, method = "GET", body?: unknown): Promise<T> {
  const response = await fetchChatResponse(path, { token: scope.token, tenantId: scope.tenantId,
    signal, method, ...(body !== undefined ? { body: JSON.stringify(body) } : {}) });
  return await response.json() as T;
}
export async function generateChat(scope: ChatScope, conversationId: string,
  payload: GenerationPayload,
  signal: AbortSignal, receive: (frame: ChatFrame) => Promise<void> | void) {
  const response = await fetchChatResponse(chatPath(conversationId), { token: scope.token, tenantId: scope.tenantId,
    method: "POST", signal, body: JSON.stringify(payload) });
  if (response.headers.get("Content-Type")?.startsWith("application/json")) {
    const value: unknown = await response.json();
    if (!isChatOperation(value)) throw new Error("operation_invalid");
    await receive({ v: 2, type: "started", operation: value });
    return;
  }
  await readChatEvents(response, receive);
}

export interface ChatMemory {
  v: 2; scope: { tenant_id: string; user_id: string; conversation_id: string }; available: boolean;
  reason: string | null; coverage: { processed_pairs: number; pending_pairs: number; recent_reserved: number };
  limitations: string[]; artifact_id: string | null; queue: { reason: string; active: boolean; pending: boolean;
    blocked?: boolean; retryable?: boolean; state?: "idle" | "pending" | "running" | "reconciling" | "failed" };
}
export function isChatMemory(value: unknown, scope: ChatScope, conversationId: string): value is ChatMemory {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const item = value as Record<string, unknown>;
  const identity = item.scope as ChatMemory["scope"] | undefined;
  const coverage = item.coverage as ChatMemory["coverage"] | undefined;
  const queue = item.queue as ChatMemory["queue"] | undefined;
  return item.v === 2 && !!identity && identity.tenant_id === scope.tenantId && identity.user_id === scope.userId
    && identity.conversation_id === conversationId && typeof item.available === "boolean"
    && (item.reason === null || typeof item.reason === "string") && !!coverage
    && [coverage.processed_pairs, coverage.pending_pairs, coverage.recent_reserved].every(n => Number.isSafeInteger(n) && n >= 0)
    && coverage.recent_reserved <= 4 && Array.isArray(item.limitations) && item.limitations.length <= 4
    && item.limitations.every(text => typeof text === "string" && text.length <= 4096)
    && (item.artifact_id === null || typeof item.artifact_id === "string")
    && (!item.available || typeof item.artifact_id === "string" && !!item.artifact_id)
    && !!queue && typeof queue.reason === "string" && typeof queue.active === "boolean" && typeof queue.pending === "boolean"
    && (queue.blocked === undefined || typeof queue.blocked === "boolean")
    && (queue.retryable === undefined || typeof queue.retryable === "boolean")
    && (queue.state === undefined || ["idle", "pending", "running", "reconciling", "failed"].includes(queue.state));
}
