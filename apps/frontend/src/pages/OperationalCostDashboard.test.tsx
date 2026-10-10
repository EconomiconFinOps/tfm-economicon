import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { billing, billingWithCost, tenants } from "../../tests/fixtures";
import { deferredResponse, expectTenantRequest, jsonResponse, mockBackend, renderApp, restoreSession } from "../../tests/test-support";
import { billingFilterKeys } from "../services/contracts";

type Request = { search: URLSearchParams };
function aligned(request: Request, data: Record<string, unknown> = billing) {
  const filters = Object.fromEntries(billingFilterKeys.filter((key) => request.search.has(key)).map((key) => [key, request.search.get(key)]));
  return { ...data,
    period: { start_date: request.search.get("start_date"), end_date: request.search.get("end_date"), timezone: "UTC" },
    group_by: request.search.get("group_by"), tag_key: request.search.get("tag_key"),
    ...(Object.keys(filters).length ? { filters } : {}) };
}
const table = () => screen.getByRole("table", { name: /desglose de costes del ámbito/i });
const ready = () => screen.findByRole("table", {}, { timeout: 10000 });
const edit = (label: string | RegExp, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } });
const apply = () => fireEvent.click(screen.getByRole("button", { name: "Aplicar filtros" }));
const costs = (requests: { path: string }[]) => requests.filter((request) => request.path === "/billing/summary");

describe("JUP-056 operational stored costs", () => {
  it("applies all filters once, retains exact scope and amounts, clears filters and exports current results", async () => {
    const data = { ...billing, monthly_spend: null, currency: null,
      totals: [{ currency: "USD", cost: "9007199254740993.01", record_count: 1 }, { currency: "EUR", cost: "-1.01", record_count: 1 }, { currency: "GBP", cost: "0.00", record_count: 1 }],
      groups: [{ currency: "USD", subscription_id: null, value: "Compute", cost: "9007199254740993.01", record_count: 1 }, { currency: "EUR", subscription_id: null, value: "Credit", cost: "-1.01", record_count: 1 }, { currency: "GBP", subscription_id: null, value: "Storage", cost: "0.00", record_count: 1 }] };
    const { requests } = mockBackend({ "GET /billing/summary": (request) => jsonResponse(aligned(request, data)) });
    restoreSession();
    renderApp(["/operational"]);
    await ready();
    expect(table()).toHaveTextContent("9007199254740993.01");
    expect(table()).toHaveTextContent("-1.01");
    expect(table()).toHaveTextContent("0.00");
    const initial = costs(requests).length;
    edit(/cuenta \(/i, "sub+one"); edit("Servicio", "Compute"); edit("Proyecto", " Project A ");
    edit("Clave de etiqueta a filtrar", " ENV "); edit("Valor de etiqueta a filtrar", "Production & Billing");
    edit("Desde (incluido)", "2024-06-01"); edit("Hasta (excluido)", "2024-07-01");
    expect(costs(requests)).toHaveLength(initial);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /exportar/i })).not.toBeInTheDocument();
    apply();
    await ready();
    expect(costs(requests)).toHaveLength(initial + 1);
    const request = requests.at(-1)!;
    expectTenantRequest(request);
    expect(Object.fromEntries(request.search)).toEqual({ start_date: "2024-06-01", end_date: "2024-07-01", group_by: "service",
      subscription_id: "sub+one", service_name: "Compute", project: " Project A ", filter_tag_key: "environment", filter_tag_value: "Production & Billing" });
    expect(screen.getByRole("region", { name: "Ámbito aplicado" })).toHaveTextContent("environment");
    const createUrl = vi.fn(() => "blob:operational");
    const revokeUrl = vi.fn();
    vi.stubGlobal("URL", class extends URL { static createObjectURL = createUrl; static revokeObjectURL = revokeUrl; });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    fireEvent.click(screen.getByRole("button", { name: /exportar csv/i }));
    expect(createUrl).toHaveBeenCalledOnce(); expect(click).toHaveBeenCalledOnce();
    await waitFor(() => expect(revokeUrl).toHaveBeenCalledWith("blob:operational"));
    fireEvent.click(screen.getByRole("button", { name: "Limpiar filtros" }));
    await ready();
    expect(requests.at(-1)!.search.get("service_name")).toBeNull();
    expect(requests.at(-1)!.search.get("start_date")).toBe("2024-06-01");
    expect(screen.queryByText("EC2 Instances")).not.toBeInTheDocument();
  });

  it("blocks invalid dates and incomplete tags without requests or stale results", async () => {
    const { requests } = mockBackend({ "GET /billing/summary": (request) => jsonResponse(aligned(request)) });
    restoreSession(); renderApp(["/operational"]); await ready();
    const initial = costs(requests).length;
    edit("Hasta (excluido)", "0000-01-01");
    expect(screen.getByRole("button", { name: "Aplicar filtros" })).toBeDisabled();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    edit("Desde (incluido)", "2024-07-01"); edit("Hasta (excluido)", "2024-07-01");
    expect(screen.getByText(/inicio anterior al fin/)).toBeVisible();
    edit("Hasta (excluido)", "2024-08-01"); edit("Clave de etiqueta a filtrar", "env");
    expect(screen.getByText(/indica su clave y su valor/)).toBeVisible();
    edit("Valor de etiqueta a filtrar", "   ");
    expect(screen.getByText(/solo espacios ni caracteres de control/)).toBeVisible();
    expect(costs(requests)).toHaveLength(initial);
    expect(screen.queryByRole("button", { name: /exportar/i })).not.toBeInTheDocument();
  });

  it("shows loading, partial, empty, zero and errors without inventing totals", async () => {
    const pending = deferredResponse();
    let first: Request | undefined;
    let data: Record<string, unknown> = { ...billing, totals: [], groups: [], data_status: "empty", monthly_spend: null, currency: null };
    let status = 200;
    mockBackend({ "GET /billing/summary": (request) => {
      if (!first) { first = request; return pending.promise; }
      return jsonResponse(status === 200 ? aligned(request, data) : { detail: { code: "ambiguous_cost_source" } }, status);
    } });
    restoreSession(); const { client } = renderApp(["/operational"]);
    await screen.findByText(/Cargando costes del ámbito/);
    expect(screen.queryByText("0.00")).not.toBeInTheDocument();
    await act(async () => pending.resolve(aligned(first!, data)));
    expect(await screen.findByText(/Sin datos de costes para el ámbito aplicado/)).toBeVisible();
    expect(screen.queryByRole("button", { name: /exportar/i })).not.toBeInTheDocument();
    data = { ...billingWithCost("0.00"), data_status: "partial", missing_dimension_count: 2, excluded_undated_count: 3,
      groups: [{ ...billing.groups[0], cost: "0.00", value: null }] };
    await act(async () => { await client.invalidateQueries(); });
    expect(await ready()).toHaveTextContent("0.00");
    expect(table()).toHaveTextContent("Sin dimensión");
    expect(screen.getByText(/Datos parciales:/)).toHaveTextContent("3 registros sin fecha");
    status = 409;
    await act(async () => { await client.invalidateQueries(); });
    expect(await screen.findByRole("alert")).toHaveTextContent(/solapamiento/);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /exportar/i })).not.toBeInTheDocument();
    status = 503;
    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Error al cargar costes");
  });

  it("cancels pending selections, isolates tenant scopes and rejects late responses", async () => {
    const user = userEvent.setup();
    const pending = deferredResponse();
    let hold = false;
    const { requests } = mockBackend({ "GET /billing/summary": (request) => hold
      ? pending.promise.then(() => jsonResponse(aligned(request, billingWithCost("777777.77")))) : jsonResponse(aligned(request)) });
    restoreSession(); renderApp(["/operational"]); await ready();
    hold = true; edit("Servicio", "Compute"); apply();
    await waitFor(() => expect(requests.at(-1)!.search.get("service_name")).toBe("Compute"));
    const fetchCall = vi.mocked(fetch).mock.calls.at(-1)!;
    expect(fetchCall[1]?.signal?.aborted).toBe(false);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    edit("Proyecto", "new project");
    await waitFor(() => expect(fetchCall[1]?.signal?.aborted).toBe(true));
    apply();
    await waitFor(() => expect(requests.at(-1)!.search.get("project")).toBe("new project"));
    await user.selectOptions(screen.getByLabelText("Ambito de cliente"), tenants[1].id);
    await waitFor(() => expect(requests.at(-1)!.headers.get("X-Tenant-Id")).toBe(tenants[1].id));
    expect(screen.getByLabelText("Proyecto")).toHaveValue("");
    expect(screen.queryByRole("button", { name: /exportar/i })).not.toBeInTheDocument();
    hold = false; edit("Servicio", "Storage"); apply();
    expect(await ready()).toHaveTextContent("12345.67");
    await act(async () => pending.resolve({}));
    expect(screen.queryByText(/777777.77/)).not.toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: "Ámbito aplicado" })).getByText(/South Operations/)).toBeVisible();
  });

  it("rejects a backend that ignores filters or returns the wrong period", async () => {
    let mismatch = false;
    mockBackend({ "GET /billing/summary": (request) => {
      const data = aligned(request);
      if (mismatch) return jsonResponse({ ...data, period: billing.period });
      delete data.filters;
      return jsonResponse(data);
    } });
    restoreSession(); renderApp(["/operational"]); await ready();
    edit("Servicio", "Compute"); apply();
    expect(await screen.findByRole("alert")).toHaveTextContent("respuesta de costes incompatible");
    expect(screen.queryByRole("button", { name: /exportar/i })).not.toBeInTheDocument();
    mismatch = true; fireEvent.click(screen.getByRole("button", { name: "Limpiar filtros" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("respuesta de costes incompatible");
  });
});
