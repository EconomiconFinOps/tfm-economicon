// Cobertura complementaria de `SessionGate` para `RF-090-003` (JUP-097, grupo
// 3 -- ver decision 2 de design.md). `SessionGate.test.tsx` y
// `SessionGate.validation.test.tsx` (ya commiteados, bloqueados por el hook
// del harness) cubren "sin sesion" y "sesion estructuralmente invalida", pero
// ninguno cubre la revalidacion contra el servidor: hoy `SessionGate` confia
// en el `user` de `localStorage` tal cual, sin invocar `fetchProfile`
// (`GET /me`). Este archivo anade, sin duplicar la cobertura existente, los
// dos escenarios de la decision 2:
//   - El servidor es la autoridad sobre la identidad, no el `localStorage`
//     (tarea 3.1).
//   - Un token que el servidor rechaza limpia la sesion y redirige al acceso
//     por el camino de fallo existente (`handleLogout`, tarea 3.2).
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (mismo patron que los otros dos
// archivos de este directorio).
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, useOutletContext } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { SessionGate, SESSION_KEY } from "./SessionGate";

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

function renderRouter(router: ReturnType<typeof createMemoryRouter>) {
  // `retry: false`: sin reintentos, para que un fallo de red en el test no
  // alargue la espera de `findByText` con reintentos exponenciales de
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

describe("SessionGate revalidacion de identidad contra /me", () => {
  it("expone la identidad devuelta por el servidor, no la guardada en localStorage", async () => {
    // Sesion persistida con una identidad "vieja": es la que dejo el ultimo
    // login, pero puede haber quedado desactualizada si el perfil cambio en
    // el servidor desde entonces (decision 2, razon 3: "la identidad deja de
    // ser un dato congelado").
    window.localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        accessToken: "tok-123",
        user: { id: "u1", full_name: "Nombre Viejo", email: "viejo@example.com", role: "operator" }
      })
    );

    // `fetch` diferenciado por URL: el bootstrap de tenants y la revalidacion
    // de perfil se emiten junto al arranque (decision 2, tarea 3.4), asi que
    // el mock debe responder a ambos contratos segun cual invoque cada uno.
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/tenants")) {
          return {
            ok: true,
            json: () => Promise.resolve({ items: [{ id: "t1", name: "Acme", slug: "acme", plan: "pro" }] })
          };
        }
        if (href.includes("/me")) {
          return {
            ok: true,
            json: () =>
              Promise.resolve({
                id: "u1",
                full_name: "Nombre Servidor",
                email: "servidor@example.com",
                role: "admin"
              })
          };
        }
        throw new Error(`URL inesperada en el test: ${href}`);
      })
    );

    // Ruta hija de prueba: lee el mismo Outlet context que expondra
    // `SessionGate` y renderiza el nombre de usuario tal como llegue por
    // contexto -- si viniera de localStorage veriamos "Nombre Viejo".
    function ChildProbe() {
      const ctx = useOutletContext<{ user?: { full_name: string } }>();
      return <p>Usuario: {ctx?.user?.full_name ?? "ninguno"}</p>;
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

    // Hoy `SessionGate` nunca invoca `fetchProfile`/`GET /me`: expone
    // `session.user` (el de localStorage) sin pasar por el servidor. Este
    // `findByText` debe fallar (nunca aparece "Nombre Servidor"; o bien se ve
    // "Nombre Viejo", o bien el `findByText` agota su timeout) hasta que el
    // coder conecte la revalidacion en fase Green.
    expect(await screen.findByText("Usuario: Nombre Servidor")).toBeInTheDocument();
  });
});

describe("SessionGate con token rechazado por el servidor", () => {
  it("limpia la sesion y redirige al acceso cuando /me rechaza el token", async () => {
    // Sesion estructuralmente valida (pasa `isSession`), pero cuyo token ya
    // no vive en el servidor -- el caso que motiva la decision 2, razon 1:
    // una validacion estructural no puede saber si el token sigue vigente.
    window.localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        accessToken: "tok-muerto",
        user: { id: "u1", full_name: "Nombre Cualquiera", email: "cualquiera@example.com", role: "operator" }
      })
    );

    // El foco de este test es el rechazo de `/me`, no el bootstrap de
    // tenants: responde `ok: true` con una coleccion vacia para no fallar por
    // un motivo distinto al que se quiere probar.
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/tenants")) {
          return { ok: true, json: () => Promise.resolve({ items: [] }) };
        }
        if (href.includes("/me")) {
          // Mismo contrato que `fetchJson` (services/api.ts): `response.ok`
          // en falso dispara `response.text()` y el `throw new Error(...)`.
          return { ok: false, status: 401, text: () => Promise.resolve("Invalid access token.") };
        }
        throw new Error(`URL inesperada en el test: ${href}`);
      })
    );

    const router = createMemoryRouter(
      [
        { path: "/login", Component: () => <p>Pantalla de acceso</p> },
        { path: "/", Component: SessionGate }
      ],
      { initialEntries: ["/"] }
    );

    renderRouter(router);

    // Hoy `SessionGate` nunca invoca `fetchProfile`: el rechazo de `/me`
    // nunca se detecta, `handleLogout()` nunca se llama y no hay
    // redireccion -- este `findByText` debe agotar su timeout en fase Red.
    expect(await screen.findByText("Pantalla de acceso")).toBeInTheDocument();
    // Ademas de la navegacion, confirma que la sesion se limpio de verdad
    // (mismo criterio que ya usa SessionGate.validation.test.tsx para sus
    // casos de sesion invalida): no debe quedar un token muerto reutilizable
    // en el siguiente arranque.
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
  });
});
