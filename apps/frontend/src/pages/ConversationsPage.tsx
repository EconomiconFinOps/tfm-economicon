import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useOutletContext } from "react-router";
import { SectionCard } from "../components/SectionCard";
import {
  createConversation,
  getConversation,
  listConversations,
  sendConversationMessage
} from "../services/api";
import type { AzureCostSelection, ConversationCreateRequest, MessageCreateRequest } from "../services/contracts";
import type { SessionOutletContext } from "../layouts/SessionGate";

export function ConversationsPage() {
  const { token, activeTenant } = useOutletContext<SessionOutletContext>();
  const queryClient = useQueryClient();
  const [selectedConversationId, setSelectedConversationId] = useState<string>("");
  const [title, setTitle] = useState<string>("Ops review");
  const [message, setMessage] = useState<string>("");
  const [costMode, setCostMode] = useState(false);
  const [costGrouping, setCostGrouping] = useState<AzureCostSelection["group_by"]>("subscription");
  const [costValue, setCostValue] = useState("");
  const [costSubscription, setCostSubscription] = useState("");
  const [costStart, setCostStart] = useState("");
  const [costEnd, setCostEnd] = useState("");
  const invalidCostPeriod = Boolean(costStart) !== Boolean(costEnd)
    || Boolean(costStart && costEnd && costStart >= costEnd);

  useEffect(() => {
    setCostValue("");
    setCostSubscription("");
    setMessage("");
  }, [activeTenant?.id]);

  const conversationsQuery = useQuery({
    queryKey: ["conversations", activeTenant?.id],
    queryFn: () => {
      if (!activeTenant) {
        throw new Error("Tenant required");
      }
      return listConversations(token, activeTenant.id);
    },
    enabled: Boolean(token && activeTenant?.id)
  });

  const conversationDetailQuery = useQuery({
    queryKey: ["conversation", activeTenant?.id, selectedConversationId],
    queryFn: () => {
      if (!activeTenant) {
        throw new Error("Tenant required");
      }
      return getConversation(token, activeTenant.id, selectedConversationId);
    },
    enabled: Boolean(token && activeTenant?.id && selectedConversationId)
  });

  useEffect(() => {
    const items = conversationsQuery.data?.items ?? [];
    if (!items.length) {
      setSelectedConversationId("");
      return;
    }

    const stillAvailable = items.some((item) => item.id === selectedConversationId);
    if (!stillAvailable) {
      setSelectedConversationId(items[0].id);
    }
  }, [conversationsQuery.data, selectedConversationId]);

  const createMutation = useMutation({
    mutationFn: (payload: ConversationCreateRequest) => {
      if (!activeTenant) {
        throw new Error("Tenant required");
      }
      return createConversation(token, activeTenant.id, payload);
    },
    onSuccess: (conversation) => {
      queryClient.invalidateQueries({ queryKey: ["conversations", activeTenant?.id] });
      setSelectedConversationId(conversation.id);
      setTitle("Ops review");
    }
  });

  const sendMutation = useMutation({
    mutationFn: (payload: MessageCreateRequest) => {
      if (!activeTenant) {
        throw new Error("Tenant required");
      }
      return sendConversationMessage(token, activeTenant.id, selectedConversationId, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations", activeTenant?.id] });
      queryClient.invalidateQueries({
        queryKey: ["conversation", activeTenant?.id, selectedConversationId]
      });
      setMessage("");
    }
  });

  function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createMutation.mutate({ title });
  }

  function handleSend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (costMode && invalidCostPeriod) return;
    sendMutation.mutate({ content: message, ...(costMode ? { cost_query: {
      group_by: costGrouping,
      ...(costValue.trim() ? { value: costValue.trim() } : {}),
      ...(costSubscription.trim() ? { subscription_id: costSubscription.trim() } : {}),
      ...(costStart ? { start_date: costStart, end_date: costEnd } : {})
    } } : {}) });
  }

  if (!activeTenant) {
    return (
      <SectionCard
        title="Tenant required"
        subtitle="Choose a tenant before opening assistant conversations."
      >
        <p className="text-sm text-muted-foreground">No active tenant selected.</p>
      </SectionCard>
    );
  }

  const messages = conversationDetailQuery.data?.messages ?? [];

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <SectionCard
        title="Conversations"
        subtitle="Each conversation stays scoped to the active tenant and operator."
      >
        <form className="flex gap-2" onSubmit={handleCreate}>
          <input
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="New conversation title"
          />
          <button
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-foreground hover:bg-primary/80 disabled:opacity-60"
            type="submit"
            disabled={createMutation.isPending}
          >
            New
          </button>
        </form>

        {createMutation.error ? (
          <p className="mt-2 text-sm text-danger">{createMutation.error.message}</p>
        ) : null}
        {conversationsQuery.error ? (
          <p className="mt-2 text-sm text-danger" role="alert">
            {conversationsQuery.error.message}
          </p>
        ) : null}

        <div className="mt-4 flex flex-col gap-2">
          {(conversationsQuery.data?.items ?? []).map((conversation) => (
            <button
              key={conversation.id}
              type="button"
              className={
                conversation.id === selectedConversationId
                  ? "rounded-md border border-primary bg-primary/10 px-3 py-2 text-left"
                  : "rounded-md border border-border bg-background px-3 py-2 text-left hover:border-primary"
              }
              onClick={() => setSelectedConversationId(conversation.id)}
            >
              <strong className="block text-sm text-foreground">{conversation.title}</strong>
              <span className="text-xs text-muted-foreground">
                {new Date(conversation.updated_at).toLocaleString()}
              </span>
            </button>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="Assistant chat"
        subtitle="Consulta documentos o el gasto Azure ingerido del tenant activo."
      >
        {conversationDetailQuery.error ? (
          <p className="text-sm text-danger" role="alert">
            {conversationDetailQuery.error.message}
          </p>
        ) : conversationDetailQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading conversation...</p>
        ) : selectedConversationId ? (
          <>
            <div className="flex flex-col gap-3">
              {messages.map((entry) => (
                <article
                  key={entry.id}
                  className="rounded-md border border-border bg-background p-3"
                >
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{entry.role}</p>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-foreground">{entry.content}</p>
                </article>
              ))}
            </div>

            <form className="mt-4 flex flex-col gap-4" onSubmit={handleSend}>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={costMode} onChange={(event) => setCostMode(event.target.checked)} />
                Consultar gasto Azure
              </label>
              {costMode ? (
                <fieldset className="grid grid-cols-1 gap-3 rounded-md border border-border p-3 sm:grid-cols-2">
                  <legend className="px-1 text-sm">Ámbito y periodo del gasto</legend>
                  <label className="flex flex-col gap-1 text-sm">Agrupar por
                    <select className="rounded-md border border-border bg-background p-2" value={costGrouping}
                      onChange={(event) => { setCostGrouping(event.target.value as AzureCostSelection["group_by"]); setCostValue(""); }}>
                      <option value="subscription">Suscripción</option>
                      <option value="account">Cuenta de facturación</option>
                      <option value="service">Servicio</option>
                    </select>
                  </label>
                  <label className="flex flex-col gap-1 text-sm">Valor exacto (opcional)
                    <input className="rounded-md border border-border bg-background p-2" value={costValue}
                      onChange={(event) => setCostValue(event.target.value)} placeholder="Vacío: todos los valores" maxLength={256} />
                  </label>
                  <label className="flex flex-col gap-1 text-sm">Limitar a suscripción (opcional)
                    <input className="rounded-md border border-border bg-background p-2" value={costSubscription}
                      onChange={(event) => setCostSubscription(event.target.value)} maxLength={256} />
                  </label>
                  <p className="text-xs text-muted-foreground">Sin fechas: mes UTC actual. Los valores deben coincidir exactamente con los datos ingeridos.</p>
                  <label className="flex flex-col gap-1 text-sm">Desde (UTC)
                    <input className="rounded-md border border-border bg-background p-2" type="date" value={costStart}
                      onChange={(event) => setCostStart(event.target.value)} />
                  </label>
                  <label className="flex flex-col gap-1 text-sm">Hasta (UTC, excluido)
                    <input className="rounded-md border border-border bg-background p-2" type="date" value={costEnd}
                      onChange={(event) => setCostEnd(event.target.value)} />
                  </label>
                  {invalidCostPeriod ? <p role="alert" className="text-sm text-danger">Indica ambas fechas y un fin posterior al inicio.</p> : null}
                </fieldset>
              ) : null}
              <textarea
                className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                rows={5}
                aria-label="Pregunta al asistente"
                placeholder={costMode ? "¿Cuánto hemos gastado en el ámbito seleccionado?" : "Ask the assistant about the ingested tenant documents."}
                value={message}
                onChange={(event) => setMessage(event.target.value)}
              />
              {sendMutation.error ? (
                <p className="text-sm text-danger">{sendMutation.error.message}</p>
              ) : null}
              <button
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-foreground hover:bg-primary/80 disabled:opacity-60"
                type="submit"
                disabled={sendMutation.isPending || !message.trim() || (costMode && invalidCostPeriod)}
              >
                {sendMutation.isPending ? "Sending..." : "Send"}
              </button>
            </form>
          </>
        ) : conversationsQuery.error ? null : (
          <p className="text-sm text-muted-foreground">Create a conversation to start the assistant flow.</p>
        )}
      </SectionCard>
    </div>
  );
}
