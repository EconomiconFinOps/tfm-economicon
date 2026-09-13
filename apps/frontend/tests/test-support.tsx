import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { afterEach, expect, vi } from "vitest";
import App from "../src/App";
import { billing, health, loginResponse, session, tenants } from "./fixtures";

export const SESSION_KEY = "finops.session";
export const TENANT_KEY = "finops.activeTenant";

type RecordedRequest = {
  method: string;
  path: string;
  headers: Headers;
  body: unknown;
};

type Handler = (request: RecordedRequest) => Response | Promise<Response>;
type Routes = Record<string, Handler>;

const queryClients = new Set<QueryClient>();
const unexpectedRequests: string[] = [];

afterEach(() => {
  for (const client of queryClients) client.clear();
  queryClients.clear();
  const unexpected = unexpectedRequests.splice(0);
  expect(unexpected, "Every HTTP request must be explicitly intercepted").toEqual([]);
});

export function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

export function deferredResponse() {
  let finish!: (response: Response) => void;
  const promise = new Promise<Response>((resolve) => { finish = resolve; });
  return {
    promise,
    resolve: (data: unknown, status = 200) => finish(jsonResponse(data, status))
  };
}

export function mockBackend(overrides: Routes = {}) {
  const requests: RecordedRequest[] = [];
  const routes: Routes = {
    "POST /auth/login": () => jsonResponse(loginResponse),
    "GET /tenants": () => jsonResponse({ items: tenants }),
    "GET /health": () => jsonResponse(health),
    "GET /billing/summary": () => jsonResponse(billing),
    ...overrides
  };

  vi.stubGlobal("fetch", vi.fn<typeof fetch>(async (input, init) => {
    const url = input instanceof Request ? input.url : String(input);
    const request = {
      method: init?.method ?? "GET",
      path: new URL(url).pathname,
      headers: new Headers(init?.headers),
      body: typeof init?.body === "string" ? JSON.parse(init.body) as unknown : undefined
    };
    requests.push(request);
    const route = `${request.method} ${request.path}`;
    const handler = routes[route];
    if (!handler) {
      unexpectedRequests.push(route);
      throw new Error(`Unmocked HTTP request: ${route}`);
    }
    return handler(request);
  }));

  return { requests };
}

export function restoreSession(tenantId?: string) {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  if (tenantId) window.localStorage.setItem(TENANT_KEY, tenantId);
}

export function renderApp() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity },
      mutations: { retry: false }
    }
  });
  queryClients.add(client);
  return {
    ...render(<QueryClientProvider client={client}><App /></QueryClientProvider>),
    client
  };
}

export function expectTenantRequest(request: RecordedRequest, tenantId = tenants[0].id) {
  expect(request.headers.get("Authorization")).toBe(`Bearer ${session.accessToken}`);
  expect(request.headers.get("X-Tenant-Id")).toBe(tenantId);
  expect(request.headers.get("Content-Type")).toBe("application/json");
}
