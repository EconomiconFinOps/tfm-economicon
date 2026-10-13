// ConversationsPage: en la nueva arquitectura de rutas (JUP-095, grupo 6,
// sub-ronda c -- ver Addendum de design.md) deja de recibir `token`/
// `activeTenant` como props desde `App.jsx` y pasa a leerlos via
// `useOutletContext<SessionOutletContext>()`, mismo patron que `IngestPage`.
// JUP-037 isolates the message composer per conversation and tenant, while
// preserving document retrieval alongside structured ownership questions.
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useOutletContext } from "react-router";
import { SectionCard } from "../components/SectionCard";
import { AnswerEvidence } from "../components/AnswerEvidence";
import { MessageComposer } from "../components/MessageComposer";
import {
  createConversation,
  getConversation,
  listConversations
} from "../services/api";
import type { ConversationCreateRequest } from "../services/contracts";
import type { SessionOutletContext } from "../layouts/SessionGate";

const ROLE_LABELS: Record<string, string> = { user: "Usuario", assistant: "Asistente" };

export function ConversationsPage() {
  const { token, activeTenant } = useOutletContext<SessionOutletContext>();
  const queryClient = useQueryClient();
  const [selectedConversationId, setSelectedConversationId] = useState<string>("");
  const [title, setTitle] = useState<string>("Revisión operativa");

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
    onSuccess: async (conversation) => {
      // Refresh the list before selecting the new ID. Otherwise the effect
      // above sees the old list and switches back to the previous conversation.
      await queryClient.invalidateQueries({ queryKey: ["conversations", activeTenant?.id] });
      setSelectedConversationId(conversation.id);
      setTitle("Revisión operativa");
    }
  });

  function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createMutation.mutate({ title });
  }

  if (!activeTenant) {
    return (
      <SectionCard
        title="Cliente requerido"
        subtitle="Elige un cliente antes de abrir conversaciones con el asistente."
      >
        <p className="text-sm text-muted-foreground">No hay ningún cliente activo.</p>
      </SectionCard>
    );
  }

  const messages = conversationDetailQuery.data?.messages ?? [];

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <SectionCard
        title="Conversaciones"
        subtitle="Cada conversación queda limitada al cliente activo y al operador."
      >
        <form className="flex gap-2" onSubmit={handleCreate}>
          <input
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-highlight"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Título de la nueva conversación"
          />
          <button
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
            type="submit"
            disabled={createMutation.isPending}
          >
            Nueva
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
                  ? "rounded-md border border-highlight bg-accent px-3 py-2 text-left"
                  : "rounded-md border border-border bg-background px-3 py-2 text-left hover:border-highlight"
              }
              onClick={() => setSelectedConversationId(conversation.id)}
            >
              <strong className="block text-sm text-foreground">{conversation.title}</strong>
              <span className="text-xs text-muted-foreground">
                {new Date(conversation.updated_at).toLocaleString("es-ES")}
              </span>
            </button>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="Chat con el asistente"
        subtitle="Consulta documentos o costes por propiedad dentro del cliente activo."
      >
        {conversationDetailQuery.error ? (
          <p className="text-sm text-danger" role="alert">
            {conversationDetailQuery.error.message}
          </p>
        ) : conversationDetailQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">Cargando conversación...</p>
        ) : selectedConversationId ? (
          <>
            <div className="flex flex-col gap-3">
              {messages.map((entry) => (
                <article
                  key={entry.id}
                  className="rounded-md border border-border bg-background p-3"
                >
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{Object.hasOwn(ROLE_LABELS, entry.role) ? ROLE_LABELS[entry.role] : entry.role}</p>
                  {entry.role === "assistant"
                    ? <AnswerEvidence content={entry.content} metadata={entry.metadata} />
                    : <p className="mt-1 whitespace-pre-wrap text-sm text-foreground">{entry.content}</p>}
                </article>
              ))}
            </div>

            <MessageComposer key={`${activeTenant.id}:${selectedConversationId}`}
              token={token} tenantId={activeTenant.id} conversationId={selectedConversationId} />
          </>
        ) : conversationsQuery.error ? null : (
          <p className="text-sm text-muted-foreground">Crea una conversación para empezar a usar el asistente.</p>
        )}
      </SectionCard>
    </div>
  );
}
