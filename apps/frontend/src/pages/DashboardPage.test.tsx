// DashboardPage: en la nueva arquitectura de rutas (JUP-095, grupo 6,
// sub-ronda d -- ver Addendum de design.md) esta pantalla deja de recibir
// `token`/`user`/`tenants`/`activeTenant` como props desde `App.jsx` y pasa a
// leerlos via `useOutletContext<SessionOutletContext>()`, mismo patron que
// `IngestPage`/`ConversationsPage`. Pasa a vivir en la ruta puente
// `/overview-legacy` (decision 6 de design.md): es la unica pantalla que
// consume datos reales del backend (`GET /billing/summary` y `GET /health`
// via `useDashboardData`, que se preserva verbatim -- es de JUP-096) hasta
// que JUP-096 conecte el nuevo Overview.
//
// La version actual (`./DashboardPage.jsx`) sigue exigiendo props: montada
// como ruta sin props, `token`/`activeTenant` llegan `undefined`, asi que
// `useDashboardData` nunca activa sus queries (`enabled: Boolean(token &&
// tenantId)`) y la pantalla queda bloqueada en "loading" para siempre -- esta
// suite debe fallar en fase Red por ese motivo exacto.
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (ver SessionGate.test.tsx/IngestPage.test.tsx,
// ya commiteados).
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `DashboardPage` reconstruida sobre `useOutletContext`, sin los props
// `token`/`user`/`tenants`/`activeTenant`. Hoy `apps/frontend/src/pages/DashboardPage.jsx`
// sigue exigiendolos -- este import por si solo no rompe la suite (el modulo
// existe), pero el comportamiento que se verifica abajo si difiere del actual.
import { DashboardPage } from "./DashboardPage";

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
// `SessionGate.tsx`, con los campos que cada caso necesita -- mismo patron
// que `IngestPage.test.tsx`/`Layout.selector.test.tsx` usan para su
// `ContextProvider`.
function makeContextProvider(context: {
  token: string;
  user: { full_name: string; email: string };
  tenants: Array<{ id: string; name: string; slug: string; plan: string }>;
  activeTenant: { id: string; name: string; slug: string; plan: string } | null;
}) {
  return function ContextProvider() {
    return <Outlet context={context} />;
  };
}

describe("DashboardPage sin tenant activo", () => {
  it("no muestra el resumen de facturacion (requiere tenant activo)", () => {
    const router = createMemoryRouter([
      {
        path: "/",
        Component: makeContextProvider({
          token: "tok",
          user: { full_name: "Ada", email: "ada@x.com" },
          tenants: [],
          activeTenant: null
        }),
        children: [{ index: true, Component: DashboardPage }]
      }
    ]);

    renderRouter(router);

    // Aserción negativa robusta: sin tenant activo, un texto que dependa de
    // los datos de facturacion ("Monthly Spend", ver DashboardPage.jsx:64) no
    // debe estar presente. No dependemos del texto exacto del mensaje de
    // "sin tenant" (eso lo decide el coder en fase Green y puede cambiar en
    // la reconstruccion), sino de que el resumen de billing real no se
    // renderiza sin un tenant activo.
    expect(screen.queryByText(/monthly spend/i)).toBeNull();
  });
});

describe("DashboardPage con tenant activo", () => {
  it("muestra el resumen de facturacion y el estado de salud", async () => {
    // `fetchJson` de services/api.js hace `fetch(url, { headers, ... })`: a
    // diferencia de IngestPage.test.tsx/SessionGate.test.tsx (un solo
        // endpoint), aqui `useDashboardData` combina dos llamadas distintas
    // (`/billing/summary` y `/health`) en la misma pantalla, asi que el mock
    // debe distinguir por URL para responder con el payload correcto a cada
    // una.
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (String(url).includes("/billing/summary")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              monthly_spend: 1200,
              savings_identified: 300,
              open_ingestions: 2,
              currency: "USD"
            })
        });
      }
      if (String(url).includes("/health")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ services: { api: "healthy", queue: "healthy" } })
        });
      }
      return Promise.reject(new Error(`URL inesperada en el mock de fetch: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    const router = createMemoryRouter([
      {
        path: "/",
        Component: makeContextProvider({
          token: "tok-1",
          user: { full_name: "Ada Lovelace", email: "ada@example.com" },
          tenants: [{ id: "tenant-1", name: "Acme", slug: "acme", plan: "pro" }],
          activeTenant: { id: "tenant-1", name: "Acme", slug: "acme", plan: "pro" }
        }),
        children: [{ index: true, Component: DashboardPage }]
      }
    ]);

    renderRouter(router);

    // No hardcodeamos el string formateado ("1,200" o "1.200") porque el
    // formato depende del locale por defecto del entorno donde corra el test
    // (Node/CI vs. maquina local pueden diferir) -- mismo patron que
    // `OperationalCostDashboard.test.tsx` (grupo 5): calculamos el valor
    // esperado con la misma llamada que hace el componente
    // (`(1200).toLocaleString()`).
    const monthlySpendEsperado = (1200).toLocaleString();

    await waitFor(() => {
      expect(screen.getByText(new RegExp(monthlySpendEsperado))).toBeInTheDocument();
    });

    // El nombre del servicio de salud ("api", clave de `health.services`
    // devuelta por `/health`) confirma que el segundo endpoint tambien se
    // consumio y se renderizo, no solo el de facturacion.
    expect(screen.getByText("api")).toBeInTheDocument();
  });
});
