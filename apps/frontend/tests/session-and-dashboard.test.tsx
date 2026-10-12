import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { billing, billingWithCost, health, loginResponse, session, tenants } from "./fixtures";
import {
  deferredResponse,
  expectTenantRequest,
  jsonResponse,
  mockBackend,
  renderApp,
  restoreSession,
  SESSION_KEY,
  TENANT_KEY
} from "./test-support";

describe("login and session recovery", () => {
  it("submits credentials, exposes pending states and opens the authenticated home screen", async () => {
    const user = userEvent.setup();
    const authentication = deferredResponse();
    const bootstrap = deferredResponse();
    const { requests } = mockBackend({
      "POST /auth/login": () => authentication.promise,
      "GET /tenants": () => bootstrap.promise
    });
    renderApp();

    expect(screen.getByLabelText("Contraseña")).toHaveValue("");
    await user.clear(screen.getByLabelText("Correo electrónico"));
    await user.type(screen.getByLabelText("Correo electrónico"), "operator@example.com");
    await user.clear(screen.getByLabelText("Contraseña"));
    await user.type(screen.getByLabelText("Contraseña"), "test-password");
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));

    expect(screen.getByRole("button", { name: "Iniciando sesión..." })).toBeDisabled();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    const loginRequest = requests.find((request) => request.path === "/auth/login");
    expect(loginRequest?.body).toEqual({ email: "operator@example.com", password: "test-password" });
    expect(loginRequest?.headers.has("Authorization")).toBe(false);
    expect(loginRequest?.headers.has("X-Tenant-Id")).toBe(false);

    await act(async () => authentication.resolve(loginResponse));
    // SessionGate.tsx presenta este estado en espanol (armazon nuevo de
    // JUP-095, no una pantalla portada del origen ingles).
    expect(await screen.findByRole("heading", { name: "Cargando clientes disponibles..." })).toBeVisible();
    expect(JSON.parse(window.localStorage.getItem(SESSION_KEY)!)).toEqual(session);
    await act(async () => bootstrap.resolve({ items: tenants }));

    // Reconciliacion con develop (JUP-095): `LoginPage.onSuccess` navega
    // siempre a "/" (indice), que hoy es `ExecutiveCostDashboard` con datos
    // de demostracion -- no `DashboardPage` (billing/health reales), que
    // vive en "/overview-legacy" (ruta puente, ver design.md decision 6).
    // Esta prueba valida la mecanica de login/persistencia; el contenido
    // especifico del dashboard conectado al backend lo cubren las pruebas de
    // "tenant bootstrap and dashboard" mas abajo, que navegan explicitamente
    // a "/overview-legacy".
    expect(await screen.findByText("Panel Ejecutivo - Coste Global")).toBeVisible();
    expect(screen.getByLabelText("Ámbito de cliente")).toHaveValue(tenants[0].id);
    expect(window.localStorage.getItem(TENANT_KEY)).toBe(tenants[0].id);
  });

  it.each([
    { name: "invalid credentials", error: "Invalid email or password.", network: false },
    { name: "network failure", error: "Unable to reach authentication service", network: true }
  ])("shows $name without saving a session and permits retry", async ({ error, network }) => {
    const user = userEvent.setup();
    let attempts = 0;
    mockBackend({
      "POST /auth/login": () => {
        attempts += 1;
        if (attempts > 1) return jsonResponse(loginResponse);
        if (network) throw new TypeError(error);
        return jsonResponse({ detail: error }, 401);
      }
    });
    renderApp();
    expect(screen.getByLabelText("Contraseña")).toHaveValue("");
    await user.type(screen.getByLabelText("Contraseña"), "test-password");
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));

    expect(await screen.findByText(new RegExp(error))).toBeVisible();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
    expect(screen.getByRole("button", { name: "Iniciar sesión" })).toBeEnabled();

    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));
    // Mismo razonamiento que el test anterior: tras login, "/" muestra
    // ExecutiveCostDashboard (demo), no el dashboard conectado al backend.
    expect(await screen.findByText("Panel Ejecutivo - Coste Global")).toBeVisible();
  });

  it("restores the saved session and tenant across reloads, then clears data on logout", async () => {
    const user = userEvent.setup();
    const { requests } = mockBackend();
    restoreSession(tenants[1].id);
    // "/overview-legacy": esta prueba verifica que la cache de react-query se
    // repuebla con datos reales entre "recargas" -- necesita el dashboard
    // conectado al backend (billing/health), no la pantalla de demostracion
    // de "/", que nunca invoca esos endpoints.
    const firstVisit = renderApp(["/overview-legacy"]);
    await screen.findByText("Gasto mensual");
    expect(screen.getByLabelText("Ámbito de cliente")).toHaveValue(tenants[1].id);
    firstVisit.unmount();
    firstVisit.client.clear();

    const reloaded = renderApp(["/overview-legacy"]);
    await screen.findByText("Gasto mensual");
    expect(screen.getByLabelText("Ámbito de cliente")).toHaveValue(tenants[1].id);
    expect(requests.some((request) => request.path === "/auth/login")).toBe(false);
    expect(reloaded.client.getQueryCache().getAll().some((query) => query.state.data !== undefined)).toBe(true);

    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(screen.getByRole("heading", { name: "Accede al centro de control de clientes" })).toBeVisible();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
    expect(reloaded.client.getQueryCache().getAll().every((query) => query.state.data === undefined)).toBe(true);
  });

  it("recovers from invalid stored JSON without contacting authenticated endpoints", () => {
    const { requests } = mockBackend();
    window.localStorage.setItem(SESSION_KEY, "{broken-json");
    window.localStorage.setItem(TENANT_KEY, tenants[0].id);
    renderApp();

    expect(screen.getByRole("button", { name: "Iniciar sesión" })).toBeEnabled();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
    expect(requests).toEqual([]);
  });
});

describe("tenant bootstrap and dashboard", () => {
  it("replaces a stale tenant selection and scopes billing requests to each selected tenant", async () => {
    const user = userEvent.setup();
    const southBilling = billingWithCost("9876.00");
    const { requests } = mockBackend({
      "GET /billing/summary": (request) => jsonResponse(
        request.headers.get("X-Tenant-Id") === tenants[1].id ? southBilling : billing
      )
    });
    restoreSession("tenant-no-longer-authorized");
    renderApp(["/overview-legacy"]);

    expect(await screen.findByText(new RegExp(billing.monthly_spend))).toBeVisible();
    expect(screen.getByLabelText("Ámbito de cliente")).toHaveValue(tenants[0].id);
    expect(window.localStorage.getItem(TENANT_KEY)).toBe(tenants[0].id);
    const bootstrap = requests.find((request) => request.path === "/tenants");
    expect(bootstrap?.headers.get("Authorization")).toBe(`Bearer ${session.accessToken}`);
    expect(bootstrap?.headers.has("X-Tenant-Id")).toBe(false);

    await user.selectOptions(screen.getByLabelText("Ámbito de cliente"), tenants[1].id);
    expect(await screen.findByText(new RegExp(southBilling.monthly_spend))).toBeVisible();
    expect(window.localStorage.getItem(TENANT_KEY)).toBe(tenants[1].id);
    const billingRequests = requests.filter((request) => request.path === "/billing/summary");
    expect(billingRequests).toHaveLength(2);
    expectTenantRequest(billingRequests[0]);
    expectTenantRequest(billingRequests[1], tenants[1].id);
    expect(screen.getByRole("heading", { name: "Salud de los servicios" })).toBeVisible();
    for (const service of Object.keys(health.services)) expect(screen.getByText(service)).toBeVisible();
  });

  it("muestra en español el estado de cada servicio y deja pasar uno que no conoce", async () => {
    mockBackend({
      "GET /health": () => jsonResponse({
        ...health,
        services: { database: "ok", rabbitmq: "degraded", vector_store: "failed", queue: "unknown", cache: "paused", extra: "toString" }
      })
    });
    restoreSession();
    renderApp(["/overview-legacy"]);

    await screen.findByText("correcto");
    const row = (service: string) => screen.getByText(service).parentElement as HTMLElement;
    expect(row("database")).toHaveTextContent("correcto");
    expect(row("rabbitmq")).toHaveTextContent("degradado");
    expect(row("vector_store")).toHaveTextContent("fallido");
    expect(row("queue")).toHaveTextContent("no verificado");
    expect(row("cache")).toHaveTextContent("paused");
    expect(row("extra")).toHaveTextContent("tostring");
  });

  // Reactivado (Punto 5 implementado): Layout ya expone enlaces reales hacia
  // /ingest y /assistant. Son <NavLink> (role "link"), no botones -- se
  // ajustan los roles/etiquetas a la UI real en vez de a los del AppShell
  // original.
  it("handles an empty tenant list without issuing tenant-scoped product requests", async () => {
    const user = userEvent.setup();
    const { requests } = mockBackend({ "GET /tenants": () => jsonResponse({ items: [] }) });
    restoreSession();
    renderApp(["/overview-legacy"]);

    expect(await screen.findByRole("heading", { name: "Elige un cliente" })).toBeVisible();
    expect(screen.getByText("No hay ningún cliente activo en esta sesión.")).toBeVisible();
    await user.click(screen.getByRole("link", { name: "Ingesta" }));
    expect(screen.getByRole("heading", { name: "Cliente requerido" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Encolar ingesta" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: "Asistente" }));
    expect(screen.getByRole("heading", { name: "Cliente requerido" })).toBeVisible();
    expect(requests.every((request) => ["/tenants", "/health", "/me"].includes(request.path))).toBe(true);
  });

  it("shows tenant authorization failure and resets the expired session", async () => {
    const user = userEvent.setup();
    mockBackend({ "GET /tenants": () => jsonResponse({ detail: "Session is no longer authorized." }, 403) });
    restoreSession(tenants[0].id);
    const { client } = renderApp();

    // Idem: SessionGate.tsx presenta este error en espanol.
    expect(await screen.findByRole("heading", { name: "No se han podido cargar los clientes" })).toBeVisible();
    expect(screen.getByText(/Session is no longer authorized/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Restablecer sesión" }));
    expect(screen.getByRole("button", { name: "Iniciar sesión" })).toBeEnabled();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
    expect(client.getQueryCache().getAll().every((query) => query.state.data === undefined)).toBe(true);
  });

  it("keeps a visible loading state until billing is available", async () => {
    const pending = deferredResponse();
    mockBackend({ "GET /billing/summary": () => pending.promise });
    restoreSession();
    renderApp(["/overview-legacy"]);

    expect(await screen.findByRole("heading", { name: "Conectando con el plano de control FinOps..." })).toBeVisible();
    expect(screen.queryByText("Gasto mensual")).not.toBeInTheDocument();
    await act(async () => pending.resolve(billing));
    expect(await screen.findByText("Gasto mensual")).toBeVisible();
    expect(screen.getByText(/unavailable|no disponible/i)).toBeVisible();
  });

  // Reactivado (Punto 5 implementado): idem, el enlace real es un <NavLink>.
  it.each(["/billing/summary", "/health"])("surfaces %s failures and keeps navigation available", async (path) => {
    const user = userEvent.setup();
    mockBackend({ [`GET ${path}`]: () => { throw new TypeError("Service connection interrupted"); } });
    restoreSession();
    renderApp(["/overview-legacy"]);

    expect(await screen.findByRole("heading", { name: "Backend no disponible" })).toBeVisible();
    expect(screen.getByText("Service connection interrupted")).toBeVisible();
    expect(screen.queryByText("Gasto mensual")).not.toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: "Ingesta" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Crear trabajo de ingesta" })).toBeVisible());
  });
});
