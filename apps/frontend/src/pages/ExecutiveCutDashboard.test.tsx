// Prueba del dashboard ejecutivo de corte global (recomendaciones de ahorro
// aplicadas), portado tal cual del repositorio de origen (JUP-095, grupo 5).
// Igual que ExecutiveCostDashboard, usa datos de demostracion estaticos, sin
// fetch ni props: se renderiza directamente y se comprueba el KPI y el
// encabezado de seccion.
//
// Importamos describe/it/expect explicitamente porque el proyecto NO usa
// `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `ExecutiveCutDashboard` no recibe props, usa datos de demostracion
// estaticos extraidos del origen y renderiza (entre otros) un KPI "Ahorro
// Total" con valor "295.200€" y un encabezado de seccion "Dashboard
// Ejecutivo - Corte Global".
import { ExecutiveCutDashboard } from "./ExecutiveCutDashboard";

describe("ExecutiveCutDashboard", () => {
  it("muestra el encabezado del dashboard y el KPI de ahorro total", () => {
    render(<ExecutiveCutDashboard />);

    // Encabezado de la seccion: distingue esta vista de las otras cuatro
    // (comparten estructura de KPIs, no queremos falsos positivos).
    expect(
      screen.getByText("Dashboard Ejecutivo - Corte Global"),
    ).toBeInTheDocument();

    // KPI principal: valor tal cual viene en los datos de demostracion del
    // origen.
    expect(screen.getByText("295.200€")).toBeInTheDocument();
  });
});
