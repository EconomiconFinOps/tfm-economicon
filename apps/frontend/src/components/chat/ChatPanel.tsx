import { createContext, useContext, useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { useLocation } from "react-router";
import { AssistantRuntimeProvider, ComposerPrimitive, MessagePrimitive, ThreadPrimitive,
  useAuiState, useExternalStoreRuntime, type AppendMessage, type ThreadMessageLike } from "@assistant-ui/react";
import * as Dialog from "@radix-ui/react-dialog";
import { MessageSquare, X, History, Plus, ArrowDown, Send, Square, RotateCcw, Trash2 } from "lucide-react";
import { AnswerEvidence } from "../AnswerEvidence";
import { ConversationTitleEditor } from "./ConversationTitleEditor";
import type { ChatScope } from "../../services/chat";
import { isOpen, memoryBlocked, useChatSession, type ChatCell } from "./useChatSession";
import { usePreparedScreen } from "./ScreenCaptureProvider";
import { ChatProgress, MessageTimestamp, userRoleLabel, useChatActivity } from "./ChatPresentation";
import "./chat.css";

const button = "inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground hover:bg-accent focus-visible:outline-2 focus-visible:outline-highlight disabled:opacity-50 disabled:cursor-not-allowed";
const MessageActivity = createContext<{ before?: string; after?: string; content: ReactNode } | null>(null);
function ChatMessage() {
  const message = useAuiState(state => state.message);
  const activity = useContext(MessageActivity);
  const provisional = message.metadata.custom?.provisional === true;
  const originalRole = message.metadata.custom?.originalRole;
  const metadata = message.metadata.custom?.persisted;
  const role = message.metadata.custom?.userRole;
  const roleLabel = typeof role === "string" ? userRoleLabel(role) : "";
  const content = message.content.filter(part => part.type === "text").map(part => part.text).join("");
  return <>{activity?.before === message.id && activity.content}<MessagePrimitive.Root className={`chat-message ${message.role === "user" ? "chat-message-user" : "chat-message-assistant"}`}>
    <div className="chat-message-header"><span className="font-medium">{originalRole && originalRole !== "user" && originalRole !== "assistant"
      ? "Mensaje histórico" : message.role === "user" ? `Tú${roleLabel ? ` · ${roleLabel}` : ""}` : "Asistente"}{provisional ? " · provisional" : ""}</span>
      <MessageTimestamp createdAt={message.metadata.custom?.persistedCreatedAt} /></div>
    {message.role === "assistant" && !provisional && metadata && typeof metadata === "object" && !Array.isArray(metadata)
      ? <AnswerEvidence content={content} metadata={metadata as Record<string, unknown>} />
      : <div className="whitespace-pre-wrap break-words text-sm"><MessagePrimitive.Parts /></div>}
  </MessagePrimitive.Root>{activity?.after === message.id && activity.content}</>;
}
function Thread({ cell, send, stop, captureReady, userRole, activity, retryMemory, retryResponse }: { cell: ChatCell; send: (message: AppendMessage) => Promise<void>; stop: () => Promise<void>; captureReady: boolean; userRole?: string; activity: ReturnType<typeof useChatActivity>; retryMemory: () => Promise<void>; retryResponse: () => Promise<void> }) {
  const messages: ThreadMessageLike[] = cell.messages.map(message => ({ id: message.id,
    role: message.role === "user" || message.role === "assistant" ? message.role : "system",
    content: message.content, createdAt: new Date(message.created_at), metadata: { custom: { persisted: message.metadata,
      originalRole: message.role, persistedCreatedAt: message.created_at, userRole } } }));
  if (cell.question && !cell.messages.some(message => message.id === cell.operation?.question_id)) {
    messages.push({ id: `pending-question-${cell.operation?.question_id ?? cell.id}`, role: "user", content: cell.question,
      metadata: { custom: { provisional: true, userRole } } });
  }
  const failed = cell.operation?.state === "failed";
  if (cell.partial) messages.push({ id: `partial-${cell.attempt ?? cell.id}`, role: "assistant", content: cell.partial,
    status: isOpen(cell) ? { type: "running" } : { type: "incomplete", reason: failed ? "error" : "cancelled" }, metadata: { custom: { provisional: true } } });
  const questionId = cell.question ? cell.operation?.question_id ?? `pending-question-${cell.id}` : cell.operation?.question_id;
  const questionIndex = messages.findIndex(message => message.role === "user" &&
    (message.id === questionId || message.id === `pending-question-${questionId}`));
  const resultId = cell.result?.operationId === cell.operation?.operation_id ? cell.result?.messageId : undefined;
  const answerIndex = messages.findIndex(message => message.role === "assistant" &&
    (cell.partial ? message.id === `partial-${cell.attempt ?? cell.id}` : !!resultId && message.id === resultId));
  // Anchor only to this operation's verified result or its local partial/question.
  const before = questionIndex >= 0 && answerIndex > questionIndex ? messages[answerIndex].id : undefined;
  const after = !before && questionIndex >= 0 ? messages[questionIndex].id : undefined;
  const progress = <><ChatProgress activity={activity} retryResponse={failed ? retryResponse : undefined}
    retryDisabled={!cell.question || isOpen(cell) || memoryBlocked(cell) || cell.loading || cell.uncertain || !captureReady} />
    {cell.memory?.queue.blocked && cell.memory.queue.state === "failed" && cell.memory.queue.retryable &&
      <button className={`${button} mb-3`} disabled={cell.memoryLoading} onClick={() => void retryMemory()}>
        <RotateCcw size={16} aria-hidden="true" />Reintentar compresión</button>}</>;
  const runtime = useExternalStoreRuntime({ messages, convertMessage: (message: ThreadMessageLike) => message, isRunning: isOpen(cell), isLoading: cell.loading,
    isSendDisabled: isOpen(cell) || memoryBlocked(cell) || cell.loading || cell.uncertain || !captureReady, onNew: send, onCancel: stop });
  const viewport = useRef<HTMLDivElement>(null);
  const follow = useRef(true);
  const [readingAbove, setReadingAbove] = useState(false);
  const scrollBottom = () => { follow.current = true; setReadingAbove(false); if (viewport.current) viewport.current.scrollTop = viewport.current.scrollHeight; };
  useLayoutEffect(() => { if (follow.current && viewport.current) viewport.current.scrollTop = viewport.current.scrollHeight; }, [cell.messages, cell.partial, cell.question]);
  useEffect(() => {
    const node = viewport.current?.firstElementChild;
    if (!node) return;
    const observer = new ResizeObserver(() => { if (follow.current && viewport.current) viewport.current.scrollTop = viewport.current.scrollHeight; });
    observer.observe(node); return () => observer.disconnect();
  }, []);
  return <AssistantRuntimeProvider runtime={runtime}><ThreadPrimitive.Root className="flex min-h-0 flex-1 flex-col">
    <div ref={viewport} className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4" role="log" aria-label="Mensajes" aria-live="off" tabIndex={0}
      onScroll={() => { const node = viewport.current; if (!node) return; follow.current = node.scrollHeight - node.scrollTop - node.clientHeight < 48; setReadingAbove(!follow.current); }}>
      <div><MessageActivity.Provider value={{ before, after, content: progress }}>
        <ThreadPrimitive.Messages components={{ Message: ChatMessage }} />
      </MessageActivity.Provider>
        {!messages.length && !cell.loading && <p className="py-8 text-sm text-muted-foreground">Consulta tus datos FinOps o abre una conversación del historial.</p>}
        {cell.loading && <p role="status" className="py-4 text-sm text-muted-foreground">Cargando conversación…</p>}
        {!before && !after && progress}
      </div>
    </div>
    {readingAbove && <button className={`${button} mx-auto my-2`} onClick={scrollBottom}><ArrowDown size={16} />Volver al final</button>}
    <ComposerPrimitive.Root className="flex items-center gap-2 border-t border-border p-4">
      <ComposerPrimitive.Input aria-label="Pregunta" placeholder="Pregunta sobre tus datos…" addAttachmentOnPaste={false}
        onKeyDown={event => { if (memoryBlocked(cell) && event.key === "Enter" && !event.shiftKey) event.preventDefault(); }}
        cancelOnEscape={false} unstable_focusOnRunStart={false} unstable_focusOnScrollToBottom={false}
        className="max-h-40 min-h-12 min-w-0 flex-1 resize-none rounded-lg border border-border bg-background p-3 text-sm focus-visible:outline-2 focus-visible:outline-highlight" />
      <ComposerPrimitive.Send className="inline-flex h-12 min-h-12 w-12 min-w-12 shrink-0 items-center justify-center rounded-lg border border-border bg-card p-0 text-foreground hover:bg-accent focus-visible:outline-2 focus-visible:outline-highlight disabled:opacity-50 disabled:cursor-not-allowed" aria-label="Enviar"><Send size={16} /><span className="sr-only">Enviar</span></ComposerPrimitive.Send>
    </ComposerPrimitive.Root>
  </ThreadPrimitive.Root></AssistantRuntimeProvider>;
}
export function ChatPanel({ scope, userRole }: { scope: ChatScope; userRole?: string }) {
  const [shown, setShown] = useState(false);
  const [historyShown, setHistoryShown] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [deletePending, setDeletePending] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const deleteBusy = useRef(false);
  const deleteTrigger = useRef<HTMLButtonElement | null>(null);
  const deleteCancel = useRef<HTMLButtonElement>(null);
  const historyClose = useRef<HTMLButtonElement>(null);
  const prepared = usePreparedScreen();
  const { session, value, cell } = useChatSession(scope, prepared);
  const activity = useChatActivity(cell, value.cells);
  useSyncExternalStore(session.screen.subscribe, session.screen.snapshot);
  const location = useLocation();
  useEffect(() => {
    if (new URLSearchParams(location.search).get("chat") === "open") setShown(true);
  }, [location.search]);
  const [deadlineTick, setDeadlineTick] = useState(0);
  const retryAt = cell.operation?.state === "paused" ? cell.operation.retry_at : null;
  useEffect(() => {
    const remaining = retryAt ? Date.parse(retryAt) - Date.now() : 0;
    if (!Number.isFinite(remaining) || remaining <= 0) return;
    const timer = setTimeout(() => setDeadlineTick(tick => tick + 1), Math.min(remaining + 1, 2147483647));
    return () => clearTimeout(timer);
  }, [value.selected, cell.operation?.operation_id, retryAt, deadlineTick]);
  const trigger = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLElement>(null);
  useLayoutEffect(() => { session.screen.ensureRoute(location.pathname); }, [session, location.pathname]);
  useEffect(() => { if (shown) panel.current?.querySelector<HTMLTextAreaElement>("textarea")?.focus(); }, [shown]);
  const hide = () => { setShown(false); setHistoryShown(false); trigger.current?.focus(); };
  const send = async (message: AppendMessage) => {
    const content = message.content.filter(part => part.type === "text").map(part => part.text).join("");
    await session.send(content, location.pathname);
  };
  const deleteBlock = deleteTarget ? session.deletionBlock(deleteTarget) : null;
  const confirmDelete = async () => {
    if (!deleteTarget || deleteBusy.current) return;
    deleteBusy.current = true; setDeletePending(true); setDeleteError("");
    try { await session.remove(deleteTarget); setDeleteTarget(null); }
    catch (error) { setDeleteError(error instanceof Error ? error.message : "No se pudo eliminar la conversación."); }
    finally { deleteBusy.current = false; setDeletePending(false); }
  };
  return <>
    <button ref={trigger} type="button" style={shown ? { display: "none" } : undefined} className={`${button} fixed bottom-6 right-6 z-30 shadow-lg`} aria-label="Abrir asistente" aria-expanded={shown} aria-controls="finops-chat"
      onClick={() => setShown(true)}><MessageSquare size={18} />Asistente FinOps</button>
    {shown && <section ref={panel} id="finops-chat" role="region" aria-label="Asistente FinOps"
      className="fixed inset-y-0 right-0 z-40 flex w-full min-w-0 flex-col border-l border-border bg-background shadow-2xl md:w-1/2"
      onKeyDown={event => { if (event.key === "Escape" && !historyShown) { event.preventDefault(); hide(); } }}>
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-card px-4 py-3">
        <div className="min-w-0 flex-1"><h2 className="font-semibold text-foreground">Asistente FinOps</h2>
          <ConversationTitleEditor key={cell.id} title={cell.title} label="Renombrar conversación"
            disabled={cell.id.startsWith("draft-") && cell.starting} onSave={title => session.rename(cell.id, title)}>
            <p className="min-w-0 max-w-[calc(100%-2.25rem)] break-words text-xs text-muted-foreground">{cell.title}</p>
          </ConversationTitleEditor></div>
        <div className="flex gap-2"><button className={button} onClick={() => { session.newConversation(); setHistoryShown(false); }}><Plus size={16} /><span className="sr-only">Nueva conversación</span></button>
          <Dialog.Root open={historyShown} onOpenChange={open => { setHistoryShown(open); if (open) void session.loadHistory(); }}>
            <Dialog.Trigger className={button} aria-label="Historial"><History size={16} /><span className="sr-only">Historial</span></Dialog.Trigger>
            <Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-50 bg-background/40" />
              <Dialog.Content className="fixed inset-y-0 right-0 z-50 flex w-full flex-col border-l border-border bg-card p-4 shadow-2xl sm:w-80" aria-describedby={undefined}
                onEscapeKeyDown={event => {
                  if (event.target instanceof Element && event.target.closest('[data-conversation-title-editor="editing"]')) event.preventDefault();
                }}>
                <div className="flex items-center justify-between"><Dialog.Title className="font-semibold">Historial de conversaciones</Dialog.Title>
                  <Dialog.Close ref={historyClose} className={button} aria-label="Cerrar historial"><X size={16} /></Dialog.Close></div>
                <div className="chat-history-scroll mt-4 flex-1 overflow-y-auto">
                  {value.historyLoading && <p role="status">Cargando historial…</p>}
                  {value.historyError && <p role="alert">No se pudo cargar el historial.</p>}
                  {!value.historyLoading && !value.historyError && !value.history.length && <p>No hay conversaciones guardadas.</p>}
                  {value.history.map(record => <div key={record.id} className="mb-2 flex min-w-0 items-center gap-1 rounded-lg border border-border bg-card p-1">
                    <ConversationTitleEditor title={record.title} label={`Renombrar ${record.title}`} onSave={title => session.rename(record.id, title)}>
                      <button className="min-w-0 flex-1 self-stretch break-words rounded px-2 py-2 text-left text-sm text-foreground hover:bg-accent focus-visible:outline-2 focus-visible:outline-highlight" disabled={value.requestsLoading} onClick={() => {
                        const request = value.requests.find(item => item.conversation_id === record.id);
                        const cell = value.cells[record.id];
                        // Restore the newest persisted operation without exposing a second history list.
                        if (request && !cell?.operation && !cell?.starting && !cell?.uncertain) void session.selectRequest(request);
                        else void session.select(record);
                        setHistoryShown(false);
                      }}>{record.title}</button>
                    </ConversationTitleEditor>
                    <button type="button" className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground focus-visible:outline-2 focus-visible:outline-highlight disabled:opacity-50"
                      aria-label={`Eliminar ${record.title}`} title={session.deletionBlock(record.id) ?? `Eliminar ${record.title}`}
                      disabled={!!session.deletionBlock(record.id)} onClick={event => {
                        deleteTrigger.current = event.currentTarget; setDeleteError(""); setDeleteTarget(record.id);
                      }}><Trash2 size={14} aria-hidden="true" /></button>
                  </div>)}
                </div>
                <Dialog.Root open={deleteTarget !== null} onOpenChange={open => { if (!open && !deleteBusy.current) setDeleteTarget(null); }}>
                  <Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-[60] bg-background/60" />
                    <Dialog.Content className="fixed left-1/2 top-1/2 z-[60] w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-card p-5 shadow-xl"
                      aria-describedby={undefined} onOpenAutoFocus={event => { event.preventDefault(); deleteCancel.current?.focus(); }}
                      onCloseAutoFocus={event => { event.preventDefault(); (deleteTrigger.current?.isConnected ? deleteTrigger.current : historyClose.current)?.focus(); }}
                      onEscapeKeyDown={event => { if (deleteBusy.current) event.preventDefault(); }}
                      onInteractOutside={event => event.preventDefault()}>
                      <Dialog.Title className="text-sm font-semibold text-foreground">¿Estás seguro? No podrás recuperar esta conversación</Dialog.Title>
                      {(deleteError || deleteBlock) && <p role="alert" className="mt-3 text-sm text-muted-foreground">{deleteError || deleteBlock}</p>}
                      {deletePending && <p role="status" className="mt-3 text-sm text-muted-foreground">Eliminando conversación…</p>}
                      <div className="mt-4 flex justify-end gap-2">
                        <button type="button" className={button} disabled={deletePending || !!deleteBlock} onClick={() => void confirmDelete()}>Sí</button>
                        <Dialog.Close ref={deleteCancel} className={button} disabled={deletePending}>No</Dialog.Close>
                      </div>
                    </Dialog.Content>
                  </Dialog.Portal>
                </Dialog.Root>
              </Dialog.Content></Dialog.Portal>
          </Dialog.Root>
          <button className={button} aria-label="Ocultar asistente" onClick={hide}><X size={16} /></button>
        </div>
      </header>
      <Thread key={value.selected} cell={cell} send={send} stop={session.stop} captureReady={session.screen.ready(location.pathname)} userRole={userRole} activity={activity} retryMemory={session.retryMemory} retryResponse={() => session.send(cell.question, location.pathname, true)} />
      {cell.memoryError && <div role="alert" className="flex items-center gap-2 px-4 pb-3 text-xs text-muted-foreground">
        <span>No se pudo comprobar el estado de la conversación.</span>
        <button type="button" title="Volver a comprobar estado" aria-label="Volver a comprobar estado"
          className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded hover:bg-accent disabled:opacity-50"
          disabled={cell.memoryLoading} onClick={() => void session.retryMemoryState()}><RotateCcw size={16} aria-hidden="true" /></button>
      </div>}
      {cell.notice && <div className="px-4 pb-3"><p role="alert" className="text-sm text-muted-foreground">{cell.notice}</p>
        {session.canCheckSend(cell.id) && <button className={`${button} mt-2`} disabled={cell.starting} onClick={() => void session.checkSend()}>Comprobar envío</button>}
        {cell.operation && <button className={`${button} mt-2`} onClick={() => void session.reconnect()}>Recuperar conexión</button>}</div>}
      {isOpen(cell) && cell.operation && <div className="flex flex-wrap gap-2 px-4 pb-3"><button className={button} disabled={cell.stopping} onClick={() => void session.stop()}><Square size={14} />Detener respuesta</button>
        {cell.operation.state === "paused" && <button className={button} disabled={!!cell.operation.retry_at && Date.parse(cell.operation.retry_at) > Date.now()} onClick={() => void session.resume()}>Reanudar solicitud</button>}
        {cell.operation.retry_at && <p className="w-full text-xs text-muted-foreground">Disponible desde {new Date(cell.operation.retry_at).toLocaleString("es-ES")}</p>}
      </div>}
    </section>}
    {shown && <div className="hidden shrink-0 md:block md:w-[50vw]" aria-hidden="true" />}
  </>;
}
