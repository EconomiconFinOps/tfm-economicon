// Prueba del dashboard operacional de coste detallado, portado tal cual del
// repositorio de origen (JUP-095, grupo 5). Incluye una tabla de datos
// detallados por servicio, sin fetch ni props: datos de demostracion
// estaticos.
//
// Importamos describe/it/expect explicitamente porque el proyecto NO usa
// `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `OperationalCostDashboard` no recibe props, usa datos de demostracion
// estaticos extraidos del origen y renderiza una tabla con una fila para el
// servicio "EC2 Instances" cuya columna de coste se formatea como
// `${row.coste.toLocaleString()}€` (sin argumento de locale explicito en el
// componente, tal cual el origen).
import { OperationalCostDashboard } from "./OperationalCostDashboard";

describe("OperationalCostDashboard", () => {
  it("muestra la fila de EC2 Instances con su coste formateado con toLocaleString", () => {
    render(<OperationalCostDashboard />);

    expect(screen.getByText("EC2 Instances")).toBeInTheDocument();

    // No hardcodeamos el string formateado ("45.200€" o "45,200€") porque el
    // formato depende del locale por defecto del entorno donde corra el
    // test (Node/CI vs. maquina local pueden diferir). Calculamos el valor
    // esperado con la misma llamada que hace el componente
    // (`(45200).toLocaleString()`, sin locale explicito) para que el test
    // sea correcto independientemente del locale del proceso.
    const costeEsperado = `${(45200).toLocaleString()}€`;
    expect(screen.getByText(costeEsperado)).toBeInTheDocument();
  });
});
