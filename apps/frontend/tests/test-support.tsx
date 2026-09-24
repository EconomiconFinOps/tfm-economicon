import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, expect, vi } from "vitest";
import { routeConfig } from "../src/routes";
import { billing, health, loginResponse, operator, session, tenants } from "./fixtures";

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
    "GET /me": () => jsonResponse(operator),
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

// Reconciliacion con JUP-095: `App` ya no acepta `onLogin`/props de sesion --
// es `<RouterProvider router={router} />` sobre `createBrowserRouter`, que
// depende de la History API real del navegador. Para las mismas razones que
// `routes.integration.test.tsx` (JUP-095, tarea 6.5), montamos aqui la MISMA
// `routeConfig` sobre `createMemoryRouter`, con `initialEntries` por
// escenario: sin enlaces de menu todavia hacia /ingest, /assistant y
// /overview-legacy (Punto 5 de la reconciliacion con develop, pendiente),
// las suites navegan a esas pantallas por su ruta inicial en vez de un click
// sobre un enlace que hoy no existe.
export function renderApp(initialEntries: string[] = ["/"]) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity },
      mutations: { retry: false }
    }
  });
  queryClients.add(client);
  const router = createMemoryRouter(routeConfig, { initialEntries });
  return {
    ...render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>),
    client
  };
}

export function expectTenantRequest(request: RecordedRequest, tenantId = tenants[0].id) {
  expect(request.headers.get("Authorization")).toBe(`Bearer ${session.accessToken}`);
  expect(request.headers.get("X-Tenant-Id")).toBe(tenantId);
  expect(request.headers.get("Content-Type")).toBe("application/json");
}
