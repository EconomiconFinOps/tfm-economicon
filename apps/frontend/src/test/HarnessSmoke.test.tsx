// Test canario del arnés de pruebas (Vitest + Testing Library + jsdom).
//
// Este test NO valida lógica de negocio: su único propósito es demostrar,
// de punta a punta, que el arnés de pruebas del frontend (JUP-095, tarea
// 2.3) funciona correctamente -- resolución de módulos JSX/TSX, entorno
// jsdom, render de React y matchers de jest-dom (`toBeInTheDocument`).
// Si en el futuro se rompe la configuración (vite.config.ts, setupFiles,
// jsdom, versión de Testing Library...) antes de que aterricen los
// componentes reales portados desde el origen, este test debe ser el
// primero en fallar y señalar la causa raíz en el propio arnés.
//
// Importamos `describe`/`it`/`expect` explícitamente porque el proyecto
// NO usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `HarnessSmoke` es un componente funcional de React sin props que
// renderiza un elemento con `role="status"` cuyo nombre accesible es
// exactamente "Entorno de pruebas del frontend operativo".
import { HarnessSmoke } from "./HarnessSmoke";

describe("HarnessSmoke", () => {
  it("renderiza un status accesible que confirma que el arnés de pruebas funciona", () => {
    render(<HarnessSmoke />);

    // Consulta por rol y nombre accesible (no por texto plano ni por
    // selector CSS) para verificar simultáneamente que jsdom expone la
    // Accessibility Tree y que Testing Library puede consultarla.
    const status = screen.getByRole("status", {
      name: "Entorno de pruebas del frontend operativo"
    });

    expect(status).toBeInTheDocument();
  });
});
