import { useEffect, useLayoutEffect, useState } from "react";
import { BookOpen, Brain, CircleAlert, Database, LoaderCircle, MessageSquare, Pause, Square, RotateCcw } from "lucide-react";
import type { ChatCell } from "./useChatSession";

const relative = new Intl.RelativeTimeFormat("es", { numeric: "auto" });
const absolute = new Intl.DateTimeFormat("es-ES", { dateStyle: "long", timeStyle: "medium" });

export function relativeMessageTime(createdAt: string, now: number) {
  const age = Math.max(0, now - Date.parse(createdAt));
  if (!Number.isFinite(age)) return null;
  if (age < 60000) return "ahora";
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["year", 365 * 86400000], ["month", 30 * 86400000], ["day", 86400000],
    ["hour", 3600000], ["minute", 60000],
  ];
  const [unit, size] = units.find(([, size]) => age >= size)!;
  return relative.format(-Math.floor(age / size), unit);
}

export function MessageTimestamp({ createdAt }: { createdAt: unknown }) {
  const [now, setNow] = useState(Date.now);
  const timestamp = typeof createdAt === "string" ? createdAt : "";
  const label = relativeMessageTime(timestamp, now);
  useEffect(() => {
    if (!timestamp || !Number.isFinite(Date.parse(timestamp))) return;
    const refresh = () => setNow(Date.now());
    const timer = setInterval(refresh, 30000);
    document.addEventListener("visibilitychange", refresh);
    return () => { clearInterval(timer); document.removeEventListener("visibilitychange", refresh); };
  }, [timestamp]);
  if (label === null) return null;
  return <time dateTime={timestamp} title={absolute.format(new Date(timestamp))}
    className="chat-message-time">{label}</time>;
}

export function userRoleLabel(role?: string) {
  if (!role?.trim()) return "";
  const labels: Record<string, string> = { admin: "Administrador", member: "Miembro",
    viewer: "Lector", professional: "Profesional" };
  return labels[role] ?? role;
}

export function operationStatus(cell: Pick<ChatCell, "starting" | "operation" | "partial" | "corrective">) {
  if (cell.starting) return "Preparando contexto";
  if (cell.corrective && ["active", "waiting"].includes(cell.operation?.state ?? "")) return "Revisando respuesta";
  switch (cell.operation?.state) {
    case "active": return cell.partial ? "Recibiendo respuesta" : "Esperando respuesta del LLM";
    case "waiting": return cell.operation.wait_info.reason === "local_capacity" ? "Esperando capacidad disponible" : "Esperando al proveedor";
    case "paused": return "Solicitud pausada. Puedes reanudarla cuando esté disponible.";
    case "completed": return "Respuesta completada";
    case "failed": return "No se pudo completar la respuesta";
    case "cancelled": return "Respuesta detenida";
    case "reserved": return "Solicitud guardada";
    default: return "";
  }
}

function observedActivity(cell: ChatCell) {
  const queue = cell.memory?.queue;
  if (queue?.blocked) {
    if (queue.state === "running") return { key: "compacting", label: "Comprimiendo contexto", icon: Database, active: true };
    if (queue.state === "pending") return { key: "memory-pending", label: "Actualizando memoria", icon: Database, active: true };
    if (queue.state === "reconciling") return { key: "reconciling", label: "Recuperación de memoria pendiente", icon: Database, active: false };
    if (queue.state === "failed") return { key: "memory-failed", label: "Actualización de memoria interrumpida", icon: CircleAlert, active: false };
  }
  if (cell.starting) return { key: "preparing", label: "Preparando contexto", icon: BookOpen, active: true };
  if (!cell.operation) return null;
  const state = cell.operation.state;
  if (state === "completed") return null;
  const icon = state === "active" ? (cell.partial ? MessageSquare : Brain)
    : state === "paused" ? Pause
    : state === "failed" ? CircleAlert : state === "cancelled" ? Square : LoaderCircle;
  return { key: `${state}:${cell.operation.attempt_count}:${state === "active" && !!cell.partial}`,
    label: operationStatus(cell), icon,
    active: state === "active" || state === "waiting" };
}

type Activity = NonNullable<ReturnType<typeof observedActivity>>;

export function useChatActivity(cell: ChatCell, cells: Record<string, ChatCell>) {
  const current = observedActivity(cell);
  const operationId = cell.operation?.operation_id ?? null;
  const [observed, setObserved] = useState({ conversation: cell.id, operationId, starting: cell.starting,
    question: cell.question, rows: current ? [current] : [] as Activity[] });
  // Ephemeral UI observations only: a restored operation starts at its current
  // state. The server's first operation id adopts the already observed prelude.
  useLayoutEffect(() => {
    setObserved(previous => {
      const adoptedDraft = previous.conversation.startsWith("draft-") && !cells[previous.conversation]
        && !cell.id.startsWith("draft-") && previous.starting && !!previous.question
        && previous.question === cell.question;
      const reset = (previous.conversation !== cell.id && !adoptedDraft) || (cell.starting && !previous.starting)
        || (operationId !== previous.operationId && !(previous.operationId === null && previous.starting));
      const rows = reset ? [] : previous.rows;
      const last = rows.at(-1);
      const next = !current ? rows : last?.key === current.key
        ? (last.label === current.label ? rows : [...rows.slice(0, -1), current]) : [...rows, current];
      if (next === previous.rows && previous.starting === cell.starting && previous.operationId === operationId
          && previous.conversation === cell.id) return previous;
      return { conversation: cell.id, operationId, starting: cell.starting, question: cell.question, rows: next };
    });
  }, [cell.id, cell.starting, cell.question, cells, operationId, current?.key, current?.label]);
  return { rows: observed.rows, current };
}

export function ChatProgress({ activity, retryResponse, retryDisabled = true }: {
  activity: ReturnType<typeof useChatActivity>; retryResponse?: () => Promise<void>; retryDisabled?: boolean;
}) {
  const { rows, current } = activity;
  if (!rows.length) return null;
  return <div role="status" aria-label="Actividad de la conversación" aria-live="polite" aria-atomic="false"
    aria-relevant="additions text" className="chat-activity">
    <ol className="chat-activity-list">{rows.map((step, index) => {
      const active = index === rows.length - 1 && current?.key === step.key && current.active;
      const Icon = active ? LoaderCircle : step.icon;
      return <li key={`${index}-${step.key}`} className="chat-activity-row" data-active={active || undefined}>
        <Icon size={15} strokeWidth={1.6} aria-hidden="true" className={active ? "chat-activity-spinner" : undefined} />
        <span className={active ? "chat-progress-shimmer" : undefined}>{step.label}</span>
        {retryResponse && step.key.startsWith("failed:") && !rows.slice(index + 1).some(row => row.key.startsWith("failed:")) &&
          <button type="button" title="Reintentar respuesta" aria-label="Reintentar respuesta"
            className="ml-auto inline-flex h-8 w-8 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground focus-visible:outline-2 focus-visible:outline-highlight disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={retryDisabled} onClick={() => void retryResponse()}><RotateCcw size={16} aria-hidden="true" /></button>}
      </li>;
    })}</ol>
  </div>;
}
