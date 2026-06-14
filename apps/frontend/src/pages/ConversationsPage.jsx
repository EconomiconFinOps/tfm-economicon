import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { SectionCard } from "../components/SectionCard";
import {
  createConversation,
  getConversation,
  listConversations,
  sendConversationMessage
} from "../services/api";

export function ConversationsPage({ token, activeTenant }) {
  const queryClient = useQueryClient();
  const [selectedConversationId, setSelectedConversationId] = useState("");
  const [title, setTitle] = useState("Ops review");
  const [message, setMessage] = useState("");

  const conversationsQuery = useQuery({
    queryKey: ["conversations", activeTenant?.id],
    queryFn: () => listConversations(token, activeTenant.id),
    enabled: Boolean(token && activeTenant?.id)
  });

  const conversationDetailQuery = useQuery({
    queryKey: ["conversation", activeTenant?.id, selectedConversationId],
    queryFn: () => getConversation(token, activeTenant.id, selectedConversationId),
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
    mutationFn: (payload) => createConversation(token, activeTenant.id, payload),
    onSuccess: (conversation) => {
      queryClient.invalidateQueries({ queryKey: ["conversations", activeTenant.id] });
      setSelectedConversationId(conversation.id);
      setTitle("Ops review");
    }
  });

  const sendMutation = useMutation({
    mutationFn: (payload) => sendConversationMessage(
      token,
      activeTenant.id,
      selectedConversationId,
      payload
    ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations", activeTenant.id] });
      queryClient.invalidateQueries({
        queryKey: ["conversation", activeTenant.id, selectedConversationId]
      });
      setMessage("");
    }
  });

  function handleCreate(event) {
    event.preventDefault();
    createMutation.mutate({ title });
  }

  function handleSend(event) {
    event.preventDefault();
    sendMutation.mutate({ content: message });
  }

  if (!activeTenant) {
    return (
      <SectionCard
        title="Tenant required"
        subtitle="Choose a tenant before opening assistant conversations."
      >
        <p>No active tenant selected.</p>
      </SectionCard>
    );
  }

  const messages = conversationDetailQuery.data?.messages ?? [];

  return (
    <div className="chat-layout">
      <SectionCard
        title="Conversations"
        subtitle="Each conversation stays scoped to the active tenant and operator."
      >
        <form className="inline-form" onSubmit={handleCreate}>
          <input
            className="text-input"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="New conversation title"
          />
          <button className="primary-button" type="submit" disabled={createMutation.isPending}>
            New
          </button>
        </form>

        {createMutation.error ? <p className="error-copy">{createMutation.error.message}</p> : null}

        <div className="conversation-list">
          {(conversationsQuery.data?.items ?? []).map((conversation) => (
            <button
              key={conversation.id}
              type="button"
              className={
                conversation.id === selectedConversationId
                  ? "conversation-item active"
                  : "conversation-item"
              }
              onClick={() => setSelectedConversationId(conversation.id)}
            >
              <strong>{conversation.title}</strong>
              <span>{new Date(conversation.updated_at).toLocaleString()}</span>
            </button>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="Assistant chat"
        subtitle="Replies use retrieval over pgvector filtered by the active tenant."
      >
        {conversationDetailQuery.isLoading ? (
          <p>Loading conversation...</p>
        ) : selectedConversationId ? (
          <>
            <div className="message-list">
              {messages.map((entry) => (
                <article key={entry.id} className={`message-bubble ${entry.role}`}>
                  <p className="message-role">{entry.role}</p>
                  <p>{entry.content}</p>
                </article>
              ))}
            </div>

            <form className="form-stack" onSubmit={handleSend}>
              <textarea
                className="text-area"
                rows={5}
                placeholder="Ask the assistant about the ingested tenant documents."
                value={message}
                onChange={(event) => setMessage(event.target.value)}
              />
              {sendMutation.error ? <p className="error-copy">{sendMutation.error.message}</p> : null}
              <button
                className="primary-button"
                type="submit"
                disabled={sendMutation.isPending || !message.trim()}
              >
                {sendMutation.isPending ? "Sending..." : "Send"}
              </button>
            </form>
          </>
        ) : (
          <p>Create a conversation to start the assistant flow.</p>
        )}
      </SectionCard>
    </div>
  );
}
