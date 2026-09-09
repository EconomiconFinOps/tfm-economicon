// Pruebas de `SessionGate`: ruta padre de `Layout` en el arbol de rutas que
// resuelve sesion y bootstrap de tenants antes de exponerlos hacia abajo via
// Outlet context (JUP-095, grupo 6, sub-ronda a - ver Addendum de design.md).
// Cubren dos escenarios de `frontend-navigation-shell`:
//   - "Sin sesion establecida se presenta el acceso" (sin red).
//   - El bootstrap de ambito de cliente que sostiene "El armazon acompana a
//     toda pantalla autenticada" y "El ambito seleccionado sobrevive a la
//     navegacion" (con red mockeada).
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (ver Layout.test.tsx, ya commiteado).
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, useOutletContext } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `SessionGate` todavia no existe en `./SessionGate` -- este import es lo que
// hace fallar la suite en fase Red por el motivo correcto (modulo inexistente).
import { SessionGate } from "./SessionGate";

// Cada test deja su propio estado de localStorage/fetch: limpiamos ambos
// despues de cada caso para que el orden de ejecucion no contamine el
// siguiente (localStorage persiste entre tests del mismo archivo en jsdom).
afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

function renderRouter(router: ReturnType<typeof createMemoryRouter>) {
  // `retry: false`: sin reintentos, para que un fallo de red en el test no
  // alargue la espera de `waitFor` con reintentos exponenciales de
  // react-query.
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

describe("SessionGate sin sesion", () => {
  it("redirige a /login sin disparar ninguna llamada de red", async () => {
    // Sin sesion previa: ninguna clave de localStorage debe sobrevivir de un
    // test anterior.
    window.localStorage.clear();

    // Espiamos fetch para confirmar que SessionGate no lo invoca cuando no
    // hay sesion -- el bootstrap de tenants esta condicionado a
    // `Boolean(session?.accessToken)` (App.jsx:46, comportamiento preservado
    // verbatim segun el Addendum de design.md).
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const router = createMemoryRouter(
      [
        { path: "/login", Component: () => <p>Pantalla de acceso</p> },
        { path: "/", Component: SessionGate }
      ],
      { initialEntries: ["/"] }
    );

    renderRouter(router);

    // `<Navigate to="/login" replace />` reemplaza la entrada del historial:
    // basta con encontrar el texto de la pantalla de acceso.
    expect(await screen.findByText("Pantalla de acceso")).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});

describe("SessionGate con sesion", () => {
  it("arranca el bootstrap de tenants y expone el tenant activo via Outlet context", async () => {
    // Sesion valida persistida como la deja `LoginPage`/`App.jsx` hoy:
    // `{ accessToken, user }` bajo la clave "finops.session".
    window.localStorage.setItem(
      "finops.session",
      JSON.stringify({
        accessToken: "tok-123",
        user: { full_name: "Ada Lovelace", email: "ada@example.com" }
      })
    );

    // `services/api.js` -> `fetchJson` hace `fetch(...)` y luego comprueba
    // `response.ok` antes de llamar a `response.json()` (ver
    // apps/frontend/src/services/api.js:14-24): un objeto con `ok: true` y
    // `json()` basta, sin necesidad del `Response` real del entorno.
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

    // Ruta hija de prueba: lee el mismo Outlet context que expondra
    // `SessionGate` y renderiza el nombre del tenant activo tras la
    // auto-seleccion (unico tenant disponible -> se selecciona solo, mismo
    // efecto que App.jsx:49-67).
    function ChildProbe() {
      const ctx = useOutletContext<{ activeTenant?: { name: string } | null }>();
      return <p>Tenant activo: {ctx?.activeTenant?.name ?? "ninguno"}</p>;
    }

    const router = createMemoryRouter(
      [
        { path: "/login", Component: () => <p>Pantalla de acceso</p> },
        {
          path: "/",
          Component: SessionGate,
          children: [{ index: true, Component: ChildProbe }]
        }
      ],
      { initialEntries: ["/"] }
    );

    renderRouter(router);

    // El bootstrap de tenants es asincrono (`useQuery` + `useEffect` de
    // auto-seleccion): esperamos a que el ciclo complete y el contexto llegue
    // hasta la ruta hija.
    await waitFor(() => {
      expect(screen.getByText("Tenant activo: Acme")).toBeInTheDocument();
    });
  });
});
