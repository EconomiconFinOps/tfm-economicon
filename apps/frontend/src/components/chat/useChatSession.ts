import { fetchChatCapabilities, isChatMemory, type ChatMemory } from "../../services/chat";
import { useEffect, useState, useSyncExternalStore } from "react";
import { chatJson, chatPath, generateChat, isChatOperation, isSavedChatRequest, type ChatOperation, type ChatScope, type GenerationPayload, type SavedChatRequest } from "../../services/chat";
import { ApiError, fetchChatResponse, getSessionGeneration } from "../../services/api";
import { readChatEvents, type ChatFrame } from "../../services/chatStream";
import { PreparedScreen } from "../../services/screenCapture";
import type { ConversationRecord, MessageRecord } from "../../services/contracts";

export interface ChatCell {
  deleting?: boolean;
  manualTitle?: boolean;
  result?: { operationId: string; messageId: string };
  memory: ChatMemory | null; memoryLoading: boolean; memoryError: boolean;
  id: string; title: string; messages: MessageRecord[]; operation: ChatOperation | null;
  question: string; partial: string; attempt: string | null; sequence: number; revision: number;
  starting: boolean; stopping: boolean; loading: boolean; notice: string; recovering: boolean; uncertain: boolean;
}
interface Snapshot { selected: string; cells: Record<string, ChatCell>; history: ConversationRecord[]; historyLoading: boolean; historyError: boolean;
  requests: SavedChatRequest[]; requestsLoading: boolean; requestsError: boolean }
const emptyCell = (id: string): ChatCell => ({ memory: null, memoryLoading: false, memoryError: false, id, title: "Nueva conversación", messages: [], operation: null,
  question: "", partial: "", attempt: null, sequence: 0, revision: 0, starting: false, stopping: false, loading: false, notice: "", recovering: false, uncertain: false });
const openStates = ["reserved", "active", "waiting", "paused"];
export const normalizeConversationTitle = (title: string) => title.replace(/\s+/gu, " ").trim();
export const isOpen = (cell: ChatCell) => cell.starting || !!cell.operation && openStates.includes(cell.operation.state);
export const memoryBlocked = (cell: ChatCell) => cell.deleting === true || !cell.id.startsWith("draft-") &&
  (cell.memoryLoading || cell.memoryError || !cell.memory || cell.memory.queue.blocked === true
    || cell.memory.queue.active || cell.memory.queue.pending);

class ChatSession {
  private alive = true;
  private generation = getSessionGeneration();
  private listeners = new Set<() => void>();
  private readers = new Map<AbortController, string | undefined>();
  private timers = new Map<ReturnType<typeof setTimeout>, string>();
  private previousAttempts = new Map<string, Set<string>>();
  private intents = new Map<string, GenerationPayload>();
  private memoryEpoch = new Map<string, number>();
  private titleRevision = 0;
  private renamedTitles = new Map<string, { revision: number; record: ConversationRecord }>();
  private renaming = new Set<string>();
  private deleting = new Set<string>();
  private deleted = new Set<string>();
  readonly screen: PreparedScreen;
  private value: Snapshot;
  constructor(readonly scope: ChatScope, prepared?: PreparedScreen | null) {
    const selected = `draft-${crypto.randomUUID()}`;
    this.value = { selected, cells: { [selected]: emptyCell(selected) }, history: [], historyLoading: false, historyError: false,
      requests: [], requestsLoading: false, requestsError: false };
    this.screen = prepared ?? new PreparedScreen(scope.tenantId, scope.userId);
  }
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  snapshot = () => this.value;
  valid = () => this.alive && this.generation === getSessionGeneration();
  private update(next: Snapshot) { if (!this.valid()) return; this.value = next; for (const listener of this.listeners) listener(); }
  private patch(id: string, changes: Partial<ChatCell>) {
    const current = this.value.cells[id];
    if (!current) return;
    if (changes.operation?.state === "completed" && (current.operation?.state !== "completed"
        || current.operation.operation_id !== changes.operation.operation_id)) {
      this.memoryEpoch.set(id, (this.memoryEpoch.get(id) ?? 0) + 1);
      changes = { ...changes, memory: null, memoryLoading: false, memoryError: false };
    }
    this.update({ ...this.value, cells: { ...this.value.cells, [id]: { ...current, ...changes } } });
  }
  attach() { this.alive = true; }
  detach() {
    this.alive = false;
    for (const reader of this.readers.keys()) reader.abort();
    for (const timer of this.timers.keys()) clearTimeout(timer);
    this.readers.clear(); this.timers.clear(); this.previousAttempts.clear(); this.intents.clear(); this.screen.clear();
  }
  private controller(id?: string) { const value = new AbortController(); this.readers.set(value, id); return value; }
  private async json<T>(path: string, method = "GET", body?: unknown): Promise<T> {
    const match = /^\/assistant\/conversations\/([^/]+)(?:\/|$)/.exec(path);
    const id = match ? decodeURIComponent(match[1]) : undefined;
    if (id && this.deleted.has(id)) throw new Error("conversation_deleted");
    const controller = this.controller(id);
    try {
      const result = await chatJson<T>(this.scope, path, controller.signal, method, body);
      if (id && this.deleted.has(id)) throw new Error("conversation_deleted");
      return result;
    }
    finally { this.readers.delete(controller); }
  }
  newConversation = () => {
    const id = `draft-${crypto.randomUUID()}`;
    this.update({ ...this.value, selected: id, cells: { ...this.value.cells, [id]: emptyCell(id) } });
  };
  loadHistory = async () => {
    const titleRevision = this.titleRevision;
    this.update({ ...this.value, historyLoading: true, historyError: false });
    const requests = this.loadRequests();
    try {
      const collection = await this.json<{ items: ConversationRecord[] }>("/assistant/conversations");
      if (!Array.isArray(collection.items) || collection.items.some(item => item.tenant_id !== this.scope.tenantId || item.user_id !== this.scope.userId)) throw new Error("scope_invalid");
      // A list request started before a rename must not restore its old title.
      const history = collection.items.filter(item => !this.deleted.has(item.id)).map(item => {
        const renamed = this.renamedTitles.get(item.id);
        return renamed && renamed.revision > titleRevision ? renamed.record : item;
      });
      this.update({ ...this.value, history, historyLoading: false });
    } catch { this.update({ ...this.value, historyLoading: false, historyError: true }); }
    await requests;
  };
  private async loadRequests() {
    this.update({ ...this.value, requestsLoading: true, requestsError: false });
    try {
      const collection = await this.json<{ items: unknown[] }>("/assistant/requests");
      if (!Array.isArray(collection.items) || !collection.items.every(item => isSavedChatRequest(item, this.scope))) throw new Error("scope_invalid");
      const requests = (collection.items as SavedChatRequest[]).filter(item => !this.deleted.has(item.conversation_id)).map(item => ({ tenant_id: item.tenant_id, user_id: item.user_id,
        conversation_id: item.conversation_id, question: item.question, operation: item.operation }));
      this.update({ ...this.value, requests, requestsLoading: false });
    } catch { this.update({ ...this.value, requests: [], requestsLoading: false, requestsError: true }); }
  }
  select = async (record: ConversationRecord) => {
    if (!this.valid() || this.deleted.has(record.id) || record.tenant_id !== this.scope.tenantId || record.user_id !== this.scope.userId) return;
    const cell = this.value.cells[record.id];
    this.update({ ...this.value, selected: record.id, cells: { ...this.value.cells,
      [record.id]: cell ?? { ...emptyCell(record.id), title: record.title, loading: true } } });
    if (cell) { void this.loadMemory(record.id); return; }
    try {
      const detail = await this.json<{ conversation: ConversationRecord; messages: MessageRecord[] }>(`/assistant/conversations/${encodeURIComponent(record.id)}`);
      if (detail.conversation.id !== record.id || detail.conversation.tenant_id !== this.scope.tenantId || detail.conversation.user_id !== this.scope.userId || !Array.isArray(detail.messages)) throw new Error("scope_invalid");
      this.patch(record.id, { messages: detail.messages, loading: false });
      void this.loadMemory(record.id);
    } catch { this.patch(record.id, { loading: false, notice: "No se pudo cargar esta conversación." }); }
  };
  loadMemory = async (id = this.value.selected) => {
    if (!this.valid() || id.startsWith("draft-") || !this.value.cells[id] || this.value.cells[id].memoryLoading) return;
    const epoch = (this.memoryEpoch.get(id) ?? 0) + 1;
    this.memoryEpoch.set(id, epoch);
    this.patch(id, { memoryLoading: true, memoryError: false });
    try {
      const value: unknown = await this.json(`/assistant/conversations/${encodeURIComponent(id)}/summary`);
      if (!this.valid() || this.memoryEpoch.get(id) !== epoch) return;
      if (!isChatMemory(value, this.scope, id)) throw new Error("summary_scope_invalid");
      this.patch(id, { memory: value, memoryLoading: false, memoryError: false });
      if (value.queue.blocked && value.queue.state !== "failed") {
        const timer = setTimeout(() => { this.timers.delete(timer); if (this.valid()) void this.loadMemory(id); }, 2000);
        this.timers.set(timer, id);
      }
    } catch {
      if (this.memoryEpoch.get(id) === epoch) this.patch(id, { memoryLoading: false, memoryError: true });
    }
  };
  rename = async (id: string, input: string): Promise<void> => {
    const title = normalizeConversationTitle(input);
    if (!title || Array.from(title).length > 60) throw new Error("title_invalid");
    if (!this.valid() || this.renaming.has(id) || this.deleting.has(id) || this.deleted.has(id)) throw new Error("rename_unavailable");
    if (id.startsWith("draft-")) {
      if (!this.value.cells[id] || this.value.cells[id].starting) throw new Error("rename_unavailable");
      this.patch(id, { title, manualTitle: true });
      return;
    }
    this.renaming.add(id);
    try {
      const record = await this.json<ConversationRecord>(`/assistant/conversations/${encodeURIComponent(id)}`, "PATCH", { title });
      if (!this.valid()) throw new Error("session_expired");
      if (record.id !== id || record.tenant_id !== this.scope.tenantId || record.user_id !== this.scope.userId
          || record.title !== title || typeof record.updated_at !== "string" || typeof record.created_at !== "string") throw new Error("scope_invalid");
      this.renamedTitles.set(id, { revision: ++this.titleRevision, record });
      const cell = this.value.cells[id];
      this.update({ ...this.value,
        cells: cell ? { ...this.value.cells, [id]: { ...cell, title, manualTitle: true } } : this.value.cells,
        history: this.value.history.map(item => item.id === id ? record : item) });
    } finally { this.renaming.delete(id); }
  };
  deletionBlock = (id: string): string | null => {
    const cell = this.value.cells[id];
    const queue = cell?.memory?.queue;
    if (cell && (isOpen(cell) || cell.uncertain) || queue && (queue.active || queue.pending
        || queue.state === "pending" || queue.state === "running" || queue.state === "reconciling")
        || this.value.requests.some(request => request.conversation_id === id && openStates.includes(request.operation.state))) {
      return "No se puede eliminar mientras haya una respuesta o compresión pendiente. Espera a que termine o resuelve su estado.";
    }
    return null;
  };
  remove = async (id: string): Promise<void> => {
    if (!this.valid() || id.startsWith("draft-") || this.deleted.has(id) || this.deleting.has(id)) throw new Error("La conversación no está disponible.");
    const blocked = this.deletionBlock(id);
    if (blocked) throw new Error(blocked);
    this.deleting.add(id);
    this.patch(id, { deleting: true });
    const controller = this.controller(id);
    try {
      const response = await fetchChatResponse(`/assistant/conversations/${encodeURIComponent(id)}`, {
        token: this.scope.token, tenantId: this.scope.tenantId, signal: controller.signal, method: "DELETE" });
      if (response.status !== 204 || !this.valid()) throw new Error("delete_unconfirmed");
      // Tombstones are session-local: old readers/lists cannot recreate a deleted cell.
      this.deleted.add(id);
      for (const [reader, owner] of this.readers) if (owner === id && reader !== controller) reader.abort();
      for (const [timer, owner] of this.timers) if (owner === id) { clearTimeout(timer); this.timers.delete(timer); }
      this.memoryEpoch.delete(id); this.previousAttempts.delete(id); this.intents.delete(id); this.renamedTitles.delete(id);
      const cells = { ...this.value.cells }; delete cells[id];
      const selected = this.value.selected === id ? `draft-${crypto.randomUUID()}` : this.value.selected;
      if (!cells[selected]) cells[selected] = emptyCell(selected);
      this.update({ ...this.value, selected, cells, history: this.value.history.filter(item => item.id !== id),
        requests: this.value.requests.filter(item => item.conversation_id !== id) });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        throw new Error("No se puede eliminar mientras haya una respuesta o compresión pendiente. Espera a que termine o resuelve su estado.");
      }
      throw new Error("No se pudo confirmar la eliminación. Revisa el historial antes de reintentar.");
    } finally { this.readers.delete(controller); this.deleting.delete(id); this.patch(id, { deleting: false }); }
  };
  retryMemory = async () => {
    const id = this.value.selected;
    if (!this.valid() || !this.value.cells[id]?.memory?.queue.retryable) return;
    try {
      await this.json(`/assistant/conversations/${encodeURIComponent(id)}/summary/retry`, "POST");
      await this.loadMemory(id);
    } catch { this.patch(id, { notice: "No se pudo recuperar la memoria. Se conserva el historial." }); }
  };
  selectRequest = async (request: SavedChatRequest) => {
    if (!this.valid() || !isSavedChatRequest(request, this.scope) || this.deleted.has(request.conversation_id)) return;
    const id = request.conversation_id;
    const existing = this.value.cells[id];
    if (existing && isOpen(existing) && existing.operation?.operation_id !== request.operation.operation_id) {
      this.update({ ...this.value, selected: id });
      this.patch(id, { notice: "Hay otra solicitud en curso en esta conversación. Consulta su estado antes de cambiar." });
      return;
    }
    const record = this.value.history.find(item => item.id === id) ?? { id, tenant_id: this.scope.tenantId, user_id: this.scope.userId,
      title: request.question.slice(0, 64), created_at: "", updated_at: "" };
    await this.select(record);
    if (!this.valid() || this.deleted.has(id)) return;
    this.patch(id, { question: request.question, operation: request.operation, partial: "", notice: "", uncertain: false });
    try {
      const operation: unknown = await this.json(chatPath(id, request.operation.operation_id));
      if (!isChatOperation(operation) || operation.operation_id !== request.operation.operation_id) throw new Error("operation_invalid");
      await this.receive(id, { v: 2, type: "started", operation });
      if (!this.valid()) return;
      if (operation.state === "active") await this.reconnect(id);
      else if (operation.state === "waiting" || operation.state === "reserved") this.poll(id);
    } catch { this.patch(id, { notice: "No se pudo consultar la solicitud guardada." }); }
  };
  send = async (content: string, route: string, retry = false) => {
    let id = this.value.selected;
    let cell = this.value.cells[id];
    if (!this.valid() || isOpen(cell) || memoryBlocked(cell) || cell.loading || cell.uncertain || !content.trim()) return;
    let capture;
    try { capture = this.screen.freeze(route); }
    catch { this.patch(id, { notice: "La pantalla aún no está preparada o supera el tamaño permitido." }); return; }
    if (new TextEncoder().encode(content).length > 16384) { this.patch(id, { notice: "La pregunta supera el tamaño permitido." }); return; }
    const retryOf = retry ? cell.operation?.operation_id : undefined;
    this.patch(id, { starting: true, operation: null, question: content, partial: "", attempt: null, sequence: 0, revision: 0, notice: "" });
    const payload: GenerationPayload = Object.freeze({ request_id: crypto.randomUUID(), content, screen_context: capture,
      ...(retryOf ? { retry_of_operation_id: retryOf } : {}) });
    const availabilityController = this.controller(id);
    try {
      const capability = await fetchChatCapabilities(this.scope, availabilityController.signal);
      if (!this.valid() || this.deleted.has(id)) return;
      if (!capability.chat_enabled) {
        this.patch(id, { starting: false, notice: 'El asistente no está activado.' });
        return;
      }
    } catch {
      this.patch(id, { starting: false, notice: 'No se pudo comprobar la disponibilidad del asistente.' });
      return;
    } finally { this.readers.delete(availabilityController); }
    try {
      if (id.startsWith("draft-")) {
        const title = cell.manualTitle ? cell.title : Array.from(normalizeConversationTitle(content)).slice(0, 60).join("");
        const record = await this.json<ConversationRecord>("/assistant/conversations", "POST", { title });
        if (!this.valid()) return;
        if (record.tenant_id !== this.scope.tenantId || record.user_id !== this.scope.userId) throw new Error("scope_invalid");
        const priorId = id;
        id = record.id;
        cell = { ...this.value.cells[priorId], id, title: record.title };
        const cells = { ...this.value.cells }; delete cells[priorId]; cells[id] = cell;
        this.update({ ...this.value, cells, selected: this.value.selected === priorId ? id : this.value.selected });
      }
      this.intents.set(id, payload);
      await this.submit(id, payload);
    } catch {
      this.patch(id, { starting: false, uncertain: true, notice: "No se pudo confirmar la conversación. Comprueba la solicitud en el historial antes de repetirla." });
    }
  };
  canCheckSend = (id: string) => this.intents.has(id) && this.value.cells[id]?.uncertain === true;
  checkSend = async () => {
    const id = this.value.selected, cell = this.value.cells[id], payload = this.intents.get(id);
    if (!this.valid() || !payload || !cell.uncertain || cell.starting) return;
    await this.submit(id, payload);
  };
  private async submit(id: string, payload: GenerationPayload) {
    const controller = this.controller(id);
    this.patch(id, { starting: true, notice: "" });
    try {
      await generateChat(this.scope, id, payload, controller.signal, frame => this.receive(id, frame));
      if (!this.valid() || this.deleted.has(id)) return;
      const current = this.value.cells[id];
      if (current.operation?.state === "waiting") this.poll(id);
      else if (isOpen(current) && current.operation?.state !== "paused") this.patch(id, { notice: "Conexión interrumpida. La solicitud sigue guardada." });
      else if (!current.operation) this.patch(id, { uncertain: true, notice: "No se pudo confirmar el envío. Comprueba la solicitud antes de repetirla." });
    } catch {
      if (!controller.signal.aborted) this.patch(id, { uncertain: !this.value.cells[id]?.operation,
        notice: "Conexión interrumpida. Comprueba la solicitud antes de repetirla." });
    } finally { this.readers.delete(controller); this.patch(id, { starting: false }); }
  }
  private async receive(id: string, frame: ChatFrame) {
    if (!this.valid()) return;
    let cell = this.value.cells[id];
    if (!cell) return;
    if (frame.operation !== undefined) {
      if (!isChatOperation(frame.operation)) throw new Error("operation_invalid");
      if (cell.operation && frame.operation.operation_id !== cell.operation.operation_id) throw new Error("operation_mismatch");
      if (cell.operation && frame.operation.attempt_count < cell.operation.attempt_count) return;
      if (cell.operation && ["completed", "failed", "cancelled"].includes(cell.operation.state)
          && !["completed", "failed", "cancelled"].includes(frame.operation.state)) return;
      this.intents.delete(id);
      this.patch(id, { operation: frame.operation, starting: false, uncertain: false });
      cell = this.value.cells[id];
    }
    if (frame.operation_id !== undefined && frame.operation_id !== cell.operation?.operation_id) throw new Error("operation_mismatch");
    if (frame.type === "attempt_started") {
      if (typeof frame.attempt_id !== "string" || !Number.isSafeInteger(frame.number) || Number(frame.number) < 1 || Number(frame.number) > 4) throw new Error("attempt_invalid");
      if (Number(frame.number) < (cell.operation?.attempt_count ?? 0)) return;
      if (frame.attempt_id === cell.attempt) {
        if (frame.revision !== cell.revision) throw new Error("attempt_invalid");
        return;
      }
      if (cell.attempt) {
        const prior = this.previousAttempts.get(id) ?? new Set<string>();
        prior.add(cell.attempt); this.previousAttempts.set(id, prior);
      }
      this.patch(id, { attempt: frame.attempt_id, sequence: 0, partial: "", revision: Number(frame.revision), notice: "",
        recovering: false,
        operation: cell.operation ? { ...cell.operation, state: "active", current_attempt_id: frame.attempt_id, attempt_count: Number(frame.number) } : null });
    }
    if (frame.type === "snapshot") {
      if (!cell.operation || frame.attempt_id !== cell.operation.current_attempt_id
          || frame.number !== cell.operation.attempt_count || !Number.isSafeInteger(frame.seq) || Number(frame.seq) < 0
          || !Number.isSafeInteger(frame.revision) || Number(frame.revision) < 0
          || typeof frame.text !== "string" || [...frame.text].length > 4000 || frame.offset !== frame.text.length) throw new Error("snapshot_invalid");
      if (cell.attempt === frame.attempt_id && (Number(frame.seq) < cell.sequence || Number(frame.revision) < cell.revision)) return;
      this.patch(id, { attempt: String(frame.attempt_id), sequence: Number(frame.seq), partial: frame.text,
        revision: Number(frame.revision), notice: "", recovering: false });
    }
    if (frame.type === "delta") {
      if (typeof frame.attempt_id === "string" && frame.attempt_id !== cell.attempt
          && this.previousAttempts.get(id)?.has(frame.attempt_id)) return;
      if (!cell.operation || frame.attempt_id !== cell.attempt || frame.revision !== cell.revision
          || !Number.isSafeInteger(frame.seq) || Number(frame.seq) < 1 || !Number.isSafeInteger(frame.offset)
          || Number(frame.offset) < 0 || typeof frame.text !== "string") throw new Error("delta_invalid");
      if (Number(frame.seq) <= cell.sequence) {
        if (Number(frame.offset) + frame.text.length > cell.partial.length
            || cell.partial.slice(Number(frame.offset), Number(frame.offset) + frame.text.length) !== frame.text) throw new Error("delta_invalid");
        return;
      }
      if (frame.seq !== cell.sequence + 1 || frame.offset !== cell.partial.length
          || [...cell.partial + frame.text].length > 4000) throw new Error("delta_invalid");
      this.patch(id, { partial: cell.partial + frame.text, sequence: Number(frame.seq) });
    }
    if (frame.type === "recovering") {
      this.patch(id, { recovering: true, notice: "El servidor está recuperando la solicitud guardada." });
    }
    if (cell.operation?.state === "completed") await this.finish(id, cell.operation);
    if (frame.type === "final" && cell.operation?.state !== "completed") throw new Error("final_unconfirmed");
    if (frame.type === "terminal" && !cell.operation) throw new Error("terminal_invalid");
  }
  private async finish(id: string, operation: ChatOperation) {
    const result = await this.json<{ id: string; content: string; metadata: Record<string, unknown> }>(chatPath(id, operation.operation_id, "result"));
    if (!this.valid()) return;
    if (typeof result.id !== "string" || typeof result.content !== "string" || !result.metadata || typeof result.metadata !== "object") throw new Error("result_invalid");
    const detail = await this.json<{ conversation: ConversationRecord; messages: MessageRecord[] }>(`/assistant/conversations/${encodeURIComponent(id)}`);
    if (detail.conversation.tenant_id !== this.scope.tenantId || detail.conversation.user_id !== this.scope.userId
        || detail.conversation.id !== id || !Array.isArray(detail.messages)
        || !detail.messages.some(message => message.id === result.id && message.role === "assistant" && message.content === result.content)) throw new Error("result_invalid");
    this.patch(id, { messages: detail.messages, question: "", partial: "", notice: "", starting: false,
      result: { operationId: operation.operation_id, messageId: result.id } });
    void this.loadMemory(id);
  }
  reconnect = async (id = this.value.selected) => {
    const operation = this.value.cells[id]?.operation;
    if (!operation) return;
    const controller = this.controller(id);
    try {
      const response = await import("../../services/api").then(({ fetchChatResponse }) => fetchChatResponse(chatPath(id, operation.operation_id, "events"),
        { token: this.scope.token, tenantId: this.scope.tenantId, signal: controller.signal }));
      this.patch(id, { partial: "", attempt: null, sequence: 0, revision: 0, notice: "", recovering: false });
      await readChatEvents(response, frame => this.receive(id, frame));
      const cell = this.value.cells[id];
      if (this.valid() && cell && (cell.operation?.state === "waiting" || cell.recovering)) this.poll(id);
      else if (this.valid() && cell && isOpen(cell) && cell.operation?.state !== "paused") this.patch(id, { notice: "Conexión interrumpida. La solicitud sigue guardada." });
    } catch { if (!controller.signal.aborted) this.patch(id, { notice: "No se pudo recuperar la conexión. La solicitud sigue guardada." }); }
    finally { this.readers.delete(controller); }
  };
  private poll(id: string) {
    const timer = setTimeout(async () => {
      this.timers.delete(timer);
      if (!this.valid()) return;
      const operation = this.value.cells[id]?.operation;
      if (!operation || !["reserved", "waiting", "active"].includes(operation.state)) return;
      try {
        const next: unknown = await this.json(chatPath(id, operation.operation_id));
        if (!isChatOperation(next) || next.operation_id !== operation.operation_id) throw new Error("operation_invalid");
        this.patch(id, { operation: next });
        if (next.state === "waiting" || next.state === "reserved") this.poll(id);
        else if (next.state === "completed") await this.finish(id, next);
        else if (next.state === "active") await this.reconnect(id);
      } catch { this.patch(id, { notice: "No se pudo consultar la solicitud guardada." }); }
    }, 5000);
    this.timers.set(timer, id);
  }
  stop = async () => {
    const id = this.value.selected, cell = this.value.cells[id];
    if (!cell.operation || cell.stopping || !isOpen(cell)) return;
    this.patch(id, { stopping: true });
    try {
      const next: unknown = await this.json(chatPath(id, cell.operation.operation_id, "stop"), "POST");
      if (!isChatOperation(next) || next.operation_id !== cell.operation.operation_id) throw new Error("operation_invalid");
      this.patch(id, { operation: next });
      if (next.state === "completed") await this.finish(id, next);
    } catch { this.patch(id, { notice: "No se pudo confirmar la detención. Consulta el estado de la solicitud." }); }
    finally { this.patch(id, { stopping: false }); }
  };
  resume = async () => {
    const id = this.value.selected, cell = this.value.cells[id];
    if (cell.operation?.state !== "paused" || cell.operation.retry_at && Date.parse(cell.operation.retry_at) > Date.now()) return;
    try {
      const next: unknown = await this.json(chatPath(id, cell.operation.operation_id, "resume"), "POST");
      if (!isChatOperation(next) || next.operation_id !== cell.operation.operation_id) throw new Error("operation_invalid");
      this.patch(id, { operation: next });
      if (next.state === "waiting") this.poll(id);
      if (next.state === "active") await this.reconnect(id);
    } catch { this.patch(id, { notice: "No se pudo reanudar la solicitud." }); }
  };
}
export function useChatSession(scope: ChatScope, prepared?: PreparedScreen | null) {
  const [session] = useState(() => new ChatSession(scope, prepared));
  const value = useSyncExternalStore(session.subscribe, session.snapshot);
  useEffect(() => { session.attach(); return () => session.detach(); }, [session]);
  return { session, value, cell: value.cells[value.selected] };
}
