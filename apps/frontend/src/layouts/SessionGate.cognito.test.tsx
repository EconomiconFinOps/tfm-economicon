import { act, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { SessionGate, SESSION_KEY } from "./SessionGate";

const user = { id: "subject", email: "operator@example.com", full_name: "Operator", role: "admin" };
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

function show(expiresAt: number) {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify({ accessToken: "signed-access", user, expiresAt }));
  const router = createMemoryRouter([
    { path: "/", Component: SessionGate, children: [{ index: true, element: <p>Área privada</p> }] },
    { path: "/login", element: <p>Acceso</p> }
  ]);
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } })}>
    <RouterProvider router={router} /></QueryClientProvider>);
}

it("discards an expired stored access token before sending API requests", async () => {
  const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
  show(Date.now()-1000);
  expect(await screen.findByText("Acceso")).toBeInTheDocument();
  expect(fetch).not.toHaveBeenCalled();
  expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
});

it("expires an open session without waiting for a later API error", async () => {
  vi.useFakeTimers();
  vi.stubGlobal("fetch", vi.fn((input: string) => Promise.resolve(new Response(JSON.stringify(
    input.endsWith("/me") ? user : { items: [{ id: "tenant-core", name: "Core", slug: "core", plan: "demo", role: "admin" }] }
  ), { status: 200, headers: { "Content-Type": "application/json" } }))));
  show(Date.now()+10000);
  await act(async () => { await vi.advanceTimersByTimeAsync(10001); });
  expect(screen.getByText("Acceso")).toBeInTheDocument();
  expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
});
