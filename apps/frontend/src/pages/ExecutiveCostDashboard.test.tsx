// Prueba del dashboard ejecutivo de coste global, portado tal cual del
// repositorio de origen (JUP-095, grupo 5). Los datos de demostracion son
// constantes estaticas (sin fetch), por lo que basta con renderizar el
// componente sin props ni wrapper adicional para verificar que expone el
// KPI principal y el encabezado esperados.
//
// Importamos describe/it/expect explicitamente porque el proyecto NO usa
// `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `ExecutiveCostDashboard` no recibe props, usa datos de demostracion
// estaticos extraidos del origen y renderiza (entre otros) un KPI "Coste
// Total Mensual" con valor "298.000€" y un encabezado de seccion
// "Dashboard Ejecutivo - Coste Global".
import { ExecutiveCostDashboard } from "./ExecutiveCostDashboard";

describe("ExecutiveCostDashboard", () => {
  it("muestra el encabezado del dashboard y el KPI de coste total mensual", () => {
    render(<ExecutiveCostDashboard />);

    // Encabezado de la seccion: confirma que se esta renderizando la vista
    // correcta (y no otro dashboard con datos de coste similares).
    expect(
      screen.getByText("Dashboard Ejecutivo - Coste Global"),
    ).toBeInTheDocument();

    // KPI principal: valor tal cual viene en los datos de demostracion del
    // origen, sin recalculo ni formateo adicional por parte del componente.
    expect(screen.getByText("298.000€")).toBeInTheDocument();
  });
});
