import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sendConversationMessage } from "../services/api";
import type { MessageCreateRequest, OwnershipQuery } from "../services/contracts";

const fieldClass = "rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary";

// The parent keys this composer by tenant and conversation. A pending request
// keeps its original query keys and cannot clear another conversation's draft.
export function MessageComposer({ token, tenantId, conversationId }: {
  token: string; tenantId: string; conversationId: string;
}) {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");
  const [ownership, setOwnership] = useState(false);
  const [groupBy, setGroupBy] = useState<OwnershipQuery["group_by"]>("application");
  const [tagKey, setTagKey] = useState("");
  const [value, setValue] = useState("");
  const [currency, setCurrency] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [validationError, setValidationError] = useState("");
  const now = new Date();
  const defaultStart = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)).toISOString().slice(0, 10);
  const defaultEnd = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1)).toISOString().slice(0, 10);
  const sendMutation = useMutation({
    mutationFn: (payload: MessageCreateRequest) =>
      sendConversationMessage(token, tenantId, conversationId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations", tenantId] });
      queryClient.invalidateQueries({ queryKey: ["conversation", tenantId, conversationId] });
      setMessage("");
    },
    onError: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation", tenantId, conversationId] });
    }
  });

  function handleSend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError("");
    sendMutation.reset();
    if (!message.trim()) return;
    const payload: MessageCreateRequest = { content: message };
    if (ownership) {
      if (Boolean(startDate) !== Boolean(endDate)) {
        setValidationError("Indica ambas fechas o deja ambas vacías para consultar el mes actual UTC.");
        return;
      }
      if (startDate && startDate >= endDate) {
        setValidationError("La fecha de fin debe ser posterior a la fecha de inicio.");
        return;
      }
      if (currency && !/^[A-Z]{3}$/.test(currency)) {
        setValidationError("La moneda debe tener tres letras mayúsculas, por ejemplo EUR.");
        return;
      }
      if (groupBy === "tag" && !tagKey.trim()) {
        setValidationError("Indica la clave de la etiqueta.");
        return;
      }
      payload.ownership_query = {
        group_by: groupBy,
        ...(groupBy === "tag" ? { tag_key: tagKey.trim() } : {}),
        ...(value.trim() ? { value: value.trim() } : {}),
        ...(currency ? { currency } : {}),
        ...(startDate && endDate ? { start_date: startDate, end_date: endDate } : {})
      };
    }
    sendMutation.mutate(payload);
  }

  return <form className="mt-4 flex flex-col gap-4" onSubmit={handleSend}>
    <label className="flex items-center gap-2 text-sm text-foreground">
      <input type="checkbox" checked={ownership} onChange={(event) => {
        setOwnership(event.target.checked);
        setValidationError("");
        sendMutation.reset();
      }} disabled={sendMutation.isPending} />
      Consultar costes por propiedad
    </label>
    {ownership && <fieldset className="grid gap-3 rounded-md border border-border p-3" disabled={sendMutation.isPending}>
      <legend className="px-1 text-sm font-medium">Selección de costes</legend>
      <label className="flex flex-col gap-1 text-sm">Agrupar por
        <select className={fieldClass} value={groupBy} onChange={(event) => {
          setGroupBy(event.target.value as OwnershipQuery["group_by"]);
          setTagKey("");
          setValidationError("");
        }}>
          <option value="application">Aplicación</option>
          <option value="owner">Equipo / responsable (owner)</option>
          <option value="project">Proyecto</option>
          <option value="cost_center">Centro de coste</option>
          <option value="tag">Etiqueta personalizada</option>
        </select>
      </label>
      {groupBy === "tag" && <label className="flex flex-col gap-1 text-sm">Clave de etiqueta
        <input className={fieldClass} value={tagKey} maxLength={256} onChange={(event) => setTagKey(event.target.value)} />
      </label>}
      <label className="flex flex-col gap-1 text-sm">Valor exacto (opcional)
        <input className={fieldClass} value={value} maxLength={256} onChange={(event) => setValue(event.target.value)} />
      </label>
      <p className="text-xs text-muted-foreground">El valor distingue mayúsculas y minúsculas. Vacío: todos los grupos. Aplicación y owner requieren etiquetas explícitas.</p>
      <label className="flex flex-col gap-1 text-sm">Moneda (opcional)
        <input className={fieldClass} value={currency} maxLength={3} placeholder="EUR" onChange={(event) => setCurrency(event.target.value)} />
      </label>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">Inicio UTC (incluido)
          <input className={fieldClass} type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
        </label>
        <label className="flex flex-col gap-1 text-sm">Fin UTC (excluido)
          <input className={fieldClass} type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
        </label>
      </div>
      <p className="text-xs text-muted-foreground">Indica ambas fechas o deja ambas vacías para el mes actual UTC. Sin moneda se muestran los totales separados por moneda.</p>
      {!startDate && !endDate && <p className="text-xs text-muted-foreground">Mes actual UTC: {defaultStart} a {defaultEnd} (fin excluido).</p>}
    </fieldset>}
    <textarea
      className={fieldClass}
      rows={5}
      maxLength={4000}
      aria-label="Pregunta"
      placeholder={ownership ? "Pregunta sobre los costes de la selección." : "Ask the assistant about the ingested tenant documents."}
      value={message}
      disabled={sendMutation.isPending}
      onChange={(event) => setMessage(event.target.value)}
    />
    <p className="text-xs text-muted-foreground">{message.length}/4000 caracteres. Cada pregunta se responde por separado; no se usa el historial como contexto.</p>
    {sendMutation.isPending && <p role="status" className="text-sm text-muted-foreground">Consultando las fuentes y preparando la respuesta…</p>}
    {validationError && <p className="text-sm text-danger" role="alert">{validationError}</p>}
    {sendMutation.error && <p className="text-sm text-danger" role="alert">{sendMutation.error.message}</p>}
    <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-foreground hover:bg-primary/80 disabled:opacity-60"
      type="submit" disabled={sendMutation.isPending || !message.trim()}>
      {sendMutation.isPending ? "Sending..." : "Send"}
    </button>
  </form>;
}
