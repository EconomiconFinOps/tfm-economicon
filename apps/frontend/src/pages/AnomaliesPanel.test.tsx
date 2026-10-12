// JUP-114: panel /anomalies conectado a los episodios guardados del cliente activo.
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AnomaliesPanel } from "./AnomaliesPanel";
import { episode, episodeList } from "../test/anomalyFixtures";

const compute = episode();
const database = episode({ id: "anomaly-2", service: "Database", start_date: "2026-09-16", reference_daily_cost: "171.43",
  opening_observed_cost: "300.00", accumulated_impact: "642.86", impact_day_count: 5, severity: "P2" });
const analytics = episode({ id: "anomaly-3", service: "Analytics", start_date: "2026-09-10", last_seen_date: "2026-09-10",
  observation: "no_longer_observed", no_longer_observed_on: "2026-09-14", reference_daily_cost: "311.14",
  opening_observed_cost: "480.00", accumulated_impact: "168.86", impact_day_count: 4, severity: "P3" });
const closed = episode({ id: "anomaly-4", service: "Storage", severity: "P3", accumulated_impact: "120.00", status: "resolved",
  closed_at: "2026-10-12T11:00:00Z", closure_reason: "Revertido", status_changed_by: "user-finops-admin" });
const demo = episodeList({ episodes: [compute, database, analytics, closed],
  open_impact_by_currency: [{ currency: "EUR", amount: "3619.43" }] });
const completedRun = {
  status: "completed", rules_version: "jup019-daily-v1", last_complete_day: "2026-09-20",
  evaluated_days: Array.from({ length: 13 }, (_, i) => `2026-09-${String(8 + i).padStart(2, "0")}`),
  skipped_days: [{ date: "2026-09-07", reason: "reference_incomplete" }], unsupported_currencies: [],
  opened: 3, continued: 0, no_longer_observed: 1,
};

type Handler = (url: string, init: RequestInit) => Promise<Response> | Response;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function stubApi(handlers: { list?: Handler | unknown; detect?: Handler | unknown; patch?: Handler | unknown }) {
  const call = (handler: unknown, url: string, init: RequestInit) =>
    typeof handler === "function" ? (handler as Handler)(url, init) : json(handler);
  const fetchMock = vi.fn((input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input);
    if (url.includes("/billing/anomalies/detect")) return Promise.resolve(call(handlers.detect, url, init));
    if (init.method === "PATCH") return Promise.resolve(call(handlers.patch, url, init));
    return Promise.resolve(call(handlers.list, url, init));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function TenantSwitcher() {
  const [tenant, setTenant] = useState({ id: "tenant-core", name: "Core Finance" });
  return <>
    <button onClick={() => setTenant({ id: "tenant-growth", name: "Growth Ops" })}>Cambiar cliente</button>
    <Outlet context={{ token: "tok-1", activeTenant: tenant, activeTenantId: tenant.id }} />
  </>;
}

function renderPanel() {
  const router = createMemoryRouter([{ path: "/", Component: TenantSwitcher, children: [{ index: true, Component: AnomaliesPanel }] }]);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
}

const rows = () => screen.getAllByRole("row").slice(1);
const rowText = () => rows().map((row) => row.textContent ?? "");

afterEach(() => vi.unstubAllGlobals());

describe("JUP-114 panel de anomalías: lectura y resumen", () => {
  it("enseña las abiertas en el orden del backend, con etiquetas y sin textos inventados", async () => {
    stubApi({ list: demo });
    renderPanel();
    await waitFor(() => expect(rows()).toHaveLength(3));
    const text = rowText();
    expect(text[0]).toContain("Alta (P1)");
    expect(text[0]).toContain("Compute");
    expect(text[0]).toContain("2807.71 EUR");
    expect(text[0]).toContain("en 12 días");
    expect(text[1]).toContain("Media (P2)");
    expect(text[2]).toContain("Baja (P3)");
    expect(text[2]).toContain("Ya no se observa desde 14/09/2026");
    expect(text[0]).toContain("Se sigue observando");
    expect(text.join(" ")).not.toMatch(/Pico de coste|Consultas costosas|AI-/);
    expect(screen.queryByText(/Storage/)).not.toBeInTheDocument();
  });

  it("resume con el total exacto del backend por moneda y no cambia con los filtros", async () => {
    stubApi({ list: demo });
    renderPanel();
    const summary = await screen.findByRole("region", { name: /Resumen de todas las anomalías del cliente/ });
    expect(within(summary).getByText("3619.43 EUR")).toBeInTheDocument();
    expect(within(summary).getByTestId("summary-open")).toHaveTextContent("3");
    expect(within(summary).getByTestId("summary-p1")).toHaveTextContent("1");
    expect(within(summary).getByTestId("summary-ended")).toHaveTextContent("1");
    fireEvent.change(screen.getByLabelText("Criticidad"), { target: { value: "P3" } });
    expect(rows()).toHaveLength(1);
    expect(within(summary).getByText("3619.43 EUR")).toBeInTheDocument();
    expect(within(summary).getByTestId("summary-open")).toHaveTextContent("3");
  });

  it("recorta el texto solo para lectores de pantalla de la tabla dentro de su contenedor con desplazamiento", async () => {
    stubApi({ list: demo });
    renderPanel();
    const region = await screen.findByRole("region", { name: /Lista de anomalías; desplazamiento horizontal disponible/ });
    // Sin `relative`, el `sr-only` (posición absoluta) escapa del recorte y alarga la página a 390 px de ancho.
    expect(region).toHaveClass("overflow-x-auto", "relative");
    expect(region.querySelector("th .sr-only")).not.toBeNull();
  });

  it("alinea arriba el contenido del detalle para que a 390 px no se estiren las filas", async () => {
    stubApi({ list: demo });
    renderPanel();
    await screen.findByRole("region", { name: /Lista de anomalías/ });
    fireEvent.click(screen.getAllByRole("button", { name: /Detalle/ })[0]);
    // La base del diálogo es un grid y en móvil ocupa toda la altura: sin `content-start` reparte la sobrante entre las filas.
    expect(await screen.findByRole("dialog")).toHaveClass("content-start", "max-sm:h-full");
  });

  it("enseña una línea por moneda sin total combinado", async () => {
    stubApi({ list: episodeList({ episodes: [compute, episode({ id: "usd", currency: "USD", accumulated_impact: "150.00", severity: "P3" })],
      open_impact_by_currency: [{ currency: "EUR", amount: "2807.71" }, { currency: "USD", amount: "150.00" }] }) });
    renderPanel();
    const summary = await screen.findByRole("region", { name: /Resumen de todas las anomalías del cliente/ });
    expect(within(summary).getByText("2807.71 EUR")).toBeInTheDocument();
    expect(within(summary).getByText("150.00 USD")).toBeInTheDocument();
    expect(within(summary).queryByText(/2957/)).not.toBeInTheDocument();
  });

  it("muestra importes enormes sin perder céntimos", async () => {
    stubApi({ list: episodeList({ episodes: [episode({ accumulated_impact: "9007199254740993.01" })],
      open_impact_by_currency: [{ currency: "EUR", amount: "9007199254740993.01" }] }) });
    renderPanel();
    await waitFor(() => expect(rowText()[0]).toContain("9007199254740993.01 EUR"));
  });

  it("la tarjeta de ya no observadas filtra la tabla", async () => {
    stubApi({ list: demo });
    renderPanel();
    await waitFor(() => expect(rows()).toHaveLength(3));
    fireEvent.click(screen.getByRole("button", { name: /Ya no se observan/ }));
    expect(rowText()).toHaveLength(1);
    expect(rowText()[0]).toContain("Analytics");
    expect(screen.getByLabelText("Observación")).toHaveValue("no_longer_observed");
  });

  it("combina filtros, enseña el vacío y restablece la vista inicial", async () => {
    stubApi({ list: demo });
    renderPanel();
    await waitFor(() => expect(rows()).toHaveLength(3));
    fireEvent.change(screen.getByLabelText("Estado"), { target: { value: "resolved" } });
    fireEvent.change(screen.getByLabelText("Criticidad"), { target: { value: "P3" } });
    expect(rowText()).toHaveLength(1);
    expect(rowText()[0]).toContain("Storage");
    fireEvent.change(screen.getByLabelText("Criticidad"), { target: { value: "P1" } });
    expect(screen.getByText("No hay anomalías con estos filtros")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /Restablecer filtros|Ver anomalías abiertas/ })[0]);
    expect(rows()).toHaveLength(3);
    expect(screen.getByLabelText("Estado")).toHaveValue("open");
    expect(screen.getByLabelText("Observación")).toHaveValue("all");
  });

  it("explica la leyenda de umbrales junto a la criticidad", async () => {
    stubApi({ list: demo });
    renderPanel();
    expect(await screen.findByText(/Alta \(P1\): impacto acumulado de más de 2000/)).toBeInTheDocument();
    expect(screen.getByText(/Media \(P2\): de 500 a 2000/)).toBeInTheDocument();
    expect(screen.getByText(/Baja \(P3\): menos de 500/)).toBeInTheDocument();
  });

  it("avisa de los datos sintéticos y nunca llama reales a los demás", async () => {
    stubApi({ list: demo });
    const view = renderPanel();
    expect(await screen.findByText("Datos sintéticos de demostración: no son facturas reales")).toBeInTheDocument();
    view.unmount();
    stubApi({ list: { ...demo, includes_synthetic_data: false } });
    renderPanel();
    await waitFor(() => expect(rows()).toHaveLength(3));
    expect(screen.queryByText(/Datos sintéticos/)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/datos reales/i);
  });

  it("enseña siempre hasta qué día está revisado", async () => {
    stubApi({ list: demo });
    renderPanel();
    expect(await screen.findByText("Revisado hasta el 20/09/2026")).toBeInTheDocument();
  });
});

describe("JUP-114 panel de anomalías: vacíos, errores y cambio de cliente", () => {
  it("distingue el cliente nunca revisado y no enseña cifras a cero", async () => {
    stubApi({ list: episodeList({ episodes: [], last_evaluated_date: null, open_impact_by_currency: [] }) });
    renderPanel();
    expect(await screen.findByText("Todavía no se han buscado anomalías en este cliente")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /Resumen de todas las anomalías/ })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Detectar ahora" })).toHaveLength(1);
  });

  it("distingue el cliente revisado sin abiertas", async () => {
    stubApi({ list: episodeList({ episodes: [closed], open_impact_by_currency: [] }) });
    renderPanel();
    expect(await screen.findByText(/No hay anomalías abiertas/)).toBeInTheDocument();
    expect(screen.getAllByText(/Revisado hasta el 20\/09\/2026/).length).toBeGreaterThan(0);
  });

  it("enseña el error con reintento y sin cifras", async () => {
    let fail = true;
    stubApi({ list: () => (fail ? json({ detail: "boom" }, 500) : json(demo)) });
    renderPanel();
    expect(await screen.findByText("No se han podido cargar las anomalías.")).toBeInTheDocument();
    expect(screen.queryByText(/EUR/)).not.toBeInTheDocument();
    fail = false;
    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    await waitFor(() => expect(rows()).toHaveLength(3));
  });

  it("al cambiar de cliente no enseña ni un instante los episodios del anterior", async () => {
    let releaseGrowth: (value: Response) => void = () => undefined;
    stubApi({ list: (url: string, init: RequestInit) => {
      const tenant = (init.headers as Record<string, string>)["X-Tenant-Id"];
      return tenant === "tenant-growth" ? new Promise<Response>((resolve) => { releaseGrowth = resolve; }) : json(demo);
    } });
    renderPanel();
    await waitFor(() => expect(rows()).toHaveLength(3));
    fireEvent.click(screen.getByRole("button", { name: "Cambiar cliente" }));
    expect(screen.queryByText("Compute")).not.toBeInTheDocument();
    expect(screen.queryByText("3619.43 EUR")).not.toBeInTheDocument();
    await act(async () => releaseGrowth(json(episodeList({ episodes: [], last_evaluated_date: null, open_impact_by_currency: [] }))));
    expect(await screen.findByText("Todavía no se han buscado anomalías en este cliente")).toBeInTheDocument();
  });
});

describe("JUP-114 panel de anomalías: Detectar ahora", () => {
  it("desactiva el botón mientras detecta, envía una sola petición y resume el resultado", async () => {
    let finish: (value: Response) => void = () => undefined;
    let listed = 0;
    const fetchMock = stubApi({
      list: () => (listed++ === 0 ? json(episodeList({ episodes: [], last_evaluated_date: null, open_impact_by_currency: [] })) : json(demo)),
      detect: () => new Promise<Response>((resolve) => { finish = resolve; }),
    });
    renderPanel();
    const [button] = await screen.findAllByRole("button", { name: "Detectar ahora" });
    fireEvent.click(button);
    const busy = await screen.findByRole("button", { name: "Detectando…" });
    expect(busy).toBeDisabled();
    fireEvent.click(busy);
    expect(fetchMock.mock.calls.filter(([url]) => String(url).includes("/detect"))).toHaveLength(1);
    await act(async () => finish(json(completedRun)));
    const status = await screen.findByRole("status", { name: "Resultado de la detección" });
    expect(status).toHaveTextContent("Detección hecha hasta el 20/09/2026 · 13 días evaluados");
    expect(status).toHaveTextContent("3 anomalías nuevas · 0 siguen activas · 1 ya no se observa");
    await waitFor(() => expect(rows()).toHaveLength(3));
    expect(rows()[0]).toHaveAttribute("data-new", "true");
  });

  it.each([
    [{ ...completedRun, status: "up_to_date", evaluated_days: [], skipped_days: [], opened: 0, no_longer_observed: 0 },
      200, "Ya estaba al día: no hay días completos nuevos desde el 20/09/2026."],
    [{ ...completedRun, status: "insufficient_data", last_complete_day: null, evaluated_days: [], opened: 0, no_longer_observed: 0 },
      200, "Aún no hay datos suficientes: hacen falta 8 días seguidos con datos del cliente."],
    [{ detail: { code: "ambiguous_cost_source" } }, 409, "Hay fuentes de coste solapadas en esas fechas; no se ha guardado nada."],
    [{ detail: { code: "detection_conflict" } }, 409, "Otra detección se estaba ejecutando a la vez; no se ha guardado nada. Vuelve a intentarlo."],
  ])("explica cada desenlace (%#)", async (body, status, message) => {
    stubApi({ list: demo, detect: () => json(body, status) });
    renderPanel();
    await waitFor(() => expect(rows()).toHaveLength(3));
    fireEvent.click(screen.getByRole("button", { name: "Detectar ahora" }));
    expect(await screen.findByRole("status", { name: "Resultado de la detección" })).toHaveTextContent(message);
  });

  it("deja los avisos en la línea principal y los días en el detalle plegado", async () => {
    stubApi({ list: demo, detect: { ...completedRun, unsupported_currencies: ["GBP"] } });
    renderPanel();
    await waitFor(() => expect(rows()).toHaveLength(3));
    fireEvent.click(screen.getByRole("button", { name: "Detectar ahora" }));
    const status = await screen.findByRole("status", { name: "Resultado de la detección" });
    expect(within(status).getByText("GBP no se evalúa (solo EUR y USD).")).toBeVisible();
    const details = within(status).getByText("Detalles").closest("details");
    expect(details).not.toHaveAttribute("open");
    expect(details).toHaveTextContent("07/09/2026: sin 7 días previos con datos");
  });
});

describe("JUP-114 panel de anomalías: detalle y estados", () => {
  async function openDetail(service = "Compute") {
    await waitFor(() => expect(rows().length).toBeGreaterThan(0));
    const row = rows().find((item) => item.textContent?.includes(service)) as HTMLElement;
    fireEvent.click(within(row).getByRole("button", { name: `Detalle de ${service}` }));
    return screen.findByRole("dialog");
  }

  it("enseña la evidencia y que es una candidata sin causa", async () => {
    stubApi({ list: demo });
    renderPanel();
    const dialog = await openDetail();
    for (const text of ["Alta (P1)", "Nueva", "Se sigue observando", "142.86 EUR/día", "2807.71 EUR en 12 días",
      "jup019-daily-v1", "Candidata: causa no establecida"]) {
      expect(dialog).toHaveTextContent(text);
    }
  });

  it("marca en investigación con PATCH y recarga", async () => {
    let listed = 0;
    const fetchMock = stubApi({
      list: () => json(listed++ === 0 ? demo : { ...demo, episodes: [{ ...compute, status: "investigating" }, database, analytics, closed] }),
      patch: (_url: string, init: RequestInit) => json({ ...compute, status: "investigating", ...JSON.parse(String(init.body)) }),
    });
    renderPanel();
    const dialog = await openDetail();
    fireEvent.click(within(dialog).getByRole("button", { name: "Marcar en investigación" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => init?.method === "PATCH")).toBe(true));
    const [, init] = fetchMock.mock.calls.find(([, call]) => call?.method === "PATCH") as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({ status: "investigating" });
    expect(await within(dialog).findByText("Investigando")).toBeInTheDocument();
    fireEvent.keyDown(dialog, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    await waitFor(() => expect(rowText()[0]).toContain("Investigando"));
  });

  it("cerrar pide motivo y confirmación y avisa de que es definitivo", async () => {
    const fetchMock = stubApi({ list: demo, patch: { ...compute, status: "false_positive", closure_reason: "Esperado" } });
    renderPanel();
    const dialog = await openDetail();
    fireEvent.click(within(dialog).getByRole("button", { name: "Cerrar…" }));
    expect(dialog).toHaveTextContent("Cerrar una anomalía no se puede deshacer");
    const confirm = within(dialog).getByRole("button", { name: "Confirmar cierre" });
    expect(confirm).toBeDisabled();
    fireEvent.change(within(dialog).getByLabelText("Motivo"), { target: { value: "   " } });
    expect(confirm).toBeDisabled();
    fireEvent.change(within(dialog).getByLabelText("Motivo"), { target: { value: "\u3164" } });
    expect(confirm).toBeDisabled();
    fireEvent.click(within(dialog).getByRole("button", { name: "Cancelar" }));
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "PATCH")).toBe(false);
    fireEvent.click(within(dialog).getByRole("button", { name: "Cerrar…" }));
    fireEvent.click(within(dialog).getByLabelText("Falso positivo"));
    fireEvent.change(within(dialog).getByLabelText("Motivo"), { target: { value: "Esperado" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Confirmar cierre" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => init?.method === "PATCH")).toBe(true));
    const [, init] = fetchMock.mock.calls.find(([, call]) => call?.method === "PATCH") as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({ status: "false_positive", reason: "Esperado" });
  });

  it("no ofrece acciones en un episodio cerrado", async () => {
    stubApi({ list: demo });
    renderPanel();
    await waitFor(() => expect(rows()).toHaveLength(3));
    fireEvent.change(screen.getByLabelText("Estado"), { target: { value: "all" } });
    const dialog = await openDetail("Storage");
    expect(within(dialog).queryByRole("button", { name: /Marcar en investigación|Cerrar…/ })).not.toBeInTheDocument();
    expect(dialog).toHaveTextContent("Revertido");
  });

  it.each([
    ["status_change_conflict", "Otra persona cambió esta anomalía a la vez"],
    ["invalid_status_transition", "Este cambio de estado ya no es posible"],
  ])("explica el conflicto %s sin cambiar el estado mostrado", async (code, message) => {
    stubApi({ list: demo, patch: () => json({ detail: { code } }, 409) });
    renderPanel();
    const dialog = await openDetail();
    fireEvent.click(within(dialog).getByRole("button", { name: "Marcar en investigación" }));
    expect(await within(dialog).findByText(new RegExp(message))).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Recargar la anomalía" })).toBeInTheDocument();
    expect(dialog).toHaveTextContent("Nueva");
  });
});


describe("JUP-114 panel de anomalías: exportación", () => {
  it("exporta solo las filas filtradas, en orden y con el nombre de cliente y revisión", async () => {
    stubApi({ list: demo });
    renderPanel();
    await waitFor(() => expect(rows()).toHaveLength(3));
    fireEvent.change(screen.getByLabelText("Criticidad"), { target: { value: "P2" } });
    let blob: Blob | undefined;
    let fileName = "";
    const originalCreate = URL.createObjectURL;
    const originalClick = HTMLAnchorElement.prototype.click;
    URL.createObjectURL = ((value: Blob) => { blob = value; return "blob:x"; }) as typeof URL.createObjectURL;
    HTMLAnchorElement.prototype.click = function click(this: HTMLAnchorElement) { fileName = this.download; };
    try {
      fireEvent.click(screen.getByText("Exportar Resultados"));
      fireEvent.click(screen.getByText("Exportar CSV"));
    } finally {
      URL.createObjectURL = originalCreate;
      HTMLAnchorElement.prototype.click = originalClick;
    }
    expect(fileName).toBe("anomalias-tenant-core-revisado-2026-09-20.csv");
    const lines = (await (blob as Blob).text()).split("\n");
    expect(lines).toHaveLength(2);
    expect(lines[1]).toContain("\"Database\"");
    expect(lines[1]).toContain("\"Sintéticos\"");
    expect(lines[1]).toContain("\"Candidata: causa no establecida\"");
  });
});
