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

// `Layout` no recibe props: renderiza la barra de navegacion y un <Outlet />.
import { Layout } from "./Layout";

describe("Layout", () => {
  it("el menú solo enlaza pantallas con datos del backend, en este orden y sin Overview", () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
    );

    const labels = screen.getAllByRole("link").map((link) => link.textContent);
    expect(labels).toEqual(["Coste Global", "Anomalías", "Ingesta", "Asistente", "Salud del sistema"]);
    for (const hidden of ["Coste Detallado", "Corte Global", "Recomendaciones", "Overview"]) {
      expect(screen.queryByText(hidden)).toBeNull();
    }
  });
});
