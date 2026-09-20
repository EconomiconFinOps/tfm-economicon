// Pruebas de `IngestPage`: en la nueva arquitectura de rutas deja de recibir
// `token`/`activeTenant` como props desde `App.jsx` (App.jsx los pasaba
// directamente) y pasa a leerlos via `useOutletContext<SessionOutletContext>()`
// de "react-router", igual que documenta el Addendum de design.md para el
// grupo 6 y como ya hace `LoginPage.tsx` para su propia migracion. La version
// actual (`./IngestPage.jsx`) sigue exigiendo props: montada como ruta sin
// props, `token`/`activeTenant` llegan `undefined`, así que esta suite debe
// fallar en fase Red por el motivo correcto.
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (ver SessionGate.test.tsx/LoginPage.test.tsx,
// ya commiteados).
import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `IngestPage` reconstruida sobre `useOutletContext`, sin el prop `token`/
// `activeTenant`. Hoy `apps/frontend/src/pages/IngestPage.jsx` sigue
// exigiendolos -- este import por si solo no rompe la suite (el modulo existe),
// pero el comportamiento que se verifica abajo si difiere del actual.
import { IngestPage } from "./IngestPage";

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

// Ruta padre de prueba que simula el `SessionGate` real: expone el mismo
// contrato de Outlet context (`SessionOutletContext`) documentado en
// `SessionGate.tsx`, con el `activeTenant` que cada caso necesita -- mismo
// patron que `Layout.selector.test.tsx` usa para su `ContextProvider`.
function makeContextProvider(context: { token: string; activeTenant: { id: string; name: string } | null }) {
  return function ContextProvider() {
    return <Outlet context={context} />;
  };
}

describe("IngestPage sin tenant activo", () => {
  it("no muestra el formulario de ingesta (requiere tenant activo)", () => {
    const router = createMemoryRouter([
      {
        path: "/",
        Component: makeContextProvider({ token: "tok", activeTenant: null }),
        children: [{ index: true, Component: IngestPage }]
      }
    ]);

    renderRouter(router);

    // Aserción negativa robusta: sin tenant activo, el campo "Source" del
    // formulario de ingesta no debe estar presente. No dependemos del texto
    // exacto del mensaje de "tenant requerido" (eso lo decide el coder en
    // fase Green), sino de que el formulario real no se renderiza.
    expect(screen.queryByLabelText(/source/i)).toBeNull();
  });
});

describe("IngestPage con tenant activo", () => {
  it("al enviar el formulario, llama a createIngestJob con el tenant del contexto (no de props)", async () => {
    // `fetchJson` de services/api.js hace `fetch(url, { headers, ... })`: un
    // objeto con `ok: true` y `json()` basta (ver SessionGate.test.tsx).
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ job_id: "j1", status: "queued", queue: "ingest" })
    });
    vi.stubGlobal("fetch", fetchMock);

    const router = createMemoryRouter([
      {
        path: "/",
        Component: makeContextProvider({
          token: "tok-1",
          activeTenant: { id: "tenant-1", name: "Acme" }
        }),
        children: [{ index: true, Component: IngestPage }]
      }
    ]);

    renderRouter(router);

    // Valores por defecto del formulario (source: "aws-cur", artifact_uri: "",
    // text_content: ""): basta con enviar, sin escribir en los campos.
    fireEvent.click(screen.getByRole("button", { name: /queue ingestion/i }));

    // Confirma que la llamada real llego a "/jobs/ingest" con la cabecera
    // `X-Tenant-Id` construida a partir del tenant leido del Outlet context
    // (no de un prop `activeTenant` inexistente en la nueva arquitectura).
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });

    const [url, requestInit] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/jobs/ingest");
    expect(requestInit.headers["X-Tenant-Id"]).toBe("tenant-1");
  });
});
