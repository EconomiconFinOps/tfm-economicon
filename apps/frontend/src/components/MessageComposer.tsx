import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useReferenceDate } from "../hooks/useReferenceDate";
import { referenceMonth } from "../lib/referenceDate";
import { sendConversationMessage } from "../services/api";
import type { AzureCostSelection, MessageCreateRequest, OwnershipQuery } from "../services/contracts";

const fieldClass = "rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-highlight";

// The parent keys this composer by tenant and conversation. A pending request
// keeps its original query keys and cannot clear another conversation's draft.
export function MessageComposer({ token, tenantId, conversationId }: {
  token: string; tenantId: string; conversationId: string;
}) {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");
  const [costMode, setCostMode] = useState(false);
  const [costGroup, setCostGroup] = useState<AzureCostSelection["group_by"]>("subscription");
  const [subscription, setSubscription] = useState("");
  const [ownership, setOwnership] = useState(false);
  const [groupBy, setGroupBy] = useState<OwnershipQuery["group_by"]>("application");
  const [tagKey, setTagKey] = useState("");
  const [value, setValue] = useState("");
  const [currency, setCurrency] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [validationError, setValidationError] = useState("");
  const reference = useReferenceDate(token);
  const referencePeriod = reference.data ? referenceMonth(reference.data) : null;
  const sendMutation = useMutation({
    mutationFn: (payload: MessageCreateRequest) =>
      sendConversationMessage(token, tenantId, conversationId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations", tenantId] });
      queryClient.invalidateQueries({ queryKey: ["conversation", tenantId, conversationId] });
      setMessage("");
    }
  });

  function handleSend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError("");
    sendMutation.reset();
    if (!message.trim()) return;
    const payload: MessageCreateRequest = { content: message };
    if (ownership || costMode) {
      if (Boolean(startDate) !== Boolean(endDate)) {
        setValidationError("Indica ambas fechas o deja ambas vacías para consultar el mes actual UTC.");
        return;
      }
      if (startDate && startDate >= endDate) {
        setValidationError("La fecha de fin debe ser posterior a la fecha de inicio.");
        return;
      }
      if (ownership && currency && !/^[A-Z]{3}$/.test(currency)) {
        setValidationError("La moneda debe tener tres letras mayúsculas, por ejemplo EUR.");
        return;
      }
      if (ownership && groupBy === "tag" && !tagKey.trim()) {
        setValidationError("Indica la clave de la etiqueta.");
        return;
      }
      if (costMode) {
        payload.cost_query = {
          group_by: costGroup,
          ...(value.trim() ? { value: value.trim() } : {}),
          ...(subscription.trim() ? { subscription_id: subscription.trim() } : {}),
          ...(startDate && endDate ? { start_date: startDate, end_date: endDate } : {})
        };
      } else payload.ownership_query = {
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
        setCostMode(false);
        setValue("");
        setValidationError("");
        sendMutation.reset();
      }} disabled={sendMutation.isPending} />
      Consultar costes por propiedad
    </label>
    <label className="flex items-center gap-2 text-sm text-foreground">
      <input type="checkbox" checked={costMode} disabled={sendMutation.isPending} onChange={(event) => {
        setCostMode(event.target.checked);
        setOwnership(false);
        setValue("");
        setValidationError("");
        sendMutation.reset();
      }} />
      Consultar gasto Azure
    </label>
    {(ownership || costMode) && <fieldset className="grid gap-3 rounded-md border border-border p-3" disabled={sendMutation.isPending}>
      <legend className="px-1 text-sm font-medium">Selección de costes</legend>
      {costMode ? <>
        <label className="flex flex-col gap-1 text-sm">Ámbito Azure
          <select className={fieldClass} value={costGroup} onChange={(event) => {
            setCostGroup(event.target.value as AzureCostSelection["group_by"]);
            setValue("");
          }}>
            <option value="subscription">Suscripción</option>
            <option value="account">Cuenta de facturación</option>
            <option value="service">Servicio</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">Suscripción (opcional)
          <input className={fieldClass} value={subscription} maxLength={256} onChange={(event) => setSubscription(event.target.value)} />
        </label>
      </> : <label className="flex flex-col gap-1 text-sm">Agrupar por
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
      </label>}
      {ownership && groupBy === "tag" && <label className="flex flex-col gap-1 text-sm">Clave de etiqueta
        <input className={fieldClass} value={tagKey} maxLength={256} onChange={(event) => setTagKey(event.target.value)} />
      </label>}
      <label className="flex flex-col gap-1 text-sm">Valor exacto (opcional)
        <input className={fieldClass} value={value} maxLength={256} onChange={(event) => setValue(event.target.value)} />
      </label>
      <p className="text-xs text-muted-foreground">El valor distingue mayúsculas y minúsculas. Vacío: todos los grupos. Aplicación y owner requieren etiquetas explícitas.</p>
      {ownership && <label className="flex flex-col gap-1 text-sm">Moneda (opcional)
        <input className={fieldClass} value={currency} maxLength={3} placeholder="EUR" onChange={(event) => setCurrency(event.target.value)} />
      </label>}
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">Inicio UTC (incluido)
          <input className={fieldClass} type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
        </label>
        <label className="flex flex-col gap-1 text-sm">Fin UTC (excluido)
          <input className={fieldClass} type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
        </label>
      </div>
      <p className="text-xs text-muted-foreground">Indica ambas fechas o deja ambas vacías para el mes actual UTC. Sin moneda se muestran los totales separados por moneda.</p>
      {!startDate && !endDate && referencePeriod && <p className="text-xs text-muted-foreground">Mes de referencia UTC: {referencePeriod.start} a {referencePeriod.end} (fin excluido).</p>}
      {!startDate && !endDate && reference.isError && !reference.data && <p role="alert" className="text-xs text-destructive">No se pudo cargar la fecha de referencia.</p>}
    </fieldset>}
    <textarea
      className={fieldClass}
      rows={5}
      aria-label="Pregunta"
      placeholder={ownership || costMode ? "Pregunta sobre los costes de la selección." : "Pregunta sobre los documentos ingeridos del cliente."}
      value={message}
      disabled={sendMutation.isPending}
      onChange={(event) => setMessage(event.target.value)}
    />
    {validationError && <p className="text-sm text-danger" role="alert">{validationError}</p>}
    {sendMutation.error && <p className="text-sm text-danger" role="alert">{sendMutation.error.message}</p>}
    <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
      type="submit" disabled={sendMutation.isPending || !message.trim()}>
      {sendMutation.isPending ? "Enviando..." : "Enviar"}
    </button>
  </form>;
}
