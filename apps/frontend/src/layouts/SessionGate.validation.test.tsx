// Cobertura complementaria de `SessionGate` (reconciliacion con develop,
// Punto 2 -- validacion de sesion). `SessionGate.test.tsx` (ya commiteado,
// bloqueado por el hook del harness) solo cubre "sin sesion" y "con sesion
// valida"; no cubre el caso intermedio que motiva esta reconciliacion: un
// JSON que parsea correctamente pero no tiene la forma de una sesion real.
// Antes de `isSession`, ese valor se aceptaba tal cual (un `{}` no lanzaba
// en `JSON.parse`), sin redirigir a /login. Este archivo anade ese caso sin
// duplicar la cobertura existente.
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (mismo patron que SessionGate.test.tsx).
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { SessionGate, SESSION_KEY } from "./SessionGate";

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

describe("SessionGate con sesion invalida", () => {
  it("descarta un JSON valido con estructura invalida, redirige a /login y no llama a la red", async () => {
    // JSON perfectamente valido (no lanza en JSON.parse), pero sin la forma
    // de una sesion real: sin `accessToken` ni `user`. Antes de `isSession`,
    // esto se aceptaba como sesion -- no redirigia a /login, aunque tampoco
    // habilitaba la consulta de tenants (`enabled: Boolean(session?.accessToken)`
    // ya la bloqueaba). El riesgo real es la falta de redireccion, no una
    // fuga de datos de otro tenant.
    window.localStorage.setItem(SESSION_KEY, JSON.stringify({}));

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

    expect(await screen.findByText("Pantalla de acceso")).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
    // La clave invalida se limpia, igual que con JSON roto: no debe quedar
    // un valor a medias que un siguiente arranque intente reinterpretar.
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
  });

  it("descarta un user con forma parcial (sin id/role) aunque accessToken sea valido", async () => {
    // Caso mas sutil: `accessToken` presente, pero `user` incompleto (falta
    // `id`/`role`) -- exactamente la forma que usaban los fixtures de test
    // antes de esta reconciliacion. Confirma que `isSession` valida el
    // `user` completo, no solo su presencia.
    window.localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        accessToken: "tok-parcial",
        user: { full_name: "Ada Lovelace", email: "ada@example.com" }
      })
    );

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

    expect(await screen.findByText("Pantalla de acceso")).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
  });
});
