import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import type { BillingGrouping, BillingSummary, BillingTotal } from "../services/contracts";
import { billing, tenants } from "../../tests/fixtures";
import { expectTenantRequest, jsonResponse, mockBackend, renderApp, restoreSession } from "../../tests/test-support";

// Only Recharts' presentation boundary is replaced. Session, router, API,
// query cache and the existing page run unchanged. Real layout/visual QA is
// a later independent gate: jsdom cannot demonstrate pixels or overflow.
const graph = vi.hoisted(() => ({
  data: [] as Record<string, unknown>[],
  key: "" as string | ((point: Record<string, unknown>) => unknown),
  connectsGaps: false
}));
vi.mock("recharts", () => {
  const passthrough = ({ children }: { children?: ReactNode }) => children;
  return {
    ResponsiveContainer: passthrough,
    AreaChart: ({ data, children }: { data: Record<string, unknown>[]; children?: ReactNode }) => {
      graph.data = data;
      return children;
    },
    LineChart: ({ data, children }: { data: Record<string, unknown>[]; children?: ReactNode }) => {
      graph.data = data;
      return children;
    },
    Area: ({ dataKey, connectNulls = false }: { dataKey: typeof graph.key; connectNulls?: boolean }) => {
      graph.key = dataKey;
      graph.connectsGaps = connectNulls;
      return null;
    },
    Line: ({ dataKey, connectNulls = false }: { dataKey: typeof graph.key; connectNulls?: boolean }) => {
      graph.key = dataKey;
      graph.connectsGaps = connectNulls;
      return null;
    },
    BarChart: passthrough,
    Bar: () => null,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    Legend: () => null
  };
});

type RequestInfo = { search: URLSearchParams; headers: Headers };
type Plan = (request: RequestInfo) => Response | Promise<Response>;
const total = (cost: string, currency = "EUR"): BillingTotal => ({ cost, currency, record_count: 1 });
const baselineMonths: Record<string, string> = {
  "2026-02": "100.00", "2026-03": "90.00", "2026-04": "100.00",
  "2026-05": "90.00", "2026-06": "300.00", "2026-07": "200.00",
  "2026-08": "400.00", "2026-09": "150.00"
};

function isMonthly(request: RequestInfo) {
  const start = request.search.get("start_date") ?? "";
  const end = request.search.get("end_date") ?? "";
  const [year, month] = start.split("-").map(Number);
  const next = month === 12 ? [year + 1, 1] : [year, month + 1];
  return end === String(next[0]).padStart(4, "0") + "-" + String(next[1]).padStart(2, "0") + "-01";
}

function summary(request: RequestInfo, totals?: BillingTotal[], extra: Partial<BillingSummary> = {}): BillingSummary {
  const values = totals ?? [total(isMonthly(request)
    ? baselineMonths[(request.search.get("start_date") ?? "").slice(0, 7)] ?? "11.00"
    : "777.77")];
  const group = (request.search.get("group_by") ?? "service") as BillingGrouping;
  return {
    ...billing,
    contract_version: 2,
    period: {
      start_date: request.search.get("start_date") ?? "2026-04-01",
      end_date: request.search.get("end_date") ?? "2026-10-01",
      timezone: "UTC"
    },
    group_by: group,
    tag_key: group === "tag" ? "cost_center" : null,
    totals: values,
    groups: values.map((value) => ({ ...value, value: "Compute", subscription_id: null })),
    data_status: values.length ? "available" : "empty",
    monthly_spend: values.length === 1 ? values[0].cost : null,
    currency: values.length === 1 ? values[0].currency : null,
    ...extra
  };
}

function backend(plan: Plan = (request) => jsonResponse(summary(request))) {
  return mockBackend({ "GET /billing/summary": plan });
}

async function start(plan?: Plan, prepare?: Parameters<typeof renderApp>[1]) {
  const network = backend(plan);
  restoreSession();
  const view = renderApp(["/"], prepare);
  await screen.findByText("Dashboard Ejecutivo - Coste Global");
  return { ...network, ...view };
}

const monthlyTable = () => screen.getByRole("table", { name: /mensual|por mes/i });
const breakdownTable = () => screen.getByRole("table", { name: /desglose/i });
function monthRow(month: string) {
  const names: Record<string, string> = {
    "04": "abr", "05": "may", "06": "jun", "07": "jul", "08": "ago", "09": "sep",
    "02": "feb", "03": "mar", "12": "dic", "01": "ene"
  };
  const [year, number] = month.split("-");
  return within(monthlyTable()).getByRole("row", {
    name: new RegExp(month + "|" + names[number] + ".*" + year, "i")
  });
}
function plottedValues() {
  const key = graph.key;
  return graph.data.map((point) => typeof key === "function" ? key(point) : point[key]);
}
async function readyBreakdown() {
  await screen.findByRole("table", { name: /desglose/i });
}
async function ready() {
  await screen.findByRole("table", { name: /mensual|por mes/i });
}
async function chooseRange(first: string, last: string) {
  // Labels and input type are part of the approved accessible selector.
  const initial = screen.getByLabelText(/mes inicial/i);
  const final = screen.getByLabelText(/mes final/i);
  expect(initial).toHaveAttribute("type", "month");
  expect(final).toHaveAttribute("type", "month");
  act(() => {
    fireEvent.change(initial, { target: { value: first } });
    fireEvent.change(final, { target: { value: last } });
  });
}
function expectDelta(absolute: string, percentage?: string) {
  const escaped = absolute.replace(/[.+-]/g, (char) => char === "." ? "[.,]" : "\\" + char);
  expect(comparisonRegion()).toHaveTextContent(new RegExp(escaped + "\\s*EUR"));
  if (percentage) {
    const percent = percentage.replace(/[.+-]/g, (char) => char === "." ? "[.,]" : "\\" + char);
    expect(comparisonRegion()).toHaveTextContent(new RegExp(percent + "\\s*%"));
  }
}

function comparisonRegion() {
  return screen.getByRole("region", { name: "Comparación de meses" });
}
function expectObservedComparison(first: string, last: string, difference: string, percent: string) {
  const comparison = comparisonRegion();
  expectDelta(difference, percent);
  expect(within(comparison).getByRole("heading"))
    .toHaveTextContent(new RegExp(last + " de 2026.*" + first + " de 2026.*EUR"));
  expect(comparison).not.toHaveTextContent(/base cero|comparación no disponible/i);
}
function expectUnavailableComparison(reason: string | RegExp) {
  const comparison = comparisonRegion();
  expect(comparison).toHaveTextContent(reason);
  expect(within(comparison).queryByText("Variación absoluta")).not.toBeInTheDocument();
  expect(within(comparison).queryByText("Variación porcentual")).not.toBeInTheDocument();
  expect(comparison).not.toHaveTextContent(/[+-]?\d+[.,]\d{2}\s*(EUR|USD|%)/);
  return comparison;
}

beforeEach(() => {
  // Timers stay real, including waitFor and React Query; only the clock is fixed.
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-10-01T00:30:00Z"));
  graph.data = [];
  graph.key = "";
  graph.connectsGaps = false;
});
afterEach(() => vi.useRealTimers());

describe("JUP-055: intervalos mensuales inclusivos", () => {
  it("por defecto solicita seis meses completos UTC y el agregado, nunca el mes en curso", async () => {
    const { requests } = await start();
    await waitFor(() => expect(requests.filter((item) => item.path === "/billing/summary")).toHaveLength(7));
    const queries = requests.filter((item) => item.path === "/billing/summary");
    expect(queries.map((request) => [request.search.get("start_date"), request.search.get("end_date")]).sort()).toEqual([
      ["2026-04-01", "2026-05-01"], ["2026-04-01", "2026-10-01"],
      ["2026-05-01", "2026-06-01"], ["2026-06-01", "2026-07-01"],
      ["2026-07-01", "2026-08-01"], ["2026-08-01", "2026-09-01"], ["2026-09-01", "2026-10-01"]
    ]);
    queries.forEach((request) => expectTenantRequest(request));
    expect(queries.every((request) => request.search.get("group_by") === "service")).toBe(true);
    expect(requests.some((request) => request.path === "/health")).toBe(false);
  });

  it("enero conserva julio-diciembre del año anterior y controles etiquetados", async () => {
    vi.setSystemTime(new Date("2027-01-01T00:30:00Z"));
    await start();
    expect(screen.getByLabelText(/mes inicial/i)).toHaveValue("2026-07");
    expect(screen.getByLabelText(/mes final/i)).toHaveValue("2026-12");
  });

  it.each([
    ["2026-02", "2026-08", "2026-02-01", "2026-09-01", 7],
    ["2026-03", "2026-06", "2026-03-01", "2026-07-01", 4],
    ["2025-12", "2026-02", "2025-12-01", "2026-03-01", 3],
    ["0099-12", "0100-01", "0099-12-01", "0100-02-01", 2],
    ["2025-01", "2026-09", "2025-01-01", "2026-10-01", 21]
  ])("rango %s–%s conserva todos sus meses y límites UTC", async (first, last, from, to, count) => {
    const { requests } = await start();
    await chooseRange(first, last);
    await ready();
    expect(requests.some((request) => request.search.get("start_date") === from && request.search.get("end_date") === to)).toBe(true);
    const rows = within(monthlyTable()).getAllByRole("row").filter((row) => within(row).queryAllByRole("cell").length > 0);
    expect(rows).toHaveLength(count);
    expect(graph.data).toHaveLength(count);
  });

  it("un único mes se consulta una vez y carece de comparación", async () => {
    const { requests } = await start();
    await ready();
    const before = requests.length;
    await chooseRange("2026-06", "2026-06");
    await ready();
    const query = requests.slice(before).filter((request) => request.path === "/billing/summary");
    expect(query).toHaveLength(1);
    expect(query[0].search.get("start_date")).toBe("2026-06-01");
    expect(query[0].search.get("end_date")).toBe("2026-07-01");
    expectUnavailableComparison("Solo hay un mes con coste para comparar");
  });

  it.each([["", "2026-09"], ["2026-09", "2026-04"], ["9999-01", "9999-02"]])(
    "selección inválida %s–%s no inicia consultas", async (first, last) => {
      const { requests } = await start();
      await ready();
      const before = requests.length;
      await chooseRange(first, last);
      expect(document.body).toHaveTextContent(/no v[aá]lido|inv[aá]lid|incompleto|fuera.*rango/i);
      await act(async () => { await Promise.resolve(); });
      expect(requests).toHaveLength(before);
      expect(screen.queryByText(/777[.,]77/)).not.toBeInTheDocument();
    }
  );

  it("acepta meses en curso/futuros y explica que no son previsión", async () => {
    await start((request) => jsonResponse(summary(request, [])));
    await chooseRange("2026-10", "2026-11");
    await screen.findByText(/sin datos.*costes|costes.*sin datos/i);
    expect(document.body).toHaveTextContent(/en curso/i);
    expect(document.body).toHaveTextContent(/futur/i);
    expect(document.body).not.toHaveTextContent(/previsi[oó]n:\s*[0-9]/i);
  });
});

describe("JUP-055: dinero, extremos y monedas", () => {
  it("usa septiembre contra abril, no agosto, y mantiene el total agregado", async () => {
    await start();
    await readyBreakdown();
    expectDelta("+50.00", "+50.00");
    expect(document.body).toHaveTextContent(/septiembre.*abril|abril.*septiembre/i);
    expect(document.body).toHaveTextContent(/777[.,]77\s*EUR/);
    expect(breakdownTable()).toHaveTextContent("777.77");
    expect(document.body).not.toHaveTextContent(/-250[.,]00\s*%/);
  });

  it("redondeo por consulta no redistribuye ni reemplaza el total por suma de meses", async () => {
    await start((request) => jsonResponse(summary(request, [total(isMonthly(request) ? "0.01" : "0.03")],
      { groups: [{ ...total("0.02"), value: "Compute", subscription_id: null }] })));
    await readyBreakdown();
    expect(document.body).toHaveTextContent(/0[.,]03\s*EUR/);
    expect(breakdownTable()).toHaveTextContent("0.02");
    expect(monthRow("2026-04")).toHaveTextContent("0.01");
    expect(document.body).toHaveTextContent(/redonde/i);
  });

  it.each([
    ["0.00", "12.00", "+7.00", "+140.00"],
    ["-100.00", "-50.00", "+50.00", "-50.00"],
    ["3.00", "4.00", "+1.00", "+33.33"],
    ["200.00", "199.99", "-0.01", "-0.01"],
    ["10000.00", "9999.99", "-0.01", "0.00"],
    ["200.00", "200.01", "+0.01", "+0.01"]
  ])("base %s y último %s preservan signo/precisión", async (first, last, difference, percent) => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      return jsonResponse(summary(request, [total(isMonthly(request) ? month === "2026-04" ? first : month === "2026-09" ? last : "5.00" : "987.65")]));
    });
    await readyBreakdown();
    expectDelta(difference, percent);
    if (first === "0.00") {
      expectObservedComparison("mayo", "septiembre", "+7.00", "+140.00");
      expect(monthRow("2026-04")).toHaveTextContent("0.00");
      expect(plottedValues()).toEqual([0, 5, 5, 5, 5, 12]);
      expect(document.body).not.toHaveTextContent(/Infinity|NaN/);
    }
    if (first.startsWith("-")) expect(document.body).toHaveTextContent(/base negativa/i);
    expect(document.body).not.toHaveTextContent(/-0[.,]00\s*%/);
  });

  it("importes grandes mantienen centavos exactos y quedan fuera del gráfico con aviso", async () => {
    await start((request) => {
      const cost = !isMonthly(request) ? "18014398509481986.06"
        : request.search.get("start_date") === "2026-04-01" ? "9007199254740993.01"
        : request.search.get("start_date") === "2026-09-01" ? "9007199254740993.03" : "2.00";
      return jsonResponse(summary(request, [total(cost)]));
    });
    await ready();
    expect(monthRow("2026-04")).toHaveTextContent("9007199254740993.01");
    expect(monthRow("2026-09")).toHaveTextContent("9007199254740993.03");
    expectDelta("+0.02");
    expect(document.body).toHaveTextContent(/representa|precisi[oó]n.*gr[aá]fic|gr[aá]fic.*l[ií]mit/i);
    const values = plottedValues();
    expect(values[0] == null).toBe(true);
    expect(values[5] == null).toBe(true);
    expect(values[1]).toBe(2);
    expect(graph.connectsGaps).toBe(false);
  });

  it("selector de moneda separa EUR/USD, conserva totales y no convierte", async () => {
    await start((request) => jsonResponse(summary(request, [
      total(isMonthly(request) ? request.search.get("start_date") === "2026-09-01" ? "150.00" : "100.00" : "700.00"),
      total(isMonthly(request) ? request.search.get("start_date") === "2026-09-01" ? "24.00" : "20.00" : "124.00", "USD")
    ])));
    await ready();
    expect(document.body).toHaveTextContent(/700[.,]00\s*EUR/);
    expect(document.body).toHaveTextContent(/124[.,]00\s*USD/);
    const currency = screen.getByRole("combobox", { name: /moneda/i });
    expect(within(currency).getAllByRole("option").map((option) => (option as HTMLOptionElement).value).sort()).toEqual(["EUR", "USD"]);
    await userEvent.setup().selectOptions(currency, "USD");
    expect(monthlyTable()).toHaveTextContent("USD");
    expect(monthlyTable()).not.toHaveTextContent("EUR");
    expect(document.body).toHaveTextContent(/\+4[.,]00\s*USD/);
    expect(document.body).toHaveTextContent(/\+20[.,]00\s*%/);
    expect(plottedValues()).toEqual([20, 20, 20, 20, 20, 24]);
  });

  it.each(["first", "last", "currency"])("extremo ausente (%s) usa el primer y último coste no cero de la moneda", async (missing) => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      const absent = isMonthly(request) && (month === (missing === "last" ? "2026-09" : "2026-04"));
      return jsonResponse(summary(request, absent ? missing === "currency" ? [total("40.00", "USD")] : [] : [total("100.00")]));
    });
    await readyBreakdown();
    expectObservedComparison(missing === "last" ? "abril" : "mayo",
      missing === "last" ? "agosto" : "septiembre", "0.00", "0.00");
    const absentMonth = missing === "last" ? "2026-09" : "2026-04";
    expect(monthRow(absentMonth)).toHaveTextContent(/sin datos|moneda.*ausente|no.*datos/i);
    expect(monthRow(absentMonth)).not.toHaveTextContent("0.00");
    expect(plottedValues()[missing === "last" ? 5 : 0]).toBeNull();
    expect(graph.data).toHaveLength(6);
    expect(graph.connectsGaps).toBe(false);
  });
});

describe("JUP-055: estados honestos y gráfico accesible", () => {
  it("hueco sin datos y cero observado son distintos y no se conectan", async () => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      return jsonResponse(summary(request, isMonthly(request) && month === "2026-05" ? []
        : [total(isMonthly(request) && month === "2026-06" ? "0.00" : "100.00")]));
    });
    await ready();
    expect(monthRow("2026-05")).toHaveTextContent(/sin datos/i);
    expect(monthRow("2026-05")).not.toHaveTextContent("0.00");
    expect(monthRow("2026-06")).toHaveTextContent("0.00");
    expect(plottedValues()[1] == null).toBe(true);
    expect(plottedValues()[2]).toBe(0);
    expect(graph.connectsGaps).toBe(false);
  });

  it.each([503, 409])("error mensual %i conserva total y dos extremos válidos, dejando hueco", async (status) => {
    await start((request) => isMonthly(request) && request.search.get("start_date") === "2026-06-01"
      ? jsonResponse({ detail: status === 409 ? { code: "ambiguous_cost_source" } : "Unavailable" }, status)
      : jsonResponse(summary(request)));
    await ready();
    expect(document.body).toHaveTextContent(/777[.,]77\s*EUR/);
    expect(monthRow("2026-06")).toHaveTextContent(status === 409 ? /solap|error/i : /error|no disponible/i);
    expect(monthRow("2026-06")).not.toHaveTextContent("0.00");
    expectDelta("+50.00", "+50.00");
    expect(comparisonRegion()).toHaveTextContent(/observad/i);
    expect(comparisonRegion()).toHaveTextContent(/error|no.*consult|fall/i);
    expect(plottedValues()[2] == null).toBe(true);
  });

  it("partial muestra omisiones/null sin sumar recuentos globales repetidos", async () => {
    await start((request) => jsonResponse(summary(request, undefined, {
      data_status: "partial", missing_dimension_count: 3, excluded_undated_count: 2,
      groups: [{ ...total("777.77"), subscription_id: null, value: null }]
    })));
    await readyBreakdown();
    expect(document.body).toHaveTextContent(/parcial/i);
    expect(document.body).toHaveTextContent(/3.*sin dimensi[oó]n/);
    expect(document.body).toHaveTextContent(/2.*sin fecha/);
    expect(document.body).not.toHaveTextContent(/12 registros sin fecha|14 registros sin fecha/);
    expect(breakdownTable()).toHaveTextContent(/sin dimensi[oó]n/i);
    expectDelta("+50.00", "+50.00");
  });

  it("error del agregado no se sustituye por meses exitosos ni demo", async () => {
    await start((request) => isMonthly(request) ? jsonResponse(summary(request))
      : jsonResponse({ detail: "Unavailable" }, 503));
    await screen.findByRole("alert");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.queryByText(/777[.,]77|100[.,]00|298\.000/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reintentar/i })).toBeEnabled();
    expect(screen.queryByRole("region", { name: /demostraci[oó]n/i })).not.toBeInTheDocument();
  });

  it("retira inventario/exportación demo y mantiene ahorro no disponible", async () => {
    await start();
    await screen.findByRole("table", { name: /desglose/i });
    expect(screen.queryByRole("region", { name: /demostraci[oó]n/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/inventario demo/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /export/i })).not.toBeInTheDocument();
    expect(document.body).toHaveTextContent(/ahorro.*no disponible/i);
  });
});

describe("JUP-055: aislamiento, metadata, cancelación y concurrencia", () => {
  it("refetch oculta todos los importes cacheados hasta completar el conjunto", async () => {
    let hold = false;
    const pending: { request: RequestInfo; resolve: (value: Response) => void }[] = [];
    const { client } = await start((request) => hold
      ? new Promise<Response>((resolve) => { pending.push({ request, resolve }); })
      : jsonResponse(summary(request, [total("123456.78")])));
    await screen.findByRole("table", { name: /desglose/i });
    hold = true;
    let finished!: Promise<unknown>;
    act(() => { finished = client.invalidateQueries(); });
    await waitFor(() => expect(pending.length).toBeGreaterThan(0));
    expect(document.body).not.toHaveTextContent(/123456[.,]78/);
    expect(document.body).toHaveTextContent(/cargando/i);
    hold = false;
    await act(async () => { pending.forEach(({ request, resolve }) => resolve(jsonResponse(summary(request, [total("123456.78")])))); await finished; });
    await ready();
    expect(document.body).toHaveTextContent(/123456[.,]78\s*EUR/);
  });

  it.each(["dates", "group", "tag"])("rechaza metadata incompatible del agregado: %s", async (fault) => {
    await start((request) => {
      const data = summary(request, [total("888888.88")]);
      {
        if (fault === "dates") data.period = { start_date: "2024-01-01", end_date: "2024-02-01", timezone: "UTC" };
        if (fault === "group") data.group_by = "project";
        if (fault === "tag") { data.group_by = "tag"; data.tag_key = "other"; }
      }
      return jsonResponse(data);
    });
    await waitFor(() => expect(screen.queryByText(/888888\.88/)).not.toBeInTheDocument());
    expect(await screen.findByRole("alert")).toHaveTextContent(/error|no disponible|incompatible/i);
  });

  it("tag usa clave canónica común y omite clave inactiva al cambiar agrupación", async () => {
    const { requests } = await start();
    await ready();
    const grouping = screen.getByRole("combobox", { name: /agrupar|desglose/i });
    await userEvent.setup().selectOptions(grouping, "tag");
    fireEvent.change(screen.getByLabelText(/clave.*etiqueta/i), { target: { value: "CostCenter" } });
    await ready();
    const tagged = requests.filter((request) => request.search.get("group_by") === "tag");
    expect(tagged).toHaveLength(7);
    expect(tagged.every((request) => request.search.get("tag_key") === "CostCenter")).toBe(true);
    expect(document.body).toHaveTextContent("cost_center");
    const before = requests.length;
    await userEvent.setup().selectOptions(grouping, "subscription");
    await ready();
    expect(requests.slice(before).every((request) => !request.search.has("tag_key"))).toBe(true);
  });

  it("metadata mensual equivocada se convierte en error/gap y no en cifra", async () => {
    await start((request) => {
      if (isMonthly(request) && request.search.get("start_date") === "2026-05-01") {
        return jsonResponse(summary(request, [total("666666.66")], { group_by: "project" }));
      }
      return jsonResponse(summary(request));
    });
    await ready();
    expect(monthRow("2026-05")).toHaveTextContent(/error|incompatible|no disponible/i);
    expect(screen.queryByText(/666666\.66/)).not.toBeInTheDocument();
  });

  it("limita a tres requests, aborta el conjunto anterior y no inicia su cola tras cambiar tenant", async () => {
    const network = backend((request) => request.headers.get("X-Tenant-Id") === tenants[0].id
      ? new Promise<Response>((resolve) => { blocked.push({ request, resolve }); })
      : jsonResponse(summary(request, [total("222.22")])));
    const originalFetch = globalThis.fetch;
    const signals: AbortSignal[] = [];
    const blocked: { request: RequestInfo; resolve: (response: Response) => void }[] = [];
    vi.stubGlobal("fetch", vi.fn<typeof fetch>((input, init) => {
      if (String(input).includes("/billing/summary") && init?.signal) signals.push(init.signal);
      return originalFetch(input, init);
    }));
    restoreSession();
    renderApp();
    await screen.findByText("Dashboard Ejecutivo - Coste Global");
    await waitFor(() => expect(blocked).toHaveLength(3));
    expect(signals).toHaveLength(3);
    expect(signals.every((signal) => !signal.aborted)).toBe(true);
    await userEvent.setup().selectOptions(screen.getByLabelText("Ambito de cliente"), tenants[1].id);
    await ready();
    expect(signals.slice(0, 3).every((signal) => signal.aborted)).toBe(true);
    expect(network.requests.filter((request) => request.path === "/billing/summary" && request.headers.get("X-Tenant-Id") === tenants[0].id)).toHaveLength(3);
    await act(async () => blocked.forEach(({ request, resolve }) => resolve(jsonResponse(summary(request, [total("999999.99")])))));
    expect(network.requests.filter((request) => request.path === "/billing/summary" && request.headers.get("X-Tenant-Id") === tenants[0].id)).toHaveLength(3);
    expect(screen.queryByText(/999999\.99/)).not.toBeInTheDocument();
    expect(document.body).toHaveTextContent(/222[.,]22\s*EUR/);
  });

  it("sin sesión no consulta billing", async () => {
    const network = backend();
    renderApp();
    await screen.findByRole("button", { name: /iniciar|entrar|sign in|login/i });
    expect(network.requests.some((request) => request.path === "/billing/summary")).toBe(false);
  });

  it("401 de billing usa invalidación existente y no presenta cantidades", async () => {
    const { requests } = backend(() => jsonResponse({ detail: "Unauthorized" }, 401));
    restoreSession();
    renderApp();
    await screen.findByRole("button", { name: /iniciar|entrar|sign in|login/i });
    expect(screen.queryByText(/777[.,]77/)).not.toBeInTheDocument();
    expect(requests.filter((request) => request.path === "/billing/summary").length).toBeLessThanOrEqual(3);
  });

  it("reintento manual obtiene TODO el conjunto y no reutiliza puntos de la ejecución anterior", async () => {
    let second = false;
    const { requests } = await start((request) => {
      if (isMonthly(request) && request.search.get("start_date") === (second ? "2026-07-01" : "2026-06-01")) {
        return jsonResponse({ detail: "Unavailable" }, 503);
      }
      return jsonResponse(summary(request, [total(second ? "456.78" : "123.45")]));
    });
    await ready();
    const before = requests.filter((request) => request.path === "/billing/summary").length;
    expect(before).toBe(7);
    second = true;
    await userEvent.setup().click(screen.getByRole("button", { name: /reintentar/i }));
    await ready();
    expect(requests.filter((request) => request.path === "/billing/summary")).toHaveLength(14);
    expect(monthRow("2026-07")).toHaveTextContent(/error|no disponible/i);
    expect(monthRow("2026-07")).not.toHaveTextContent("123.45");
    expect(monthRow("2026-06")).toHaveTextContent("456.78");
  });
});

describe("JUP-055: controles y límites adicionales", () => {
  it("sin tenant disponible no solicita costes ni muestra importes previos", async () => {
    const { requests } = mockBackend({ "GET /tenants": () => jsonResponse({ items: [] }) });
    restoreSession();
    renderApp();
    await screen.findByText(/selecciona un cliente|sin clientes|no hay tenants/i);
    expect(requests.some((request) => request.path === "/billing/summary")).toBe(false);
    expect(screen.queryByText(/12345\.67/)).not.toBeInTheDocument();
  });

  it("los controles mensuales son alcanzables por teclado y conservan foco", async () => {
    await start();
    const initial = screen.getByLabelText(/mes inicial/i);
    const final = screen.getByLabelText(/mes final/i);
    initial.focus();
    expect(initial).toHaveFocus();
    await userEvent.setup().tab();
    expect(final).toHaveFocus();
  });

  it.each([409, 422])("no hereda reintentos automáticos en error %i", async (status) => {
    const { requests } = await start(() => jsonResponse({
      detail: status === 409 ? { code: "ambiguous_cost_source" } : "Invalid selection"
    }, status), (client) => client.setDefaultOptions({
      queries: { retry: 2, retryDelay: 0, gcTime: Infinity }
    }));
    await screen.findByRole("alert");
    const query = requests.filter((request) => request.path === "/billing/summary");
    const unique = new Set(query.map((request) => request.search.toString()));
    expect(query).toHaveLength(unique.size);
    expect(screen.queryByText(/0\.00/)).not.toBeInTheDocument();
  });

  it("tag mensual canónico incompatible no se usa como punto", async () => {
    await start((request) => jsonResponse(summary(request, [total("555555.55")], {
      tag_key: request.search.get("group_by") === "tag"
        ? isMonthly(request) && request.search.get("start_date") === "2026-05-01" ? "other" : "cost_center"
        : null
    })));
    await ready();
    await userEvent.setup().selectOptions(screen.getByRole("combobox", { name: /agrupar|desglose/i }), "tag");
    fireEvent.change(screen.getByLabelText(/clave.*etiqueta/i), { target: { value: "CostCenter" } });
    await ready();
    expect(monthRow("2026-05")).toHaveTextContent(/error|incompatible|no disponible/i);
    expect(monthRow("2026-05")).not.toHaveTextContent("555555.55");
  });

  it("grupo de recursos con ámbito nulo declara la suscripción ausente", async () => {
    await start((request) => jsonResponse(summary(request, undefined, {
      data_status: "partial", missing_dimension_count: 1,
      groups: [{ ...total("777.77"), value: null, subscription_id: null }]
    })));
    await ready();
    await userEvent.setup().selectOptions(screen.getByRole("combobox", { name: /agrupar|desglose/i }), "resource_group");
    await ready();
    expect(breakdownTable()).toHaveTextContent(/sin dimensi[oó]n/i);
    expect(breakdownTable()).toHaveTextContent(/sin suscripci[oó]n/i);
  });
});


describe("JUP-055: refinamiento del desglose junto al selector", () => {
  it("sitúa una sola instancia del desglose después del selector y avisos, antes de los resultados financieros", async () => {
    await start((request) => jsonResponse(summary(request, undefined, {
      data_status: "partial", missing_dimension_count: 1, excluded_undated_count: 0
    })));
    await ready();
    const selection = screen.getByRole("region", { name: "Selección de costes de Azure" });
    const notice = screen.getByText(/1 registros sin dimensión; 0 registros sin fecha excluidos/);
    const breakdown = screen.getByRole("heading", { name: "Desglose del periodo" });
    const totals = screen.getByRole("heading", { name: "Coste total del periodo" });
    const comparison = screen.getByRole("region", { name: "Comparación de meses" });
    const trend = screen.getByRole("heading", { name: "Evolución de costes mensuales" });
    expect(screen.getAllByRole("heading", { name: "Desglose del periodo" })).toHaveLength(1);
    expect(screen.getAllByRole("table", { name: /desglose/i })).toHaveLength(1);
    expect(within(selection).getByRole("combobox", { name: "Agrupar por" })).toBeVisible();
    expect(notice).toHaveAttribute("role", "status");
    // DOM order is the reading order exposed to assistive technology.
    // Actual visual positioning still needs the independent browser check.
    const expectBefore = (first: HTMLElement, next: HTMLElement) => {
      expect(first.compareDocumentPosition(next) & Node.DOCUMENT_POSITION_FOLLOWING)
        .toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    };
    expectBefore(selection, notice);
    expectBefore(notice, breakdown);
    expectBefore(breakdown, totals);
    expectBefore(totals, comparison);
    expectBefore(comparison, trend);
    expectBefore(trend, monthlyTable());
  });

  it("cambiar servicio por proyecto cambia grupos visibles sin filtrar totales, meses, comparación o tendencia", async () => {
    await start((request) => {
      const data = summary(request);
      if (!isMonthly(request)) {
        data.totals = [{ ...total("777.77"), record_count: 2 }];
        data.groups = (request.search.get("group_by") === "project"
          ? [["Finance", "345.00"], ["Platform", "432.77"]]
          : [["Compute", "455.00"], ["Storage", "322.77"]])
          .map(([value, cost]) => ({ ...total(cost), value, subscription_id: null }));
      }
      return jsonResponse(data);
    });
    await ready();
    expect(within(breakdownTable()).getByRole("row", { name: /Compute.*EUR.*455\.00/ })).toBeVisible();
    expect(within(breakdownTable()).getByRole("row", { name: /Storage.*EUR.*322\.77/ })).toBeVisible();
    const totals = screen.getByRole("region", { name: "Totales de costes" }).textContent;
    const months = monthlyTable().textContent;
    const comparison = screen.getByRole("region", { name: "Comparación de meses" }).textContent;
    const trend = plottedValues();
    expect(screen.getByRole("region", { name: "Totales de costes" })).toHaveTextContent("777.77 EUR");

    await userEvent.setup().selectOptions(screen.getByRole("combobox", { name: "Agrupar por" }), "project");
    expect(await screen.findByRole("row", { name: /Finance.*EUR.*345\.00/ })).toBeVisible();
    expect(within(breakdownTable()).getByRole("row", { name: /Platform.*EUR.*432\.77/ })).toBeVisible();
    expect(breakdownTable()).not.toHaveTextContent(/Compute|Storage/);
    expect(screen.getByRole("region", { name: "Totales de costes" }).textContent).toBe(totals);
    expect(monthlyTable().textContent).toBe(months);
    expect(screen.getByRole("region", { name: "Comparación de meses" }).textContent).toBe(comparison);
    expect(plottedValues()).toEqual(trend);
  });
});


describe("JUP-055: comparación por meses con coste no cero", () => {
  it("año completo compara marzo–agosto y conserva doce posiciones, total y ceros", async () => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      const cost = month === "2026-03" ? "20.00" : month === "2026-08" ? "60.00"
        : month === "2026-05" ? "0.00" : null;
      return jsonResponse(summary(request, !isMonthly(request) ? [total("80.00")]
        : cost === null ? [] : [total(cost)]));
    });
    await ready();
    await chooseRange("2026-01", "2026-12");
    await ready();
    expectObservedComparison("marzo", "agosto", "+40.00", "+200.00");
    expect(screen.getByLabelText(/mes inicial/i)).toHaveValue("2026-01");
    expect(screen.getByLabelText(/mes final/i)).toHaveValue("2026-12");
    expect(screen.getByRole("region", { name: "Selección de costes de Azure" }))
      .toHaveTextContent(/enero de 2026.*diciembre de 2026/);
    expect(screen.getByRole("region", { name: "Totales de costes" })).toHaveTextContent("80.00 EUR");
    expect(breakdownTable()).toHaveTextContent("80.00");
    expect(within(monthlyTable()).getAllByRole("row")).toHaveLength(13);
    expect(graph.data.map((point) => point.month)).toEqual([
      "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06",
      "2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"
    ]);
    expect(plottedValues()).toEqual([null, null, 20, null, 0, null, null, 60, null, null, null, null]);
    expect(monthRow("2026-01")).toHaveTextContent(/sin datos/i);
    expect(monthRow("2026-05")).toHaveTextContent("0.00");
    expect(monthRow("2026-12")).toHaveTextContent(/sin datos/i);
    expect(graph.connectsGaps).toBe(false);
  });

  it.each([
    ["créditos negativos", "-100.00", "-50.00", "-150.00", "+50.00", "-50.00"],
    ["importes fuera del gráfico", "9007199254740993.01", "9007199254740993.03", "18014398509481986.04", "+0.02", "0.00"],
    ["total neto cero", "20.00", "-20.00", "0.00", "-40.00", "-200.00"]
  ])("%s conserva dos meses elegibles interiores y precisión exacta", async (_case, first, last, aggregate, delta, percent) => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      const cost = !isMonthly(request) ? aggregate : month === "2026-05" ? first
        : month === "2026-08" ? last : "0.00";
      return jsonResponse(summary(request, [total(cost)]));
    });
    await ready();
    expectObservedComparison("mayo", "agosto", delta, percent);
    expect(screen.getByRole("region", { name: "Totales de costes" })).toHaveTextContent(aggregate + " EUR");
    expect(monthRow("2026-05")).toHaveTextContent(first);
    expect(monthRow("2026-08")).toHaveTextContent(last);
    expect(monthRow("2026-04")).toHaveTextContent("0.00");
    expect(graph.data).toHaveLength(6);
    if (_case === "importes fuera del gráfico") {
      expect(plottedValues()).toEqual([0, null, 0, 0, null, 0]);
      expect(document.body).toHaveTextContent(/límite de representación gráfica/);
      expect(graph.connectsGaps).toBe(false);
    }
    if (first.startsWith("-")) expect(comparisonRegion()).toHaveTextContent(/base negativa/);
    expect(comparisonRegion()).not.toHaveTextContent(/Infinity|NaN|-0[.,]00\s*%/);
  });

  it("cada moneda elige sus propios extremos sin sumar ni convertir los costes", async () => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      const eur = month === "2026-05" ? "40.00" : month === "2026-08" ? "80.00" : "0.00";
      const usd = month === "2026-06" ? "-20.00" : month === "2026-09" ? "-10.00" : "0.00";
      return jsonResponse(summary(request, isMonthly(request)
        ? [total(eur), total(usd, "USD")] : [total("120.00"), total("-30.00", "USD")]));
    });
    await ready();
    expectObservedComparison("mayo", "agosto", "+40.00", "+100.00");
    expect(plottedValues()).toEqual([0, 40, 0, 0, 80, 0]);
    await userEvent.setup().selectOptions(screen.getByRole("combobox", { name: /moneda/i }), "USD");
    const comparison = comparisonRegion();
    expect(within(comparison).getByRole("heading")).toHaveTextContent(/septiembre.*junio.*USD/);
    expect(comparison).toHaveTextContent(/\+10[.,]00\s*USD/);
    expect(comparison).toHaveTextContent(/-50[.,]00\s*%/);
    expect(comparison).not.toHaveTextContent(/\+40[.,]00\s*EUR/);
    expect(plottedValues()).toEqual([0, 0, -20, 0, 0, -10]);
    expect(monthlyTable()).not.toHaveTextContent("EUR");
    expect(screen.getByRole("region", { name: "Totales de costes" }))
      .toHaveTextContent(/120[.,]00\s*EUR.*-30[.,]00\s*USD/);
  });

  it.each(["ceros", "ausencias", "mixto"])("ningún elegible entre %s explica el límite sin comparación numérica", async (mode) => {
    await start((request) => {
      const zero = mode === "ceros" || mode === "mixto" && request.search.get("start_date") === "2026-06-01";
      return jsonResponse(summary(request, !isMonthly(request) ? [total("0.00")]
        : zero ? [total("0.00")] : []));
    });
    await ready();
    expectUnavailableComparison("No hay meses con coste en este periodo");
    expect(graph.data).toHaveLength(6);
    expect(monthRow("2026-06")).toHaveTextContent(mode === "ausencias" ? /sin datos/i : /0[.,]00/);
    expect(monthRow("2026-04")).toHaveTextContent(mode === "ceros" ? /0[.,]00/ : /sin datos/i);
  });

  it.each([
    ["positivo", "40.00", "ceros"],
    ["negativo", "-40.00", "ausencias"],
    ["no representable", "9007199254740993.01", "ceros"]
  ])("un único elegible %s interior no compara con ceros o ausencias", async (_case, cost, edges) => {
    await start((request) => {
      const values = !isMonthly(request) || request.search.get("start_date") === "2026-06-01"
        ? [total(cost)] : edges === "ceros" ? [total("0.00")] : [];
      return jsonResponse(summary(request, values));
    });
    await ready();
    expectUnavailableComparison("Solo hay un mes con coste para comparar");
    expect(monthRow("2026-06")).toHaveTextContent(cost);
    expect(graph.data).toHaveLength(6);
    if (_case === "no representable") {
      expect(plottedValues()[2]).toBeNull();
      expect(document.body).toHaveTextContent(/límite de representación gráfica/);
    }
  });

  it.each([
    ["2026-04", "HTTP 503", "2026-05", "2026-08"],
    ["2026-09", "HTTP 409", "2026-05", "2026-08"],
    ["2026-04", "metadata", "2026-05", "2026-08"],
    ["2026-09", "metadata", "2026-05", "2026-08"],
    ["2026-05", "HTTP 503", "2026-06", "2026-08"],
    ["2026-08", "HTTP 409", "2026-05", "2026-07"]
  ])("fallo exterior %s (%s) impide afirmar los extremos observados", async (failedMonth, cause, firstMonth, lastMonth) => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      if (isMonthly(request) && month === failedMonth) {
        if (cause === "metadata") return jsonResponse(summary(request, [total("666666.66")], { group_by: "project" }));
        return jsonResponse({ detail: cause === "HTTP 409" ? { code: "ambiguous_cost_source" } : "Unavailable" },
          cause === "HTTP 409" ? 409 : 503);
      }
      return jsonResponse(summary(request, [total(!isMonthly(request) ? "60.00"
        : month === firstMonth ? "20.00" : month === lastMonth ? "40.00" : "0.00")]));
    });
    await ready();
    const comparison = expectUnavailableComparison(/comparación no disponible/i);
    const names: Record<string, string> = { "2026-04": "abril", "2026-05": "mayo", "2026-08": "agosto", "2026-09": "septiembre" };
    expect(comparison).toHaveTextContent(names[failedMonth] + " de 2026");
    expect(comparison).toHaveTextContent(cause === "metadata" ? /incompatible/ : cause === "HTTP 409" ? /solap/ : /error|no disponible/i);
    expect(comparison).not.toHaveTextContent(/Solo hay un mes con coste|No hay meses con coste/);
    expect(monthRow(failedMonth)).not.toHaveTextContent("0.00");
    expect(plottedValues()[Number(failedMonth.slice(5, 7)) - 4]).toBeNull();
    expect(screen.queryByText("666666.66")).not.toBeInTheDocument();
  });

  it.each([
    ["ninguno", false, 503],
    ["uno", true, 409],
    ["uno con metadata inválida", true, 200]
  ])("%s y un mes fallido no se convierte en certeza sobre la cantidad de meses con coste", async (_case, one, status) => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      if (isMonthly(request) && month === "2026-07") {
        return status === 200 ? jsonResponse(summary(request, [total("666666.66")], { group_by: "project" }))
          : jsonResponse({ detail: status === 409 ? { code: "ambiguous_cost_source" } : "Unavailable" }, status);
      }
      return jsonResponse(summary(request, [total(!isMonthly(request) || one && month === "2026-06" ? "20.00" : "0.00")]));
    });
    await ready();
    const comparison = expectUnavailableComparison(/comparación no disponible/i);
    expect(comparison).toHaveTextContent(/julio de 2026/);
    expect(comparison).toHaveTextContent(status === 200 ? /incompatible/ : status === 409 ? /solap/ : /error|no disponible/i);
    expect(comparison).not.toHaveTextContent(/Solo hay un mes con coste|No hay meses con coste/);
    expect(monthRow("2026-07")).not.toHaveTextContent("0.00");
    expect(plottedValues()[3]).toBeNull();
  });

  it.each([503, 409, 200])("error interior %i conserva comparación observada y su limitación explícita", async (status) => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      if (isMonthly(request) && month === "2026-06") {
        return status === 200 ? jsonResponse(summary(request, [total("666666.66")], { group_by: "project" }))
          : jsonResponse({ detail: status === 409 ? { code: "ambiguous_cost_source" } : "Unavailable" }, status);
      }
      return jsonResponse(summary(request, [total(!isMonthly(request) ? "60.00"
        : month === "2026-05" ? "20.00" : month === "2026-08" ? "40.00" : "0.00")]));
    });
    await ready();
    expectObservedComparison("mayo", "agosto", "+20.00", "+100.00");
    expect(comparisonRegion()).toHaveTextContent(/observad/i);
    expect(comparisonRegion()).toHaveTextContent(/error|no.*consult|fall/i);
    expect(monthRow("2026-06")).toHaveTextContent(status === 200 ? /incompatible/ : status === 409 ? /solap/ : /error|no disponible/i);
    expect(monthRow("2026-06")).not.toHaveTextContent("0.00");
    expect(plottedValues()).toEqual([0, 20, null, 0, 40, 0]);
    expect(graph.connectsGaps).toBe(false);
  });

  it("costes partial interiores siguen elegibles y limitan la comparación observada", async () => {
    await start((request) => {
      const month = request.search.get("start_date")?.slice(0, 7);
      const eligible = isMonthly(request) && (month === "2026-05" || month === "2026-08");
      return jsonResponse(summary(request, [total(!isMonthly(request) ? "60.00"
        : month === "2026-05" ? "20.00" : month === "2026-08" ? "40.00" : "0.00")],
      eligible ? { data_status: "partial", missing_dimension_count: 1, excluded_undated_count: 2 } : {}));
    });
    await ready();
    expectObservedComparison("mayo", "agosto", "+20.00", "+100.00");
    expect(comparisonRegion()).toHaveTextContent(/parcial.*observad|observad.*parcial/i);
    expect(monthRow("2026-05")).toHaveTextContent(/parciales/);
    expect(monthRow("2026-08")).toHaveTextContent(/parciales/);
    expect(monthRow("2026-05")).toHaveTextContent(/1 sin dimensión; 2 sin fecha/);
    expect(graph.data).toHaveLength(6);
  });
});
