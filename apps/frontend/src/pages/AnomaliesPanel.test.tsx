// Prueba del panel de anomalias y alertas, portado tal cual del repositorio
// de origen (JUP-095, grupo 5). Datos de demostracion estaticos, sin fetch
// ni props.
//
// Importamos describe/it/expect explicitamente porque el proyecto NO usa
// `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `AnomaliesPanel` no recibe props, usa datos de demostracion estaticos
// extraidos del origen y renderiza (entre otros) un encabezado "Panel de
// Anomalias y Alertas" y un stat "Impacto Total" con valor "44.500€".
import { AnomaliesPanel } from "./AnomaliesPanel";

describe("AnomaliesPanel", () => {
  it("muestra el encabezado del panel y el stat de impacto total", () => {
    render(<AnomaliesPanel />);

    expect(screen.getByText("Panel de Anomalías y Alertas")).toBeInTheDocument();

    // Verificamos el valor formateado del stat ("44.500€") en vez del
    // primer stat ("23"): un numero corto de una o dos cifras puede
    // coincidir por accidente con otro texto del arbol (contador de
    // elementos, indice de fila, etc.), mientras que "44.500€" es
    // inequivoco dentro de este panel.
    expect(screen.getByText("44.500€")).toBeInTheDocument();
    expect(screen.getByText("Impacto Total")).toBeInTheDocument();
  });
});
