const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
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

export function fetchProfile() {
  return fetchJson("/me");
}

export function fetchTenants() {
  return fetchJson("/tenants");
}

export function fetchBillingSummary() {
  return fetchJson("/billing/summary");
}

export function login(payload) {
  return fetchJson("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

