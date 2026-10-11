import { act, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { Layout } from "../src/layouts/Layout";
import { useChatSession } from "../src/components/chat/useChatSession";
import { PreparedScreen } from "../src/services/screenCapture";

const scope = { token: "synthetic", tenantId: "t", userId: "alice" };
const record = (id = "old", title = "Original") => ({ id, title, tenant_id: "t", user_id: "alice", created_at: "2026-10-10T00:00:00Z", updated_at: "2026-10-10T00:00:00Z" });
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { "Content-Type": "application/json" } });
let calls: { path: string; method: string; body: Record<string, string> }[];
let patch: (body: Record<string, string>) => Promise<Response>;
beforeEach(() => {
  calls = [];
  patch = async body => json(record("old", body.title));
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
    const path = new URL(String(input), "http://test").pathname;
    const method = options.method ?? "GET";
    const body = typeof options.body === "string" ? JSON.parse(options.body) : {};
    calls.push({ path, method, body });
    if (method === "PATCH") return patch(body);
    if (path === "/assistant/conversations") return method === "POST" ? json(record("new", body.title), 201) : json({ items: [record()] });
    if (path === "/assistant/requests") return json({ items: [] });
    if (path.endsWith("/summary")) return json({ v: 2, scope: { tenant_id: "t", user_id: "alice", conversation_id: "old" }, available: false,
      reason: null, coverage: { processed_pairs: 0, pending_pairs: 0, recent_reserved: 4 }, limitations: [], artifact_id: null,
      queue: { reason: "idle", active: false, pending: false, blocked: false } });
    if (path.endsWith("/generations")) return json({}, 503);
    return json({ conversation: record(), messages: [] });
  }));
});
function hook() {
  const prepared = new PreparedScreen("t", "alice");
  vi.spyOn(prepared, "freeze").mockReturnValue({} as ReturnType<PreparedScreen["freeze"]>);
  return renderHook(() => useChatSession(scope, prepared));
}
function mount() {
  function Session() { return <Outlet context={{ token: "synthetic", user: { id: "alice", full_name: "Alice", email: "a@example.test", role: "member" }, tenants: [{ id: "t", name: "Tenant" }], activeTenant: { id: "t", name: "Tenant" }, activeTenantId: "t", onTenantChange: () => {}, onLogout: () => {} }} />; }
  const router = createMemoryRouter([{ path: "/", Component: Session, children: [{ Component: Layout, children: [{ path: "operational", element: <p>Datos</p> }] }] }], { initialEntries: ["/operational"] });
  render(<RouterProvider router={router} />);
  fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
}

it("names creation from first question, normalizes spaces and truncates 60 Unicode points only", async () => {
  const { result } = hook();
  const question = "  Hola\n\t " + "\u{1f600}".repeat(65);
  await act(async () => result.current.session.send(question, "/operational"));
  expect(calls.find(call => call.method === "POST" && call.path.endsWith("/conversations"))?.body.title).toBe("Hola " + "\u{1f600}".repeat(55));
  expect(calls.find(call => call.path.endsWith("/generations"))?.body.content).toBe(question);
});

it("preserves a manual draft title on creation and never creates again for existing history", async () => {
  const { result } = hook();
  await act(async () => result.current.session.rename(result.current.cell.id, "  Mi   nombre "));
  await act(async () => result.current.session.send("Primera pregunta diferente", "/operational"));
  expect(calls.find(call => call.method === "POST" && call.path.endsWith("/conversations"))?.body.title).toBe("Mi nombre");
  expect(calls.filter(call => call.method === "PATCH")).toHaveLength(0);
  await act(async () => result.current.session.select(record()));
  await act(async () => result.current.session.rename("old", "Nombre manual"));
  await waitFor(() => expect(result.current.cell.memory?.queue.blocked).toBe(false));
  await act(async () => result.current.session.send("Otra pregunta", "/operational"));
  expect(result.current.cell.title).toBe("Nombre manual");
  expect(calls.filter(call => call.path.endsWith("/generations"))).toHaveLength(2);
  expect(calls.filter(call => call.method === "POST" && call.path.endsWith("/conversations"))).toHaveLength(1);
});

it("late rename updates its own cell/history without changing selection; stale history cannot undo it", async () => {
  const { result } = hook();
  await act(async () => result.current.session.select(record()));
  let release!: (response: Response) => void;
  patch = () => new Promise(resolve => { release = resolve; });
  let saving!: Promise<void>;
  act(() => { saving = result.current.session.rename("old", "Guardado"); });
  const originalFetch = globalThis.fetch;
  let releaseHistory!: (response: Response) => void;
  vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, options?: RequestInit) => String(input).endsWith("/assistant/conversations") ? new Promise<Response>(resolve => { releaseHistory = resolve; }) : originalFetch(input, options)));
  let loading!: Promise<void>;
  act(() => { loading = result.current.session.loadHistory(); result.current.session.newConversation(); });
  const selected = result.current.cell.id;
  await act(async () => { release(json(record("old", "Guardado"))); await saving; });
  await act(async () => { releaseHistory(json({ items: [record()] })); await loading; });
  expect(result.current.cell.id).toBe(selected);
  expect(result.current.value.cells.old.title).toBe("Guardado");
  expect(result.current.value.history[0].title).toBe("Guardado");
});

it("rejects a mismatched rename response without changing the title", async () => {
  const { result } = hook();
  await act(async () => result.current.session.select(record()));
  patch = async () => json({ ...record("old", "Wrong"), user_id: "bob" });
  await act(async () => { await expect(result.current.session.rename("old", "New")).rejects.toThrow(); });
  expect(result.current.cell.title).toBe("Original");
});

it("header editor supports Enter, Escape, validation and accessible controls", async () => {
  mount();
  fireEvent.click(screen.getByRole("button", { name: "Renombrar conversación" }));
  const input = screen.getByRole("textbox", { name: "Nombre de conversación" });
  fireEvent.change(input, { target: { value: "   " } });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(await screen.findByRole("alert")).toHaveTextContent("60");
  fireEvent.change(input, { target: { value: "Manual" } });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(await screen.findByText("Manual")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Renombrar conversación" }));
  fireEvent.keyDown(screen.getByRole("textbox", { name: "Nombre de conversación" }), { key: "Escape" });
  expect(screen.getByRole("region", { name: "Asistente FinOps" })).toBeVisible();
  expect(screen.queryByRole("textbox", { name: "Nombre de conversación" })).toBeNull();
});

it("history editor prevents duplicate save, displays errors and preserves selection", async () => {
  mount();
  fireEvent.click(screen.getByRole("button", { name: "Historial" }));
  const dialog = await screen.findByRole("dialog", { name: "Historial de conversaciones" });
  fireEvent.click(await within(dialog).findByRole("button", { name: "Renombrar Original" }));
  fireEvent.keyDown(within(dialog).getByRole("textbox", { name: "Nombre de conversación" }), { key: "Escape" });
  expect(dialog).toBeVisible();
  expect(calls.filter(call => call.method === "PATCH")).toHaveLength(0);
  fireEvent.click(within(dialog).getByRole("button", { name: "Renombrar Original" }));
  const input = within(dialog).getByRole("textbox", { name: "Nombre de conversación" });
  fireEvent.change(input, { target: { value: "Renombrado" } });
  let release!: (response: Response) => void;
  patch = () => new Promise(resolve => { release = resolve; });
  fireEvent.keyDown(input, { key: "Enter" });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(within(dialog).getByRole("button", { name: "Guardar nombre" })).toBeDisabled();
  expect(calls.filter(call => call.method === "PATCH")).toHaveLength(1);
  await act(async () => release(json({}, 500)));
  expect(await within(dialog).findByRole("alert")).toHaveTextContent("No se pudo");
  patch = async body => json(record("old", body.title));
  fireEvent.click(within(dialog).getByRole("button", { name: "Guardar nombre" }));
  expect(await within(dialog).findByRole("button", { name: "Renombrado" })).toBeVisible();
  fireEvent.click(within(dialog).getByRole("button", { name: "Cerrar historial" }));
  await waitFor(() => expect(screen.getByText("Nueva conversación", { selector: "p" })).toBeVisible());
});
