import './chat-enabled-runtime';
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { useState } from "react";
import { Layout } from "../src/layouts/Layout";
import * as chatSession from "../src/components/chat/useChatSession";

const record = (id: string, title: string) => ({ id, title, tenant_id: "t", user_id: "alice",
  created_at: "2026-10-10T00:00:00Z", updated_at: "2026-10-10T00:00:00Z" });
const operation = { v: 2, operation_id: "op", question_id: "question", request_id: "request",
  state: "active", attempt_count: 1, current_attempt_id: "attempt", attempt_deadline: "2026-10-10T00:02:00Z",
  retry_at: null, prompt_version: "test-v2", status_url: "/assistant/conversations/new/generations/op",
  events_url: "/assistant/conversations/new/generations/op/events", result_url: null,
  wait_info: { reason: null, local_remaining_ms: 120000, provider_remaining_ms: 120000,
    automatic_until: null, retry_at: null, pause_reason: null } };

let calls: { path: string; method: string; headers: Headers; body?: Record<string, unknown> }[];
let controller: ReadableStreamDefaultController<Uint8Array> | undefined;
function event(type: string, value: Record<string, unknown>) {
  controller?.enqueue(new TextEncoder().encode(`event: ${type}\ndata: ${JSON.stringify({ v: 2, type, ...value })}\n\n`));
}
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status,
  headers: { "Content-Type": "application/json" } });

function mount(identity = "alice", tenant = "t") {
  let changeIdentity: ((next: { identity: string; tenant: string }) => void) | undefined;
  function Session() {
    const [scope, update] = useState({ identity, tenant });
    changeIdentity = update;
    return <Outlet context={{ token: "synthetic-token", user: { id: scope.identity, full_name: "Alice", email: "alice@example.test", role: "member" },
      tenants: [{ id: scope.tenant, name: "Tenant", slug: "tenant", plan: "test" }],
      activeTenant: { id: scope.tenant, name: "Tenant", slug: "tenant", plan: "test" }, activeTenantId: scope.tenant,
      onTenantChange: () => {}, onLogout: () => {} }} />;
  }
  const router = createMemoryRouter([{ path: "/", Component: Session, children: [{ Component: Layout,
    children: [{ path: "operational", element: <p>Pantalla financiera</p> }] }] }], { initialEntries: ["/operational"] });
  return { ...render(<RouterProvider router={router} />), router,
    changeScope: (nextIdentity: string, nextTenant: string) => changeIdentity?.({ identity: nextIdentity, tenant: nextTenant }) };
}

beforeEach(() => {
  calls = []; controller = undefined;
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
    const path = new URL(String(input), "http://test").pathname;
    const method = options.method ?? "GET";
    const body = typeof options.body === "string" ? JSON.parse(options.body) : undefined;
    calls.push({ path, method, headers: new Headers(options.headers), body });
    if (path.endsWith("/generations") && method === "POST") {
      return new Response(new ReadableStream<Uint8Array>({ start(value) { controller = value; } }),
        { headers: { "Content-Type": "text/event-stream; charset=utf-8" } });
    }
    if (path.endsWith("/stop")) {
      event("terminal", { operation_id: "op", revision: 3, operation: { ...operation, state: "cancelled" } });
      controller?.close(); controller = undefined;
      return json({ ...operation, state: "cancelled" });
    }
    if (path === "/assistant/conversations") {
      return method === "POST" ? json(record("new", "Nueva conversación"), 201)
        : json({ items: [record("old", "Historial privado")] });
    }
    if (path === "/assistant/conversations/old") return json({ conversation: record("old", "Historial privado"),
      messages: [{ id: "old-q", role: "user", content: "Pregunta histórica", metadata: {}, created_at: "2026-10-10T00:00:00Z" },
        { id: "old-a", role: "assistant", content: "Respuesta histórica", metadata: {}, created_at: "2026-10-10T00:00:00Z" }] });
    return json({ conversation: record("new", "Nueva conversación"), messages: [] });
  }));
});

describe("Panel conversacional propio JUP-035", () => {
  it("conserva preparación en transcript al adoptar draft, conversación y operación", async () => {
    const originalFetch = globalThis.fetch;
    let create!: () => void;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
      if (String(input).endsWith("/assistant/conversations") && options.method === "POST") {
        await new Promise<void>(resolve => { create = resolve; });
      }
      return originalFetch(input, options);
    }));
    mount();
    fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    fireEvent.change(await screen.findByRole("textbox", { name: "Pregunta" }), { target: { value: "Pregunta nueva" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    const activity = () => within(screen.getByRole("log", { name: "Mensajes" }))
      .getByRole("status", { name: "Actividad de la conversación" });
    expect(activity()).toHaveTextContent("Preparando contexto");
    await waitFor(() => expect(create).toBeTypeOf('function'));
    await act(async () => create());
    await waitFor(() => expect(controller).toBeDefined());
    expect(activity()).toHaveTextContent("Preparando contexto");
    await act(async () => event("started", { operation }));
    expect(Array.from(activity().querySelectorAll("li"), row => row.textContent)).toEqual([
      "Preparando contexto", "Esperando respuesta del LLM",
    ]);
    expect(activity().querySelectorAll(".chat-progress-shimmer")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Detener respuesta" }));
    await waitFor(() => expect(activity()).toHaveTextContent("Respuesta detenida"));
    expect(activity().querySelector(".chat-progress-shimmer")).toBeNull();
  });

  it("se abre junto a la pantalla autenticada y se puede ocultar", async () => {
    mount();
    expect(screen.queryByRole("link", { name: "Assistant" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    expect(await screen.findByRole("region", { name: "Asistente FinOps" })).toBeVisible();
    expect(screen.getByText("Pantalla financiera")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Ocultar asistente" }));
    expect(screen.queryByRole("region", { name: "Asistente FinOps" })).toBeNull();
    expect(calls.some(call => call.path.endsWith("/stop"))).toBe(false);
  });

  it("abre historial en overlay, selecciona el chat privado y cierra el overlay", async () => {
    mount();
    fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    fireEvent.click(await screen.findByRole("button", { name: "Historial" }));
    const dialog = await screen.findByRole("dialog", { name: "Historial de conversaciones" });
    fireEvent.click(await within(dialog).findByRole("button", { name: "Historial privado" }));
    expect(await screen.findByText("Respuesta histórica")).toBeVisible();
    expect(screen.getByText("Tú · Miembro")).toBeVisible();
    expect(screen.getByText("Pregunta histórica").closest(".chat-message-user")).not.toBeNull();
    expect(screen.getByText("Respuesta histórica").closest(".chat-message-assistant")).not.toBeNull();
    expect(document.querySelectorAll('time[datetime="2026-10-10T00:00:00Z"]')).toHaveLength(2);
    expect(screen.queryByRole("dialog", { name: "Historial de conversaciones" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Nueva conversación" }));
    await waitFor(() => expect(screen.queryByText("Respuesta histórica")).toBeNull());
  });

  it("envía captura preparada y muestra deltas; ocultar conserva el productor y Stop es explícito", async () => {
    mount();
    fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    const question = await screen.findByRole("textbox", { name: "Pregunta" });
    fireEvent.change(question, { target: { value: "¿Qué datos hay?" } });
    const getCount = calls.filter(call => call.method === "GET").length;
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(controller).toBeDefined());
    const sent = calls.find(call => call.path.endsWith("/generations"))!;
    expect(sent.headers.get("Authorization")).toBe("Bearer synthetic-token");
    expect(sent.headers.get("X-Tenant-Id")).toBe("t");
    expect(sent.body?.content).toBe("¿Qué datos hay?");
    expect(sent.body?.screen_context).toMatchObject({ schema_version: "2", route: "/operational", source: "no-adapter",
      identity: { tenant_id: "t", user_id: "alice" }, datasets: [] });
    expect(JSON.stringify(sent.body)).not.toContain("synthetic-token");
    expect(calls.filter(call => call.method === "GET")).toHaveLength(getCount);
    await act(async () => {
      event("started", { operation });
      event("attempt_started", { operation_id: "op", revision: 2, attempt_id: "attempt", number: 1, seq: 0 });
      event("delta", { operation_id: "op", revision: 2, attempt_id: "attempt", seq: 1, offset: 0, text: "Respuesta parcial" });
    });
    expect(await screen.findByText("Respuesta parcial")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Ocultar asistente" }));
    expect(calls.some(call => call.path.endsWith("/stop"))).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    expect(await screen.findByText("Respuesta parcial")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Detener respuesta" }));
    await waitFor(() => expect(calls.filter(call => call.path.endsWith("/stop"))).toHaveLength(1));
    expect(await screen.findByText("Respuesta detenida")).toBeVisible();
    expect(screen.queryByRole("button", { name: "Reintentar respuesta" })).toBeNull();
  });

  it("no activa chat sin identidad y tenant completos", () => {
    const router = createMemoryRouter([{ path: "/", Component: Layout }]);
    render(<RouterProvider router={router} />);
    expect(screen.queryByRole("button", { name: "Abrir asistente" })).toBeNull();
  });

  async function startQuestion(content = "Pregunta actual") {
    const mounted = mount();
    fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    fireEvent.change(await screen.findByRole("textbox", { name: "Pregunta" }), { target: { value: content } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(controller).toBeDefined());
    await act(async () => {
      event("started", { operation });
      event("attempt_started", { operation_id: "op", revision: 2, attempt_id: "attempt", number: 1, seq: 0 });
    });
    return mounted;
  }

  it("devuelve foco al control al ocultar por Escape sin detener", async () => {
    mount();
    const trigger = screen.getByRole("button", { name: "Abrir asistente" });
    expect(trigger).not.toHaveFocus();
    const focus = trigger.focus.bind(trigger);
    // Browsers ignore focus on display:none; jsdom otherwise masks this bug.
    vi.spyOn(trigger, "focus").mockImplementation(options => {
      if (trigger.style.display !== "none") focus(options);
    });
    fireEvent.click(trigger);
    const input = await screen.findByRole("textbox", { name: "Pregunta" });
    await waitFor(() => expect(input).toHaveFocus());
    fireEvent.keyDown(input, { key: "Escape" });
    expect(screen.getByRole("button", { name: "Abrir asistente" })).toHaveFocus();
    expect(calls.some(call => call.path.endsWith("/stop"))).toBe(false);
  });

  it("reinicia el borrador entre intentos sin concatenar respuestas", async () => {
    await startQuestion();
    await act(async () => {
      event("delta", { operation_id: "op", revision: 2, attempt_id: "attempt", seq: 1, offset: 0, text: "Borrador anterior" });
    });
    expect(await screen.findByText("Borrador anterior")).toBeVisible();
    await act(async () => {
      event("attempt_started", { operation_id: "op", revision: 3, attempt_id: "attempt-2", number: 2, seq: 0 });
      event("delta", { operation_id: "op", revision: 3, attempt_id: "attempt-2", seq: 1, offset: 0, text: "Nuevo borrador" });
    });
    expect(await screen.findByText("Nuevo borrador")).toBeVisible();
    expect(screen.queryByText("Borrador anterior")).toBeNull();
    expect(calls.filter(call => call.path.endsWith("/generations"))).toHaveLength(1);
  });

  it("situa actividad antes del parcial y del resultado propio persistido sin atribuirla al historico", async () => {
    const previous = globalThis.fetch;
    const msg = (id: string, role: string, content: string) => ({ id, role, content, metadata: {}, created_at: "2026-10-11T12:00:00Z" });
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
      const path = new URL(String(input), "http://test").pathname;
      if (path.endsWith("/result")) return json({ id: "result-own", content: "Resultado propio", metadata: {} });
      if (path === "/assistant/conversations/new") return json({ conversation: record("new", "Nueva conversación"), messages: [
        msg("historical-q", "user", "Pregunta anterior"), msg("historical-a", "assistant", "Respuesta anterior"),
        msg("question", "user", "Pregunta actual"), msg("alternative", "assistant", "Alternativa anterior"),
        msg("result-own", "assistant", "Resultado propio"),
      ] });
      return previous(input, options);
    }));
    await startQuestion();
    await act(async () => event("delta", { operation_id: "op", revision: 2, attempt_id: "attempt", seq: 1, offset: 0, text: "Parcial propio" }));
    await screen.findByText("Parcial propio");
    const activity = () => screen.getByRole("status", { name: "Actividad de la conversación" });
    const before = (left: Element, right: Element) => expect(left.compareDocumentPosition(right) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
    before(screen.getByText("Pregunta actual"), activity());
    before(activity(), screen.getByText("Parcial propio"));
    expect(screen.getAllByRole("status", { name: "Actividad de la conversación" })).toHaveLength(1);
    await act(async () => { event("final", { operation: { ...operation, state: "completed" } }); });
    await screen.findByText("Resultado propio");
    before(screen.getByText("Respuesta anterior"), activity());
    before(screen.getByText("Pregunta actual"), activity());
    before(screen.getByText("Alternativa anterior"), activity());
    before(activity(), screen.getByText("Resultado propio"));
    expect(screen.queryByText("Parcial propio")).toBeNull();
    expect(activity().querySelector(".chat-progress-shimmer")).toBeNull();
    expect(screen.getAllByRole("status", { name: "Actividad de la conversación" })).toHaveLength(1);
  });

  it("oculta solicitudes guardadas y conserva recuperacion interna del fallo historico", async () => {
    const previous = globalThis.fetch;
    const failed = { ...operation, question_id: "old-q", state: "failed" };
    const originalSession = chatSession.useChatSession;
    let current!: ReturnType<typeof originalSession>;
    const sessionSpy = vi.spyOn(chatSession, "useChatSession").mockImplementation((...args) => {
      current = originalSession(...args); return current;
    });
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
      const path = new URL(String(input), "http://test").pathname;
      if (path === "/assistant/requests") return json({ items: [{ tenant_id: "t", user_id: "alice", conversation_id: "old", question: "Pregunta histórica", operation: failed }] });
      if (path === "/assistant/conversations/old/generations/op") return json(failed);
      return previous(input, options);
    }));
    try {
      mount();
      fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
      fireEvent.click(screen.getByRole("button", { name: "Historial" }));
      await waitFor(() => expect(current.value.requests).toHaveLength(1));
      const history = screen.getByRole("dialog", { name: "Historial de conversaciones" });
      expect(within(history).queryAllByText(/Solicitudes guardadas|Pregunta histórica/i)).toHaveLength(0);
      fireEvent.click(within(history).getByRole("button", { name: "Cerrar historial" }));
      await act(async () => current.session.selectRequest(current.value.requests[0]));
      const retry = await screen.findByRole("button", { name: "Reintentar respuesta" });
      const activity = retry.closest('[role="status"]')!;
      expect(screen.getByText("Pregunta histórica").compareDocumentPosition(activity) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
      expect(activity.compareDocumentPosition(screen.getByText("Respuesta histórica")) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
      expect(screen.getAllByRole("status", { name: "Actividad de la conversación" })).toHaveLength(1);
      expect(screen.queryByText("Preparando contexto")).toBeNull();
    } finally { sessionSpy.mockRestore(); }
  });

  it.each([false, true])("reintento junto a fila failed, parcial=%s, respeta bloqueo y no duplica envio", async partial => {
    const previous = globalThis.fetch;
    let blocked = true;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
      const path = new URL(String(input), "http://test").pathname;
      if (path === "/assistant/conversations" && (!options.method || options.method === "GET"))
        return json({ items: [record("new", "Solicitud fallida")] });
      if (path.endsWith("/summary")) return json({ v: 2, scope: { tenant_id: "t", user_id: "alice", conversation_id: "new" },
        available: false, reason: null, artifact_id: null, limitations: [], coverage: { processed_pairs: 0, pending_pairs: 0, recent_reserved: 4 },
        queue: { reason: "test", active: blocked, pending: false, blocked, state: blocked ? "running" : "idle" } });
      return previous(input, options);
    }));
    await startQuestion();
    expect(screen.queryByRole("button", { name: "Reintentar respuesta" })).toBeNull();
    await act(async () => {
      if (partial) event("delta", { operation_id: "op", revision: 2, attempt_id: "attempt", seq: 1, offset: 0, text: "Texto incompleto" });
      event("terminal", { operation: { ...operation, state: "failed" } });
      controller?.close();
    });
    const retry = await screen.findByRole("button", { name: "Reintentar respuesta" });
    expect(retry).toHaveAttribute("title", "Reintentar respuesta");
    expect(retry).toHaveClass("h-8", "w-8");
    expect(retry.closest(".chat-activity-row")).toHaveTextContent("No se pudo completar la respuesta");
    expect(retry.previousElementSibling).toHaveTextContent("No se pudo completar la respuesta");
    expect(retry.closest(".chat-message-assistant")).toBeNull();
    expect(screen.getAllByText("No se pudo completar la respuesta")).toHaveLength(1);
    expect(screen.queryByText("No se pudo completar esta respuesta.")).toBeNull();
    if (partial) {
      expect(screen.getByText("Texto incompleto").closest(".chat-message-assistant")).toHaveTextContent("Asistente · provisional");
    }
    fireEvent.click(screen.getByRole("button", { name: "Historial" }));
    fireEvent.click(await screen.findByRole("button", { name: "Solicitud fallida" }));
    await screen.findByText("Comprimiendo contexto");
    expect(retry).toBeDisabled();
    fireEvent.click(retry);
    expect(calls.filter(call => call.path.endsWith("/generations"))).toHaveLength(1);
    blocked = false;
    await waitFor(() => expect(screen.getByRole("button", { name: "Reintentar respuesta" })).not.toBeDisabled(), { timeout: 3500 });
    const availableRetry = screen.getByRole("button", { name: "Reintentar respuesta" });
    expect(screen.getAllByRole("button", { name: "Reintentar respuesta" })).toHaveLength(1);
    fireEvent.click(availableRetry);
    fireEvent.click(availableRetry);
    await waitFor(() => expect(calls.filter(call => call.path.endsWith("/generations"))).toHaveLength(2));
    expect(calls.filter(call => call.path.endsWith("/generations"))[1].body).toMatchObject({ content: "Pregunta actual", retry_of_operation_id: "op" });
    expect(screen.queryByRole("button", { name: "Reintentar respuesta" })).toBeNull();
  });

  it("rechaza un salto de secuencia sin presentar el incremento como final", async () => {
    await startQuestion();
    await act(async () => {
      event("delta", { operation_id: "op", revision: 2, attempt_id: "attempt", seq: 2, offset: 0, text: "Texto fuera de secuencia" });
    });
    expect(await screen.findByRole("alert")).toHaveTextContent("Conexión interrumpida");
    expect(screen.queryByText("Texto fuera de secuencia")).toBeNull();
    expect(screen.queryByText("Respuesta completada")).toBeNull();
    expect(calls.some(call => call.path.endsWith("/stop"))).toBe(false);
  });

  it("no arrastra la lectura anterior cuando llegan deltas y permite volver abajo", async () => {
    await startQuestion();
    const log = screen.getByRole("log", { name: "Mensajes" });
    Object.defineProperty(log, "scrollHeight", { configurable: true, value: 1000 });
    Object.defineProperty(log, "clientHeight", { configurable: true, value: 200 });
    log.scrollTop = 10;
    fireEvent.scroll(log);
    await act(async () => {
      event("delta", { operation_id: "op", revision: 2, attempt_id: "attempt", seq: 1, offset: 0, text: "Mientras lees arriba" });
    });
    expect(await screen.findByText("Mientras lees arriba")).toBeVisible();
    expect(log.scrollTop).toBe(10);
    fireEvent.click(screen.getByRole("button", { name: "Volver al final" }));
    expect(log.scrollTop).toBe(1000);
    expect(screen.queryByRole("button", { name: "Volver al final" })).toBeNull();
  });

  it.each([["bob", "t"], ["alice", "other"]])("limpia al cambiar scope a %s/%s y descarta callbacks tardíos sin Stop", async (identity, tenant) => {
    const mounted = await startQuestion();
    await act(async () => {
      event("delta", { operation_id: "op", revision: 2, attempt_id: "attempt", seq: 1, offset: 0, text: "Contenido privado anterior" });
    });
    expect(await screen.findByText("Contenido privado anterior")).toBeVisible();
    const oldReader = controller;
    await act(async () => mounted.changeScope(identity, tenant));
    expect(screen.queryByText("Contenido privado anterior")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    expect(await screen.findByRole("textbox", { name: "Pregunta" })).toHaveValue("");
    // A transport may already have buffered a callback when its observer leaves.
    try { oldReader?.enqueue(new TextEncoder().encode('event: delta\ndata: {"v":2,"type":"delta","operation_id":"op","attempt_id":"attempt","revision":2,"seq":2,"offset":26,"text":"Privado tardío"}\n\n')); } catch { /* Reader was cancelled. */ }
    await act(async () => {});
    expect(screen.queryByText("Privado tardío")).toBeNull();
    expect(calls.some(call => call.path.endsWith("/stop"))).toBe(false);
  });

  it("un cierre sin final válido anuncia interrupción y conserva la pregunta recuperable", async () => {
    await startQuestion();
    await act(async () => controller?.close());
    expect(await screen.findByRole("alert")).toHaveTextContent("La solicitud sigue guardada");
    expect(screen.getByText("Pregunta actual")).toBeVisible();
    expect(screen.queryByText("Respuesta completada")).toBeNull();
    expect(calls.some(call => call.path.endsWith("/stop"))).toBe(false);
  });
});

// Chat fixtures freeze the new JUP-119 clock dependency; its HTTP/cache contract has separate tests.
vi.mock("../src/hooks/useReferenceDate", () => ({ useReferenceDate: () => ({ data: { reference_date: "2026-10-10", simulated: false } }) }));
