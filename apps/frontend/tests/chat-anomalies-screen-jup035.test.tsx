import { useState } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { ScreenCaptureProvider, usePreparedScreen } from "../src/components/chat/ScreenCaptureProvider";
import { AnomaliesPanel } from "../src/pages/AnomaliesPanel";
import { episode, episodeList } from "../src/test/anomalyFixtures";
import type { ScreenCapture } from "../src/services/screenCapture";

afterEach(() => vi.unstubAllGlobals());
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), {
  status, headers: { "Content-Type": "application/json" },
});
function mount() {
  const captures: ScreenCapture[] = [];
  function Capture() {
    const prepared = usePreparedScreen();
    return <button onClick={() => captures.push(prepared!.freeze("/anomalies"))}>Capturar</button>;
  }
  function Workspace() {
    const [tenant, setTenant] = useState("a");
    return <ScreenCaptureProvider tenantId={tenant} userId="u" token="synthetic">
      <button onClick={() => setTenant("b")}>Otro cliente</button><Capture />
      <Outlet context={{ token: "synthetic", activeTenant: { id: tenant, name: tenant }, activeTenantId: tenant }} />
    </ScreenCaptureProvider>;
  }
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter([{ path: "/", Component: Workspace,
    children: [{ path: "anomalies", Component: AnomaliesPanel }] }], { initialEntries: ["/anomalies"] });
  render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
  return { client, capture: () => { fireEvent.click(screen.getByText("Capturar")); return captures.at(-1)!; } };
}

it("conserva moneda y periodo por episodio, filtros y captura sin consultas adicionales", async () => {
  const fetch = vi.fn(async () => json(episodeList({ episodes: [episode(), episode({ id: "usd", currency: "USD", severity: "P2" })] })));
  vi.stubGlobal("fetch", fetch);
  const { capture } = mount();
  await screen.findByText("2807.71 USD");
  const calls = fetch.mock.calls.length;
  const snapshot = capture();
  expect(snapshot.identity.tenant_id).toBe("a");
  expect(snapshot.source).toBe("loaded-screen");
  const dataset = snapshot.datasets[0];
  expect(dataset.totals).toEqual([]);
  expect(dataset.groups).toEqual(expect.arrayContaining([
    expect.objectContaining({ currency: "EUR", amount: "2807.71", period: { start_date: "2026-09-09", end_date: "2026-09-20", timezone: "UTC" } }),
    expect.objectContaining({ currency: "USD", amount: "2807.71" }),
  ]));
  fireEvent.change(screen.getByLabelText("Criticidad"), { target: { value: "P2" } });
  expect(capture().datasets[0].groups).toEqual([expect.objectContaining({ episode_id: "usd" })]);
  expect(fetch).toHaveBeenCalledTimes(calls);
});

it("vacía captura durante carga, error de recarga y cambio de cliente sin reutilizar episodios", async () => {
  let complete!: (value: Response) => void;
  let fail = false;
  vi.stubGlobal("fetch", vi.fn(() => fail ? Promise.resolve(json({ detail: "unavailable" }, 503)) :
    new Promise<Response>(resolve => { complete = resolve; })));
  const { client, capture } = mount();
  expect(capture()).toMatchObject({ source: "loading", datasets: [] });
  await act(async () => complete(json(episodeList())));
  await waitFor(() => expect(capture().source).toBe("loaded-screen"));
  fail = true;
  await act(async () => { await client.invalidateQueries({ queryKey: ["anomaly-episodes"] }); });
  await waitFor(() => expect(capture()).toMatchObject({ source: "error", datasets: [] }));
  fail = false;
  fireEvent.click(screen.getByText("Otro cliente"));
  expect(capture()).toMatchObject({ source: "loading", identity: { tenant_id: "b" }, datasets: [] });
  await act(async () => complete(json(episodeList({ episodes: [], open_impact_by_currency: [] }))));
  await waitFor(() => expect(capture().source).toBe("loaded-screen"));
  expect(capture().datasets[0]).toMatchObject({ groups: [], totals: [], load_state: "empty" });
});

it("descarta una recarga tardía del cliente anterior mientras carga el nuevo", async () => {
  const pending = new Map<string, (value: Response) => void>();
  vi.stubGlobal("fetch", vi.fn((_input: RequestInfo | URL, init: RequestInit = {}) => {
    const tenant = new Headers(init.headers).get("X-Tenant-Id")!;
    return new Promise<Response>(resolve => { pending.set(tenant, resolve); });
  }));
  const { client, capture } = mount();
  await waitFor(() => expect(pending.has("a")).toBe(true));
  await act(async () => pending.get("a")!(json(episodeList({ episodes: [episode({ id: "only-a" })] }))));
  await waitFor(() => expect(capture().datasets[0]?.groups).toEqual([
    expect.objectContaining({ episode_id: "only-a" }),
  ]));
  const first = pending.get("a");
  await act(async () => { void client.invalidateQueries({ queryKey: ["anomaly-episodes"] }); });
  await waitFor(() => expect(pending.get("a")).not.toBe(first));
  fireEvent.click(screen.getByText("Otro cliente"));
  expect(capture()).toMatchObject({ identity: { tenant_id: "b" }, source: "loading", datasets: [] });
  await act(async () => pending.get("a")!(json(episodeList({ episodes: [episode({ id: "late-a" })] }))));
  expect(capture()).toMatchObject({ identity: { tenant_id: "b" }, source: "loading", datasets: [] });
  await waitFor(() => expect(pending.has("b")).toBe(true));
  await act(async () => pending.get("b")!(json(episodeList({ episodes: [episode({ id: "only-b" })] }))));
  await waitFor(() => expect(capture().datasets[0]?.groups).toEqual([
    expect.objectContaining({ episode_id: "only-b" }),
  ]));
});
