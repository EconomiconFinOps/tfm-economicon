import { fetchProfile } from "./api";
import type { UserProfile } from "./contracts";

export const COGNITO_FLOW_KEY = "economicon.cognito.flow";
const FLOW_TTL = 10 * 60 * 1000;

export function usesCognito(): boolean {
  return import.meta.env.VITE_AUTH_PROVIDER === "cognito";
}

function configuration() {
  const domain = import.meta.env.VITE_COGNITO_DOMAIN || "";
  const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID || "";
  if (!usesCognito() || !/^https:\/\/[a-z0-9-]+\.auth\.[a-z]{2}-[a-z]+-\d\.amazoncognito\.com$/.test(domain)
      || !/^[A-Za-z0-9_-]{1,128}$/.test(clientId)) {
    throw new Error("La configuración del acceso no está disponible.");
  }
  return { domain, clientId, redirectUri: `${window.location.origin}/auth/callback` };
}

function base64url(value: Uint8Array): string {
  return btoa(String.fromCharCode(...value)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function random(): string {
  return base64url(crypto.getRandomValues(new Uint8Array(32)));
}

export async function beginCognitoLogin(): Promise<string> {
  const { domain, clientId, redirectUri } = configuration();
  const verifier = random();
  const state = random();
  const challenge = base64url(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier))));
  window.sessionStorage.setItem(COGNITO_FLOW_KEY, JSON.stringify({ verifier, state, createdAt: Date.now() }));
  const url = new URL(`${domain}/oauth2/authorize`);
  url.search = new URLSearchParams({ response_type: "code", client_id: clientId, redirect_uri: redirectUri,
    scope: "openid email profile", state, code_challenge: challenge, code_challenge_method: "S256" }).toString();
  return url.href;
}

interface CognitoSession { accessToken: string; user: UserProfile; expiresAt: number }
let inflight: { callback: string; promise: Promise<CognitoSession> } | undefined;

// React StrictMode may run the callback effect twice while one code exchange
// is pending. Share only that in-flight exchange; a later replay is rejected.
export function completeCognitoLogin(callback: string): Promise<CognitoSession> {
  if (inflight?.callback === callback) return inflight.promise;
  const promise = exchange(callback).finally(() => {
    if (inflight?.promise === promise) inflight = undefined;
  });
  inflight = { callback, promise };
  return promise;
}

async function exchange(callback: string): Promise<CognitoSession> {
  const { domain, clientId, redirectUri } = configuration();
  const raw = window.sessionStorage.getItem(COGNITO_FLOW_KEY);
  window.sessionStorage.removeItem(COGNITO_FLOW_KEY);
  const url = new URL(callback);
  let flow: { state?: unknown; verifier?: unknown; createdAt?: unknown };
  try { flow = JSON.parse(raw || "null"); } catch { throw new Error("El acceso ha caducado. Inicia sesión de nuevo."); }
  if (!flow || typeof flow.state !== "string" || !/^[A-Za-z0-9_-]{43}$/.test(flow.state)
      || typeof flow.verifier !== "string" || !/^[A-Za-z0-9_-]{43}$/.test(flow.verifier)
      || typeof flow.createdAt !== "number" || !Number.isFinite(flow.createdAt)
      || Date.now() < flow.createdAt || Date.now() - flow.createdAt > FLOW_TTL
      || `${url.origin}${url.pathname}` !== redirectUri || url.hash
      || url.searchParams.has("error") || url.searchParams.getAll("state").length !== 1
      || url.searchParams.get("state") !== flow.state || url.searchParams.getAll("code").length !== 1) {
    throw new Error("El acceso no es válido o ha caducado. Inicia sesión de nuevo.");
  }
  const code = url.searchParams.get("code");
  if (!code || code.length > 8192) throw new Error("El acceso no es válido.");
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(`${domain}/oauth2/token`, { method: "POST", credentials: "omit",
      redirect: "error", cache: "no-store", signal: controller.signal,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ grant_type: "authorization_code", client_id: clientId,
        code, redirect_uri: redirectUri, code_verifier: flow.verifier }) });
    if (!response.ok) throw new Error("No se pudo completar el acceso.");
    const payload: unknown = await response.json();
    if (!payload || typeof payload !== "object" || !("access_token" in payload)
        || typeof payload.access_token !== "string" || !payload.access_token || payload.access_token.length > 16384
        || !("token_type" in payload) || typeof payload.token_type !== "string" || payload.token_type.toLowerCase() !== "bearer"
        || !("expires_in" in payload) || typeof payload.expires_in !== "number" || !Number.isInteger(payload.expires_in)
        || payload.expires_in <= 0 || payload.expires_in > 3600) {
      throw new Error("La respuesta del acceso no es válida.");
    }
    const expiresAt = Date.now() + payload.expires_in * 1000;
    const user = await fetchProfile(payload.access_token);
    return { accessToken: payload.access_token, user, expiresAt };
  } finally { window.clearTimeout(timeout); }
}

export function cognitoLogoutUrl(): string {
  const { domain, clientId } = configuration();
  const url = new URL(`${domain}/logout`);
  url.search = new URLSearchParams({ client_id: clientId, logout_uri: `${window.location.origin}/` }).toString();
  return url.href;
}
