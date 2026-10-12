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
  it("rotula en español quién escribió cada mensaje y deja pasar un rol que no conoce", async () => {
    mockBackend({
      [`GET ${collectionPath}`]: () => jsonResponse({ items: [conversation] }),
      [`GET ${detailPath}`]: () => jsonResponse({
        conversation,
        messages: [userMessage, assistantMessage, { ...userMessage, id: "message-system", role: "system", content: "Aviso interno" }]
      })
    });
    restoreSession();
    renderApp(["/assistant"]);

    const articles = await screen.findAllByRole("article");
    expect(articles).toHaveLength(3);
    expect(articles[0]).toHaveTextContent("Usuario");
    expect(articles[1]).toHaveTextContent("Asistente");
    expect(articles[2]).toHaveTextContent("system");
    expect(articles[2]).not.toHaveTextContent("Usuario");
  });

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
    renderApp(["/assistant"]);
    expect(await screen.findByText("Crea una conversación para empezar a usar el asistente.")).toBeVisible();

    const title = screen.getByPlaceholderText("Título de la nueva conversación");
    await user.clear(title);
    await user.type(title, conversation.title);
    await user.click(screen.getByRole("button", { name: "Nueva" }));
    expect(await screen.findByRole("button", { name: new RegExp(conversation.title) })).toBeVisible();
    const composer = await screen.findByPlaceholderText("Pregunta sobre los documentos ingeridos del cliente.");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    await user.type(composer, "   ");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    await user.clear(composer);
    await user.type(composer, userMessage.content);
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect(screen.getByRole("button", { name: "Enviando..." })).toBeDisabled();

    await act(async () => pendingReply.resolve(assistantReply, 201));
    expect(await screen.findByText(assistantMessage.content)).toBeVisible();
    expect(screen.getByText(userMessage.content)).toBeVisible();
    expect(composer).toHaveValue("");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
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
    renderApp(["/assistant"]);
    expect(await screen.findByText(userMessage.content)).toBeVisible();
    await user.click(screen.getByRole("button", { name: /Storage review/ }));
    expect(await screen.findByText("Cargando conversación...")).toBeVisible();
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
    renderApp(["/assistant"]);
    const title = await screen.findByPlaceholderText("Título de la nueva conversación");
    await user.clear(title);
    await user.type(title, "Retain this cost investigation");
    await user.click(screen.getByRole("button", { name: "Nueva" }));

    expect(await screen.findByText(/Conversation creation unavailable/)).toBeVisible();
    expect(title).toHaveValue("Retain this cost investigation");
    expect(screen.getByRole("button", { name: "Nueva" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Enviar" })).not.toBeInTheDocument();
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
    renderApp(["/assistant"]);
    const composer = await screen.findByPlaceholderText("Pregunta sobre los documentos ingeridos del cliente.");
    await user.type(composer, userMessage.content);
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Assistant connection interrupted")).toBeVisible();
    expect(composer).toHaveValue(userMessage.content);
    expect(screen.getByRole("button", { name: "Enviar" })).toBeEnabled();
    expect(screen.queryByText(assistantMessage.content)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText(assistantMessage.content)).toBeVisible();
    await waitFor(() => expect(composer).toHaveValue(""));
    expect(screen.queryByText("Assistant connection interrupted")).not.toBeInTheDocument();
  });

  it("reports a failed conversation list instead of presenting it as an empty result", async () => {
    mockBackend({
      [`GET ${collectionPath}`]: () => jsonResponse({ detail: "Conversation access denied." }, 403)
    });
    restoreSession();
    renderApp(["/assistant"]);

    expect(await screen.findByText(/Conversation access denied/)).toBeVisible();
    expect(screen.queryByText("Crea una conversación para empezar a usar el asistente.")).not.toBeInTheDocument();
    // El shell (Layout) sigue disponible aunque el listado falle: la
    // pantalla no revienta y el enlace de vuelta al indice sigue visible.
    // "Overview" no existe como boton en el Layout real (Spanish, NavLink);
    // el equivalente es el enlace "Coste Global" hacia "/".
    expect(screen.getByRole("link", { name: /Coste Global/i })).toBeVisible();
  });

  it("reports conversation detail failures without crashing the shell", async () => {
    mockBackend({
      [`GET ${collectionPath}`]: () => jsonResponse({ items: [conversation] }),
      [`GET ${detailPath}`]: () => jsonResponse({ detail: "Conversation not found." }, 404)
    });
    restoreSession();
    renderApp(["/assistant"]);

    expect(await screen.findByText(/Conversation not found/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Enviar" })).not.toBeInTheDocument();
    // "Logout" no existe como texto visible en el Layout real: el boton usa
    // aria-label="Cerrar sesión" (icono sin texto).
    expect(screen.getByRole("button", { name: "Cerrar sesión" })).toBeEnabled();
  });
});
