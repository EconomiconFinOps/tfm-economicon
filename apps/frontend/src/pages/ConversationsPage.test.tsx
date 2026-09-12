// Prueba de `ConversationsPage`: en la nueva arquitectura de rutas deja de
// recibir `token`/`activeTenant` como props desde `App.jsx` y pasa a leerlos
// via `useOutletContext<SessionOutletContext>()` de "react-router" (mismo
// patron que `IngestPage.tsx`/`LoginPage.tsx`, ver Addendum de design.md,
// grupo 6). Caso unico y ligero (a diferencia de `IngestPage.test.tsx`):
// `ConversationsPage` combina dos queries y dos mutaciones, así que aquí solo
// se confirma que la query de listado usa el tenant del contexto -- el resto
// de su logica (mutaciones de crear/enviar mensaje) no es objeto de esta
// tarjeta.
//
// La version actual (`./ConversationsPage.jsx`) sigue exigiendo props:
// montada como ruta sin props, `token`/`activeTenant` llegan `undefined`, la
// query de listado queda `enabled: false` y la pagina muestra el aviso de
// "tenant requerido" en vez de listar conversaciones -- la suite debe fallar
// en fase Red por ese motivo.
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `ConversationsPage` reconstruida sobre `useOutletContext`, sin los props
// `token`/`activeTenant`.
import { ConversationsPage } from "./ConversationsPage";

afterEach(() => {
  vi.unstubAllGlobals();
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

// Ruta padre de prueba que simula `SessionGate`: mismo patron que
// `IngestPage.test.tsx` y `Layout.selector.test.tsx`.
function ContextProvider() {
  return (
    <Outlet
      context={{
        token: "tok-1",
        activeTenant: { id: "tenant-1", name: "Acme" }
      }}
    />
  );
}

describe("ConversationsPage con tenant activo", () => {
  it("lista las conversaciones existentes usando el tenant leido del Outlet context", async () => {
    // No se diferencia por endpoint: cualquier llamada de fetch devuelve la
    // misma lista de conversaciones, suficiente para confirmar que la query
    // de listado se disparo con el tenant del contexto (no de props).
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            items: [{ id: "c1", title: "Revisión de costes", updated_at: "2026-01-01T00:00:00Z" }]
          })
      })
    );

    const router = createMemoryRouter([
      {
        path: "/",
        Component: ContextProvider,
        children: [{ index: true, Component: ConversationsPage }]
      }
    ]);

    renderRouter(router);

    // La query de listado (`enabled: Boolean(token && activeTenant?.id)`)
    // solo se dispara si ambos datos llegan por contexto -- confirma la
    // migracion de props a `useOutletContext`.
    await waitFor(() => {
      expect(screen.getByText("Revisión de costes")).toBeInTheDocument();
    });
  });
});
