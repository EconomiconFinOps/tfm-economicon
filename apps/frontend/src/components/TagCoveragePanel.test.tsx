import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { deferredResponse, expectTenantRequest, jsonResponse, mockBackend, renderApp, restoreSession } from "../../tests/test-support";
import { isTagCoverage } from "@/services/contracts";
import { tenants } from "../../tests/fixtures";
import type { TagCoverage } from "@/services/contracts";

const coverage: TagCoverage = {
  contract_version: 1, policy_version: "economicon-minimum-v1",
  required_tags: ["owner", "environment", "application", "cost_center", "project"],
  period: { start_date: "2024-06-01", end_date: "2024-07-01", timezone: "UTC" },
  data_status: "available", excluded_undated_count: 0,
  currencies: [{
    currency: "USD", record_count: 3, compliant_record_count: 2, noncompliant_record_count: 1,
    positive_cost: "9007199254740993.01", compliant_cost: "9007199254740993.01",
    noncompliant_cost: "0.00", negative_adjustments: "-30.00",
    compliant_negative_adjustments: "-30.00", noncompliant_negative_adjustments: "0.00",
    net_cost: "9007199254740963.01", compliant_net_cost: "9007199254740963.01",
    noncompliant_net_cost: "0.00", compliant_percent: "100.00", noncompliant_percent: "0.00",
    no_positive_cost_reason: null,
    missing_or_invalid_tag_counts: { owner: 1, environment: 0, application: 1, cost_center: 0, project: 0 }
  }]
};

async function openPanel() {
  await screen.findByText("Dashboard Ejecutivo - Coste Global");
  fireEvent.change(screen.getByLabelText("Mes inicial"), { target: { value: "2024-06" } });
  fireEvent.change(screen.getByLabelText("Mes final"), { target: { value: "2024-06" } });
  await userEvent.click(screen.getByText("Cobertura de etiquetas FinOps"));
  return screen.findByRole("region", { name: "Cobertura de etiquetas" });
}

describe("TagCoveragePanel", () => {
  it("loads on expansion with tenant headers and exact money, within the current executive dashboard", async () => {
    const { requests } = mockBackend({ "GET /billing/tag-coverage": () => jsonResponse(coverage) });
    restoreSession(); renderApp();
    await screen.findByText("Dashboard Ejecutivo - Coste Global");
    expect(requests.some((r) => r.path === "/billing/tag-coverage")).toBe(false);
    const panel = await openPanel();
    expect((await within(panel).findAllByText("9007199254740993.01 USD"))[0]).toBeVisible();
    expect(panel).toHaveTextContent("100.00%");
    expect(panel).toHaveTextContent("-30.00 USD");
    expect(panel).toHaveTextContent("owner: 1");
    const request = requests.find((r) => r.path === "/billing/tag-coverage")!;
    expectTenantRequest(request);
    expect(request.search.get("start_date")).toBe("2024-06-01");
    expect(request.search.get("end_date")).toBe("2024-07-01");
    expect(request.search.has("group_by")).toBe(false);
  });

  it("shows N/D, empty and terminal errors without invented percentages or retries", async () => {
    let data: unknown = { ...coverage, currencies: [{
      ...coverage.currencies[0], compliant_percent: null, noncompliant_percent: null,
      no_positive_cost_reason: "negative_adjustments_only", positive_cost: "0.00",
      compliant_cost: "0.00", net_cost: "-30.00", compliant_net_cost: "-30.00"
    }] };
    let status = 200;
    const { requests } = mockBackend({ "GET /billing/tag-coverage": () => jsonResponse(data, status) });
    restoreSession(); const { client } = renderApp();
    const panel = await openPanel();
    await waitFor(() => expect(panel).toHaveTextContent("N/D"));
    expect(panel).not.toHaveTextContent("100.00%");
    data = { ...coverage, data_status: "empty", currencies: [] };
    await act(async () => { await client.invalidateQueries({ queryKey: ["tag-coverage"] }); });
    await waitFor(() => expect(panel).toHaveTextContent("Sin datos"));
    data = { detail: { code: "ambiguous_cost_source" } }; status = 409;
    await act(async () => { await client.invalidateQueries({ queryKey: ["tag-coverage"] }); });
    expect(await within(panel).findByRole("alert")).toHaveTextContent("solapamiento");
    expect(panel).not.toHaveTextContent("9007199254740993");
    expect(requests.filter((r) => r.path === "/billing/tag-coverage")).toHaveLength(3);
  });

  it("does not display an obsolete response after changing period", async () => {
    const stale = deferredResponse();
    let calls = 0;
    mockBackend({ "GET /billing/tag-coverage": () => ++calls === 1 ? stale.promise : jsonResponse({
      ...coverage, period: { ...coverage.period, start_date: "2024-05-01" }, currencies: []
    }) });
    restoreSession(); renderApp();
    const panel = await openPanel();
    expect(panel).toHaveTextContent("Cargando cobertura");
    fireEvent.change(screen.getByLabelText("Mes inicial"), { target: { value: "2024-05" } });
    await waitFor(() => expect(calls).toBe(2));
    await act(async () => { stale.resolve(coverage); });
    await waitFor(() => expect(panel).toHaveTextContent("Sin datos"));
    expect(panel).not.toHaveTextContent("9007199254740993");
  });

  it("hides previous tenant amounts while the next tenant is loading", async () => {
    const pending = deferredResponse();
    const { requests } = mockBackend({ "GET /billing/tag-coverage": ({ headers }) =>
      headers.get("X-Tenant-Id") === tenants[0].id ? jsonResponse(coverage) : pending.promise });
    restoreSession(); renderApp();
    const panel = await openPanel();
    await within(panel).findAllByText("9007199254740993.01 USD");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Ambito de cliente" }), tenants[1].id);
    await waitFor(() => expect(requests.filter((r) => r.path === "/billing/tag-coverage").at(-1)?.headers.get("X-Tenant-Id")).toBe(tenants[1].id));
    expect(panel).not.toHaveTextContent("9007199254740993");
    expect(panel).toHaveTextContent("Cargando cobertura");
    await act(async () => { pending.resolve({ ...coverage, currencies: [], data_status: "empty" }); });
    await waitFor(() => expect(panel).toHaveTextContent("Sin datos"));
  });

  it("hides coverage and stops requests when the dashboard month range is invalid", async () => {
    const { requests } = mockBackend({ "GET /billing/tag-coverage": () => jsonResponse(coverage) });
    restoreSession(); renderApp();
    const panel = await openPanel();
    await within(panel).findAllByText("9007199254740993.01 USD");
    const count = requests.filter((r) => r.path === "/billing/tag-coverage").length;
    fireEvent.change(screen.getByLabelText("Mes inicial"), { target: { value: "2024-08" } });
    expect(panel).toHaveTextContent("Selecciona un cliente y un periodo válido");
    expect(panel).not.toHaveTextContent("9007199254740993");
    expect(requests.filter((r) => r.path === "/billing/tag-coverage")).toHaveLength(count);
  });

  it("validates policy, typed amounts, dates and percentage states before rendering", () => {
    expect(isTagCoverage(coverage)).toBe(true);
    expect(isTagCoverage({ ...coverage, required_tags: ["project"] })).toBe(false);
    expect(isTagCoverage({ ...coverage, period: { ...coverage.period, start_date: "2024-06-31" } })).toBe(false);
    for (const changes of [{ compliant_cost: 123 }, { compliant_percent: "101.00" },
      { no_positive_cost_reason: "zero_cost_only" }, { missing_or_invalid_tag_counts: {} }]) {
      expect(isTagCoverage({ ...coverage, currencies: [{ ...coverage.currencies[0], ...changes }] })).toBe(false);
    }
  });
});
