// Casos adicionales (remediacion de mutation testing, JUP-097 grupo 5, tarea
// 5.4) complementarios a DashboardPage.test.tsx, que ya esta commiteado y
// bloqueado por el hook del harness (lock-committed-tests.mjs). No se
// duplican sus aserciones (bloqueo sin tenant / resumen con tenant activo);
// este archivo cubre dos mutantes distintos que sobrevivieron:
// - OptionalChaining en `user?.full_name` (linea 74): sin este caso, ningun
//   test ejercitaba una sesion con `user` todavia sin confirmar (el tipo
//   `SessionOutletContext.user` es opcional -- ver SessionGate.tsx).
// - ArrowFunction en `tenants.map(...)` (linea 112): ningun test existente
//   verificaba el contenido de cada articulo de tenant (nombre/plan), asi que
//   un mapeo que descartara el tenant (`tenants.map(() => undefined)`) no se
//   detectaba.
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (mismo patron que DashboardPage.test.tsx).
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { DashboardPage } from "./DashboardPage";

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderRouter(router: ReturnType<typeof createMemoryRouter>) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

// Variante local de `makeContextProvider` (DashboardPage.test.tsx) con `user`
// opcional, para reflejar fielmente `SessionOutletContext.user?: UserProfile`.
function makeContextProvider(context: {
  token: string;
  user?: { full_name: string; email: string };
  tenants: Array<{ id: string; name: string; slug: string; plan: string }>;
  activeTenant: { id: string; name: string; slug: string; plan: string } | null;
}) {
  return function ContextProvider() {
    return <Outlet context={context} />;
  };
}

function stubDashboardFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((url: string) => {
      if (String(url).includes("/billing/summary")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ monthly_spend: 1200, savings_identified: 300, open_ingestions: 2, currency: "USD" })
        });
      }
      if (String(url).includes("/health")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ services: { api: "healthy" } }) });
      }
      return Promise.reject(new Error(`URL inesperada en el mock de fetch: ${url}`));
    })
  );
}

describe("DashboardPage (mutacion: optional chaining sobre user)", () => {
  it("renderiza el dashboard sin reventar cuando el perfil del operador todavia no esta confirmado", async () => {
    stubDashboardFetch();

    const router = createMemoryRouter([
      {
        path: "/",
        // `user` ausente: escenario legitimo segun el tipo
        // `SessionOutletContext.user?: UserProfile` (p.ej. la consulta `/me`
        // en SessionGate todavia no resolvio). Con `user?.full_name` (codigo
        // real) esto no revienta; con el mutante `user.full_name` lanzaria un
        // TypeError durante el render y "Monthly Spend" nunca aparecería.
        Component: makeContextProvider({
          token: "tok",
          user: undefined,
          tenants: [{ id: "tenant-1", name: "Acme", slug: "acme", plan: "pro" }],
          activeTenant: { id: "tenant-1", name: "Acme", slug: "acme", plan: "pro" }
        }),
        children: [{ index: true, Component: DashboardPage }]
      }
    ]);

    renderRouter(router);

    await waitFor(() => expect(screen.getByText("Monthly Spend")).toBeInTheDocument());
    // El nombre del operador no puede aparecer (no hay datos que mostrar),
    // pero eso no debe impedir que el resto del dashboard se renderice.
    expect(screen.queryByText(/Ada|Lovelace/)).not.toBeInTheDocument();
  });
});

describe("DashboardPage (mutacion: condicion de bootstrapping)", () => {
  it("sigue mostrando 'Connecting...' cuando el token esta vacio y el billing summary queda deshabilitado sin marcarse como loading", async () => {
    // Mata dos mutantes de la linea 43
    // (`if (loading || (!error && !payload))`):
    // - LogicalOperator (`||` -> `&&`).
    // - ConditionalExpression (colapsa `(!error && !payload)` a `false`,
    //   dejando efectivamente `if (loading)`).
    // Escenario (documentado en el comentario de reconciliacion JUP-087 de
    // DashboardPage.tsx): con `token` vacio, `useDashboardData` calcula
    // `enabled: Boolean(token && tenantId)` como `false` para la consulta de
    // facturacion -- una consulta deshabilitada sin datos previos tiene
    // `isLoading: false` en react-query (no esta "cargando", esta inactiva).
    // Como `/health` si resuelve, `loading` global cae a `false` sin que
    // `payload` llegue a poblarse (billing nunca corre) y sin `error`. Solo
    // el segundo operando (`!error && !payload`) sostiene la pantalla de
    // "Connecting...": si un mutante lo neutraliza, el componente cae al
    // `if (!payload) return null` y deja una pantalla en blanco.
    const fetchCalls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        fetchCalls.push(String(url));
        if (String(url).includes("/health")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ services: { api: "healthy" } }) });
        }
        return Promise.reject(new Error(`URL inesperada en el mock de fetch: ${url}`));
      })
    );

    const router = createMemoryRouter([
      {
        path: "/",
        Component: makeContextProvider({
          token: "",
          user: { full_name: "Ada Lovelace", email: "ada@example.com" },
          tenants: [{ id: "tenant-1", name: "Acme", slug: "acme", plan: "pro" }],
          activeTenant: { id: "tenant-1", name: "Acme", slug: "acme", plan: "pro" }
        }),
        children: [{ index: true, Component: DashboardPage }]
      }
    ]);

    renderRouter(router);

    await waitFor(() => expect(fetchCalls.some((url) => url.includes("/health"))).toBe(true));
    expect(
      await screen.findByRole("heading", { name: "Connecting to the FinOps control plane..." })
    ).toBeVisible();
    expect(fetchCalls.some((url) => url.includes("/billing/summary"))).toBe(false);
  });
});

describe("DashboardPage (mutacion: tenants.map)", () => {
  it("renderiza el nombre y el plan de cada tenant visible para el operador", async () => {
    stubDashboardFetch();

    const router = createMemoryRouter([
      {
        path: "/",
        Component: makeContextProvider({
          token: "tok",
          user: { full_name: "Ada Lovelace", email: "ada@example.com" },
          tenants: [{ id: "tenant-1", name: "Acme Corp", slug: "acme", plan: "pro-plan" }],
          activeTenant: { id: "tenant-1", name: "Acme Corp", slug: "acme", plan: "pro-plan" }
        }),
        children: [{ index: true, Component: DashboardPage }]
      }
    ]);

    renderRouter(router);

    // "Acme Corp" (tenant.name) y "pro-plan" (tenant.plan, via StatusPill)
    // solo existen dentro del <article> generado por `tenants.map`. Si el
    // mapeo se sustituyera por `tenants.map(() => undefined)` (mutante
    // ArrowFunction), ninguno de los dos apareceria en el documento.
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());
    expect(screen.getByText("pro-plan")).toBeInTheDocument();
  });
});
