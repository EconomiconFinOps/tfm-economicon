import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { billing, health, loginResponse, session, tenants } from "./fixtures";
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
  it("submits credentials, exposes pending states and opens the authenticated dashboard", async () => {
    const user = userEvent.setup();
    const authentication = deferredResponse();
    const bootstrap = deferredResponse();
    const { requests } = mockBackend({
      "POST /auth/login": () => authentication.promise,
      "GET /tenants": () => bootstrap.promise
    });
    renderApp();

    expect(screen.getByLabelText("Password")).toHaveValue("");
    await user.clear(screen.getByLabelText("Email"));
    await user.type(screen.getByLabelText("Email"), "operator@example.com");
    await user.clear(screen.getByLabelText("Password"));
    await user.type(screen.getByLabelText("Password"), "test-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(screen.getByRole("button", { name: "Signing in..." })).toBeDisabled();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    const loginRequest = requests.find((request) => request.path === "/auth/login");
    expect(loginRequest?.body).toEqual({ email: "operator@example.com", password: "test-password" });
    expect(loginRequest?.headers.has("Authorization")).toBe(false);
    expect(loginRequest?.headers.has("X-Tenant-Id")).toBe(false);

    await act(async () => authentication.resolve(loginResponse));
    expect(await screen.findByRole("heading", { name: "Loading available tenants..." })).toBeVisible();
    expect(JSON.parse(window.localStorage.getItem(SESSION_KEY)!)).toEqual(session);
    await act(async () => bootstrap.resolve({ items: tenants }));

    expect(await screen.findByText("Monthly Spend")).toBeVisible();
    expect(screen.getByLabelText("Active tenant")).toHaveValue(tenants[0].id);
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
    expect(screen.getByLabelText("Password")).toHaveValue("");
    await user.type(screen.getByLabelText("Password"), "test-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText(new RegExp(error))).toBeVisible();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();

    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("Monthly Spend")).toBeVisible();
  });

  it("restores the saved session and tenant across reloads, then clears data on logout", async () => {
    const user = userEvent.setup();
    const { requests } = mockBackend();
    restoreSession(tenants[1].id);
    const firstVisit = renderApp();
    await screen.findByText("Monthly Spend");
    expect(screen.getByLabelText("Active tenant")).toHaveValue(tenants[1].id);
    firstVisit.unmount();
    firstVisit.client.clear();

    const reloaded = renderApp();
    await screen.findByText("Monthly Spend");
    expect(screen.getByLabelText("Active tenant")).toHaveValue(tenants[1].id);
    expect(requests.some((request) => request.path === "/auth/login")).toBe(false);
    expect(reloaded.client.getQueryCache().getAll().some((query) => query.state.data !== undefined)).toBe(true);

    await user.click(screen.getByRole("button", { name: "Logout" }));
    expect(screen.getByRole("heading", { name: "Access the tenant control tower" })).toBeVisible();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
    expect(reloaded.client.getQueryCache().getAll().every((query) => query.state.data === undefined)).toBe(true);
  });

  it("recovers from invalid stored JSON without contacting authenticated endpoints", () => {
    const { requests } = mockBackend();
    window.localStorage.setItem(SESSION_KEY, "{broken-json");
    window.localStorage.setItem(TENANT_KEY, tenants[0].id);
    renderApp();

    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
    expect(requests).toEqual([]);
  });
});

describe("tenant bootstrap and dashboard", () => {
  it("replaces a stale tenant selection and scopes billing requests to each selected tenant", async () => {
    const user = userEvent.setup();
    const southBilling = { ...billing, monthly_spend: 9876 };
    const { requests } = mockBackend({
      "GET /billing/summary": (request) => jsonResponse(
        request.headers.get("X-Tenant-Id") === tenants[1].id ? southBilling : billing
      )
    });
    restoreSession("tenant-no-longer-authorized");
    renderApp();

    expect(await screen.findByText(`$${billing.monthly_spend.toLocaleString()}`)).toBeVisible();
    expect(screen.getByLabelText("Active tenant")).toHaveValue(tenants[0].id);
    expect(window.localStorage.getItem(TENANT_KEY)).toBe(tenants[0].id);
    const bootstrap = requests.find((request) => request.path === "/tenants");
    expect(bootstrap?.headers.get("Authorization")).toBe(`Bearer ${session.accessToken}`);
    expect(bootstrap?.headers.has("X-Tenant-Id")).toBe(false);

    await user.selectOptions(screen.getByLabelText("Active tenant"), tenants[1].id);
    expect(await screen.findByText(`$${southBilling.monthly_spend.toLocaleString()}`)).toBeVisible();
    expect(window.localStorage.getItem(TENANT_KEY)).toBe(tenants[1].id);
    const billingRequests = requests.filter((request) => request.path === "/billing/summary");
    expect(billingRequests).toHaveLength(2);
    expectTenantRequest(billingRequests[0]);
    expectTenantRequest(billingRequests[1], tenants[1].id);
    expect(screen.getByRole("heading", { name: "Service Health" })).toBeVisible();
    for (const service of Object.keys(health.services)) expect(screen.getByText(service)).toBeVisible();
  });

  it("handles an empty tenant list without issuing tenant-scoped product requests", async () => {
    const user = userEvent.setup();
    const { requests } = mockBackend({ "GET /tenants": () => jsonResponse({ items: [] }) });
    restoreSession();
    renderApp();

    expect(await screen.findByRole("heading", { name: "Select a tenant" })).toBeVisible();
    expect(screen.getByText("No tenant is active for this session.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Ingestions" }));
    expect(screen.getByRole("heading", { name: "Tenant required" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Queue ingestion" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Assistant" }));
    expect(screen.getByRole("heading", { name: "Tenant required" })).toBeVisible();
    expect(requests.every((request) => ["/tenants", "/health"].includes(request.path))).toBe(true);
  });

  it("shows tenant authorization failure and resets the expired session", async () => {
    const user = userEvent.setup();
    mockBackend({ "GET /tenants": () => jsonResponse({ detail: "Session is no longer authorized." }, 403) });
    restoreSession(tenants[0].id);
    const { client } = renderApp();

    expect(await screen.findByRole("heading", { name: "Unable to load tenants" })).toBeVisible();
    expect(screen.getByText(/Session is no longer authorized/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Reset session" }));
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
    expect(client.getQueryCache().getAll().every((query) => query.state.data === undefined)).toBe(true);
  });

  it("keeps a visible loading state until billing is available", async () => {
    const pending = deferredResponse();
    mockBackend({ "GET /billing/summary": () => pending.promise });
    restoreSession();
    renderApp();

    expect(await screen.findByRole("heading", { name: "Connecting to the FinOps control plane..." })).toBeVisible();
    expect(screen.queryByText("Monthly Spend")).not.toBeInTheDocument();
    await act(async () => pending.resolve(billing));
    expect(await screen.findByText("Monthly Spend")).toBeVisible();
    expect(screen.getByText(`$${billing.savings_identified.toLocaleString()}`)).toBeVisible();
  });

  it.each(["/billing/summary", "/health"])("surfaces %s failures and keeps navigation available", async (path) => {
    const user = userEvent.setup();
    mockBackend({ [`GET ${path}`]: () => { throw new TypeError("Service connection interrupted"); } });
    restoreSession();
    renderApp();

    expect(await screen.findByRole("heading", { name: "Backend unavailable" })).toBeVisible();
    expect(screen.getByText("Service connection interrupted")).toBeVisible();
    expect(screen.queryByText("Monthly Spend")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ingestions" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Create ingestion job" })).toBeVisible());
  });
});
