import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { BillingSummary, BillingTotal } from "../services/contracts";
import { monthLabel } from "../lib/executiveCostDashboard";
import { billing, tenants } from "../../tests/fixtures";
import { jsonResponse, mockBackend, renderApp, restoreSession } from "../../tests/test-support";

// Recharts is deliberately real. Only jsdom's missing layout measurements are
// supplied: the production ResponsiveContainer/Area compute the actual SVG.
// The shared afterEach restores these vi spies/globals and unmounts each tree.
beforeEach(() => {
  const rectangle = new DOMRect(0, 0, 1000, 300);
  const originalBounds = HTMLElement.prototype.getBoundingClientRect;
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
    return this.classList.contains("recharts-responsive-container")
      ? rectangle : originalBounds.call(this);
  });
  class MeasuredResizeObserver implements ResizeObserver {
    constructor(private readonly callback: ResizeObserverCallback) {}
    observe(target: Element) {
      this.callback([{
        target, contentRect: rectangle, borderBoxSize: [], contentBoxSize: [], devicePixelContentBoxSize: []
      }], this);
    }
    unobserve() {}
    disconnect() {}
  }
  vi.stubGlobal("ResizeObserver", MeasuredResizeObserver);
});

type Series = Record<string, BillingTotal[]>;
const total = (cost: string, currency = "USD"): BillingTotal => ({ cost, currency, record_count: 1 });

function responseFor(selection: URLSearchParams, series: Series): BillingSummary {
  const start = selection.get("start_date")!;
  const end = selection.get("end_date")!;
  const observed = new Map<string, { cents: bigint; records: number }>();
  for (const [month, values] of Object.entries(series)) {
    if (month + "-01" < start || month + "-01" >= end) continue;
    for (const value of values) {
      const previous = observed.get(value.currency) ?? { cents: 0n, records: 0 };
      observed.set(value.currency, {
        cents: previous.cents + BigInt(value.cost.replace(".", "")),
        records: previous.records + value.record_count
      });
    }
  }
  const totals = [...observed.entries()].map(([currency, value]) => ({
    currency, cost: (value.cents / 100n).toString() + "." + (value.cents % 100n).toString().padStart(2, "0"),
    record_count: value.records
  }));
  return {
    ...billing, contract_version: 2,
    period: { start_date: start, end_date: end, timezone: "UTC" },
    group_by: "service", tag_key: null, data_status: totals.length ? "available" : "empty",
    totals, groups: totals.map((value) => ({ ...value, value: "Synthetic Compute", subscription_id: null })),
    monthly_spend: totals.length === 1 ? totals[0].cost : null,
    currency: totals.length === 1 ? totals[0].currency : null,
    open_ingestions: 0
  };
}

async function showPeriod(series: Series, first = "2024-05", last = "2024-08", failedMonth?: string) {
  mockBackend({ "GET /billing/summary": ({ search }) => {
    if (failedMonth && search.get("start_date") === failedMonth + "-01"
        && search.get("end_date") === "2024-07-01") {
      return jsonResponse({ detail: "Synthetic monthly failure" }, 503);
    }
    return jsonResponse(responseFor(search, series));
  } });
  restoreSession(tenants[0].id);
  renderApp();
  await screen.findByRole("heading", { name: "Dashboard Ejecutivo - Coste Global" });
  act(() => {
    fireEvent.change(screen.getByLabelText("Mes inicial"), { target: { value: first } });
    fireEvent.change(screen.getByLabelText("Mes final"), { target: { value: last } });
  });
  await screen.findByRole("table", { name: "Costes mensuales" });
  return measuredChart("USD");
}

async function measuredChart(currency: string) {
  const chart = await screen.findByRole("img", {
    name: "Gráfico mensual en " + currency + "; valores exactos en la tabla de costes mensuales"
  });
  await waitFor(() => {
    const svg = chart.querySelector("svg.recharts-surface");
    // A missing/zero-sized SVG is a geometry/helper failure, not valid Red.
    expect(svg, "real Recharts must produce a measured SVG before checking observations").not.toBeNull();
    expect(Number(svg!.getAttribute("width"))).toBeGreaterThan(0);
    expect(Number(svg!.getAttribute("height"))).toBeGreaterThan(0);
  });
  return chart;
}

function monthlyRow(month: string) {
  return within(screen.getByRole("table", { name: "Costes mensuales" }))
    .getByRole("row", { name: new RegExp(monthLabel(month)) });
}

function expectMarkersAt(chart: HTMLElement, months: string[]) {
  const markers = [...chart.querySelectorAll<SVGCircleElement>(".recharts-area-dots circle")];
  expect(markers, "every observed finite monthly value needs a visible marker; null months need none")
    .toHaveLength(months.length);
  const svg = chart.querySelector("svg.recharts-surface")!;
  const width = Number(svg.getAttribute("width"));
  const height = Number(svg.getAttribute("height"));
  markers.forEach((marker, index) => {
    for (const name of ["cx", "cy", "r"]) {
      expect(marker).toHaveAttribute(name);
      expect(Number.isFinite(Number(marker.getAttribute(name)))).toBe(true);
    }
    expect(Number(marker.getAttribute("r")), "a zero-radius circle is not a visible observation").toBeGreaterThan(0);
    expect(Number(marker.getAttribute("cx"))).toBeGreaterThanOrEqual(0);
    expect(Number(marker.getAttribute("cx"))).toBeLessThanOrEqual(width);
    expect(Number(marker.getAttribute("cy"))).toBeGreaterThanOrEqual(0);
    expect(Number(marker.getAttribute("cy"))).toBeLessThanOrEqual(height);
    const tick = [...chart.querySelectorAll<SVGTextElement>(".recharts-xAxis text")]
      .find((element) => element.textContent === monthLabel(months[index]));
    expect(tick, "marker must correspond to its selected month, not an invented gap").toBeDefined();
    expect(Number(marker.getAttribute("cx"))).toBeCloseTo(Number(tick!.getAttribute("x")), 5);
  });
  return markers;
}

function expectIndependentSegments(chart: HTMLElement, count: number) {
  const curves = [...chart.querySelectorAll("path.recharts-area-curve")];
  expect(curves).toHaveLength(1);
  const path = curves[0].getAttribute("d")!;
  expect(path.match(/[Mm]/g) ?? [], "each observed month separated by a gap has an independent segment")
    .toHaveLength(count);
  expect(path, "isolated observations must not be joined through absence/error/plotting limits")
    .not.toMatch(/[LlCc]/);
}

describe("JUP-055 isolated observations with real Recharts", () => {
  it.each(["0.06", "0.00"])("plots isolated observed %s among missing months", async (cost) => {
    const chart = await showPeriod({ "2024-06": [total(cost)] });
    expect(monthlyRow("2024-06")).toHaveTextContent(cost);
    expect(monthlyRow("2024-06")).toHaveTextContent("Coste observado");
    for (const month of ["2024-05", "2024-07", "2024-08"]) {
      expect(monthlyRow(month)).toHaveTextContent("Sin datos de esta moneda.");
      expect(monthlyRow(month)).not.toHaveTextContent("0.00");
    }
    expectIndependentSegments(chart, 1);
    const markers = expectMarkersAt(chart, ["2024-06"]);
    if (cost === "0.00") {
      const zeroTick = [...chart.querySelectorAll<SVGTextElement>(".recharts-yAxis text")]
        .find((element) => element.textContent === "0");
      expect(zeroTick).toBeDefined();
      expect(Number(markers[0].getAttribute("cy"))).toBeCloseTo(Number(zeroTick!.getAttribute("y")), 5);
    }
  });

  it.each(["0.06", "0.00"])("retains the existing single-month marker for observed %s", async (cost) => {
    const chart = await showPeriod({ "2024-06": [total(cost)] }, "2024-06", "2024-06");
    const rows = within(screen.getByRole("table", { name: "Costes mensuales" })).getAllByRole("row");
    expect(rows).toHaveLength(2);
    expect(monthlyRow("2024-06")).toHaveTextContent(cost);
    expectMarkersAt(chart, ["2024-06"]);
  });

  it("shows two isolated observations without connecting the missing month", async () => {
    const chart = await showPeriod({ "2024-05": [total("0.03")], "2024-07": [total("0.09")] });
    expect(monthlyRow("2024-06")).toHaveTextContent("Sin datos de esta moneda.");
    expect(monthlyRow("2024-05")).toHaveTextContent("0.03");
    expect(monthlyRow("2024-07")).toHaveTextContent("0.09");
    expectIndependentSegments(chart, 2);
    expectMarkersAt(chart, ["2024-05", "2024-07"]);
  });

  it.each(["absent", "error", "unrepresentable"] as const)("does not create a marker or bridge for an %s month", async (kind) => {
    const series: Series = { "2024-05": [total("0.03")], "2024-07": [total("0.09")] };
    if (kind === "unrepresentable") series["2024-06"] = [total("9007199254740993.01")];
    const chart = await showPeriod(series, "2024-05", "2024-08", kind === "error" ? "2024-06" : undefined);
    const june = monthlyRow("2024-06");
    if (kind === "absent") expect(june).toHaveTextContent("Sin datos de esta moneda.");
    else if (kind === "error") expect(june).toHaveTextContent("Error al cargar costes. Datos no disponibles.");
    else {
      expect(june).toHaveTextContent("9007199254740993.01");
      expect(june).toHaveTextContent("Fuera del límite de representación gráfica");
    }
    expect(june).not.toHaveTextContent("0.00");
    expectIndependentSegments(chart, 2);
    expectMarkersAt(chart, ["2024-05", "2024-07"]);
  });

  it.each(["EUR", "USD"])("plots only selected %s observations, including a zero in a different month", async (currency) => {
    const series = { "2024-05": [total("5.00", "EUR")], "2024-06": [total("0.00", "USD")] };
    mockBackend({ "GET /billing/summary": ({ search }) => jsonResponse(responseFor(search, series)) });
    restoreSession(tenants[0].id);
    renderApp();
    await screen.findByRole("heading", { name: "Dashboard Ejecutivo - Coste Global" });
    act(() => {
      fireEvent.change(screen.getByLabelText("Mes inicial"), { target: { value: "2024-05" } });
      fireEvent.change(screen.getByLabelText("Mes final"), { target: { value: "2024-08" } });
    });
    await screen.findByRole("table", { name: "Costes mensuales" });
    await measuredChart("EUR");
    fireEvent.change(screen.getByLabelText("Moneda"), { target: { value: currency } });
    const chart = await measuredChart(currency);
    const observedMonth = currency === "EUR" ? "2024-05" : "2024-06";
    const otherMonth = currency === "EUR" ? "2024-06" : "2024-05";
    expect(monthlyRow(observedMonth)).toHaveTextContent(currency === "EUR" ? "5.00" : "0.00");
    expect(monthlyRow(otherMonth)).toHaveTextContent("Sin datos de esta moneda.");
    expectIndependentSegments(chart, 1);
    expectMarkersAt(chart, [observedMonth]);
  });
});
