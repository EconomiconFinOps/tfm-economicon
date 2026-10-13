import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { billing } from "../../tests/fixtures";
import { jsonResponse, mockBackend, renderApp, restoreSession } from "../../tests/test-support";

// JUP-119: the default period and the header come from the backend reference date, never from the browser clock.
function aligned(search: URLSearchParams) {
  return {
    ...billing,
    period: { start_date: search.get("start_date"), end_date: search.get("end_date"), timezone: "UTC" },
    group_by: search.get("group_by") ?? "service", tag_key: null
  };
}

describe("fecha de referencia en el panel ejecutivo", () => {
  it("abre el periodo por defecto en los meses anteriores a la fecha de referencia, no a la del navegador", async () => {
    const { requests } = mockBackend({
      "GET /billing/reference-date": () => jsonResponse({ reference_date: "2024-03-10", simulated: true }),
      "GET /billing/summary": (request) => jsonResponse(aligned(request.search))
    });
    restoreSession();
    renderApp();
    await screen.findByRole("table", { name: /desglose/i });
    expect(screen.getByLabelText(/mes inicial/i)).toHaveValue("2023-09");
    expect(screen.getByLabelText(/mes final/i)).toHaveValue("2024-02");
    const summary = requests.find((item) => item.path === "/billing/summary");
    expect(summary?.search.get("start_date")).toBe("2023-09-01");
  });

  it("muestra 'Fecha simulada' con la fecha cuando el backend la fija", async () => {
    mockBackend({
      "GET /billing/reference-date": () => jsonResponse({ reference_date: "2026-10-15", simulated: true }),
      "GET /billing/summary": (request) => jsonResponse(aligned(request.search))
    });
    restoreSession();
    renderApp();
    expect(await screen.findByText("Fecha simulada: 15/10/2026")).toBeVisible();
  });

  it("no muestra ninguna etiqueta cuando la fecha es la real", async () => {
    mockBackend({
      "GET /billing/reference-date": () => jsonResponse({ reference_date: "2026-10-15", simulated: false }),
      "GET /billing/summary": (request) => jsonResponse(aligned(request.search))
    });
    restoreSession();
    renderApp();
    await screen.findByRole("table", { name: /desglose/i });
    expect(screen.queryByText(/fecha simulada/i)).not.toBeInTheDocument();
  });

  it("si falla el endpoint muestra un error explícito y no pide costes con un periodo del reloj del navegador", async () => {
    const { requests } = mockBackend({
      "GET /billing/reference-date": () => jsonResponse({ detail: "boom" }, 500)
    });
    restoreSession();
    renderApp();
    expect(await screen.findByText(/no se pudo cargar la fecha de referencia/i)).toBeVisible();
    await waitFor(() => expect(requests.some((item) => item.path === "/billing/reference-date")).toBe(true));
    expect(requests.some((item) => item.path === "/billing/summary")).toBe(false);
  });

  it("rechaza una respuesta con forma inválida como error de la fecha de referencia", async () => {
    const { requests } = mockBackend({
      "GET /billing/reference-date": () => jsonResponse({ reference_date: "15/10/2026", simulated: "si" })
    });
    restoreSession();
    renderApp();
    expect(await screen.findByText(/no se pudo cargar la fecha de referencia/i)).toBeVisible();
    expect(requests.some((item) => item.path === "/billing/summary")).toBe(false);
  });
});
