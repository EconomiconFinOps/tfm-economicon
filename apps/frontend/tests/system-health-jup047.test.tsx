import { StrictMode, useLayoutEffect } from "react";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, matchRoutes, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { routeConfig } from "../src/routes";
import { advanceSessionGeneration } from "../src/services/api";
import { useSystemHealth } from "../src/hooks/useSystemHealth";
import { loginResponse, tenants } from "./fixtures";
import { deferredResponse, expectTenantRequest, jsonResponse, mockBackend, renderApp, restoreSession, SESSION_KEY } from "./test-support";

// Public route + existing session and fetch seams: no future page/hook imports.
const statusPath = "/health/status";
const checkPath = "/health/provider-check";
const verified = "2026-10-06T12:00:00Z";
type DiagnosticState = "ok" | "degraded" | "failed" | "unknown";

function diagnostic(tenantId = tenants[0].id, state: DiagnosticState = "degraded") {
  return {
    tenant_id: tenantId, status: state, checked_at: "2026-10-06T12:00:30Z",
    window: { start: "2026-10-05T12:00:30Z", end: "2026-10-06T12:00:30Z" },
    components: ["backend", "database", "rabbitmq", "processor", "vector_store", "azure_cost_api", "litellm", "openrouter"].map((id) => ({
      id, status: id === "openrouter" ? "unknown" : "ok", checked_at: "2026-10-06T12:00:30Z", latency_ms: 12,
      reason_code: id === "openrouter" ? "not_verified" : "none",
      source_kind: id === "azure_cost_api" ? "simulated" : id === "openrouter" ? "unverified" : "live",
      ...(id === "openrouter" ? { verified_at: null, last_attempt_at: null, expires_at: null, check_id: null } : {})
    })),
    jobs: { data_status: "available", counts: { publish_pending: 1, publish_failed: 2, publish_unknown: 3, queued: 4, running: 5, completed: 6, failed: 7, other: 0 }, failed_last_24h: 9, last_updated_at: "2026-10-06T11:55:00Z" },
    ingestion: { data_status: "empty", counts: { running: 0, completed: 0, failed: 0, other: 0 }, failed_last_24h: 0, last_completed_at: null }
  };
}

function provider() {
  return { id: "openrouter", status: "ok", reason_code: "none", source_kind: "live", checked_at: verified, latency_ms: 15, verified_at: verified, last_attempt_at: verified, expires_at: "2026-10-06T12:01:00Z", check_id: "synthetic-check" };
}

function requirePublicRoute() {
  expect(matchRoutes(routeConfig, "/system-health"), "The approved dashboard route must exist in the application's actual router").not.toBeNull();
}

async function mount(overrides: Parameters<typeof mockBackend>[0] = {}, strict = false) {
  requirePublicRoute();
  const backend = mockBackend({
    [`GET ${statusPath}`]: ({ headers }) => jsonResponse(diagnostic(headers.get("X-Tenant-Id") ?? undefined)),
    [`POST ${checkPath}`]: () => jsonResponse(provider()), ...overrides
  });
  const interceptedFetch = globalThis.fetch;
  const signals: { path: string; signal: AbortSignal | null | undefined }[] = [];
  vi.stubGlobal("fetch", vi.fn<typeof fetch>(async (input, init) => {
    const signal = init?.signal;
    signals.push({ path: new URL(input instanceof Request ? input.url : String(input)).pathname, signal });
    if (!signal) return interceptedFetch(input, init);
    let onAbort!: () => void;
    const aborted = new Promise<never>((_, reject) => {
      onAbort = () => reject(new DOMException("Aborted", "AbortError"));
      signal.addEventListener("abort", onAbort, { once: true });
      if (signal.aborted) onAbort();
    });
    try { return await Promise.race([interceptedFetch(input, init), aborted]); }
    finally { signal.removeEventListener("abort", onAbort); }
  }));
  restoreSession(tenants[0].id);
  let view!: ReturnType<typeof renderApp>;
  if (strict) {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
    const router = createMemoryRouter(routeConfig, { initialEntries: ["/system-health"] });
    await act(async () => {
      view = { ...render(<StrictMode><QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider></StrictMode>), router, client };
      await vi.advanceTimersByTimeAsync(0);
    });
    clients.push(client);
  } else {
    await act(async () => {
      view = renderApp(["/system-health"]);
      await vi.advanceTimersByTimeAsync(0);
    });
  }
  for (let phase = 0; phase < 5; phase += 1) {
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  }
  await screen.findByRole("heading", { level: 1, name: /salud del sistema/i });
  await waitFor(() => expect(backend.requests.some((r) => r.path === statusPath)).toBe(true));
  return { ...view!, ...backend, signals };
}

function useHealthTimers() {
  // A second useFakeTimers call does not reinstall an already active Date-only clock.
  vi.useRealTimers();
  vi.useFakeTimers({ toFake: ["Date", "performance", "setTimeout", "clearTimeout", "setInterval", "clearInterval"] });
  vi.setSystemTime(new Date("2026-10-06T12:00:30Z"));
  // Testing Library detects fake timers via its Jest-compatible advancement seam.
  vi.stubGlobal("jest", { advanceTimersByTime: vi.advanceTimersByTime });
}

const clients: QueryClient[] = [];
beforeEach(() => {
  advanceSessionGeneration();
  vi.useRealTimers();
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-10-06T12:00:30Z"));
  vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
});
afterEach(() => {
  clients.splice(0).forEach((client) => client.clear());
  vi.useRealTimers();
});

describe("JUP-047 system health public flow", () => {
  it("adds an accessible navigation entry inside the authenticated layout", async () => {
    await mount();
    expect(screen.getByRole("link", { name: /salud del sistema/i })).toHaveAttribute("href", "/system-health");
    expect(screen.getByRole("combobox", { name: "Ambito de cliente" })).toBeVisible();
    expect(screen.getByRole("button", { name: /actualizar/i })).toBeEnabled();
  });

  it("protects direct dashboard entry before sending any diagnostics", async () => {
    requirePublicRoute();
    const { requests } = mockBackend();
    renderApp(["/system-health"]);
    expect(await screen.findByRole("button", { name: /entrar|iniciar|sign in|log in/i })).toBeVisible();
    expect(requests.filter((r) => r.path.startsWith("/health"))).toEqual([]);
  });

  it("opening and one manual action each send exactly one tenant-authenticated POST", async () => {
    const user = userEvent.setup();
    const { requests } = await mount();
    await waitFor(() => expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1));
    requests.filter((r) => r.path === statusPath || r.path === checkPath).forEach((r) => expectTenantRequest(r));
    const opening = requests.find((r) => r.path === checkPath)!;
    expect(opening.method).toBe("POST");
    expect(Object.keys(opening.body as object)).toEqual(["idempotency_key"]);
    expect((opening.body as { idempotency_key: string }).idempotency_key).toBeTruthy();
    await user.click(screen.getByRole("button", { name: /actualizar/i }));
    await waitFor(() => expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2));
    const manual = requests.filter((r) => r.path === checkPath)[1];
    expect(manual.body).not.toEqual(opening.body);
    expectTenantRequest(manual);
  });

  it("StrictMode does not duplicate the opening inference intent", async () => {
    const { requests } = await mount({}, true);
    await waitFor(() => expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1));
    await act(async () => { await Promise.resolve(); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
  });

  it("30-second visible polling issues only GET and preserves the provider verification date", async () => {
    useHealthTimers();
    const { requests } = await mount();
    await waitFor(() => expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1));
    const before = requests.filter((r) => r.path === statusPath).length;
    await act(async () => { await vi.advanceTimersByTimeAsync(30_000); });
    expect(requests.filter((r) => r.path === statusPath).length).toBeGreaterThan(before);
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    expect(screen.getByText(/respuesta válida a/i)).toBeVisible();
  });

  it("hidden pages suspend polling and unmount stops both request types", async () => {
    useHealthTimers();
    const { requests, unmount } = await mount();
    await waitFor(() => expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1));
    vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
    await act(async () => { document.dispatchEvent(new Event("visibilitychange")); });
    const before = requests.length;
    await act(async () => { await vi.advanceTimersByTimeAsync(60_000); });
    expect(requests).toHaveLength(before);
    unmount();
    await act(async () => { await vi.advanceTimersByTimeAsync(60_000); });
    expect(requests).toHaveLength(before);
  });

  it.each([409, 429, 503])("provider refusal/error %s is visible and never automatically retried", async (code) => {
    useHealthTimers();
    const { requests } = await mount({ [`POST ${checkPath}`]: () => jsonResponse({ reason_code: code === 409 ? "busy" : code === 429 ? "cooldown" : "upstream_error", retry_after: 60 }, code) });
    expect((await screen.findAllByText(/ocupad|esper|error|no se pudo|enfriamiento|disponible/i)).length).toBeGreaterThan(0);
    await act(async () => { await vi.advanceTimersByTimeAsync(90_000); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    expect(screen.queryByText(/respuesta válida a/i)).not.toBeInTheDocument();
  });

  it("a stale provider observation remains dated and never claims a new successful check", async () => {
    vi.setSystemTime(new Date("2026-10-06T12:02:00Z"));
    const snapshot = diagnostic();
    Object.assign(snapshot.components.find((c) => c.id === "openrouter")!, { status: "unknown", reason_code: "stale", verified_at: verified, last_attempt_at: verified, expires_at: "2026-10-06T12:01:00Z" });
    snapshot.checked_at = "2026-10-06T12:02:00Z";
    snapshot.window = { start: "2026-10-05T12:02:00Z", end: snapshot.checked_at };
    await mount({ [`GET ${statusPath}`]: () => jsonResponse(snapshot), [`POST ${checkPath}`]: () => jsonResponse({ reason_code: "cooldown", retry_after: 60 }, 429) });
    expect(await screen.findByText(/obsolet|caducad|sin verificar|desactualizad/i)).toBeVisible();
    expect(screen.getByText(/respuesta válida a/i)).toBeVisible();
  });

  it("unavailable data never turns into invented zero history", async () => {
    const snapshot = diagnostic();
    Object.assign(snapshot.ingestion, { data_status: "unavailable", counts: null, failed_last_24h: null });
    const { requests } = await mount({ [`GET ${statusPath}`]: () => jsonResponse(snapshot), [`POST ${checkPath}`]: () => jsonResponse({ reason_code: "budget_unavailable" }, 429) });
    const ingestion = within(screen.getByRole("heading", { name: "Ingesta de costes" }).closest("section")!);
    expect(await ingestion.findByText(/no disponible|sin datos disponibles/i)).toBeVisible();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    expect(screen.getByText(/simulad/i)).toBeVisible();
  });

  it.each([{ status: "ok" }, { ...diagnostic(), status: "invented-green" }])("rejects malformed diagnostic payload rather than fabricating health", async (payload) => {
    await mount({ [`GET ${statusPath}`]: () => jsonResponse(payload), [`POST ${checkPath}`]: () => jsonResponse({ reason_code: "budget_unavailable" }, 429) });
    expect((await screen.findAllByText(/no disponible|error|no se pudo|invalid/i)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/todos los sistemas.*correct|sistema.*saludable/i)).not.toBeInTheDocument();
  });

  it.each(["success", "error"] as const)("discards late old-tenant GET/POST %s after changing scope", async (outcome) => {
    const pendingStatus = deferredResponse();
    const pendingCheck = deferredResponse();
    const user = userEvent.setup();
    const { requests } = await mount({
      [`GET ${statusPath}`]: ({ headers }) => headers.get("X-Tenant-Id") === tenants[0].id ? pendingStatus.promise : jsonResponse(diagnostic(tenants[1].id)),
      [`POST ${checkPath}`]: ({ headers }) => headers.get("X-Tenant-Id") === tenants[0].id ? pendingCheck.promise : jsonResponse({ reason_code: "cooldown" }, 429)
    });
    await user.selectOptions(screen.getByRole("combobox", { name: "Ambito de cliente" }), tenants[1].id);
    await waitFor(() => expect(requests.some((r) => r.path === statusPath && r.headers.get("X-Tenant-Id") === tenants[1].id)).toBe(true));
    await act(async () => {
      pendingStatus.resolve(diagnostic(tenants[0].id, "failed"), outcome === "success" ? 200 : 503);
      pendingCheck.resolve(provider(), outcome === "success" ? 200 : 503);
    });
    expect(screen.queryByText(/respuesta válida a/i)).not.toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Ambito de cliente" })).toHaveValue(tenants[1].id);
  });

  it("logout ignores an old generation and stops timers", async () => {
    useHealthTimers();
    const pending = deferredResponse();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const { requests } = await mount({ [`POST ${checkPath}`]: () => pending.promise });
    await waitFor(() => expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1));
    await user.click(screen.getByRole("button", { name: "Cerrar sesion" }));
    await act(async () => { pending.resolve(provider()); });
    expect(screen.queryByRole("heading", { name: /salud del sistema/i })).not.toBeInTheDocument();
    const before = requests.length;
    await act(async () => { await vi.advanceTimersByTimeAsync(60_000); });
    expect(requests).toHaveLength(before);
  });

  it.each([200, 401])("a late old-session provider response %s cannot replace or invalidate a new session", async (code) => {
    const pending = deferredResponse();
    const user = userEvent.setup();
    const { requests, router } = await mount({
      "POST /auth/login": () => jsonResponse({ ...loginResponse, access_token: "synthetic-fresh-token" }),
      [`POST ${checkPath}`]: ({ headers }) => headers.get("Authorization") === "Bearer synthetic-fresh-token"
        ? jsonResponse({ reason_code: "cooldown" }, 429) : pending.promise
    });
    await waitFor(() => expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1));
    await user.click(screen.getByRole("button", { name: "Cerrar sesion" }));
    await user.clear(screen.getByLabelText("Email"));
    await user.type(screen.getByLabelText("Email"), "synthetic@example.com");
    await user.type(screen.getByLabelText("Password"), "synthetic-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    await screen.findByRole("button", { name: "Cerrar sesion" });
    await act(async () => { await router.navigate("/system-health"); });
    await waitFor(() => expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2));
    await act(async () => { pending.resolve(code === 200 ? provider() : { detail: "Unauthorized" }, code); });
    expect(JSON.parse(window.localStorage.getItem(SESSION_KEY) ?? "null").accessToken).toBe("synthetic-fresh-token");
    expect(router.state.location.pathname).toBe("/system-health");
    expect(screen.queryByText(/respuesta válida a/i)).not.toBeInTheDocument();
  });

  it.each([[statusPath, 7_000], [checkPath, 35_000]] as const)("aborts a stalled %s at its client deadline %sms without retrying inference", async (path, deadline) => {
    useHealthTimers();
    const pending = deferredResponse();
    const { requests, signals } = await mount({ [`${path === statusPath ? "GET" : "POST"} ${path}`]: () => pending.promise });
    await act(async () => { await vi.advanceTimersByTimeAsync(deadline - 1); });
    expect(signals.find((entry) => entry.path === path)?.signal?.aborted).toBe(false);
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(signals.find((entry) => entry.path === path)?.signal?.aborted).toBe(true);
    expect(requests.filter((request) => request.path === checkPath)).toHaveLength(1);
  });

  it.each([390, 768, 1440])("retains shared card tokens, headings and textual provenance at viewport %spx", async (width) => {
    vi.stubGlobal("innerWidth", width);
    const { container } = await mount();
    expect(screen.getByRole("heading", { level: 1, name: /salud del sistema/i })).toBeVisible();
    expect(await screen.findByText(/simulad/i)).toBeVisible();
    expect(screen.getAllByText(/OpenRouter/i).length).toBeGreaterThan(0);
    const cards = container.querySelectorAll("section.from-card.border-border, article.from-card.border-border");
    expect(cards.length).toBeGreaterThan(1);
    cards.forEach((card) => expect(card.className).toContain("rounded-lg"));
    // jsdom proves semantic/style integration only, not pixels or overflow.
  });
});


describe("JUP-047 elapsed verification and first scope render", () => {
  it.each([[30, false], [61, false]] as const)("retains successful observations at %ss without age expiry", async (seconds, stale) => {
    vi.setSystemTime(new Date(Date.parse(verified) + seconds * 1000));
    const snapshot = diagnostic();
    Object.assign(snapshot.components.find((component) => component.id === "openrouter")!, provider());
    await mount({ [`GET ${statusPath}`]: () => jsonResponse(snapshot), [`POST ${checkPath}`]: () => jsonResponse(provider()) });
    expect(await screen.findByText(/respuesta válida a/i)).toHaveTextContent(verified);
    if (stale) expect(await screen.findByText("Verificación desactualizada")).toBeVisible();
    else expect(screen.queryByText("Verificación desactualizada")).not.toBeInTheDocument();
  });

  it("hides the previous tenant stamp on the first commit before passive effects", async () => {
    const pending = deferredResponse();
    const stampA = "2026-10-06T11:40:00Z";
    const stampB = "2026-10-06T11:50:00Z";
    const a = diagnostic(tenants[0].id); a.jobs.last_updated_at = stampA;
    const b = diagnostic(tenants[1].id); b.jobs.last_updated_at = stampB;
    mockBackend({
      [`GET ${statusPath}`]: ({ headers }) => headers.get("X-Tenant-Id") === tenants[0].id ? jsonResponse(a) : pending.promise,
      [`POST ${checkPath}`]: () => jsonResponse(provider())
    });
    restoreSession(tenants[0].id);
    const commits: { tenant: string; stamp: string | null; loading: boolean }[] = [];
    function ScopeView({ tenant }: { tenant: string }) {
      const health = useSystemHealth(loginResponse.access_token, tenant, "scope-test-entry");
      useLayoutEffect(() => {
        commits.push({ tenant, stamp: screen.getByTestId("scope-stamp").textContent, loading: health.loading });
      }, [health.loading, tenant]);
      return <output data-testid="scope-stamp">{health.data?.jobs.last_updated_at ?? "loading"}</output>;
    }
    const view = render(<ScopeView tenant={tenants[0].id} />);
    await waitFor(() => expect(screen.getByTestId("scope-stamp")).toHaveTextContent(stampA));
    view.rerender(<ScopeView tenant={tenants[1].id} />);
    expect(commits.find((commit) => commit.tenant === tenants[1].id)).toEqual({ tenant: tenants[1].id, stamp: "loading", loading: true });
    expect(screen.getByTestId("scope-stamp")).not.toHaveTextContent(stampA);
    await act(async () => { pending.resolve(b); });
    await waitFor(() => expect(screen.getByTestId("scope-stamp")).toHaveTextContent(stampB));
    expect(screen.getByTestId("scope-stamp")).not.toHaveTextContent(stampA);
  });
});


describe("JUP-047 approved exact expiry and cancelled opening intent", () => {
  it.each([[59_999, false], [60_000, false], [60_001, false]] as const)("retains the backend observation at %sms and preserves verified_at", async (milliseconds, expired) => {
    vi.setSystemTime(new Date(Date.parse(verified) + milliseconds));
    const snapshot = diagnostic();
    Object.assign(snapshot.components.find((component) => component.id === "openrouter")!, provider());
    const { requests } = await mount({ [`GET ${statusPath}`]: () => jsonResponse(snapshot), [`POST ${checkPath}`]: () => jsonResponse(provider()) });
    expect(await screen.findByText(/respuesta válida a/i)).toHaveTextContent(verified);
    const row = screen.getByText("OpenRouter").closest("li");
    expect(row).not.toBeNull();
    await waitFor(() => expect(within(row!).getByText(expired ? "no verificado" : "Disponible")).toBeVisible());
    if (expired) expect(await screen.findByText("Verificación desactualizada")).toBeVisible();
    else expect(screen.queryByText("Verificación desactualizada")).not.toBeInTheDocument();
    expect(screen.getByText(/respuesta válida a/i)).toHaveTextContent(verified);
    expect(requests.filter((request) => request.method === "POST" && request.path === checkPath)).toHaveLength(1);
  });

  it("unmounts synchronously before the opening microtask without a provider send", async () => {
    const pendingGet = deferredResponse();
    let providerSends = 0;
    const { requests } = mockBackend({
      [`GET ${statusPath}`]: () => pendingGet.promise,
      [`POST ${checkPath}`]: () => { providerSends += 1; return jsonResponse(provider()); }
    });
    restoreSession(tenants[0].id);
    function OpeningIntent() {
      useSystemHealth(loginResponse.access_token, tenants[0].id, "cancelled-entry");
      return null;
    }
    let microtasksDrained = false;
    const marker = Promise.resolve().then(() => { microtasksDrained = true; });
    const view = render(<OpeningIntent />);
    // This proves the effect ran; mounting/unmounting an uncommitted root
    // would exercise no queued opening intent and would be a false detector.
    expect(requests.filter((request) => request.method === "GET" && request.path === statusPath)).toHaveLength(1);
    expect(providerSends).toBe(0);
    view.unmount();
    expect(microtasksDrained).toBe(false);
    await act(async () => { await marker; await Promise.resolve(); await Promise.resolve(); });
    expect(microtasksDrained).toBe(true);
    expect(providerSends).toBe(0);
    expect(requests.filter((request) => request.method === "POST" && request.path === checkPath)).toHaveLength(0);
    expect(requests.filter((request) => request.method === "GET" && request.path === statusPath)).toHaveLength(1);
    await act(async () => { pendingGet.resolve(diagnostic()); });
    expect(providerSends).toBe(0);
    expect(requests.filter((request) => request.method === "POST" && request.path === checkPath)).toHaveLength(0);
    expect(requests.filter((request) => request.method === "GET" && request.path === statusPath)).toHaveLength(1);
  });
});


describe("JUP-047 approved functional availability and informational identity/cost", () => {
  function information(model: string | null = "economicon-chat", extra: Record<string, unknown> = {}) {
    return { ...provider(), reported_model: model, model_identity: "unconfirmed",
      reported_cost_usd: "0.00002", cost_status: "gateway_reported", cost_confirmation: "unconfirmed", ...extra };
  }

  function providerRow() {
    return within(screen.getByText("OpenRouter", { exact: true }).closest("li")!);
  }

  it.each(["economicon-chat", "openrouter/z-ai/glm-5.2", "z-ai/glm-5.2-20260616", "other-model"])(
    "shows available functional response and unconfirmed identity for %s", async (model) => {
      await mount({ [`POST ${checkPath}`]: () => jsonResponse(information(model)) });
      const row = providerRow();
      expect(await row.findByText("Disponible", { exact: true })).toBeVisible();
      expect(row.getByText(/Respuesta válida a:/i)).toHaveTextContent(verified);
      expect(row.getByText(`Modelo informado: ${model}`, { exact: true })).toBeVisible();
      expect(row.getByText("Identidad no confirmada", { exact: true })).toBeVisible();
      expect(row.getByText(/Coste informado por el gateway:/i)).toHaveTextContent("0.00002");
      expect(row.getByText(/Coste informado por el gateway:/i)).toHaveTextContent(/No confirmado/i);
      expect(row.queryByText(/modelo verificado|coste confirmado|gratis/i)).not.toBeInTheDocument();
    }
  );

  it.each([
    ["unavailable", null, "Coste no disponible"],
    ["invalid", null, "Dato de coste no válido"],
    ["gateway_reported", "0", "Coste informado por el gateway:"],
  ])("keeps functional availability while cost is %s", async (cost_status, reported_cost_usd, label) => {
    await mount({ [`POST ${checkPath}`]: () => jsonResponse(information(null, { cost_status, reported_cost_usd })) });
    const row = providerRow();
    expect(await row.findByText("Disponible", { exact: true })).toBeVisible();
    expect(row.getByText("Modelo no informado", { exact: true })).toBeVisible();
    expect(row.getByText("Identidad no confirmada", { exact: true })).toBeVisible();
    expect(row.getByText(new RegExp(label, "i"))).toBeVisible();
    expect(row.queryByText(/gratis|coste confirmado/i)).not.toBeInTheDocument();
  });

  it("uses the selected POST attempt information rather than old GET information", async () => {
    const snapshot = diagnostic();
    Object.assign(snapshot.components.find((item) => item.id === "openrouter")!,
      information("old-get-model", { reported_cost_usd: "0.00001",
        verified_at: "2026-10-06T11:59:50Z", last_attempt_at: "2026-10-06T11:59:50Z" }));
    await mount({ [`GET ${statusPath}`]: () => jsonResponse(snapshot),
      [`POST ${checkPath}`]: () => jsonResponse(information("new-post-model")) });
    const row = providerRow();
    expect(await row.findByText("Modelo informado: new-post-model", { exact: true })).toBeVisible();
    expect(row.queryByText(/old-get-model|0\.00001/)).not.toBeInTheDocument();
    expect(row.getByText(/Respuesta válida a:/i)).toHaveTextContent(verified);
  });

  it("does not render informational data from a late abandoned tenant response", async () => {
    const pending = deferredResponse();
    const user = userEvent.setup();
    const { requests } = await mount({
      [`POST ${checkPath}`]: ({ headers }) => headers.get("X-Tenant-Id") === tenants[0].id
        ? pending.promise : jsonResponse(information("current-tenant-model"))
    });
    await user.selectOptions(screen.getByRole("combobox", { name: "Ambito de cliente" }), tenants[1].id);
    await waitFor(() => expect(requests.filter((request) => request.path === checkPath)).toHaveLength(2));
    await act(async () => { pending.resolve(information("abandoned-tenant-model", { reported_cost_usd: "999" })); });
    const row = providerRow();
    expect(await row.findByText("Modelo informado: current-tenant-model", { exact: true })).toBeVisible();
    expect(row.queryByText(/abandoned-tenant-model|999/)).not.toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Ambito de cliente" })).toHaveValue(tenants[1].id);
  });
});


function RetentionProbe({ entry = "retention-entry", name = "probe" }: { entry?: string; name?: string }) {
  const health = useSystemHealth(loginResponse.access_token, tenants[0].id, entry);
  return <><button onClick={health.refresh}>Probe refresh {name}</button><output data-testid={name}>{JSON.stringify({
    state: health.providerStatus, reason: health.providerReason, verified: health.verified,
    checked: health.provider?.checked_at, last: health.provider?.last_attempt_at
  })}</output></>;
}
async function drainRetention() {
  for (let i = 0; i < 5; i += 1) await act(async () => { await vi.advanceTimersByTimeAsync(0); });
}
function probeValue() { return JSON.parse(screen.getByTestId("probe").textContent ?? "{}"); }
function probeBackend(overrides: Parameters<typeof mockBackend>[0] = {}) {
  const backend = mockBackend({
    ["GET " + statusPath]: () => jsonResponse(diagnostic()),
    ["POST " + checkPath]: () => jsonResponse(provider()), ...overrides
  });
  // Browser fetch rejects on abort; the deferred in-memory double must do so too.
  const intercepted = globalThis.fetch;
  vi.stubGlobal("fetch", vi.fn<typeof fetch>(async (input, init) => {
    const signal = init?.signal;
    if (!signal) return intercepted(input, init);
    let listener!: () => void;
    const aborted = new Promise<never>((_, reject) => {
      listener = () => reject(new DOMException("Aborted", "AbortError"));
      signal.addEventListener("abort", listener, { once: true });
      if (signal.aborted) listener();
    });
    try { return await Promise.race([intercepted(input, init), aborted]); }
    finally { signal.removeEventListener("abort", listener); }
  }));
  return backend;
}
describe("JUP-047 retained result and visible ten-minute lifecycle", () => {
  it("dispatches periodically at exactly 600000ms, not 599999, with GET isolated", async () => {
    useHealthTimers();
    const { requests } = probeBackend();
    render(<RetentionProbe />); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(599_999); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    expect(probeValue().state).toBe("ok");
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2);
    await act(async () => { await vi.advanceTimersByTimeAsync(600_000); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(3);
    expect(requests.filter((r) => r.path === statusPath).every((r) => r.method === "GET")).toBe(true);
  });
  it("does not start hidden and coalesces overdue reentry without catch-up", async () => {
    useHealthTimers();
    const visibility = vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
    const { requests } = probeBackend(); render(<RetentionProbe />); await drainRetention();
    await act(async () => { await vi.advanceTimersByTimeAsync(1_800_000); });
    expect(requests).toHaveLength(0);
    visibility.mockReturnValue("visible");
    await act(async () => { document.dispatchEvent(new Event("visibilitychange")); }); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    visibility.mockReturnValue("hidden");
    await act(async () => { document.dispatchEvent(new Event("visibilitychange")); await vi.advanceTimersByTimeAsync(1_800_000); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    visibility.mockReturnValue("visible");
    await act(async () => { document.dispatchEvent(new Event("visibilitychange")); }); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2);
    await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2);
  });
  it("preserves remaining time across a short hidden pause", async () => {
    useHealthTimers(); const { requests } = probeBackend(); render(<RetentionProbe />); await drainRetention();
    await act(async () => { await vi.advanceTimersByTimeAsync(300_000); });
    const visibility = vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
    await act(async () => { document.dispatchEvent(new Event("visibilitychange")); await vi.advanceTimersByTimeAsync(100_000); });
    visibility.mockReturnValue("visible");
    await act(async () => { document.dispatchEvent(new Event("visibilitychange")); await vi.advanceTimersByTimeAsync(199_999); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2);
  });
  it("manual dispatch resets the deadline and cannot overlap a periodic request", async () => {
    useHealthTimers(); let calls = 0; const pending = deferredResponse();
    const { requests } = probeBackend({ ["POST " + checkPath]: () => ++calls === 3 ? pending.promise : jsonResponse(provider()) });
    render(<RetentionProbe />); await drainRetention();
    await act(async () => { await vi.advanceTimersByTimeAsync(300_000); screen.getByText("Probe refresh probe").click(); }); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2);
    await act(async () => { await vi.advanceTimersByTimeAsync(599_999); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2);
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(3);
    await act(async () => { screen.getByText("Probe refresh probe").click(); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(3);
    await act(async () => { pending.resolve(provider()); });
  });
  it("remounting the same entry keeps one opening and its existing deadline", async () => {
    useHealthTimers(); const { requests } = probeBackend();
    const view = render(<RetentionProbe />); await drainRetention();
    await act(async () => { await vi.advanceTimersByTimeAsync(300_000); }); view.unmount();
    render(<RetentionProbe />); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(300_000); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2);
  });
  it("duplicate consumers share ownership and a genuinely new navigation opens once", async () => {
    useHealthTimers(); const { requests } = probeBackend();
    const view = render(<><RetentionProbe name="a" /><RetentionProbe name="b" /></>); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    view.rerender(<><RetentionProbe entry="new-entry" name="a" /><RetentionProbe entry="new-entry" name="b" /></>); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2);
  });
  it.each([false, true])("returning to the same historical entry preserves shared deadline, manual=%s", async (manual) => {
    useHealthTimers(); const { requests } = probeBackend();
    const view = render(<RetentionProbe entry="history-a" />); await drainRetention();
    await act(async () => { await vi.advanceTimersByTimeAsync(100_000); });
    view.rerender(<RetentionProbe entry="history-b" />); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(2);
    await act(async () => { await vi.advanceTimersByTimeAsync(100_000); });
    if (manual) {
      await act(async () => { screen.getByText("Probe refresh probe").click(); }); await drainRetention();
    }
    const expected = manual ? 3 : 2;
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(expected);
    view.rerender(<RetentionProbe entry="history-a" />); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(expected);
    await act(async () => { await vi.advanceTimersByTimeAsync((manual ? 600_000 : 500_000) - 1); });
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(expected);
    await act(async () => { await vi.advanceTimersByTimeAsync(1); }); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(expected + 1);
    await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(expected + 1);
  });
  it("keeps the last real success when a manual action is refused without sending", async () => {
    useHealthTimers(); let calls = 0;
    probeBackend({ ["POST " + checkPath]: () => ++calls === 1 ? jsonResponse(provider()) : jsonResponse({ reason_code: "cooldown" }, 429) });
    render(<RetentionProbe />); await drainRetention();
    await act(async () => { screen.getByText("Probe refresh probe").click(); }); await drainRetention();
    expect(probeValue()).toMatchObject({ state: "ok", reason: "cooldown", verified });
  });
  it("new client timeout stays unknown despite an older GET and retains successful history", async () => {
    useHealthTimers(); let calls = 0; const pending = deferredResponse();
    const old = diagnostic(); Object.assign(old.components.find((c) => c.id === "openrouter")!, provider());
    probeBackend({ ["GET " + statusPath]: () => jsonResponse(old),
      ["POST " + checkPath]: () => ++calls === 1 ? jsonResponse(provider()) : pending.promise });
    render(<RetentionProbe />); await drainRetention();
    await act(async () => { await vi.advanceTimersByTimeAsync(61_000); screen.getByText("Probe refresh probe").click(); }); await drainRetention();
    await act(async () => { await vi.advanceTimersByTimeAsync(35_000); });
    expect(probeValue()).toMatchObject({ state: "unknown", reason: "timeout", verified });
    await act(async () => { await vi.advanceTimersByTimeAsync(30_000); });
    expect(probeValue()).toMatchObject({ state: "unknown", reason: "timeout", verified });
  });
  it("visible unmount releases every active health timer and prevents future dispatch", async () => {
    useHealthTimers(); const { requests } = probeBackend();
    const view = render(<RetentionProbe />); await drainRetention();
    expect(document.visibilityState).toBe("visible");
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    expect(vi.getTimerCount()).toBeGreaterThan(0);
    view.unmount();
    expect(vi.getTimerCount()).toBe(0);
    const before = requests.length;
    await act(async () => { await vi.advanceTimersByTimeAsync(1_800_000); });
    expect(requests).toHaveLength(before);
    expect(vi.getTimerCount()).toBe(0);
  });
  it("stops periodic checks on unmount and does not dispatch manual actions while hidden", async () => {
    useHealthTimers(); const { requests } = probeBackend(); const view = render(<RetentionProbe />); await drainRetention();
    vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
    await act(async () => { document.dispatchEvent(new Event("visibilitychange")); screen.getByText("Probe refresh probe").click(); }); await drainRetention();
    expect(requests.filter((r) => r.path === checkPath)).toHaveLength(1);
    view.unmount(); const before = requests.length;
    await act(async () => { await vi.advanceTimersByTimeAsync(1_800_000); });
    expect(requests).toHaveLength(before);
  });
  it.each([0, 29, 40, 999, 1000, 1001, 60000])("uses one bounded observation clock for simulator/gateway at +%sms", async (offset) => {
    const snapshot = diagnostic();
    const stamp = new Date(Date.now() + offset).toISOString();
    for (const id of ["azure_cost_api", "litellm"]) snapshot.components.find((c) => c.id === id)!.checked_at = stamp;
    await mount({ ["GET " + statusPath]: () => jsonResponse(snapshot) });
    for (const label of ["Servicio de costes Azure", "Gateway de modelos"]) {
      const row = within(screen.getByText(label).closest("li")!);
      expect(row.getByText(offset <= 1000 ? "correcto" : "no verificado")).toBeVisible();
      if (offset <= 1000) {
        expect(row.queryByText(/Fecha no disponible/)).not.toBeInTheDocument();
        expect(row.getByText(/Observación:/)).toHaveTextContent(stamp);
      }
    }
    const providerRow = within(screen.getByText("OpenRouter").closest("li")!);
    expect(await providerRow.findByText("Disponible", { exact: true })).toBeVisible();
    await waitFor(() => expect(providerRow.queryByText("Comprobando…")).not.toBeInTheDocument());
    const metric = within(screen.getByText("Servicios correctos").closest("article")!);
    expect(metric.getByText(offset <= 1000 ? "8" : "6", { exact: true })).toBeVisible();
    expect(screen.getByText(/SIMULADO: no acredita/)).toBeVisible();
  });
  it.each([40, 1000, 1001])("applies the same finite tolerance to real verified timestamps +%sms", async (offset) => {
    const stamp = new Date(Date.now() + offset).toISOString();
    const item = { ...provider(), checked_at: stamp, verified_at: stamp, last_attempt_at: stamp };
    await mount({ ["POST " + checkPath]: () => jsonResponse(item) });
    const row = within(screen.getByText("OpenRouter").closest("li")!);
    expect(row.getByText(offset <= 1000 ? "Disponible" : "no verificado")).toBeVisible();
    if (offset <= 1000) expect(row.getByText(/Respuesta válida a:/)).toHaveTextContent(stamp);
  });
});
