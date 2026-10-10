import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { SessionOutletContext } from "@/layouts/SessionGate";
import { defaultMonthSelection, monthlyPeriod } from "@/lib/executiveCostDashboard";
import { demoRecommendationReport } from "@/data/demo/recommendationsPanel";
import { RecommendationsPanel } from "./RecommendationsPanel";

const context = vi.hoisted(() => ({ session: null as SessionOutletContext | null }));
vi.mock("react-router", async importOriginal => ({ ...(await importOriginal<typeof import("react-router")>()), useOutletContext: () => context.session }));
const tenant = (id: string) => ({ id, name: `Cliente ${id}`, slug: id, plan: "demo" });
const report = (month = defaultMonthSelection().last, title = "Propuesta del cliente") => {
  const value = JSON.parse(JSON.stringify(demoRecommendationReport)) as typeof demoRecommendationReport;
  value.period = { ...monthlyPeriod(month), timezone: "UTC" };
  value.evidence.forEach(item => { item.query.period = value.period; });
  value.recommendations[0].action = title;
  return value;
};
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { "Content-Type": "application/json" } });
let client: QueryClient;
let fetchMock: ReturnType<typeof vi.fn>;
const page = () => <QueryClientProvider client={client}><RecommendationsPanel /></QueryClientProvider>;
beforeEach(() => {
  client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  context.session = { token: "test-token", activeTenant: tenant("one"), activeTenantId: "one", tenants: [tenant("one"), tenant("two")], onTenantChange: () => {}, onLogout: () => {} };
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => { client.clear(); vi.unstubAllGlobals(); });

describe("recommendations client: explicit HTTP contract doubles", () => {
  it("only fetches on opt-in, sends tenant/session/period, and displays loading followed by unestimated savings", async () => {
    let settle!: (value: Response) => void;
    fetchMock.mockImplementation(() => new Promise<Response>(resolve => { settle = resolve; }));
    const user = userEvent.setup();
    render(page());
    expect(fetchMock).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Consultar cliente" }));
    expect(screen.getByText("Cargando recomendaciones del cliente…")).toBeVisible();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain(`/billing/recommendations?start_date=${report().period.start_date}&end_date=${report().period.end_date}`);
    expect(init.headers).toMatchObject({ Authorization: "Bearer test-token", "X-Tenant-Id": "one" });
    expect(init.signal).toBeInstanceOf(AbortSignal);
    await act(async () => settle(json(report())));
    expect(await screen.findByRole("article", { name: "Propuesta del cliente" })).toHaveTextContent("No estimado");
    expect(screen.getByLabelText("Origen del informe")).toHaveTextContent("Datos simulados del cliente");
    expect(screen.queryByLabelText("Datos de demostración")).not.toBeInTheDocument();
    expect(screen.queryByText("900,00")).not.toBeInTheDocument();
  });

  it("shows endpoint errors without exposing server text or substituting demo, then retries an empty response", async () => {
    const empty = { ...report(), recommendations: [], evidence: [], total_candidates: 0, status: "insufficient_data", data_status: "empty" };
    fetchMock.mockResolvedValueOnce(json({ detail: "sensitive upstream failure" }, 404)).mockResolvedValueOnce(json(empty));
    const user = userEvent.setup();
    render(page());
    await user.click(screen.getByRole("button", { name: "Consultar cliente" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("todavía no está disponible");
    expect(screen.queryByText(/sensitive upstream/)).not.toBeInTheDocument();
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Reintentar consulta" }));
    expect(await screen.findByText("No hay recomendaciones para este periodo")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("rejects a valid report for the wrong period and malformed evidence", async () => {
    const malformed = report();
    malformed.recommendations[0].evidence_ids = ["missing-id"];
    fetchMock.mockResolvedValueOnce(json(report("2020-01"))).mockResolvedValueOnce(json(malformed));
    const user = userEvent.setup();
    render(page());
    await user.click(screen.getByRole("button", { name: "Consultar cliente" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No se ha podido verificar");
    await user.click(screen.getByRole("button", { name: "Reintentar consulta" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole("alert")).toHaveTextContent("No se ha podido verificar");
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
  });

  it("hides old-tenant data immediately, aborts obsolete work, and ignores late completion", async () => {
    let settleOld!: (value: Response) => void;
    let settleNew!: (value: Response) => void;
    fetchMock.mockImplementationOnce(() => new Promise<Response>(resolve => { settleOld = resolve; }))
      .mockImplementationOnce(() => new Promise<Response>(resolve => { settleNew = resolve; }));
    const user = userEvent.setup();
    const view = render(page());
    await user.click(screen.getByRole("button", { name: "Consultar cliente" }));
    const oldSignal = fetchMock.mock.calls[0][1].signal as AbortSignal;
    context.session = { ...context.session!, activeTenant: tenant("two"), activeTenantId: "two" };
    view.rerender(page());
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(oldSignal.aborted).toBe(true);
    await act(async () => settleOld(json(report(undefined, "Propuesta antigua"))));
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
    await act(async () => settleNew(json(report(undefined, "Propuesta nueva"))));
    expect(await screen.findByRole("article", { name: "Propuesta nueva" })).toBeVisible();
    expect(screen.queryByRole("article", { name: "Propuesta antigua" })).not.toBeInTheDocument();
    expect(fetchMock.mock.calls[1][1].headers["X-Tenant-Id"]).toBe("two");
  });

  it("does not fetch without a tenant or valid month and clears the old period when changing selection", async () => {
    context.session = { ...context.session!, activeTenant: null, activeTenantId: "" };
    const user = userEvent.setup();
    const view = render(page());
    await user.click(screen.getByRole("button", { name: "Consultar cliente" }));
    expect(screen.getByText("Selecciona un cliente.")).toBeVisible();
    expect(fetchMock).not.toHaveBeenCalled();
    context.session = { ...context.session!, activeTenant: tenant("one"), activeTenantId: "one" };
    fetchMock.mockResolvedValue(json(report()));
    view.rerender(page());
    expect(await screen.findByRole("article", { name: "Propuesta del cliente" })).toBeVisible();
    fireEvent.change(screen.getByLabelText("Mes de análisis"), { target: { value: "" } });
    expect(screen.getByText("Selecciona un mes válido entre los años 0001 y 9998.")).toBeVisible();
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
