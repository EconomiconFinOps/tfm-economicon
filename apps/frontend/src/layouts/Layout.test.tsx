// Prueba del layout general de la aplicacion (navegacion + Outlet), portado
// tal cual del repositorio de origen (JUP-095, grupo 5).
//
// Importamos describe/it/expect explicitamente porque el proyecto NO usa
// `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
// `Layout` usa NavLink/Outlet de "react-router" (v7.13.0): necesita contexto
// de router para renderizar sin lanzar. MemoryRouter es el wrapper estandar
// para tests que no dependen de un navegador real.
import { MemoryRouter } from "react-router";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `Layout` no recibe props, renderiza una barra de navegacion con enlaces a
// las 5 vistas portadas y un <Outlet /> para el contenido de la ruta activa.
import { Layout } from "./Layout";

describe("Layout", () => {
  it("muestra los 5 enlaces de navegacion a las vistas portadas", () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
    );

    // Verificamos los 5 items de navegacion por su texto visible: son el
    // contrato observable de que las 5 vistas portadas son accesibles desde
    // el layout comun, tal cual el origen.
    expect(screen.getByText("Coste Global")).toBeInTheDocument();
    expect(screen.getByText("Coste Detallado")).toBeInTheDocument();
    expect(screen.getByText("Corte Global")).toBeInTheDocument();
    expect(screen.getByText("Anomalías")).toBeInTheDocument();
    expect(screen.getByText("Recomendaciones")).toBeInTheDocument();
  });
});
