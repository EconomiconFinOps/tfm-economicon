import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { Check, Pencil, X } from "lucide-react";
import { normalizeConversationTitle } from "./useChatSession";

const iconButton = "inline-flex h-8 w-8 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground focus-visible:outline-2 focus-visible:outline-highlight disabled:opacity-50";

export function ConversationTitleEditor({ title, label, disabled = false, onSave, children }: {
  title: string; label: string; disabled?: boolean; onSave: (title: string) => Promise<void>; children: ReactNode;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(title);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const busy = useRef(false);
  const mounted = useRef(true);
  const trigger = useRef<HTMLButtonElement>(null);
  const returnFocus = useRef(false);
  const errorId = useId();
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    if (!editing && returnFocus.current) { trigger.current?.focus(); returnFocus.current = false; }
  }, [editing]);
  const save = async () => {
    if (busy.current || disabled) return;
    const normalized = normalizeConversationTitle(draft);
    if (!normalized || Array.from(normalized).length > 60) {
      setError("El nombre debe tener entre 1 y 60 caracteres."); return;
    }
    busy.current = true; setPending(true); setError("");
    try { await onSave(normalized); if (mounted.current) setEditing(false); }
    catch { if (mounted.current) setError("No se pudo guardar el nombre. Inténtalo de nuevo."); }
    finally { busy.current = false; if (mounted.current) setPending(false); }
  };
  return <div data-conversation-title-editor={editing ? "editing" : undefined} className="flex min-w-0 flex-1 flex-wrap items-center gap-1">
    {!editing ? <>{children}<button ref={trigger} type="button" className={iconButton} aria-label={label} title={label} disabled={disabled}
      onClick={() => { returnFocus.current = true; setDraft(title); setError(""); setEditing(true); }}><Pencil size={14} aria-hidden="true" /></button></> : <>
      <input autoFocus aria-label="Nombre de conversación" aria-invalid={!!error} aria-describedby={error ? errorId : undefined}
        className="min-w-0 flex-1 rounded border border-border bg-background px-2 py-1 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-highlight"
        value={draft} disabled={pending || disabled} onChange={event => { setDraft(event.target.value); setError(""); }}
        onKeyDown={event => {
          if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); if (!busy.current) setEditing(false); }
          if (event.key === "Enter" && !event.nativeEvent.isComposing) { event.preventDefault(); event.stopPropagation(); void save(); }
        }} />
      <button type="button" className={iconButton} title="Guardar nombre" aria-label="Guardar nombre" disabled={pending || disabled} onClick={() => void save()}><Check size={16} aria-hidden="true" /></button>
      <button type="button" className={iconButton} title="Cancelar edición" aria-label="Cancelar edición" disabled={pending} onClick={() => setEditing(false)}><X size={16} aria-hidden="true" /></button>
      {pending && <span role="status" className="sr-only">Guardando nombre</span>}
      {error && <p id={errorId} role="alert" className="w-full text-xs text-destructive">{error}</p>}
    </>}
  </div>;
}
