import { readFileSync } from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { routeConfig } from "./routes";
import type { TenantCollection, UserProfile } from "./services/contracts";
import { billing, health } from "../tests/fixtures";

const profile = {
  id: "u1", full_name: "Ada Lovelace", email: "ada@example.com", role: "operator"
} satisfies UserProfile;

const hiddenAddresses = ["/operational", "/cuts", "/recommendations"];

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

function stubSession() {
  window.localStorage.setItem("finops.session", JSON.stringify({ accessToken: "tok-1", user: profile }));
}

function stubBackend(extra: Record<string, unknown> = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn<typeof fetch>(async (input) => {
      const path = new URL(input instanceof Request ? input.url : String(input)).pathname;
      if (path === "/me") return Response.json(profile);
      if (path === "/tenants") {
        return Response.json({
          items: [
            { id: "t1", name: "Acme", slug: "acme", plan: "pro" },
            { id: "t2", name: "Globex", slug: "globex", plan: "enterprise" }
          ]
        } satisfies TenantCollection);
      }
      if (path in extra) return Response.json(extra[path]);
      return Response.json({ detail: "not under test" }, { status: 500 });
    })
  );
}

function renderRoutes(initialEntries: string[]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(routeConfig, { initialEntries });
  const view = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
  return { router, ...view };
}

const selector = () => screen.getByRole("combobox", { name: /ámbito de cliente/i });

describe("pantallas de demostración no publicadas", () => {
  it.each(hiddenAddresses)("abrir %s con sesión presenta la pantalla inicial, no la oculta", async (address) => {
    stubSession();
    stubBackend();
    renderRoutes([address]);

    await waitFor(() => expect(screen.getByText("Panel Ejecutivo - Coste Global")).toBeInTheDocument());
    expect(screen.queryByText(/Panel Operativo|Corte Global$|Panel de Recomendaciones/)).toBeNull();
    expect(screen.queryByText(/Unexpected Application Error|404/)).toBeNull();
  });

  it("una dirección que no existe también lleva a la pantalla inicial", async () => {
    stubSession();
    stubBackend();
    renderRoutes(["/no-existe"]);

    await waitFor(() => expect(screen.getByText("Panel Ejecutivo - Coste Global")).toBeInTheDocument());
    expect(screen.queryByText(/Unexpected Application Error|404/)).toBeNull();
  });

  it.each(hiddenAddresses)("navegar a %s conserva el ámbito de cliente elegido", async (address) => {
    stubSession();
    stubBackend();
    const { router } = renderRoutes(["/"]);

    await waitFor(() => expect(selector()).toHaveValue("t1"));
    fireEvent.change(selector(), { target: { value: "t2" } });
    await act(async () => { await router.navigate(address); });

    await waitFor(() => expect(screen.getByText("Panel Ejecutivo - Coste Global")).toBeInTheDocument());
    expect(selector()).toHaveValue("t2");
    expect(router.state.location.pathname).toBe("/");
  });

  it("la dirección oculta no se queda en el historial: Atrás no vuelve a ella", async () => {
    stubSession();
    stubBackend();
    const { router } = renderRoutes(["/anomalies"]);

    await waitFor(() => expect(selector()).toHaveValue("t1"));
    await act(async () => { await router.navigate("/cuts"); });
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
    await act(async () => { await router.navigate(-1); });

    expect(router.state.location.pathname).toBe("/anomalies");
  });

  it.each(hiddenAddresses)("sin sesión, abrir %s presenta el acceso y no consulta nada", async (address) => {
    window.localStorage.clear();
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    renderRoutes([address]);

    await waitFor(() => expect(screen.getByRole("button", { name: /iniciar sesión/i })).toBeInTheDocument());
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});

describe("vista heredada del resumen de facturación", () => {
  it("se presenta por su dirección dentro del armazón", async () => {
    stubSession();
    stubBackend({ "/billing/summary": billing, "/health": health });
    renderRoutes(["/overview-legacy"]);

    await waitFor(() => expect(screen.getByText(/Espacio FinOps por cliente/)).toBeInTheDocument());
    expect(screen.getByRole("combobox", { name: /ámbito de cliente/i })).toBeInTheDocument();
  });
});

describe("pantallas de demostración publicadas", () => {
  const src = (...parts: string[]) => readFileSync(path.resolve(__dirname, ...parts), "utf8");

  it("toda pantalla enrutada que lee datos de demostración declara visiblemente su origen", () => {
    const screens = [...src("routes.tsx").matchAll(/from "\.\/pages\/(\w+)"/g)].map((m) => m[1]);
    expect(screens).toContain("AnomaliesPanel");
    const unlabelled = screens.filter((name) => {
      const code = src("pages", `${name}.tsx`);
      return code.includes("data/demo") && !code.includes("Datos de demostración");
    });
    expect(unlabelled).toEqual([]);
  });
});

describe("direcciones hostiles no publicadas", () => {
  it.each(["/%E0%A4%A", "/cuts?x=1#h", "/" + "a".repeat(5000)])("%s no presenta error del enrutador", async (address) => {
    stubSession();
    stubBackend();
    renderRoutes([address]);

    await waitFor(() => expect(screen.getByText("Panel Ejecutivo - Coste Global")).toBeInTheDocument());
    expect(screen.queryByText(/Unexpected Application Error|404/)).toBeNull();
  });
});
