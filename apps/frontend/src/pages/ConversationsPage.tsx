// ConversationsPage: en la nueva arquitectura de rutas (JUP-095, grupo 6,
// sub-ronda c -- ver Addendum de design.md) deja de recibir `token`/
// `activeTenant` como props desde `App.jsx` y pasa a leerlos via
// `useOutletContext<SessionOutletContext>()`, mismo patron que `IngestPage`.
// Las dos queries, el efecto de auto-seleccion de conversacion y las dos
// mutaciones se conservan verbatim del origen (`ConversationsPage.jsx`);
// solo cambian el origen de `token`/`activeTenant` y la presentacion
// (Tailwind + SectionCard reconstruido).
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
import type { SessionOutletContext } from "../layouts/SessionGate";

// Formas minimas de los datos que esta pantalla necesita de la frontera
// JS->TS de `services/api.js` (no tipada, checkJs: false, JUP-096
// pendiente). Tipamos explicitamente lo que consumimos, sin forzar casts.
interface ConversationSummary {
  id: string;
  title: string;
  updated_at: string;
}

interface ConversationsListResult {
  items: ConversationSummary[];
}

interface ConversationMessage {
  id: string;
  role: string;
  content: string;
}

interface ConversationDetailResult {
  messages: ConversationMessage[];
}

export function ConversationsPage() {
  const { token, activeTenant } = useOutletContext<SessionOutletContext>();
  const queryClient = useQueryClient();
  const [selectedConversationId, setSelectedConversationId] = useState<string>("");
  const [title, setTitle] = useState<string>("Ops review");
  const [message, setMessage] = useState<string>("");

  const conversationsQuery = useQuery({
    queryKey: ["conversations", activeTenant?.id],
    queryFn: (): Promise<ConversationsListResult> =>
      listConversations(token, activeTenant?.id),
    enabled: Boolean(token && activeTenant?.id)
  });

  const conversationDetailQuery = useQuery({
    queryKey: ["conversation", activeTenant?.id, selectedConversationId],
    queryFn: (): Promise<ConversationDetailResult> =>
      getConversation(token, activeTenant?.id, selectedConversationId),
    enabled: Boolean(token && activeTenant?.id && selectedConversationId)
  });

  useEffect(() => {
    const items: ConversationSummary[] = conversationsQuery.data?.items ?? [];
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
    mutationFn: (payload: { title: string }) =>
      createConversation(token, activeTenant?.id, payload),
    onSuccess: (conversation: ConversationSummary) => {
      queryClient.invalidateQueries({ queryKey: ["conversations", activeTenant?.id] });
      setSelectedConversationId(conversation.id);
      setTitle("Ops review");
    }
  });

  const sendMutation = useMutation({
    mutationFn: (payload: { content: string }) =>
      sendConversationMessage(token, activeTenant?.id, selectedConversationId, payload),
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
    sendMutation.mutate({ content: message });
  }

  if (!activeTenant) {
    return (
      <SectionCard
        title="Tenant required"
        subtitle="Choose a tenant before opening assistant conversations."
      >
        <p className="text-sm text-slate-400">No active tenant selected.</p>
      </SectionCard>
    );
  }

  const messages: ConversationMessage[] = conversationDetailQuery.data?.messages ?? [];

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <SectionCard
        title="Conversations"
        subtitle="Each conversation stays scoped to the active tenant and operator."
      >
        <form className="flex gap-2" onSubmit={handleCreate}>
          <input
            className="flex-1 rounded-md border border-[#2d3748] bg-[#0f1419] px-3 py-2 text-sm text-white outline-none focus:border-[#0078d4]"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="New conversation title"
          />
          <button
            className="rounded-md bg-[#0078d4] px-4 py-2 text-sm font-medium text-white hover:bg-[#0078d4]/80 disabled:opacity-60"
            type="submit"
            disabled={createMutation.isPending}
          >
            New
          </button>
        </form>

        {createMutation.error ? (
          <p className="mt-2 text-sm text-red-400">{createMutation.error.message}</p>
        ) : null}

        <div className="mt-4 flex flex-col gap-2">
          {(conversationsQuery.data?.items ?? []).map((conversation) => (
            <button
              key={conversation.id}
              type="button"
              className={
                conversation.id === selectedConversationId
                  ? "rounded-md border border-[#0078d4] bg-[#0078d4]/10 px-3 py-2 text-left"
                  : "rounded-md border border-[#2d3748] bg-[#0f1419] px-3 py-2 text-left hover:border-[#0078d4]"
              }
              onClick={() => setSelectedConversationId(conversation.id)}
            >
              <strong className="block text-sm text-white">{conversation.title}</strong>
              <span className="text-xs text-slate-400">
                {new Date(conversation.updated_at).toLocaleString()}
              </span>
            </button>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="Assistant chat"
        subtitle="Replies use retrieval over pgvector filtered by the active tenant."
      >
        {conversationDetailQuery.isLoading ? (
          <p className="text-sm text-slate-400">Loading conversation...</p>
        ) : selectedConversationId ? (
          <>
            <div className="flex flex-col gap-3">
              {messages.map((entry) => (
                <article
                  key={entry.id}
                  className="rounded-md border border-[#2d3748] bg-[#0f1419] p-3"
                >
                  <p className="text-xs uppercase tracking-wide text-slate-400">{entry.role}</p>
                  <p className="mt-1 text-sm text-white">{entry.content}</p>
                </article>
              ))}
            </div>

            <form className="mt-4 flex flex-col gap-4" onSubmit={handleSend}>
              <textarea
                className="rounded-md border border-[#2d3748] bg-[#0f1419] px-3 py-2 text-sm text-white outline-none focus:border-[#0078d4]"
                rows={5}
                placeholder="Ask the assistant about the ingested tenant documents."
                value={message}
                onChange={(event) => setMessage(event.target.value)}
              />
              {sendMutation.error ? (
                <p className="text-sm text-red-400">{sendMutation.error.message}</p>
              ) : null}
              <button
                className="rounded-md bg-[#0078d4] px-4 py-2 text-sm font-medium text-white hover:bg-[#0078d4]/80 disabled:opacity-60"
                type="submit"
                disabled={sendMutation.isPending || !message.trim()}
              >
                {sendMutation.isPending ? "Sending..." : "Send"}
              </button>
            </form>
          </>
        ) : (
          <p className="text-sm text-slate-400">Create a conversation to start the assistant flow.</p>
        )}
      </SectionCard>
    </div>
  );
}
