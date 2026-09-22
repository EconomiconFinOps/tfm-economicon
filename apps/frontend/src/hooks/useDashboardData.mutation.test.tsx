// Casos adicionales (remediacion de mutation testing, JUP-097 grupo 5, tarea
// 5.4) sobre useDashboardData.ts. Ningun test existente ejercita el hook de
// forma aislada: todos pasan por DashboardPage/App completos, donde varias
// ramas tempranas (p.ej. "!activeTenant" en DashboardPage) descartan el
// resultado del hook antes de que se pueda observar la diferencia entre el
// codigo real y ciertos mutantes (enabled/queryKey/loading/payload). Este
// archivo monta el hook por si solo (renderHook + QueryClientProvider) para
// cerrar ese hueco de cobertura.
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts.
import type { ReactNode } from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useDashboardData } from "./useDashboardData";

function wrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

function jsonResponse(body: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(body) } as Response);
}

const billingBody = { monthly_spend: 10, savings_identified: 1, open_ingestions: 0, currency: "USD" };
const healthBody = { services: {} };

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useDashboardData (mutacion: enabled/queryKey/loading/payload)", () => {
  it("no solicita /billing/summary sin tenantId, aunque /health si se consulte", async () => {
    // Mata dos mutantes de la condicion `enabled` (linea 20 de
    // useDashboardData.ts): `Boolean(token && tenantId)` -> `Boolean(true)` y
    // -> `Boolean(token || tenantId)`. Ambos forzarian a react-query a
    // ejecutar la consulta de facturacion aun sin tenantId (el token esta
    // presente). Ningun test existente lo detecta porque siempre pasan por
    // DashboardPage, que corta la renderizacion antes de llegar a observar
    // si `fetchBillingSummary` se invoco.
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        calls.push(String(url));
        return String(url).includes("/health") ? jsonResponse(healthBody) : jsonResponse({});
      })
    );

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    renderHook(() => useDashboardData({ token: "tok", tenantId: undefined }), { wrapper: wrapper(client) });

    await waitFor(() => expect(calls.some((url) => url.includes("/health"))).toBe(true));
    expect(calls.some((url) => url.includes("/billing/summary"))).toBe(false);
  });

  it("puebla la cache con las claves exactas ['billing-summary', tenantId] y ['health']", async () => {
    // Mata los mutantes StringLiteral/ArrayDeclaration de las lineas 13 y 23
    // (queryKey ["billing-summary", tenantId] -> ["", tenantId]; ["health"]
    // -> [] / [""]). React-query identifica cada consulta por su `queryKey`
    // exacta -- si cambia, el resultado poblado no es localizable con la
    // clave documentada. `exact: true` evita que un match parcial oculte la
    // diferencia.
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => (String(url).includes("/billing/summary") ? jsonResponse(billingBody) : jsonResponse(healthBody)))
    );

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { result } = renderHook(() => useDashboardData({ token: "tok", tenantId: "tenant-1" }), {
      wrapper: wrapper(client)
    });

    await waitFor(() => expect(result.current.payload).not.toBeNull());

    expect(
      client.getQueryCache().find({ queryKey: ["billing-summary", "tenant-1"], exact: true })?.state.data
    ).toEqual(billingBody);
    expect(client.getQueryCache().find({ queryKey: ["health"], exact: true })?.state.data).toEqual(healthBody);
  });

  it("loading permanece true mientras /health sigue pendiente, aunque /billing/summary ya respondio", async () => {
    // Mata el mutante ConditionalExpression de la linea 30
    // (`billingQuery.isLoading || healthQuery.isLoading` -> `false`): sin
    // este caso, ningun test aislado del hook comprueba que `loading` sea
    // realmente `true` mientras una de las dos consultas no ha resuelto.
    let resolveHealth: () => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (String(url).includes("/billing/summary")) return jsonResponse(billingBody);
        return new Promise((resolve) => {
          resolveHealth = () => resolve({ ok: true, json: () => Promise.resolve(healthBody) } as Response);
        });
      })
    );

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { result } = renderHook(() => useDashboardData({ token: "tok", tenantId: "tenant-1" }), {
      wrapper: wrapper(client)
    });

    expect(result.current.loading).toBe(true);

    // Punto de control intermedio (mata al mutante LogicalOperator que
    // cambia `||` por `&&` en la linea 30): con `&&`, en cuanto
    // /billing/summary resuelve mientras /health SIGUE pendiente, `loading`
    // pasaria a `false` de inmediato (false && true) en vez de seguir en
    // `true` (false || true), que es el comportamiento real esperado.
    await waitFor(() =>
      expect(
        client.getQueryCache().find({ queryKey: ["billing-summary", "tenant-1"], exact: true })?.state.data
      ).toEqual(billingBody)
    );
    expect(result.current.loading).toBe(true);

    await act(async () => resolveHealth());
    await waitFor(() => expect(result.current.loading).toBe(false));
  });

  it("payload permanece null hasta que AMBAS consultas resuelven (no basta con una sola)", async () => {
    // Mata dos mutantes de la linea 32:
    // - ConditionalExpression (`billingQuery.data && healthQuery.data ? {...}
    //   : null` -> `true`): forzaria `payload` a un literal `true` desde el
    //   primer render, antes de que ninguna consulta resuelva.
    // - LogicalOperator (`&&` -> `||`): bastaria con que UNA de las dos
    //   consultas tuviera datos para que `payload` dejara de ser null,
    //   exponiendo un objeto con la otra mitad (`health` o `billing`) todavia
    //   `undefined`. Se verifica explicitamente la ventana en la que
    //   /billing/summary ya resolvio pero /health sigue pendiente.
    let resolveHealth: () => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (String(url).includes("/billing/summary")) return jsonResponse(billingBody);
        return new Promise((resolve) => {
          resolveHealth = () => resolve({ ok: true, json: () => Promise.resolve(healthBody) } as Response);
        });
      })
    );

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { result } = renderHook(() => useDashboardData({ token: "tok", tenantId: "tenant-1" }), {
      wrapper: wrapper(client)
    });

    // Estado inicial: ninguna consulta ha resuelto todavia.
    expect(result.current.payload).toBeNull();

    // /billing/summary ya resolvio (visible en la cache), pero /health sigue
    // pendiente: payload debe seguir siendo null.
    await waitFor(() =>
      expect(
        client.getQueryCache().find({ queryKey: ["billing-summary", "tenant-1"], exact: true })?.state.data
      ).toEqual(billingBody)
    );
    expect(result.current.payload).toBeNull();

    await act(async () => resolveHealth());
    await waitFor(() => expect(result.current.payload).not.toBeNull());
    expect(result.current.payload).toEqual({ billing: billingBody, health: healthBody });
  });
});
