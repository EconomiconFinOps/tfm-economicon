import './chat-enabled-runtime';
import { act, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { Layout } from "../src/layouts/Layout";
import { useChatSession } from "../src/components/chat/useChatSession";

const scope = { token: "synthetic", tenantId: "t", userId: "alice" };
const record = (id = "old") => ({ id, title: id === "old" ? "Original" : "Otra", tenant_id: "t", user_id: "alice", created_at: "2026-10-10T00:00:00Z", updated_at: "2026-10-10T00:00:00Z" });
const operation = { v: 2, operation_id: "op", question_id: "q", request_id: "r", state: "failed", attempt_count: 1, current_attempt_id: null, attempt_deadline: null, retry_at: null, result_url: null,
  wait_info: { reason: null, local_remaining_ms: 0, provider_remaining_ms: 0, automatic_until: null, retry_at: null, pause_reason: null } };
const saved = () => ({ tenant_id: "t", user_id: "alice", conversation_id: "old", question: "Pregunta", operation });
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
let calls: { path: string; method: string; signal?: AbortSignal | null }[];
let remove: () => Promise<Response>;
beforeEach(() => {
  operation.state = "failed";
  calls = [];
  remove = async () => new Response(null, { status: 204 });
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
    const path = new URL(String(input), "http://test").pathname;
    const method = options.method ?? "GET";
    calls.push({ path, method, signal: options.signal });
    if (method === "DELETE") return remove();
    if (path === "/assistant/conversations") return json({ items: [record(), record("other")] });
    if (path === "/assistant/requests") return json({ items: [saved()] });
    if (path.endsWith("/summary")) return json({ v: 2, scope: { tenant_id: "t", user_id: "alice", conversation_id: path.split("/")[3] }, available: false,
      reason: null, coverage: { processed_pairs: 0, pending_pairs: 0, recent_reserved: 4 }, limitations: [], artifact_id: null,
      queue: { reason: "idle", active: false, pending: false, blocked: false } });
    return json({ conversation: record(path.split("/")[3]), messages: [] });
  }));
});
function mount() {
  function Session() { return <Outlet context={{ token: "synthetic", user: { id: "alice", full_name: "Alice", email: "a@example.test", role: "member" }, tenants: [{ id: "t", name: "Tenant" }], activeTenant: { id: "t", name: "Tenant" }, activeTenantId: "t", onTenantChange: () => {}, onLogout: () => {} }} />; }
  const router = createMemoryRouter([{ path: "/", Component: Session, children: [{ Component: Layout, children: [{ path: "operational", element: <p>Datos</p> }] }] }], { initialEntries: ["/operational"] });
  render(<RouterProvider router={router} />);
  fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
  fireEvent.click(screen.getByRole("button", { name: "Historial" }));
}

it("deletes current cell, history and saved requests; stale lists and selection cannot resurrect it", async () => {
  const { result } = renderHook(() => useChatSession(scope));
  await act(async () => { await result.current.session.loadHistory(); await result.current.session.select(record()); });
  await act(async () => result.current.session.remove("old"));
  expect(result.current.cell.id).toMatch(/^draft-/);
  expect(result.current.value.cells.old).toBeUndefined();
  expect(result.current.value.history.map(item => item.id)).toEqual(["other"]);
  expect(result.current.value.requests).toHaveLength(0);
  await act(async () => { await result.current.session.loadHistory(); await result.current.session.select(record()); await result.current.session.selectRequest(saved() as never); });
  expect(result.current.cell.id).toMatch(/^draft-/);
  expect(result.current.value.history.map(item => item.id)).toEqual(["other"]);
  expect(result.current.value.requests).toHaveLength(0);
});

it("pending delete does not steal a newer selection and sends only once", async () => {
  const { result } = renderHook(() => useChatSession(scope));
  await act(async () => result.current.session.select(record()));
  let release!: (response: Response) => void;
  remove = () => new Promise(resolve => { release = resolve; });
  let pending!: Promise<void>;
  act(() => { pending = result.current.session.remove("old"); });
  await act(async () => { await expect(result.current.session.remove("old")).rejects.toThrow(); await result.current.session.select(record("other")); });
  await act(async () => { release(new Response(null, { status: 204 })); await pending; });
  expect(result.current.cell.id).toBe("other");
  expect(calls.filter(call => call.method === "DELETE")).toHaveLength(1);
});

it("aborts an old conversation reader and ignores its late callback after deletion", async () => {
  const { result } = renderHook(() => useChatSession(scope));
  const original = globalThis.fetch;
  let release!: (response: Response) => void;
  let signal: AbortSignal | null | undefined;
  vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, options: RequestInit = {}) => {
    if (String(input).endsWith("/assistant/conversations/old") && !options.method) {
      signal = options.signal;
      return new Promise<Response>(resolve => { release = resolve; });
    }
    if (String(input).endsWith("/assistant/conversations/old") && options.method === "GET") {
      signal = options.signal;
      return new Promise<Response>(resolve => { release = resolve; });
    }
    return original(input, options);
  }));
  let selecting!: Promise<void>;
  act(() => { selecting = result.current.session.select(record()); });
  await act(async () => result.current.session.remove("old"));
  expect(signal?.aborted).toBe(true);
  await act(async () => { release(json({ conversation: record(), messages: [] })); await selecting; });
  expect(result.current.value.cells.old).toBeUndefined();
  expect(result.current.cell.id).toMatch(/^draft-/);
});

it("known active requests block deletion without HTTP and server 409 retains all local data", async () => {
  const { result } = renderHook(() => useChatSession(scope));
  operation.state = "active";
  await act(async () => result.current.session.loadHistory());
  await act(async () => { await expect(result.current.session.remove("old")).rejects.toThrow(/respuesta|compresi/); });
  expect(calls.filter(call => call.method === "DELETE")).toHaveLength(0);
  operation.state = "failed";
  await act(async () => { await result.current.session.loadHistory(); await result.current.session.select(record()); });
  remove = async () => json({ detail: "conversation_compacting" }, 409);
  await act(async () => { await expect(result.current.session.remove("old")).rejects.toThrow(/respuesta|compresi/); });
  expect(result.current.cell.id).toBe("old");
  expect(result.current.value.history).toHaveLength(2);
  expect(result.current.value.requests).toHaveLength(1);
});

it("exact confirmation, No/Escape cancel without delete, focus restored, Yes pending/error/retry", async () => {
  mount();
  const history = await screen.findByRole("dialog", { name: "Historial de conversaciones" });
  const trash = await within(history).findByRole("button", { name: "Eliminar Original" });
  fireEvent.click(trash);
  const name = "¿Estás seguro? No podrás recuperar esta conversación";
  let dialog = await screen.findByRole("dialog", { name });
  expect(within(dialog).getByRole("button", { name: "No" })).toHaveFocus();
  fireEvent.keyDown(within(dialog).getByRole("button", { name: "No" }), { key: "Escape" });
  await waitFor(() => expect(screen.queryByRole("dialog", { name })).toBeNull());
  expect(trash).toHaveFocus();
  expect(history).toBeVisible();
  fireEvent.click(trash);
  dialog = await screen.findByRole("dialog", { name });
  fireEvent.click(within(dialog).getByRole("button", { name: "No" }));
  expect(calls.filter(call => call.method === "DELETE")).toHaveLength(0);
  fireEvent.click(trash);
  dialog = await screen.findByRole("dialog", { name });
  let release!: (response: Response) => void;
  remove = () => new Promise(resolve => { release = resolve; });
  fireEvent.click(within(dialog).getByRole("button", { name: "Sí" }));
  fireEvent.click(within(dialog).getByRole("button", { name: "Sí" }));
  expect(calls.filter(call => call.method === "DELETE")).toHaveLength(1);
  expect(within(dialog).getByRole("button", { name: "Sí" })).toBeDisabled();
  await act(async () => release(json({}, 409)));
  expect(await within(dialog).findByRole("alert")).toHaveTextContent(/respuesta|compresi/);
  remove = async () => new Response(null, { status: 204 });
  fireEvent.click(within(dialog).getByRole("button", { name: "Sí" }));
  await waitFor(() => expect(screen.queryByRole("dialog", { name })).toBeNull());
  expect(within(history).queryByRole("button", { name: "Original" })).toBeNull();
  expect(within(history).getByRole("button", { name: "Cerrar historial" })).toHaveFocus();
});

// Chat fixtures freeze the new JUP-119 clock dependency; its HTTP/cache contract has separate tests.
vi.mock("../src/hooks/useReferenceDate", () => ({ useReferenceDate: () => ({ data: { reference_date: "2026-10-10", simulated: false } }) }));
