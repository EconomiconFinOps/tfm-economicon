import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { assistantMessage, assistantReply, conversation, userMessage } from "./fixtures";
import {
  deferredResponse,
  expectTenantRequest,
  jsonResponse,
  mockBackend,
  renderApp,
  restoreSession
} from "./test-support";

const collectionPath = "/assistant/conversations";
const detailPath = `${collectionPath}/${conversation.id}`;
const messagePath = `${detailPath}/messages`;

describe("assistant conversations", () => {
  it("creates a conversation from an empty list and sends a message with a visible reply", async () => {
    const user = userEvent.setup();
    const pendingReply = deferredResponse();
    let created = false;
    let sent = false;
    const { requests } = mockBackend({
      [`GET ${collectionPath}`]: () => jsonResponse({ items: created ? [conversation] : [] }),
      [`POST ${collectionPath}`]: () => {
        created = true;
        return jsonResponse(conversation, 201);
      },
      [`GET ${detailPath}`]: () => jsonResponse({
        conversation,
        messages: sent ? [userMessage, assistantMessage] : []
      }),
      [`POST ${messagePath}`]: async () => {
        const response = await pendingReply.promise;
        sent = true;
        return response;
      }
    });
    restoreSession();
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Assistant" }));
    expect(await screen.findByText("Create a conversation to start the assistant flow.")).toBeVisible();

    const title = screen.getByPlaceholderText("New conversation title");
    await user.clear(title);
    await user.type(title, conversation.title);
    await user.click(screen.getByRole("button", { name: "New" }));
    expect(await screen.findByRole("button", { name: new RegExp(conversation.title) })).toBeVisible();
    const composer = await screen.findByPlaceholderText("Ask the assistant about the ingested tenant documents.");
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    await user.type(composer, "   ");
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    await user.clear(composer);
    await user.type(composer, userMessage.content);
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(screen.getByRole("button", { name: "Sending..." })).toBeDisabled();

    await act(async () => pendingReply.resolve(assistantReply, 201));
    expect(await screen.findByText(assistantMessage.content)).toBeVisible();
    expect(screen.getByText(userMessage.content)).toBeVisible();
    expect(composer).toHaveValue("");
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    const createdRequest = requests.find((request) => request.method === "POST" && request.path === collectionPath);
    const sentRequest = requests.find((request) => request.path === messagePath);
    expect(createdRequest?.body).toEqual({ title: conversation.title });
    expect(sentRequest?.body).toEqual({ content: userMessage.content });
    for (const request of requests.filter((request) => request.path.startsWith(collectionPath))) {
      expectTenantRequest(request);
    }
  });

  it("lists existing conversations and loads the selected conversation history", async () => {
    const user = userEvent.setup();
    const secondConversation = { ...conversation, id: "conversation-storage", title: "Storage review" };
    const pendingDetail = deferredResponse();
    const { requests } = mockBackend({
      [`GET ${collectionPath}`]: () => jsonResponse({ items: [conversation, secondConversation] }),
      [`GET ${detailPath}`]: () => jsonResponse({ conversation, messages: [userMessage] }),
      [`GET ${collectionPath}/${secondConversation.id}`]: () => pendingDetail.promise
    });
    restoreSession();
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Assistant" }));
    expect(await screen.findByText(userMessage.content)).toBeVisible();
    await user.click(screen.getByRole("button", { name: /Storage review/ }));
    expect(await screen.findByText("Loading conversation...")).toBeVisible();
    expect(screen.queryByText(userMessage.content)).not.toBeInTheDocument();

    await act(async () => pendingDetail.resolve({
      conversation: secondConversation,
      messages: [{ ...assistantMessage, id: "message-storage", content: "Archive old storage snapshots." }]
    }));
    expect(await screen.findByText("Archive old storage snapshots.")).toBeVisible();
    expect(requests.some((request) => request.path === `${collectionPath}/${secondConversation.id}`)).toBe(true);
  });

  it("preserves the proposed title after conversation creation fails", async () => {
    const user = userEvent.setup();
    mockBackend({
      [`GET ${collectionPath}`]: () => jsonResponse({ items: [] }),
      [`POST ${collectionPath}`]: () => jsonResponse({ detail: "Conversation creation unavailable." }, 503)
    });
    restoreSession();
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Assistant" }));
    const title = screen.getByPlaceholderText("New conversation title");
    await user.clear(title);
    await user.type(title, "Retain this cost investigation");
    await user.click(screen.getByRole("button", { name: "New" }));

    expect(await screen.findByText(/Conversation creation unavailable/)).toBeVisible();
    expect(title).toHaveValue("Retain this cost investigation");
    expect(screen.getByRole("button", { name: "New" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Send" })).not.toBeInTheDocument();
  });

  it("retains an unsent message after a send error and permits retry", async () => {
    const user = userEvent.setup();
    let attempts = 0;
    let sent = false;
    mockBackend({
      [`GET ${collectionPath}`]: () => jsonResponse({ items: [conversation] }),
      [`GET ${detailPath}`]: () => jsonResponse({
        conversation,
        messages: sent ? [userMessage, assistantMessage] : []
      }),
      [`POST ${messagePath}`]: () => {
        attempts += 1;
        if (attempts === 1) throw new TypeError("Assistant connection interrupted");
        sent = true;
        return jsonResponse(assistantReply, 201);
      }
    });
    restoreSession();
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Assistant" }));
    const composer = await screen.findByPlaceholderText("Ask the assistant about the ingested tenant documents.");
    await user.type(composer, userMessage.content);
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Assistant connection interrupted")).toBeVisible();
    expect(composer).toHaveValue(userMessage.content);
    expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();
    expect(screen.queryByText(assistantMessage.content)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByText(assistantMessage.content)).toBeVisible();
    await waitFor(() => expect(composer).toHaveValue(""));
    expect(screen.queryByText("Assistant connection interrupted")).not.toBeInTheDocument();
  });

  it("reports a failed conversation list instead of presenting it as an empty result", async () => {
    const user = userEvent.setup();
    mockBackend({
      [`GET ${collectionPath}`]: () => jsonResponse({ detail: "Conversation access denied." }, 403)
    });
    restoreSession();
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Assistant" }));

    expect(await screen.findByText(/Conversation access denied/)).toBeVisible();
    expect(screen.queryByText("Create a conversation to start the assistant flow.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Overview" })).toBeEnabled();
  });

  it("reports conversation detail failures without crashing the shell", async () => {
    const user = userEvent.setup();
    mockBackend({
      [`GET ${collectionPath}`]: () => jsonResponse({ items: [conversation] }),
      [`GET ${detailPath}`]: () => jsonResponse({ detail: "Conversation not found." }, 404)
    });
    restoreSession();
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Assistant" }));

    expect(await screen.findByText(/Conversation not found/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Send" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Logout" })).toBeEnabled();
  });
});
