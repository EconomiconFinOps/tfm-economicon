// Pruebas de `LoginPage`: en la nueva arquitectura vive fuera del arbol
// protegido por `SessionGate` (JUP-095, grupo 6, sub-ronda b -- ver Addendum
// de design.md). Ya no recibe el callback `onLogin` de `App.jsx`: su
// mutacion hace ella misma, en `onSuccess`, lo que hoy hace
// `App.jsx.handleLogin` (App.jsx:74-81) -- construir `{ accessToken, user }`
// y persistirlo en localStorage bajo "finops.session" -- y navega a "/" con
// `useNavigate()` de react-router. Este test cubre ese comportamiento nuevo,
// no repite la cobertura del prop `onLogin` que desaparece.
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (ver SessionGate.test.tsx, ya
// commiteado).
import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `LoginPage` reconstruida sobre el nuevo sistema de estilos, sin el prop
// `onLogin`. Hoy `apps/frontend/src/pages/LoginPage.jsx` sigue exigiendolo
// -- este test debe fallar en fase Red porque la version actual no navega ni
// persiste sesion por si misma.
import { LoginPage } from "./LoginPage";

// Cada test deja su propio estado de localStorage/fetch: limpiamos ambos
// despues del caso (mismo patron de afterEach que SessionGate.test.tsx) para
// que el orden de ejecucion no contamine otros archivos de test.
afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

function renderRouter(router: ReturnType<typeof createMemoryRouter>) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

describe("LoginPage", () => {
  it("al iniciar sesion con exito, persiste la sesion en localStorage y navega a /", async () => {
    // Sin sesion previa de otro test: localStorage limpio antes de empezar.
    window.localStorage.clear();

    // Mockeamos fetch (no `login` de services/api.js, que no se toca en esta
    // tarjeta -- JUP-096) para que la llamada real a `/auth/login` que hace
    // `fetchJson` resuelva con un payload de sesion valido.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            access_token: "tok-abc",
            user: { full_name: "Ada Lovelace", email: "ada@example.com" }
          })
      })
    );

    // Ruta raiz como sonda: confirma que LoginPage navego tras el exito de
    // la mutacion, sin depender de que exista SessionGate (LoginPage vive
    // fuera del arbol protegido).
    const router = createMemoryRouter(
      [
        { path: "/login", Component: LoginPage },
        { path: "/", Component: () => <p>Area protegida</p> }
      ],
      { initialEntries: ["/login"] }
    );

    renderRouter(router);

    // El formulario ya trae valores por defecto (seed local del README):
    // basta con disparar el envio. Se localiza el boton por rol y texto, sin
    // depender de una clase CSS que puede cambiar en la reconstruccion.
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    // Tras el exito de la mutacion, LoginPage navega a "/": la sonda
    // "Area protegida" confirma que RouterProvider cambio de ruta.
    await waitFor(() => {
      expect(screen.getByText("Area protegida")).toBeInTheDocument();
    });

    // La sesion persistida debe tener exactamente la forma que
    // App.jsx.handleLogin construye hoy (App.jsx:74-78): no una reinvencion
    // del shape.
    const storedSession = JSON.parse(
      window.localStorage.getItem("finops.session") ?? "null"
    );
    expect(storedSession).toEqual({
      accessToken: "tok-abc",
      user: { full_name: "Ada Lovelace", email: "ada@example.com" }
    });
  });
});
