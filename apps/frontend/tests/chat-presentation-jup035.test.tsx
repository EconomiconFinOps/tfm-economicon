import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatProgress as ActivityRows, useChatActivity, MessageTimestamp, relativeMessageTime, userRoleLabel } from "../src/components/chat/ChatPresentation";
import type { ChatCell } from "../src/components/chat/useChatSession";
import type { ChatOperation } from "../src/services/chat";

const cell: ChatCell = { id: "chat", title: "Chat", messages: [], operation: null, question: "", partial: "", attempt: null,
  sequence: 0, revision: 0, starting: false, stopping: false, loading: false, notice: "", recovering: false,
  uncertain: false, memory: null, memoryLoading: false, memoryError: false };
const operation: ChatOperation = { v: 2, operation_id: "op", question_id: "q", request_id: "r", state: "active", attempt_count: 1,
  current_attempt_id: "a", attempt_deadline: null, retry_at: null, result_url: null,
  wait_info: { reason: null, local_remaining_ms: 120000, provider_remaining_ms: 120000, automatic_until: null, retry_at: null, pause_reason: null } };

afterEach(() => vi.useRealTimers());

function ChatProgress({ cell }: { cell: ChatCell }) {
  const activity = useChatActivity(cell, { [cell.id]: cell });
  return <ActivityRows key={cell.id} activity={activity} />;
}

describe("Presentación del chat", () => {
  it("refresca la fecha relativa española conservando fecha real y tooltip absoluto", () => {
    vi.useFakeTimers();vi.setSystemTime(new Date("2026-10-11T12:00:00Z"));
    const createdAt = "2026-10-11T11:59:00Z";
    const { unmount } = render(<MessageTimestamp createdAt={createdAt} />);
    const time = screen.getByText("hace 1 minuto");
    expect(time).toHaveAttribute("datetime", createdAt);
    expect(time.title).toMatch(/11 de octubre de 2026/);
    expect(time.closest('[aria-live="polite"]')).toBeNull();
    act(() => vi.advanceTimersByTime(60000));
    expect(screen.getByText("hace 2 minutos")).toBeVisible();
    unmount();expect(vi.getTimerCount()).toBe(0);
  });

  it("no inventa fecha provisional ni rol profesional", () => {
    const { container, rerender } = render(<MessageTimestamp createdAt={undefined} />);
    expect(container.querySelector("time")).toBeNull();
    rerender(<MessageTimestamp createdAt="invalid" />);
    expect(container.querySelector("time")).toBeNull();
    expect(userRoleLabel()).toBe("");expect(userRoleLabel("member")).toBe("Miembro");
    expect(userRoleLabel("admin")).toBe("Administrador");expect(userRoleLabel("professional")).toBe("Profesional");
    expect(relativeMessageTime("2026-10-12T00:00:00Z", Date.parse("2026-10-11T00:00:00Z"))).toBe("ahora");
  });

  it("solo cambia etapas al recibir estado real y no por temporizador", () => {
    vi.useFakeTimers();
    const { rerender } = render(<ChatProgress cell={{ ...cell, starting: true }} />);
    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("Preparando contexto");
    act(() => vi.advanceTimersByTime(60000));
    expect(status).toHaveTextContent("Preparando contexto");
    rerender(<ChatProgress cell={{ ...cell, operation }} />);
    expect(status).toHaveTextContent("Esperando respuesta del LLM");
    rerender(<ChatProgress cell={{ ...cell, operation, partial: "Texto" }} />);
    expect(status).toHaveTextContent("Recibiendo respuesta");
    expect(Array.from(status.querySelectorAll("li"), row => row.textContent)).toEqual([
      "Preparando contexto", "Esperando respuesta del LLM", "Recibiendo respuesta",
    ]);
    expect(status.querySelectorAll(".chat-progress-shimmer")).toHaveLength(1);
    expect(status.querySelector(".chat-progress-shimmer")).toHaveTextContent("Recibiendo respuesta");
    for (const state of ["paused", "failed", "cancelled", "completed"] as const) {
      rerender(<ChatProgress cell={{ ...cell, operation: { ...operation, state } }} />);
      expect(status.querySelector(".chat-progress-shimmer")).toBeNull();
    }
  });

  it("finaliza sin fila de exito conservando etapas estaticas y no reconstruye completed", () => {
    const completed = { ...cell, operation: { ...operation, state: "completed" as const } };
    const { rerender, unmount, container } = render(<ChatProgress cell={{ ...cell, operation, partial: "Texto" }} />);
    expect(container.querySelector(".chat-progress-shimmer")).not.toBeNull();
    rerender(<ChatProgress cell={completed} />);
    expect(screen.getAllByRole("listitem").map(row => row.textContent)).toEqual(["Recibiendo respuesta"]);
    expect(container.querySelector(".chat-progress-shimmer")).toBeNull();
    expect(container.querySelector(".chat-activity-spinner")).toBeNull();
    expect(screen.queryByText("Respuesta lista")).toBeNull();
    unmount();
    const restored = render(<ChatProgress cell={completed} />);
    expect(restored.container).toBeEmptyDOMElement();
  });

  it("no reconstruye etapas al restaurar y limpia observaciones al cambiar conversación u operación", () => {
    const { rerender } = render(<ChatProgress cell={cell} />);
    expect(screen.queryByRole("status")).toBeNull();
    rerender(<ChatProgress cell={{ ...cell, operation }} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(screen.queryByText("Preparando contexto")).toBeNull();
    rerender(<ChatProgress cell={{ ...cell, operation, partial: "Texto" }} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    rerender(<ChatProgress cell={{ ...cell, operation: { ...operation, operation_id: "other" } }} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    rerender(<ChatProgress cell={{ ...cell, id: "other-chat" }} />);
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("prioriza compresión acreditada, distingue espera y no duplica región viva", () => {
    const memory = { v: 2 as const, scope: { tenant_id: "t", user_id: "u", conversation_id: "chat" }, available: false,
      reason: null, coverage: { processed_pairs: 0, pending_pairs: 2, recent_reserved: 4 }, limitations: [], artifact_id: null,
      queue: { reason: "queued", active: false, pending: true, blocked: true, state: "pending" as const } };
    const { rerender } = render(<ChatProgress cell={{ ...cell, operation: { ...operation, state: "completed" }, memory }} />);
    expect(screen.getByRole("status")).toHaveTextContent("Actualizando memoria");
    rerender(<ChatProgress cell={{ ...cell, memory: { ...memory, queue: { ...memory.queue, state: "running", active: true } } }} />);
    expect(screen.getByRole("status")).toHaveTextContent("Comprimiendo contexto");
    expect(screen.getAllByRole("status")).toHaveLength(1);
    rerender(<ChatProgress cell={{ ...cell, operation: { ...operation, state: "waiting", wait_info: { ...operation.wait_info, reason: "local_capacity" } } }} />);
    expect(screen.getByRole("status")).toHaveTextContent("Esperando capacidad disponible");
  });
});
