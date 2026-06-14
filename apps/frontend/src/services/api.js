const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function buildHeaders(token, tenantId, headers = {}) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(tenantId ? { "X-Tenant-Id": tenantId } : {}),
    ...headers
  };
}

async function fetchJson(path, options = {}) {
  const { token, tenantId, headers, ...requestInit } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: buildHeaders(token, tenantId, headers),
    ...requestInit
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed for ${path}`);
  }

  return response.json();
}

export function fetchHealth() {
  return fetchJson("/health");
}

export function fetchProfile(token) {
  return fetchJson("/me", { token });
}

export function fetchTenants(token) {
  return fetchJson("/tenants", { token });
}

export function fetchBillingSummary(token, tenantId) {
  return fetchJson("/billing/summary", { token, tenantId });
}

export function login(payload) {
  return fetchJson("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function createIngestJob(token, tenantId, payload) {
  return fetchJson("/jobs/ingest", {
    method: "POST",
    token,
    tenantId,
    body: JSON.stringify(payload)
  });
}

export function listConversations(token, tenantId) {
  return fetchJson("/assistant/conversations", { token, tenantId });
}

export function createConversation(token, tenantId, payload) {
  return fetchJson("/assistant/conversations", {
    method: "POST",
    token,
    tenantId,
    body: JSON.stringify(payload)
  });
}

export function getConversation(token, tenantId, conversationId) {
  return fetchJson(`/assistant/conversations/${conversationId}`, {
    token,
    tenantId
  });
}

export function sendConversationMessage(token, tenantId, conversationId, payload) {
  return fetchJson(`/assistant/conversations/${conversationId}/messages`, {
    method: "POST",
    token,
    tenantId,
    body: JSON.stringify(payload)
  });
}
