import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useReferenceDate } from "../hooks/useReferenceDate";
import { referenceMonth } from "../lib/referenceDate";
import { ApiError, sendConversationMessage } from "../services/api";
import type { MessageCreateRequest, OwnershipQuery } from "../services/contracts";
import { AnomalyExplanationFields } from "./AnomalyExplanationFields";

const fieldClass = "rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-highlight";

// Pregunta que se propone al activar el modo «Explicar una anomalia» con el cuadro vacio.
const PROPOSED_ANOMALY_QUESTION = "¿Por qué se ha marcado esta anomalía?";

// El backend responde a los fallos de la explicacion con `detail.code`. Se traduce por CODIGO y no por
// estado HTTP: un 404 tambien lo da la conversacion inexistente (con `detail` como cadena) y un 409 o un
// 422 pueden venir de otras causas; solo los dos codigos de anomalia tienen texto propio. Cualquier otro
// error conserva el mensaje generico de siempre (el cuerpo de la respuesta).
function anomalyErrorText(error: Error): string {
  if (!(error instanceof ApiError)) return error.message;
  try {
    const body: unknown = JSON.parse(error.message);
    const detail = typeof body === "object" && body !== null ? (body as { detail?: unknown }).detail : undefined;
    const code = typeof detail === "object" && detail !== null ? (detail as { code?: unknown }).code : undefined;
    if (code === "anomaly_episode_not_found") return "No se ha encontrado esa anomalía en el cliente activo. Actualiza la lista y elige otra.";
    if (code === "anomaly_explanation_unavailable") return "Esta anomalía no se puede explicar con las reglas actuales.";
  } catch { /* Cuerpo que no es JSON: se muestra tal cual. */ }
  return error.message;
}

// The parent keys this composer by tenant and conversation. A pending request
// keeps its original query keys and cannot clear another conversation's draft.
// `initialEpisodeId` (parametro `?episode=` de la direccion) solo arma el modo de anomalia al nacer el
// redactor; es un dato no fiable que `AnomalyExplanationFields` valida contra la lista del cliente.
// `onSent` avisa a la pagina de un envio correcto para que limpie ese parametro. Ambas son opcionales
// para no tocar los usos que no conocen el modo.
export function MessageComposer({ token, tenantId, conversationId, initialEpisodeId = "", onSent }: {
  token: string; tenantId: string; conversationId: string; initialEpisodeId?: string; onSent?: () => void;
}) {
  const queryClient = useQueryClient();
  const [anomaly, setAnomaly] = useState(initialEpisodeId !== "");
  const [episodeId, setEpisodeId] = useState("");
  const [message, setMessage] = useState(initialEpisodeId !== "" ? PROPOSED_ANOMALY_QUESTION : "");
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
      onSent?.();
    }
  });

  function handleSend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError("");
    sendMutation.reset();
    if (!message.trim()) return;
    const payload: MessageCreateRequest = { content: message };
    if (anomaly) {
      // Una sola seleccion por mensaje: el modo de anomalia nunca lleva `ownership_query`.
      if (!episodeId) return;
      payload.anomaly_query = { episode_id: episodeId };
      sendMutation.mutate(payload);
      return;
    }
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
        // Los dos modos son excluyentes (una seleccion estructurada por mensaje): activar uno apaga el otro.
        if (event.target.checked) {
          setAnomaly(false);
          setEpisodeId("");
        }
        setOwnership(event.target.checked);
        setValidationError("");
        sendMutation.reset();
      }} disabled={sendMutation.isPending} />
      Consultar costes por propiedad
    </label>
    <label className="flex items-center gap-2 text-sm text-foreground">
      <input type="checkbox" checked={anomaly} onChange={(event) => {
        if (event.target.checked) {
          setOwnership(false);
          // Se propone la pregunta solo con el cuadro vacio: nunca se pisa lo que la persona ya escribio.
          if (!message.trim()) setMessage(PROPOSED_ANOMALY_QUESTION);
        } else {
          setEpisodeId("");
        }
        setAnomaly(event.target.checked);
        setValidationError("");
        sendMutation.reset();
      }} disabled={sendMutation.isPending} />
      Explicar una anomalía
    </label>
    {anomaly && <AnomalyExplanationFields token={token} tenantId={tenantId} selected={episodeId}
      onSelect={setEpisodeId} linkedId={initialEpisodeId} disabled={sendMutation.isPending} />}
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
      {!startDate && !endDate && referencePeriod && <p className="text-xs text-muted-foreground">Mes de referencia UTC: {referencePeriod.start} a {referencePeriod.end} (fin excluido).</p>}
      {!startDate && !endDate && reference.isError && !reference.data && <p role="alert" className="text-xs text-destructive">No se pudo cargar la fecha de referencia.</p>}
    </fieldset>}
    <textarea
      className={fieldClass}
      rows={5}
      aria-label="Pregunta"
      placeholder={anomaly ? "Pregunta sobre la anomalía elegida."
        : ownership ? "Pregunta sobre los costes de la selección." : "Pregunta sobre los documentos ingeridos del cliente."}
      value={message}
      disabled={sendMutation.isPending}
      onChange={(event) => setMessage(event.target.value)}
    />
    {validationError && <p className="text-sm text-danger" role="alert">{validationError}</p>}
    {sendMutation.error && <p className="text-sm text-danger" role="alert">{anomalyErrorText(sendMutation.error)}</p>}
    <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
      type="submit" disabled={sendMutation.isPending || !message.trim() || (anomaly && !episodeId)}>
      {sendMutation.isPending ? "Enviando..." : "Enviar"}
    </button>
  </form>;
}
