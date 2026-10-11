import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { Layout } from "../src/layouts/Layout";
import { OperationalCostDashboard } from "../src/pages/OperationalCostDashboard";
import { ExecutiveCutDashboard } from "../src/pages/ExecutiveCutDashboard";
import { AnomaliesPanel } from "../src/pages/AnomaliesPanel";
import { RecommendationsPanel } from "../src/pages/RecommendationsPanel";
import { PreparedScreen } from "../src/services/screenCapture";
import { ExecutiveCostDashboard } from "../src/pages/ExecutiveCostDashboard";
import type { ScreenCapture } from "../src/services/screenCapture";
import type { BillingSummary } from "../src/services/contracts";
import type { ExecutiveSnapshot } from "../src/lib/executiveCostDashboard";

const queryState = vi.hoisted(() => ({ value: {} as { data?: ExecutiveSnapshot; isFetching: boolean; isError: boolean; error: unknown; refetch: () => void } }));
vi.mock("../src/hooks/useExecutiveCostKpis", () => ({ useExecutiveCostKpis: () => queryState.value }));
let captures: ScreenCapture[];
let requests: { path: string; method: string }[];
const billing = (): BillingSummary => ({ contract_version: 2,
  period: { start_date: "2026-04-01", end_date: "2026-10-01", timezone: "UTC" },
  group_by: "service", tag_key: null, data_status: "partial", missing_dimension_count: 1, excluded_undated_count: 2,
  totals: [{ currency: "EUR", cost: "-12.34", record_count: 2 }, { currency: "USD", cost: "0.00", record_count: 1 }],
  groups: [{ currency: "EUR", cost: "-12.34", record_count: 2, subscription_id: "subscription-a", value: "Compute" },
    { currency: "USD", cost: "0.00", record_count: 1, subscription_id: "subscription-b", value: "Storage" }],
  monthly_spend: null, savings_identified: null, open_ingestions: 0, currency: null });

beforeEach(() => {
  captures = []; requests = [];
  queryState.value = { isFetching: false, isError: false, error: null, refetch: () => {}, data: {
    aggregate: { kind: "success", data: billing() }, months: [
      { month: "2026-04", result: { kind: "success", data: { ...billing(), period: { start_date: "2026-04-01", end_date: "2026-05-01", timezone: "UTC" } } } },
      { month: "2026-05", result: { kind: "error", error: new Error("Secret raw service error") } }
    ] } };
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
    const path = new URL(String(input), "http://test").pathname, method = options.method ?? "GET";
    requests.push({ path, method });
    if (path.endsWith("/generations")) {
      captures.push(JSON.parse(String(options.body)).screen_context);
      return new Response(new ReadableStream(), { headers: { "Content-Type": "text/event-stream" } });
    }
    return new Response(JSON.stringify({ id: crypto.randomUUID(), tenant_id: "t", user_id: "alice", title: "Nueva conversación",
      created_at: "2026-10-10T00:00:00Z", updated_at: "2026-10-10T00:00:00Z" }), { status: 201, headers: { "Content-Type": "application/json" } });
  }));
});

function mount(path: string) {
  function Session() { return <Outlet context={{ token: "secret-token", user: { id: "alice", full_name: "Private name", email: "private@example.test", role: "member" },
    activeTenant: { id: "t", name: "Tenant", slug: "tenant", plan: "test" }, activeTenantId: "t" }} />; }
  const router = createMemoryRouter([{ path: "/", Component: Session, children: [{ Component: Layout, children: [
    { index: true, element: <ExecutiveCostDashboard /> },
    { path: "operational", element: <OperationalCostDashboard /> },
    { path: "cuts", element: <ExecutiveCutDashboard /> },
    { path: "anomalies", element: <AnomaliesPanel /> },
    { path: "recommendations", element: <RecommendationsPanel /> },
    { path: "ingest", element: <p>Sin adaptador financiero</p> }
  ] }] }], { initialEntries: [path] });
  return { ...render(<RouterProvider router={router} />), router };
}
async function send() {
  if (screen.queryByRole("button", { name: "Abrir asistente" })) fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
  fireEvent.change(await screen.findByRole("textbox", { name: "Pregunta" }), { target: { value: "Describe la pantalla" } });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
  await waitFor(() => expect(captures).toHaveLength(1));
  return captures[0];
}
describe("Capturas funcionales preparadas antes de Send JUP-035", () => {
  it.each(["/operational", "/cuts", "/anomalies", "/recommendations"])("prepara la vista demo %s sin consultar datos al enviar", async path => {
    mount(path);
    const count = requests.length;
    const prepare = vi.spyOn(PreparedScreen.prototype, "prepare");
    const capture = await send();
    expect(capture.source).toBe("loaded-screen");
    expect(capture.route).toBe(path);
    expect(capture.datasets.length).toBeGreaterThan(0);
    expect(capture.datasets.every(dataset => dataset.data_environment === "demo")).toBe(true);
    expect(capture.datasets.some(dataset => Number((dataset.counts as { records: number }).records) > 0)).toBe(true);
    expect(requests.filter(request => request.method === "GET")).toHaveLength(count);
    expect(prepare).not.toHaveBeenCalled();
    expect(JSON.stringify(capture)).not.toMatch(/secret-token|private@example|Private name|icon|className|prompts/);
  });
  it("conserva monedas separadas, créditos exactos, meses fallidos y selección de costes observados", async () => {
    mount("/");
    const capture = await send();
    expect(capture.source).toBe("loaded-screen");
    const aggregate = capture.datasets[0];
    expect(aggregate.source).toBe("billing-summary-v2");
    expect(aggregate.data_environment).toBe("unknown");
    expect(aggregate.totals).toEqual([{ currency: "EUR", amount: "-12.34", record_count: 2 }, { currency: "USD", amount: "0.00", record_count: 1 }]);
    expect(aggregate.groups).toEqual([
      { label: "Compute", currency: "EUR", amount: "-12.34", record_count: 2, subscription_id: "subscription-a" },
      { label: "Storage", currency: "USD", amount: "0.00", record_count: 1, subscription_id: "subscription-b" }
    ]);
    expect(aggregate.counts).toEqual({ records: 3, groups: 2, series: 0 });
    expect(aggregate.completeness).toMatchObject({ status: "partial", excluded_undated_count: 2,
      missing_dimensions: ["grouping_dimension"] });
    expect(capture.datasets).toHaveLength(3);
    expect(capture.datasets[2]).toMatchObject({ load_state: "error", totals: [], groups: [],
      selection: { period: { start_date: "2026-05-01", end_date: "2026-06-01" } } });
    expect(JSON.stringify(capture)).not.toContain("Secret raw service error");
  });
  it("una selección nueva en carga no reutiliza los costes de la selección anterior", async () => {
    mount("/");
    queryState.value = { ...queryState.value, isFetching: true };
    fireEvent.change(screen.getByLabelText("Mes inicial"), { target: { value: "2026-05" } });
    const capture = await send();
    expect(capture.source).toBe("loading");
    expect(capture.selection).toMatchObject({ start_date: "2026-05-01", end_date: "2026-10-01" });
    expect(capture.datasets).toEqual([]);
    expect(JSON.stringify(capture)).not.toContain("-12.34");
  });
  it("actualiza filtros de anomalías usando exclusivamente los registros visibles", async () => {
    mount("/anomalies");
    fireEvent.change(screen.getByLabelText("Criticidad"), { target: { value: "Alta" } });
    const capture = await send();
    expect(capture.selection).toMatchObject({ filters: { tags: expect.arrayContaining([{ key: "severity", value: "Alta" }, { key: "status", value: "Abiertas" }]) } });
    expect(capture.datasets[0].groups).toHaveLength(2);
    expect(capture.datasets[0].groups).toEqual(expect.arrayContaining([
      expect.objectContaining({ amount: "15800" }),
      expect.objectContaining({ amount: "12500" })
    ]));
  });
  it("un cambio de ruta elimina el descriptor financiero anterior", async () => {
    const mounted = mount("/operational");
    await act(async () => mounted.router.navigate("/ingest"));
    const capture = await send();
    expect(capture).toMatchObject({ route: "/ingest", source: "no-adapter", datasets: [] });
  });
  it("captura el filtro de resueltas sin mezclar el resumen global de abiertas", async () => {
    mount("/anomalies");
    fireEvent.change(screen.getByLabelText("Estado"), { target: { value: "Resuelto" } });
    const capture = await send();
    expect(capture.selection).toMatchObject({ filters: { tags: expect.arrayContaining([{ key: "status", value: "Resuelto" }]) } });
    expect(capture.datasets[0].groups).toHaveLength(2);
    expect(capture.datasets[0].groups).toEqual(expect.arrayContaining([
      expect.objectContaining({ amount: "8200" }), expect.objectContaining({ amount: "5600" })
    ]));
    expect(capture.datasets[1].groups).toHaveLength(3);
    expect(capture.datasets[1].totals).toEqual([{ currency: "EUR", amount: "30700" }]);
  });
  it("conserva la moneda seleccionada sin convertir ni fusionar los importes", async () => {
    mount("/");
    fireEvent.change(screen.getByLabelText("Moneda"), { target: { value: "USD" } });
    const capture = await send();
    expect(capture.selection).toMatchObject({ selected_currency: "USD" });
    expect(capture.datasets[0].totals).toEqual([
      { currency: "EUR", amount: "-12.34", record_count: 2 },
      { currency: "USD", amount: "0.00", record_count: 1 }
    ]);
  });
  it("la copia preparada es inmutable, exacta en UTF-8 y conserva más de un frame SSE", () => {
    const registry = new PreparedScreen("t", "alice");
    const groups = Array.from({ length: 1000 }, (_, index) => ({ label: `Grupo ${index} ñ <&>`, currency: "EUR", amount: "0.12345678901234567890" }));
    registry.prepare("/operational", { source: "loaded-screen", selection: {}, datasets: [{ source: "demo", groups }] });
    const frozen = registry.freeze("/operational");
    groups[0].amount = "999.00";
    expect(new TextEncoder().encode(JSON.stringify(frozen)).length).toBeGreaterThan(65536);
    expect((frozen.datasets[0].groups as { amount: string }[])[0].amount).toBe("0.12345678901234567890");
    expect(registry.freeze("/operational")).toEqual(frozen);
    expect(() => registry.freeze("/cuts")).toThrow("screen_not_ready");
  });
  it("exceso de 1MiB no se recorta ni se envía sin captura", () => {
    const registry = new PreparedScreen("t", "alice");
    registry.prepare("/operational", { source: "loaded-screen", selection: {}, datasets: [{ source: "demo", groups: [{ label: "ñ".repeat(600000) }] }] });
    expect(registry.ready("/operational")).toBe(false);
    expect(() => registry.freeze("/operational")).toThrow("screen_limit");
  });
});
