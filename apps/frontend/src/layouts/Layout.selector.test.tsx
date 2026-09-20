// Cobertura complementaria de `Layout`: selector de ambito de cliente y panel
// de sesion que anade al leer el Outlet context inyectado por `SessionGate`
// (JUP-095, grupo 6, sub-ronda a - ver Addendum de design.md). El archivo
// `Layout.test.tsx` (ya commiteado, bloqueado por el hook del harness) solo
// verifica los 5 enlaces de navegacion sin contexto: no se duplica esa
// asercion aqui, solo se anade la cobertura nueva.
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Outlet, createMemoryRouter, RouterProvider } from "react-router";

// Contrato esperado (a modificar por el agente coder en fase Green): `Layout`
// debe leer `useOutletContext()` de forma defensiva y, cuando hay contexto,
// mostrar un <select> de tenants y el nombre del usuario de sesion.
import { Layout } from "./Layout";

// Componente de prueba que simula la ruta padre real (`SessionGate` en
// produccion): expone via Outlet context el mismo contrato documentado en el
// Addendum de design.md -- tenants, ambito activo, identidad de sesion y los
// callbacks de cambio de tenant/logout.
function ContextProvider() {
  return (
    <Outlet
      context={{
        tenants: [{ id: "t1", name: "Acme" }],
        activeTenantId: "t1",
        onTenantChange: () => {},
        user: { full_name: "Ada Lovelace", email: "ada@example.com" },
        onLogout: () => {}
      }}
    />
  );
}

describe("Layout sin Outlet context", () => {
  it("no muestra selector de ambito ni panel de sesion (sigue siendo seguro de renderizar sin contexto)", () => {
    // Mismo montaje que el test ya commiteado del grupo 5: sin arbol de rutas
    // real que provea contexto, Layout debe comportarse exactamente igual que
    // hoy -- nav presente, selector/panel ausentes por falta de datos, sin
    // lanzar ni mostrar UI a medias.
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>
    );

    expect(screen.queryByRole("combobox")).toBeNull();
    // Ningun texto con forma de email (patron generico, no atado al valor
    // concreto usado en el otro caso): confirma que el panel de sesion no se
    // renderiza a medias con datos ausentes.
    expect(screen.queryByText(/@/)).toBeNull();
  });
});

describe("Layout con Outlet context", () => {
  it("muestra el selector de ambito de cliente y el panel de sesion (spec: 'El armazon acompana a toda pantalla autenticada')", () => {
    // `Layout` necesita ser el consumidor real de un Outlet context: se monta
    // como ruta hija index de un padre de prueba (`ContextProvider`) que hace
    // de `SessionGate`, en vez de instanciarlo directamente con props.
    const router = createMemoryRouter([
      {
        path: "/",
        element: <ContextProvider />,
        children: [{ index: true, Component: Layout }]
      }
    ]);

    render(<RouterProvider router={router} />);

    // Selector de ambito de cliente: un <select> nativo con la opcion del
    // unico tenant provisto por el contexto.
    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Acme" })).toBeInTheDocument();

    // Panel de sesion: identidad del usuario activo visible en el armazon.
    expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
  });
});
