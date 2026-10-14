import './chat-enabled-runtime';
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { useState } from "react";
import { Layout } from "../src/layouts/Layout";

const record = (id = "old", user = "alice", tenant = "t") => ({ id, title: "Diálogo original", tenant_id: tenant, user_id: user,
  created_at: "2026-10-10T00:00:00Z", updated_at: "2026-10-10T00:00:00Z" });
const originals = [{ id: "q", role: "user", content: "Pregunta original sin reemplazo", metadata: {}, created_at: "2026-10-10T00:00:00Z" },
  { id: "a", role: "assistant", content: "Respuesta original sin reemplazo", metadata: {}, created_at: "2026-10-10T00:00:00Z" },
  { id: "alt", role: "assistant", content: "Alternativa histórica íntegra", metadata: {}, created_at: "2026-10-10T00:00:00Z" }];
const memory = () => ({ v: 2, scope: { tenant_id: "t", user_id: "alice", conversation_id: "old" }, available: true,
  reason: null, coverage: { processed_pairs: 2, pending_pairs: 2, recent_reserved: 4 },
  limitations: ["La memoria puede omitir matices y no acredita datos financieros."], artifact_id: "synthetic-artifact",
  queue: { reason: "cold", active: false, pending: false } });
let value: unknown;
let calls: { path: string; method: string; headers: Headers }[];
let resolveSummary: ((response: Response) => void) | undefined;
let delayed: boolean;
const json = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
function mount() {
  let change: ((next: { user: string; tenant: string }) => void) | undefined;
  function Session() {
    const [scope, update] = useState({ user: "alice", tenant: "t" }); change = update;
    return <Outlet context={{ token: "synthetic-token", user: { id: scope.user, full_name: "Alice", email: "alice@example.test", role: "member" },
      tenants: [{ id: scope.tenant, name: "Tenant", slug: "tenant", plan: "test" }], activeTenantId: scope.tenant,
      activeTenant: { id: scope.tenant, name: "Tenant", slug: "tenant", plan: "test" }, onTenantChange: () => {}, onLogout: () => {} }} />;
  }
  const router = createMemoryRouter([{ path: "/", Component: Session, children: [{ Component: Layout,
    children: [{ path: "operational", element: <p>Pantalla financiera</p> }] }] }], { initialEntries: ["/operational"] });
  render(<RouterProvider router={router} />);
  return (user: string, tenant: string) => change?.({ user, tenant });
}
async function select() {
  fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
  await reopenHistory();
}
async function reopenHistory() {
  fireEvent.click(await screen.findByRole("button", { name: "Historial" }));
  const dialog = await screen.findByRole("dialog", { name: "Historial de conversaciones" });
  fireEvent.click(await within(dialog).findByRole("button", { name: "Diálogo original" }));
  expect(await screen.findByText("Respuesta original sin reemplazo")).toBeVisible();
}
beforeEach(() => {
  calls = []; value = memory(); delayed = false; resolveSummary = undefined;
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
    const path = new URL(String(input), "http://test").pathname, method = options.method ?? "GET";
    calls.push({ path, method, headers: new Headers(options.headers) });
    if (path === "/assistant/conversations") return json({ items: [record()] });
    if (path === "/assistant/requests") return json({ items: [] });
    if (path === "/assistant/conversations/old") return json({ conversation: record(), messages: originals });
    if (path.endsWith("/summary")) return delayed ? new Promise<Response>(resolve => { resolveSummary = resolve; }) : json(value);
    return json({}, 404);
  }));
});
describe("Memoria derivada de diálogo JUP-035", () => {
  it.each([false, true])("bloquea atomico al final e ignora memoria anterior pendiente=%s", async stale => {
    const previous = globalThis.fetch;
    let reader: ReadableStreamDefaultController<Uint8Array> | undefined;
    let result: ((response: Response) => void) | undefined;
    let posts = 0;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
      const path = new URL(String(input), "http://test").pathname;
      if (path.endsWith("/generations") && options.method === "POST") {
        posts++;
        return new Response(new ReadableStream<Uint8Array>({ start(value) { reader = value; } }),
          { headers: { "Content-Type": "text/event-stream" } });
      }
      if (path.endsWith("/result")) return new Promise<Response>(resolve => { result = resolve; });
      return previous(input, options);
    }));
    const operation = { v: 2, operation_id: "op", question_id: "question", request_id: "request", state: "active",
      attempt_count: 1, current_attempt_id: "attempt", attempt_deadline: "2026-10-10T00:02:00Z", retry_at: null,
      result_url: null, wait_info: { reason: null, local_remaining_ms: 120000, provider_remaining_ms: 120000,
        automatic_until: null, retry_at: null, pause_reason: null } };
    const emit = (state: string) => reader?.enqueue(new TextEncoder().encode(`event: ${state === "completed" ? "final" : "started"}\ndata: ${JSON.stringify({
      v: 2, type: state === "completed" ? "final" : "started", operation: { ...operation, state } })}\n\n`));
    mount(); await select();
    const input = screen.getByRole("textbox", { name: "Pregunta" });
    fireEvent.change(input, { target: { value: "Primera pregunta" } });
    await waitFor(() => expect(screen.getByRole("button", { name: "Enviar" })).not.toBeDisabled());
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(reader).toBeDefined());
    await act(async () => { emit("active"); });
    fireEvent.change(input, { target: { value: "Borrador siguiente intacto" } });
    if (stale) {
      delayed = true;
      await reopenHistory();
      await waitFor(() => expect(resolveSummary).toBeDefined());
    }
    await act(async () => { emit("completed"); });
    await waitFor(() => expect(result).toBeDefined());
    expect(screen.queryByRole("button", { name: "Reintentar respuesta" })).toBeNull();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    if (stale) {
      delayed = false;
      await act(async () => { resolveSummary?.(json(memory())); });
      expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    }
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
    expect(input).toHaveValue("Borrador siguiente intacto");
    expect(posts).toBe(1);
    value = { ...memory(), queue: { state: "pending", reason: "queued", blocked: true, active: false, pending: true } };
    await act(async () => { result?.(json({ id: "a", content: originals[1].content, metadata: {} })); });
    await screen.findByText("Actualizando memoria");
    expect(input).toHaveValue("Borrador siguiente intacto");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    value = memory();
    await waitFor(() => expect(screen.getByRole("button", { name: "Enviar" })).not.toBeDisabled(), { timeout: 3500 });
    expect(posts).toBe(1);
  });
  it("conserva borrador editable y bloquea Enter y boton durante compresion durable", async () => {
    value = { ...memory(), queue: { reason: "running", active: true, pending: false,
      blocked: true, retryable: false, state: "running" } };
    mount(); await select();
    await screen.findByText("Comprimiendo contexto");
    const input = screen.getByRole("textbox", { name: "Pregunta" });
    fireEvent.change(input, { target: { value: "Borrador intacto" } });
    expect(input).toHaveValue("Borrador intacto");
    expect(input).not.toBeDisabled();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
    expect(input).toHaveValue("Borrador intacto");
    expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
    value = memory();
    expect(screen.queryByRole("button", { name: "Reintentar compresión" })).toBeNull();
    await waitFor(() => expect(screen.getByRole("button", { name: "Enviar" })).not.toBeDisabled(), { timeout: 3500 });
    expect(input).toHaveValue("Borrador intacto");
  });
  it("muestra recuperacion incierta y no libera envio por refrescar", async () => {
    value = { ...memory(), queue: { reason: "remote_uncertain", active: false, pending: true,
      blocked: true, retryable: true, state: "reconciling" } };
    mount(); await select();
    await screen.findByText("Recuperación de memoria pendiente");
    expect(screen.queryByRole("button", { name: "Reintentar compresión" })).toBeNull();
    await waitFor(() => expect(calls.filter(call => call.path.endsWith("/summary")).length).toBeGreaterThan(1), { timeout: 3500 });
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    expect(calls.filter(call => call.method === "POST")).toHaveLength(0);
  });
  it("oculta panel y controles de memoria conservando todos los originales y alternativas", async () => {
    mount(); await select();
    fireEvent.change(screen.getByRole("textbox", { name: "Pregunta" }), { target: { value: "Borrador" } });
    await waitFor(() => expect(screen.getByRole("button", { name: "Enviar" })).not.toBeDisabled());
    expect(screen.queryByRole("complementary", { name: "Memoria de conversación" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Actualizar memoria" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Recuperar memoria" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Reintentar compresión" })).toBeNull();
    expect(screen.queryByText(/pares procesados/)).toBeNull();
    expect(screen.queryByText(memory().limitations[0])).toBeNull();
    for (const message of originals) expect(screen.getByText(message.content)).toBeVisible();
    expect(calls.filter(call => call.path.endsWith("/summary"))).toHaveLength(1);
    expect(calls.every(call => call.method === "GET")).toBe(true);
    const call = calls.find(call => call.path.endsWith("/summary"))!;
    expect(call.headers.get("Authorization")).toBe("Bearer synthetic-token"); expect(call.headers.get("X-Tenant-Id")).toBe("t");
  });
  it("permite reintentar solo compresion fallida bloqueada y recuperable", async () => {
    const failed = { ...memory(), queue: { reason: "failed", state: "failed", blocked: true, retryable: false, active: false, pending: false } };
    value = failed;
    const previous = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
      if (String(input).endsWith("/summary/retry") && options.method === "POST") {
        calls.push({ path: "/assistant/conversations/old/summary/retry", method: "POST", headers: new Headers(options.headers) });
        value = memory();
        return json({});
      }
      return previous(input, options);
    }));
    mount(); await select();
    await screen.findByText("Actualización de memoria interrumpida");
    fireEvent.change(screen.getByRole("textbox", { name: "Pregunta" }), { target: { value: "Borrador" } });
    expect(screen.queryByRole("button", { name: "Reintentar compresión" })).toBeNull();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    value = { ...failed, queue: { ...failed.queue, retryable: true } };
    await reopenHistory();
    const retry = await screen.findByRole("button", { name: "Reintentar compresión" });
    expect(retry.closest('[role="log"]')).not.toBeNull();
    fireEvent.click(retry);
    await waitFor(() => expect(screen.getByRole("button", { name: "Enviar" })).not.toBeDisabled());
    expect(screen.queryByRole("button", { name: "Reintentar compresión" })).toBeNull();
    expect(calls.filter(call => call.method === "POST").map(call => call.path)).toEqual(["/assistant/conversations/old/summary/retry"]);
    for (const message of originals) expect(screen.getByText(message.content)).toBeVisible();
  });
  it("reabrir historial actualiza mediante GET sin sustituir originales ni iniciar generación", async () => {
    mount(); await select();
    fireEvent.change(screen.getByRole("textbox", { name: "Pregunta" }), { target: { value: "Borrador" } });
    await waitFor(() => expect(screen.getByRole("button", { name: "Enviar" })).not.toBeDisabled());
    value = { ...memory(), coverage: { processed_pairs: 4, pending_pairs: 0, recent_reserved: 4 } };
    await reopenHistory();
    await waitFor(() => expect(screen.getByRole("button", { name: "Enviar" })).not.toBeDisabled());
    expect(calls.filter(call => call.path.endsWith("/summary"))).toHaveLength(2);
    expect(calls.every(call => call.method === "GET")).toBe(true);
    for (const message of originals) expect(screen.getByText(message.content)).toBeVisible();
  });
  it.each(["tenant", "user", "conversation", "version", "negative", "fraction"])("rechaza memoria inválida %s y conserva originales", async defect => {
    const bad = memory();
    if (defect === "tenant") bad.scope.tenant_id = "foreign";
    if (defect === "user") bad.scope.user_id = "bob";
    if (defect === "conversation") bad.scope.conversation_id = "foreign";
    if (defect === "version") bad.v = 1;
    if (defect === "negative") bad.coverage.processed_pairs = -1;
    if (defect === "fraction") bad.coverage.pending_pairs = .5;
    bad.limitations = ["LIMITACIÓN PRIVADA AJENA"]; value = bad;
    mount(); await select();
    fireEvent.change(screen.getByRole("textbox", { name: "Pregunta" }), { target: { value: "Borrador" } });
    await waitFor(() => expect(calls.some(call => call.path.endsWith("/summary"))).toBe(true));
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    expect(screen.queryByText("LIMITACIÓN PRIVADA AJENA")).toBeNull();
    for (const message of originals) expect(screen.getByText(message.content)).toBeVisible();
  });
  it("un GET tardío del ámbito anterior no aparece al cambiar de usuario y tenant", async () => {
    delayed = true; const change = mount(); await select();
    await waitFor(() => expect(resolveSummary).toBeDefined());
    await act(async () => { change("bob", "other"); });
    await act(async () => { resolveSummary?.(json(memory())); });
    expect(screen.queryByText(memory().limitations[0])).toBeNull();
    expect(screen.queryByText("Respuesta original sin reemplazo")).toBeNull();
    expect(calls.every(call => call.method === "GET")).toBe(true);
  });
  it("abrir un borrador no consulta memoria ni inicia inferencia", async () => {
    mount(); fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
    await screen.findByRole("textbox", { name: "Pregunta" });
    expect(calls.some(call => call.path.endsWith("/summary") || call.method === "POST")).toBe(false);
  });
});

// Chat fixtures freeze the new JUP-119 clock dependency; its HTTP/cache contract has separate tests.
vi.mock("../src/hooks/useReferenceDate", () => ({ useReferenceDate: () => ({ data: { reference_date: "2026-10-10", simulated: false } }) }));
