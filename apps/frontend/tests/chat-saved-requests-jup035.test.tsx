import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Layout } from "../src/layouts/Layout";

const conversation = { id: "saved", title: "Conversación propia", tenant_id: "t", user_id: "alice",
  created_at: "2026-10-10T00:00:00Z", updated_at: "2026-10-10T00:00:00Z" };
const operation = { v: 2, operation_id: "op", question_id: "question", request_id: "intent",
  state: "paused", attempt_count: 1, current_attempt_id: "attempt", attempt_deadline: null,
  retry_at: null as string | null, result_url: null as string | null, wait_info: { reason: "local_capacity", local_remaining_ms: 0,
    provider_remaining_ms: 120000, automatic_until: null, retry_at: null, pause_reason: "local_budget" } };
type Call = { path: string; method: string; raw: string | undefined; headers: Headers };
let calls: Call[];
let requests: unknown[];
let current: typeof operation;
let messages: unknown[];
let failGeneration: boolean;
let failCreation: boolean;
let reader: ReadableStreamDefaultController<Uint8Array> | undefined;
const json = (value: unknown) => new Response(JSON.stringify(value), { headers: { "Content-Type": "application/json" } });
function event(type: string, value: Record<string, unknown>) {
  reader?.enqueue(new TextEncoder().encode(`event: ${type}\ndata: ${JSON.stringify({ v: 2, type, ...value })}\n\n`));
}
function mount() {
  let change: ((value: { tenant: string; user: string }) => void) | undefined;
  function Session() {
    const [scope, update] = useState({ tenant: "t", user: "alice" }); change = update;
    return <Outlet context={{ token: "synthetic-token", user: { id: scope.user, full_name: "Alice", email: "alice@example.test", role: "member" },
      activeTenant: { id: scope.tenant, name: "Tenant", slug: "tenant", plan: "test" }, activeTenantId: scope.tenant }} />;
  }
  const router = createMemoryRouter([{ path: "/", Component: Session, children: [{ Component: Layout,
    children: [{ path: "operational", element: <p>Vista original</p> }, { path: "recommendations", element: <p>Otra vista</p> }] }] }], { initialEntries: ["/operational"] });
  return { ...render(<RouterProvider router={router} />), router, change: (tenant: string, user: string) => change?.({ tenant, user }) };
}
async function openHistory() {
  fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
  fireEvent.click(await screen.findByRole("button", { name: "Historial" }));
  return screen.findByRole("dialog", { name: "Historial de conversaciones" });
}
async function selectRequest() {
  const dialog = await openHistory();
  fireEvent.click(await within(dialog).findByRole("button", { name: /Pregunta guardada/ }));
}
async function uncertainSend() {
  failGeneration = true;
  fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
  fireEvent.change(await screen.findByRole("textbox", { name: "Pregunta" }), { target: { value: "Pregunta incierta" } });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
  await waitFor(() => expect(calls.filter(call => call.path.endsWith("/generations"))).toHaveLength(1));
  expect(await screen.findByRole("alert")).toHaveTextContent("Comprueba la solicitud");
}
beforeEach(() => {
  calls = []; messages = []; reader = undefined; failGeneration = false; failCreation = false;
  current = { ...operation, wait_info: { ...operation.wait_info } };
  requests = [{ tenant_id: "t", user_id: "alice", conversation_id: "saved", question: "Pregunta guardada", operation: current }];
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
    const path = new URL(String(input), "http://test").pathname, method = options.method ?? "GET";
    calls.push({ path, method, raw: typeof options.body === "string" ? options.body : undefined, headers: new Headers(options.headers) });
    if (path === "/assistant/requests") return json({ items: requests });
    if (path.endsWith("/summary")) return json({ v: 2,
      scope: { tenant_id: "t", user_id: "alice", conversation_id: path.split("/")[3] },
      available: false, reason: "summary_absent", artifact_id: null, limitations: [],
      coverage: { processed_pairs: 0, pending_pairs: 0, recent_reserved: 0 },
      queue: { state: "idle", reason: "cold", active: false, pending: false, blocked: false, retryable: false } });
    if (path === "/assistant/conversations") {
      if (method === "POST" && failCreation) throw new TypeError("Synthetic lost creation response");
      return json(method === "POST" ? conversation : { items: [conversation] });
    }
    if (path.endsWith("/generations") && method === "POST" || path.endsWith("/events")) {
      if (method === "POST" && failGeneration) throw new TypeError("Synthetic lost reservation response");
      return new Response(new ReadableStream<Uint8Array>({ start(value) { reader = value; } }), { headers: { "Content-Type": "text/event-stream" } });
    }
    if (path.endsWith("/stop")) { current = { ...current, state: "cancelled" }; return json(current); }
    if (path.endsWith("/resume")) { current = { ...current, state: "waiting" }; return json(current); }
    if (path.endsWith("/result")) return json({ id: "answer", content: "Respuesta confirmada", metadata: {} });
    if (path.endsWith(`/generations/${current.operation_id}`)) return json(current);
    if (path === "/assistant/conversations/saved") return json({ conversation, messages });
    if (path === "/assistant/conversations/other-saved") return json({ conversation: { ...conversation, id: "other-saved" }, messages: [] });
    throw new Error(`Unexpected synthetic request ${method} ${path}`);
  }));
});
describe("Solicitudes privadas y envío incierto JUP-035", () => {
  async function selectAtDeadline(retryAt: string | null) {
    current = { ...current, retry_at: retryAt };
    requests = [{ tenant_id: "t", user_id: "alice", conversation_id: "saved", question: "Pregunta guardada", operation: current }];
    const view = mount();
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" })); });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Historial" })); });
    await act(async () => { fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: /Pregunta guardada/ })); });
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    return view;
  }
  it("deadline habilita reanudar al llegar la fecha sin interacción ni recarga y nunca envía sola", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setTimeout", "clearTimeout"] });
    let view: ReturnType<typeof mount> | undefined;
    try {
      const retryAt = new Date(Date.now() + 1000).toISOString();
      view = await selectAtDeadline(retryAt);
      const resume = screen.getByRole("button", { name: "Reanudar solicitud" });
      expect(resume).toBeDisabled();
      await act(async () => { await vi.advanceTimersByTimeAsync(999); });
      expect(resume).toBeDisabled();
      await act(async () => { await vi.advanceTimersByTimeAsync(2); });
      expect(resume).toBeEnabled();
      expect(screen.getByText("Pregunta guardada")).toBeVisible();
      expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
      expect(current.attempt_count).toBe(1);
      expect(current.wait_info.local_remaining_ms).toBe(0);
      await act(async () => { fireEvent.click(resume); });
      expect(calls.filter(call => call.path.endsWith("/resume"))).toHaveLength(1);
      expect(calls.filter(call => call.path.endsWith("/generations") && call.method === "POST")).toHaveLength(0);
    } finally { view?.unmount(); vi.useRealTimers(); }
  });
  it("deadline cancela la supervisión pendiente al desmontar sin acciones huérfanas", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setTimeout", "clearTimeout"] });
    let view: ReturnType<typeof mount> | undefined;
    try {
      // Baseline of the same UI lifecycle without a future resume deadline.
      view = await selectAtDeadline(null);
      view.unmount(); view = undefined;
      await act(async () => { await vi.advanceTimersByTimeAsync(0); });
      const ordinaryPending = vi.getTimerCount();
      vi.clearAllTimers();
      view = await selectAtDeadline(new Date(Date.now() + 1000).toISOString());
      expect(screen.getByRole("button", { name: "Reanudar solicitud" })).toBeDisabled();
      view.unmount(); view = undefined;
      await act(async () => { await vi.advanceTimersByTimeAsync(0); });
      expect(vi.getTimerCount()).toBe(ordinaryPending);
      await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
      expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
    } finally { view?.unmount(); vi.useRealTimers(); }
  });
  it("deadline de otra operación no permite reanudar antes de su propia fecha", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setTimeout", "clearTimeout"] });
    let view: ReturnType<typeof mount> | undefined;
    try {
      const start = Date.now();
      view = await selectAtDeadline(new Date(start + 1000).toISOString());
      current = { ...current, operation_id: "other", request_id: "other-intent", retry_at: new Date(start + 5000).toISOString() };
      requests = [{ tenant_id: "t", user_id: "alice", conversation_id: "other-saved", question: "Otra pregunta pausada", operation: current }];
      await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Historial" })); });
      await act(async () => { fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: /Otra pregunta pausada/ })); });
      const resume = screen.getByRole("button", { name: "Reanudar solicitud" });
      await act(async () => { await vi.advanceTimersByTimeAsync(1001); });
      expect(resume).toBeDisabled();
      expect(within(screen.getByRole("log", { name: "Mensajes" })).getByText("Otra pregunta pausada")).toBeVisible();
      await act(async () => { await vi.advanceTimersByTimeAsync(4000); });
      expect(resume).toBeEnabled();
      expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
    } finally { view?.unmount(); vi.useRealTimers(); }
  });

  it("recupera la pregunta pausada tras recarga separada del historial y no reanuda sola", async () => {
    mount();
    await selectRequest();
    expect(await screen.findByText("Pregunta guardada")).toBeVisible();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(await screen.findByRole("button", { name: "Reanudar solicitud" })).toBeEnabled();
    expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
    expect(calls.some(call => call.path.endsWith("/events"))).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Detener respuesta" }));
    expect(await screen.findByText("Respuesta detenida")).toBeVisible();
    expect(calls.filter(call => call.path.endsWith("/stop"))).toHaveLength(1);
    expect(calls.some(call => call.path.endsWith("/resume"))).toBe(false);
    expect(messages).toEqual([]);
  });
  it("reengancha una solicitud activa mediante GET y snapshot sin crear otra operación", async () => {
    current = { ...current, state: "active" }; requests = [{ tenant_id: "t", user_id: "alice", conversation_id: "saved", question: "Pregunta guardada", operation: current }];
    mount(); await selectRequest();
    await waitFor(() => expect(reader).toBeDefined());
    await act(async () => {
      event("started", { operation: current });
      event("snapshot", { operation_id: "op", attempt_id: "attempt", number: 1, revision: 2, seq: 70, offset: 10, text: "Parcial 🌍" });
    });
    expect(await screen.findByText("Parcial 🌍")).toBeVisible();
    expect(screen.getByText("Pregunta guardada")).toBeVisible();
    expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
    expect(calls.filter(call => call.path.endsWith("/events"))).toHaveLength(1);
    for (const call of calls) { expect(call.headers.get("Authorization")).toBe("Bearer synthetic-token"); expect(call.headers.get("X-Tenant-Id")).toBe("t"); }
  });
  it("solo reanuda la operación pausada cuando el usuario lo pide", async () => {
    mount(); await selectRequest();
    fireEvent.click(await screen.findByRole("button", { name: "Reanudar solicitud" }));
    await waitFor(() => expect(calls.filter(call => call.path.endsWith("/resume"))).toHaveLength(1));
    expect(calls.some(call => call.path.endsWith("/generations") && call.method === "POST")).toBe(false);
  });
  it("observa la espera existente sin reiniciar presupuesto ni generar", async () => {
    current = { ...current, state: "waiting" };
    requests = [{ tenant_id: "t", user_id: "alice", conversation_id: "saved", question: "Pregunta guardada", operation: current }];
    mount(); await selectRequest();
    expect(await screen.findByText("Esperando capacidad disponible")).toBeVisible();
    expect(await screen.findByText("Pregunta guardada")).toBeVisible();
    expect(calls.some(call => call.path.endsWith("/generations/op") && call.method === "GET")).toBe(true);
    expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
  });
  it("reintenta una solicitud terminal sólo por acción humana con clave nueva y vínculo a la anterior", async () => {
    current = { ...current, state: "cancelled" };
    requests = [{ tenant_id: "t", user_id: "alice", conversation_id: "saved", question: "Pregunta guardada", operation: current }];
    mount(); await selectRequest();
    const retry = await screen.findByRole("button", { name: "Reintentar respuesta" });
    expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
    fireEvent.click(retry);
    await waitFor(() => expect(reader).toBeDefined());
    const payload = JSON.parse(calls.find(call => call.path.endsWith("/generations"))!.raw!);
    expect(payload).toMatchObject({ content: "Pregunta guardada", retry_of_operation_id: "op" });
    expect(payload.request_id).not.toBe("intent");
    expect(calls.filter(call => call.path.endsWith("/generations"))).toHaveLength(1);
  });
  it.each([["other", "alice"], ["t", "bob"]])("rechaza solicitudes ajenas %s/%s conservando el historial propio", async (tenant_id, user_id) => {
    requests = [{ tenant_id, user_id, conversation_id: "saved", question: "Privado ajeno", operation }];
    mount(); const dialog = await openHistory();
    expect(await within(dialog).findByText("No se pudieron cargar las solicitudes guardadas.")).toBeVisible();
    expect(within(dialog).getByRole("button", { name: "Conversación propia" })).toBeVisible();
    expect(screen.queryByText("Privado ajeno")).toBeNull();
    expect(calls.some(call => call.path.endsWith("/events"))).toBe(false);
  });
  it("comprueba el envío incierto con idéntica clave, pregunta y captura aunque cambie la pantalla", async () => {
    const mounted = mount(); await uncertainSend();
    const original = calls.find(call => call.path.endsWith("/generations"))!;
    await act(async () => mounted.router.navigate("/recommendations"));
    failGeneration = false;
    fireEvent.click(await screen.findByRole("button", { name: "Comprobar envío" }));
    await waitFor(() => expect(reader).toBeDefined());
    const submitted = calls.filter(call => call.path.endsWith("/generations"));
    expect(submitted).toHaveLength(2); expect(submitted[1].raw).toBe(original.raw);
    expect(JSON.parse(submitted[1].raw!).screen_context.route).toBe("/operational");
    expect(calls.filter(call => call.path === "/assistant/conversations" && call.method === "POST")).toHaveLength(1);
    await act(async () => event("started", { operation: { ...current, state: "active" } }));
    expect(await screen.findByRole("button", { name: "Detener respuesta" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Comprobar envío" })).toBeNull();
  });
  it("impide sustituir una intención incierta por una segunda pregunta", async () => {
    mount(); await uncertainSend();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    fireEvent.change(screen.getByRole("textbox", { name: "Pregunta" }), { target: { value: "Otra pregunta" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(calls.filter(call => call.path.endsWith("/generations"))).toHaveLength(1);
    expect(screen.getByText("Pregunta incierta")).toBeVisible();
  });
  it("descarta la comprobación y pregunta incierta al cambiar de tenant sin Stop", async () => {
    const mounted = mount(); await uncertainSend();
    expect(await screen.findByRole("button", { name: "Comprobar envío" })).toBeVisible();
    await act(async () => mounted.change("other", "alice"));
    fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    expect(await screen.findByRole("textbox", { name: "Pregunta" })).toHaveValue("");
    expect(screen.queryByRole("button", { name: "Comprobar envío" })).toBeNull();
    expect(screen.queryByText("Pregunta incierta")).toBeNull();
    expect(calls.some(call => call.path.endsWith("/stop"))).toBe(false);
  });
  it("confirma una respuesta guardada con GET result e historial canónico sin generación", async () => {
    current = { ...current, state: "completed", result_url: "/assistant/conversations/saved/generations/op/result" };
    requests = [{ tenant_id: "t", user_id: "alice", conversation_id: "saved", question: "Pregunta guardada", operation: current }];
    messages = [{ id: "question", role: "user", content: "Pregunta guardada", metadata: {}, created_at: conversation.created_at },
      { id: "answer", role: "assistant", content: "Respuesta confirmada", metadata: {}, created_at: conversation.created_at }];
    mount(); await selectRequest();
    expect(await screen.findByText("Respuesta confirmada")).toBeVisible();
    await waitFor(() => expect(calls.filter(call => call.path.endsWith("/result"))).toHaveLength(1));
    expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
    expect(screen.queryByText(/provisional/)).toBeNull();
  });
  it("descarta una colección privada tardía tras cambiar de usuario", async () => {
    const ordinary = globalThis.fetch;
    let resolve: ((value: Response) => void) | undefined;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, options?: RequestInit) => {
      if (new URL(String(input), "http://test").pathname === "/assistant/requests") return new Promise<Response>(done => { resolve = done; });
      return ordinary(input, options);
    }));
    const mounted = mount(); await openHistory();
    await waitFor(() => expect(resolve).toBeDefined());
    await act(async () => mounted.change("t", "bob"));
    await act(async () => resolve?.(json({ items: requests })));
    fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    expect(await screen.findByRole("textbox", { name: "Pregunta" })).toHaveValue("");
    expect(screen.queryByText("Pregunta guardada")).toBeNull();
    expect(calls.some(call => call.path.endsWith("/stop") || call.path.endsWith("/events"))).toBe(false);
  });
});
