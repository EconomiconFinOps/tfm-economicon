import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { billing, tenants } from "./fixtures";
import { deferredResponse, jsonResponse, mockBackend, renderApp, restoreSession } from "./test-support";

// Archivo nuevo (en vez de ampliar session-and-dashboard.test.tsx, ya
// commiteado y protegido por el hook lock-committed-tests.mjs) para no tener
// que pedir autorizacion de edicion: el escenario es autocontenido y encaja
// igual de bien como suite propia dentro del mismo directorio de tests.
//
// JUP-097, grupo 5 (tareas 5.1/5.3): las tres transiciones basicas (carga
// visible, fallo comunicado, reconsulta al cambiar de tenant con nueva
// peticion X-Tenant-Id) ya estan cubiertas por session-and-dashboard.test.tsx.
// Falta un matiz que ningun test existente verifica de forma explicita: que
// durante la ventana en que la peticion del tenant NUEVO sigue en vuelo, la
// pantalla no debe mostrar en ningun frame intermedio el dato del tenant
// ANTERIOR como si perteneciera al nuevo ambito. Se usa deferredResponse()
// para congelar la respuesta del segundo tenant y poder inspeccionar ese
// frame intermedio antes de resolverla.
describe("dashboard tenant transition", () => {
  it("never shows the previous tenant's billing figure while the new tenant's request is in flight", async () => {
    const user = userEvent.setup();
    const southBilling = { ...billing, monthly_spend: 54321 };
    const southPending = deferredResponse();
    mockBackend({
      "GET /billing/summary": (request) =>
        request.headers.get("X-Tenant-Id") === tenants[1].id
          ? southPending.promise
          : jsonResponse(billing)
    });
    // Sin tenant fijado: SessionGate auto-selecciona tenants[0] ("North").
    restoreSession();
    renderApp(["/overview-legacy"]);

    // Punto de partida: el dashboard muestra el gasto mensual del primer
    // tenant con normalidad.
    expect(await screen.findByText(`$${billing.monthly_spend.toLocaleString()}`)).toBeVisible();

    // Se cambia al segundo tenant, cuya respuesta de /billing/summary queda
    // deliberadamente sin resolver (southPending.promise nunca se entrega
    // todavia).
    await user.selectOptions(screen.getByLabelText("Ambito de cliente"), tenants[1].id);

    // Comportamiento bajo prueba: mientras la respuesta del tenant nuevo
    // sigue pendiente, el dato del tenant ANTERIOR ya no debe estar visible
    // (no se "cuela" como si fuera del nuevo ambito) y la pantalla debe
    // mostrar el estado de carga, tal como hace useDashboardData/DashboardPage
    // cuando payload es null (queryKey ["billing-summary", tenantId] cambio
    // de valor, isLoading vuelve a true).
    expect(screen.queryByText(`$${billing.monthly_spend.toLocaleString()}`)).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Connecting to the FinOps control plane..." })).toBeVisible();

    // Al resolver la respuesta pendiente, el dashboard adopta el dato
    // correcto del tenant nuevo (y solo ese).
    await act(async () => southPending.resolve(southBilling));
    expect(await screen.findByText(`$${southBilling.monthly_spend.toLocaleString()}`)).toBeVisible();
    expect(screen.queryByText(`$${billing.monthly_spend.toLocaleString()}`)).not.toBeInTheDocument();
  });
});
