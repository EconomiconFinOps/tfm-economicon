import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { billing, billingWithCost, tenants } from "../../tests/fixtures";
import { deferredResponse, expectTenantRequest, jsonResponse, mockBackend, renderApp, restoreSession } from "../../tests/test-support";

describe("ExecutiveCostDashboard", () => {
  it("muestra el encabezado y el coste real exacto, con demos separados", async () => {
    const live = { ...billing, monthly_spend: null, currency: null,
      totals: [{ currency: "USD", cost: "9007199254740993.01", record_count: 1 },
               { currency: "EUR", cost: "-1.01", record_count: 1 }],
      groups: [{ currency: "USD", subscription_id: null, value: "Compute", cost: "9007199254740993.01", record_count: 1 },
               { currency: "EUR", subscription_id: null, value: "Credit", cost: "-1.01", record_count: 1 }] };
    const { requests } = mockBackend({ "GET /billing/summary": () => jsonResponse(live) });
    restoreSession();
    renderApp();
    expect(await screen.findByText("Dashboard Ejecutivo - Coste Global")).toBeVisible();
    const table = await screen.findByRole("table");
    expect(table).toHaveTextContent("9007199254740993.01");
    expect(table).toHaveTextContent("-1.01");
    expect(table).toHaveTextContent("USD");
    expect(table).toHaveTextContent("EUR");
    expect(screen.getAllByText(/unavailable|no disponible/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/demo|demostraci[oó]n/i).length).toBeGreaterThan(0);
    expect(screen.queryByText("298.000€")).not.toBeInTheDocument();
    const request = requests.find((item) => item.path === "/billing/summary");
    expect(request).toBeDefined();
    expectTenantRequest(request!);
    expect(request!.search.get("group_by")).toBe("service");
    expect(requests.some((item) => item.path === "/health")).toBe(false);
  });

  it("keys pending requests by dates, grouping, tag and tenant without stale values", async () => {
    const user = userEvent.setup();
    const obsolete = deferredResponse();
    let hold = false;
    const { requests } = mockBackend({ "GET /billing/summary": () => hold ? obsolete.promise : jsonResponse(billing) });
    restoreSession();
    renderApp();
    await screen.findByRole("table");
    const grouping = screen.getByRole("combobox", { name: /group|agrupar|desglose/i });
    expect(within(grouping).getAllByRole("option").map((item) => (item as HTMLOptionElement).value).sort())
      .toEqual(["project", "resource_group", "service", "subscription", "tag"]);
    hold = true;
    await user.selectOptions(grouping, "resource_group");
    await waitFor(() => expect(requests.at(-1)?.search.get("group_by")).toBe("resource_group"));
    expect(screen.queryByText(/12345\.67/)).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/start|desde|inicio/i), { target: { value: "2024-06-01" } });
    fireEvent.change(screen.getByLabelText(/end|hasta|fin/i), { target: { value: "2024-07-01" } });
    await user.selectOptions(grouping, "tag");
    fireEvent.change(screen.getByLabelText(/tag key|clave.*etiqueta|clave.*tag/i), { target: { value: "environment" } });
    await waitFor(() => expect(requests.at(-1)?.search.get("tag_key")).toBe("environment"));
    expect(requests.at(-1)?.search.get("start_date")).toBe("2024-06-01");
    expect(requests.at(-1)?.search.get("end_date")).toBe("2024-07-01");
    await user.selectOptions(screen.getByLabelText("Ambito de cliente"), tenants[1].id);
    await waitFor(() => expect(requests.at(-1)?.headers.get("X-Tenant-Id")).toBe(tenants[1].id));
    hold = false;
    await user.selectOptions(grouping, "project");
    expect(await screen.findByRole("table")).toHaveTextContent("12345.67");
    await act(async () => obsolete.resolve(billingWithCost("777777.77")));
    expect(screen.queryByText(/777777\.77/)).not.toBeInTheDocument();
    expect(screen.getByRole("table")).toHaveTextContent("12345.67");
  });

  it("distinguishes loading, empty, observed zero, partial and failure without fallback", async () => {
    const pending = deferredResponse();
    let response = jsonResponse(billing);
    let first = true;
    mockBackend({ "GET /billing/summary": () => { if (first) { first = false; return pending.promise; } return Promise.resolve(response); } });
    restoreSession();
    const { client } = renderApp();
    expect((await screen.findAllByText(/loading|cargando|connecting/i)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/298\.000|0\.00/)).not.toBeInTheDocument();
    await act(async () => pending.resolve({ ...billing, data_status: "empty", totals: [], groups: [], monthly_spend: null, currency: null }));
    expect((await screen.findAllByText(/sin datos|no (cost )?data|empty/i)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/0\.00/)).not.toBeInTheDocument();
    response = jsonResponse(billingWithCost("0.00"));
    await act(async () => { await client.invalidateQueries(); });
    expect(await screen.findByRole("table")).toHaveTextContent("0.00");
    response = jsonResponse({ ...billing, data_status: "partial", missing_dimension_count: 3, excluded_undated_count: 2,
      groups: [{ ...billing.groups[0], value: null }] });
    await act(async () => { await client.invalidateQueries(); });
    expect((await screen.findAllByText(/partial|parcial/i)).length).toBeGreaterThan(0);
    expect(document.body).toHaveTextContent(/3.*(dimension|dimensi[oó]n)|(dimension|dimensi[oó]n).*3/i);
    expect(document.body).toHaveTextContent(/2.*(undated|fecha)|(undated|fecha).*2/i);
    expect(screen.getByRole("table")).toHaveTextContent(/sin.*(dato|servicio|dimensi[oó]n)|missing|unknown|unassigned/i);
    response = jsonResponse({ detail: "Billing unavailable" }, 503);
    await act(async () => { await client.invalidateQueries(); });
    expect((await screen.findAllByText(/error|unavailable|no.*disponible/i)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/12345\.67|298\.000/)).not.toBeInTheDocument();
  });

  it.each(["/", "/overview-legacy"])("warns on overlap without amounts or replacement at %s", async (path) => {
    const { requests } = mockBackend({ "GET /billing/summary": () => jsonResponse({ detail: { code: "ambiguous_cost_source" } }, 409) });
    restoreSession();
    renderApp([path]);
    expect((await screen.findAllByText(/possible.*overlap|posible.*solap|fuentes.*solap|overlapping.*source/i)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/12345\.67|298\.000|184250|0\.00/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /replace|reemplaz|sustitu|confirm/i })).not.toBeInTheDocument();
    expect(requests.every((item) => item.method === "GET")).toBe(true);
  });
});
