// Prueba del panel de recomendaciones de ahorro, portado tal cual del
// repositorio de origen (JUP-095, grupo 5). Datos de demostracion estaticos,
// sin fetch ni props.
//
// Importamos describe/it/expect explicitamente porque el proyecto NO usa
// `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `RecommendationsPanel` no recibe props, usa datos de demostracion
// estaticos extraidos del origen y renderiza (entre otros) un encabezado
// "Panel de Recomendaciones" y un stat "Ahorro Potencial Total" con valor
// "106.000€".
import { RecommendationsPanel } from "./RecommendationsPanel";

describe("RecommendationsPanel", () => {
  it("muestra el encabezado del panel y el stat de ahorro potencial total", () => {
    render(<RecommendationsPanel />);

    expect(screen.getByText("Panel de Recomendaciones")).toBeInTheDocument();
    expect(screen.getByText("106.000€")).toBeInTheDocument();
    expect(screen.getByText("Ahorro Potencial Total")).toBeInTheDocument();
  });
});
