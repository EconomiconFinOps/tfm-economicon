import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { jsonResponse, mockBackend } from "../../tests/test-support";
import { MessageComposer } from "./MessageComposer";

// JUP-119: the hint of the default ownership period is the month of the backend reference date.
async function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(<QueryClientProvider client={client}><MessageComposer token="t" tenantId="tenant-a" conversationId="c-1" /></QueryClientProvider>);
  await userEvent.click(screen.getByLabelText(/consultar costes por propiedad/i));
}

describe("MessageComposer y la fecha de referencia", () => {
  it("indica el mes de la fecha de referencia como periodo por defecto, no el del reloj del navegador", async () => {
    mockBackend({ "GET /billing/reference-date": () => jsonResponse({ reference_date: "2024-12-31", simulated: true }) });
    await mount();
    expect(await screen.findByText("Mes de referencia UTC: 2024-12-01 a 2025-01-01 (fin excluido).")).toBeVisible();
  });

  it("si falla el endpoint muestra un error y no inventa un periodo", async () => {
    mockBackend({ "GET /billing/reference-date": () => jsonResponse({ detail: "boom" }, 500) });
    await mount();
    expect(await screen.findByText(/no se pudo cargar la fecha de referencia/i)).toBeVisible();
    expect(screen.queryByText(/mes de referencia utc/i)).not.toBeInTheDocument();
  });
});
