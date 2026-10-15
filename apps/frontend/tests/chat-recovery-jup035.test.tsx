import './chat-enabled-runtime';
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { Layout } from "../src/layouts/Layout";

const record = { id: "new", title: "Chat", tenant_id: "t", user_id: "alice",
  created_at: "2026-10-10T00:00:00Z", updated_at: "2026-10-10T00:00:00Z" };
const operation = { v: 2, operation_id: "op", question_id: "question", request_id: "request",
  state: "active", attempt_count: 1, current_attempt_id: "attempt", attempt_deadline: "2026-10-10T00:02:00Z",
  retry_at: null, result_url: null, wait_info: { reason: null, local_remaining_ms: 120000,
    provider_remaining_ms: 120000, automatic_until: null, retry_at: null, pause_reason: null } };
let calls: { path: string; method: string }[];
let postReader: ReadableStreamDefaultController<Uint8Array> | undefined;
let reconnectReader: ReadableStreamDefaultController<Uint8Array> | undefined;
const json = (value: unknown) => new Response(JSON.stringify(value), { headers: { "Content-Type": "application/json" } });
function event(reader: ReadableStreamDefaultController<Uint8Array> | undefined, type: string, values: Record<string, unknown>) {
  reader?.enqueue(new TextEncoder().encode(`event: ${type}\ndata: ${JSON.stringify({ v: 2, type, ...values })}\n\n`));
}
function mount() {
  function Session() { return <Outlet context={{ token: "synthetic-token", user: { id: "alice", full_name: "Alice", email: "alice@example.test", role: "member" },
    activeTenant: { id: "t", name: "Tenant", slug: "tenant", plan: "test" }, activeTenantId: "t" }} />; }
  const router = createMemoryRouter([{ path: "/", Component: Session, children: [{ Component: Layout,
    children: [{ path: "operational", element: <p>Vista</p> }] }] }], { initialEntries: ["/operational"] });
  return render(<RouterProvider router={router} />);
}
beforeEach(() => {
  calls = []; postReader = undefined; reconnectReader = undefined;
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
    const path = new URL(String(input), "http://test").pathname, method = options.method ?? "GET";
    calls.push({ path, method });
    if (path.endsWith("/generations") && method === "POST" || path.endsWith("/events") && method === "GET") {
      return new Response(new ReadableStream<Uint8Array>({ start(reader) {
        if (method === "POST") postReader = reader; else reconnectReader = reader;
      } }), { headers: { "Content-Type": "text/event-stream" } });
    }
    if (path === "/assistant/conversations") return json(record);
    return json({ conversation: record, messages: [] });
  }));
});
async function start() {
  mount();
  fireEvent.click(screen.getByRole("button", { name: "Abrir asistente" }));
  fireEvent.change(await screen.findByRole("textbox", { name: "Pregunta" }), { target: { value: "Pregunta recuperable" } });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
  await waitFor(() => expect(postReader).toBeDefined());
  await act(async () => {
    event(postReader, "started", { operation });
    event(postReader, "attempt_started", { operation_id: "op", attempt_id: "attempt", number: 1, revision: 2, seq: 0 });
  });
}
describe("Observación y reenganche del mismo intento JUP-035", () => {
  it("usa offsets UTF-16 para astrales y no pierde el incremento posterior", async () => {
    await start();
    await act(async () => {
      event(postReader, "delta", { operation_id: "op", attempt_id: "attempt", revision: 2, seq: 1, offset: 0, text: "🌍" });
      event(postReader, "delta", { operation_id: "op", attempt_id: "attempt", revision: 2, seq: 2, offset: 2, text: " listo" });
    });
    expect(await screen.findByText("🌍 listo")).toBeVisible();
    expect(calls.filter(call => call.method === "POST" && call.path.endsWith("/generations"))).toHaveLength(1);
  });
  it("tolera un delta idéntico duplicado sin repetir texto ni interrumpir los siguientes", async () => {
    await start();
    await act(async () => {
      const first = { operation_id: "op", attempt_id: "attempt", revision: 2, seq: 1, offset: 0, text: "Uno" };
      event(postReader, "delta", first); event(postReader, "delta", first);
      event(postReader, "delta", { operation_id: "op", attempt_id: "attempt", revision: 2, seq: 2, offset: 3, text: " dos" });
    });
    expect(await screen.findByText("Uno dos")).toBeVisible();
    expect(screen.queryByText("UnoUno")).toBeNull();
  });
  it("reengancha desde snapshot actual después de más64deltas y continúa sin otra generación", async () => {
    await start();
    await act(async () => { postReader?.close(); postReader = undefined; });
    expect(await screen.findByRole("alert")).toHaveTextContent("Conexión interrumpida");
    fireEvent.click(screen.getByRole("button", { name: "Recuperar conexión" }));
    await waitFor(() => expect(reconnectReader).toBeDefined());
    await act(async () => {
      event(reconnectReader, "started", { operation });
      event(reconnectReader, "snapshot", { operation_id: "op", attempt_id: "attempt", number: 1, revision: 2,
        seq: 100, offset: 200, text: "🌍".repeat(100) });
      event(reconnectReader, "delta", { operation_id: "op", attempt_id: "attempt", revision: 2, seq: 101, offset: 200, text: " listo" });
    });
    expect(await screen.findByText("🌍".repeat(100) + " listo")).toBeVisible();
    expect(calls.filter(call => call.method === "POST" && call.path.endsWith("/generations"))).toHaveLength(1);
    expect(calls.some(call => call.path.endsWith("/stop") || call.path.endsWith("/resume"))).toBe(false);
  });
  it("rechaza duplicados con contenido diferente sin mostrarlo como respuesta", async () => {
    await start();
    await act(async () => {
      event(postReader, "delta", { operation_id: "op", attempt_id: "attempt", revision: 2, seq: 1, offset: 0, text: "Uno" });
      event(postReader, "delta", { operation_id: "op", attempt_id: "attempt", revision: 2, seq: 1, offset: 0, text: "Otro" });
    });
    expect(await screen.findByRole("alert")).toHaveTextContent("Conexión interrumpida");
    expect(screen.queryByText("Otro")).toBeNull();
    expect(calls.some(call => call.path.endsWith("/stop"))).toBe(false);
  });
  it("descarta un delta tardío conocido del intento anterior y conserva el nuevo buffer", async () => {
    await start();
    await act(async () => {
      event(postReader, "delta", { operation_id: "op", attempt_id: "attempt", revision: 2, seq: 1, offset: 0, text: "Anterior" });
      event(postReader, "attempt_started", { operation_id: "op", attempt_id: "attempt-two", number: 2, revision: 3, seq: 0 });
      event(postReader, "delta", { operation_id: "op", attempt_id: "attempt", revision: 2, seq: 2, offset: 8, text: " tardío" });
      event(postReader, "delta", { operation_id: "op", attempt_id: "attempt-two", revision: 3, seq: 1, offset: 0, text: "Nuevo" });
    });
    expect(await screen.findByText("Nuevo")).toBeVisible();
    expect(screen.queryByText("Anterior tardío")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(calls.filter(call => call.path.endsWith("/generations") && call.method === "POST")).toHaveLength(1);
  });
  it("rechaza un snapshot cuyo offset no coincide con sus unidades UTF-16", async () => {
    await start();
    await act(async () => {
      event(postReader, "snapshot", { operation_id: "op", attempt_id: "attempt", revision: 2, number: 1,
        seq: 100, offset: 100, text: "🌍".repeat(100) });
    });
    expect(await screen.findByRole("alert")).toHaveTextContent("Conexión interrumpida");
    expect(screen.queryByText("🌍".repeat(100))).toBeNull();
  });
  it("rechaza un snapshot de otra operación sin sustituir el borrador propio", async () => {
    await start();
    await act(async () => {
      event(postReader, "snapshot", { operation_id: "foreign-operation", attempt_id: "attempt", revision: 2, number: 1,
        seq: 1, offset: 5, text: "Ajeno" });
    });
    expect(await screen.findByRole("alert")).toHaveTextContent("Conexión interrumpida");
    expect(screen.queryByText("Ajeno")).toBeNull();
    expect(calls.some(call => call.path.endsWith("/stop"))).toBe(false);
  });
});

// Chat fixtures freeze the new JUP-119 clock dependency; its HTTP/cache contract has separate tests.
vi.mock("../src/hooks/useReferenceDate", () => ({ useReferenceDate: () => ({ data: { reference_date: "2026-10-10", simulated: false } }) }));
