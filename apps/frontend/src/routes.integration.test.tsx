// Pruebas de enrutado extremo a extremo sobre el arbol de rutas REAL (JUP-095,
// grupo 6, tarea 6.5). A diferencia del resto de la suite del grupo 6 (que
// monta providers de contexto simulados -- `ContextProvider`/
// `makeContextProvider`, ver Layout.selector.test.tsx/IngestPage.test.tsx/
// DashboardPage.test.tsx), aqui se monta `routeConfig` tal cual lo exporta
// `./routes` sobre `createMemoryRouter`, con distintas `initialEntries` por
// escenario: lo que se verifica es que el arbol completo (SessionGate ->
// Layout -> pantalla) se comporta como exige `frontend-navigation-shell/spec.md`,
// no piezas aisladas.
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (ver SessionGate.test.tsx, ya commiteado).
import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { routeConfig } from "./routes";

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

function renderRoutes(initialEntries: string[]) {
  // `retry: false`: sin reintentos, para que un fallo de red en el test no
  // alargue la espera de `waitFor` con reintentos exponenciales de
  // react-query (mismo patron que SessionGate.test.tsx/DashboardPage.test.tsx).
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  const router = createMemoryRouter(routeConfig, { initialEntries });

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

function stubSession() {
  // Sesion valida persistida como la deja `LoginPage`/`App.jsx` hoy:
  // `{ accessToken, user }` bajo la clave "finops.session" (misma forma que
  // SessionGate.test.tsx/LoginPage.test.tsx).
  window.localStorage.setItem(
    "finops.session",
    JSON.stringify({
      accessToken: "tok-1",
      user: { full_name: "Ada Lovelace", email: "ada@example.com" }
    })
  );
}

describe("Arbol de rutas real: abrir una direccion directamente presenta su pantalla", () => {
  it("presenta OperationalCostDashboard al abrir /operational directamente, no la ruta indice", async () => {
    // Cubre frontend-navigation-shell: "Abrir directamente la direccion de
    // una pantalla" -- con sesion establecida, abrir /operational debe
    // presentar esa pantalla, no ExecutiveCostDashboard (la ruta indice de
    // "/").
    stubSession();

    // OperationalCostDashboard usa datos de demostracion estaticos: solo
    // hace falta mockear /tenants, que SessionGate consulta en su bootstrap.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            items: [{ id: "t1", name: "Acme", slug: "acme", plan: "pro" }]
          })
      })
    );

    renderRoutes(["/operational"]);

    await waitFor(() => {
      expect(screen.getByText("Dashboard Operativo - Coste Detallado")).toBeInTheDocument();
    });

    // Aserción negativa complementaria: el encabezado de la ruta indice
    // (ExecutiveCostDashboard) no debe estar presente -- confirma que se
    // presento /operational, no "/".
    expect(screen.queryByText("Dashboard Ejecutivo - Coste Global")).toBeNull();
  });
});

describe("Arbol de rutas real: el ambito activo sobrevive a la navegacion", () => {
  it("conserva el tenant seleccionado tras navegar de la raiz a /operational", async () => {
    // Cubre frontend-navigation-shell: "El ambito seleccionado sobrevive a la
    // navegacion" -- se selecciona un tenant distinto del auto-seleccionado
    // y, tras navegar a otra pantalla via un enlace real del Layout, el
    // selector debe seguir mostrando ese tenant.
    stubSession();

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            items: [
              { id: "t1", name: "Acme", slug: "acme", plan: "pro" },
              { id: "t2", name: "Globex", slug: "globex", plan: "enterprise" }
            ]
          })
      })
    );

    renderRoutes(["/"]);

    // SessionGate auto-selecciona el primer tenant de la lista cuando el
    // activo actual no esta entre los disponibles (SessionGate.tsx:106-111):
    // con la lista vacia de localStorage al arrancar, auto-selecciona "t1".
    // Esperamos a que el selector este disponible antes de cambiarlo.
    await waitFor(() => {
      expect(screen.getByRole("combobox", { name: /ambito de cliente/i })).toHaveValue("t1");
    });

    const selector = screen.getByRole("combobox", { name: /ambito de cliente/i });
    fireEvent.change(selector, { target: { value: "t2" } });

    // Navegacion real via el NavLink del Layout hacia /operational (no
    // navegacion imperativa de prueba): "Coste Detallado" es la etiqueta del
    // item de navegacion a esa ruta (Layout.tsx:17).
    fireEvent.click(screen.getByText("Coste Detallado"));

    await waitFor(() => {
      expect(screen.getByText("Dashboard Operativo - Coste Detallado")).toBeInTheDocument();
    });

    // El selector, ya en la nueva pantalla, sigue mostrando "t2": el cambio
    // de tenant sobrevivio a la navegacion entre pantallas.
    expect(screen.getByRole("combobox", { name: /ambito de cliente/i })).toHaveValue("t2");
  });
});

describe("Arbol de rutas real: sin sesion se presenta el acceso", () => {
  it("redirige a /login al abrir /operational directamente sin sesion establecida", async () => {
    // Cubre frontend-navigation-shell: "Sin sesion establecida se presenta el
    // acceso" -- abrir CUALQUIER direccion protegida sin sesion (no solo "/")
    // debe presentar la pantalla de acceso.
    window.localStorage.clear();

    // Sin sesion, SessionGate no deberia invocar fetch en absoluto
    // (`enabled: Boolean(session?.accessToken)`, ver SessionGate.tsx:89 y
    // SessionGate.test.tsx "sin sesion").
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    renderRoutes(["/operational"]);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    });

    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
