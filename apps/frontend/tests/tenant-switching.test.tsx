import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { assistantReply, conversation, ingestJob, tenants, userMessage } from "./fixtures";
import {
  deferredResponse,
  expectTenantRequest,
  jsonResponse,
  mockBackend,
  renderApp,
  restoreSession
} from "./test-support";

const collectionPath = "/assistant/conversations";
const northDetailPath = `${collectionPath}/${conversation.id}`;
const southConversation = {
  ...conversation,
  id: "conversation-south",
  tenant_id: tenants[1].id,
  title: "South cost review"
};
const southDetailPath = `${collectionPath}/${southConversation.id}`;
const southMessage = { ...userMessage, id: "message-south", content: "South tenant history" };
const composerPlaceholder = "Ask the assistant about the ingested tenant documents.";

function mockTenantConversations(overrides: Parameters<typeof mockBackend>[0] = {}) {
  return mockBackend({
    [`GET ${collectionPath}`]: ({ headers }) => jsonResponse({
      items: headers.get("X-Tenant-Id") === tenants[0].id ? [conversation] : [southConversation]
    }),
    [`GET ${northDetailPath}`]: () => jsonResponse({ conversation, messages: [userMessage] }),
    [`GET ${southDetailPath}`]: () => jsonResponse({
      conversation: southConversation,
      messages: [southMessage]
    }),
    ...overrides
  });
}

describe("tenant changes isolate page state", () => {
  it("resets conversation selection and drafts before requesting the next tenant's history", async () => {
    const user = userEvent.setup();
    const pendingSouthList = deferredResponse();
    const { requests } = mockTenantConversations({
      [`GET ${collectionPath}`]: ({ headers }) => headers.get("X-Tenant-Id") === tenants[0].id
        ? jsonResponse({ items: [conversation] })
        : pendingSouthList.promise
    });
    restoreSession(tenants[0].id);
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Assistant" }));
    expect(await screen.findByText(userMessage.content)).toBeVisible();
    await user.clear(screen.getByPlaceholderText("New conversation title"));
    await user.type(screen.getByPlaceholderText("New conversation title"), "North private title");
    await user.type(screen.getByPlaceholderText(composerPlaceholder), "North private draft");

    await user.selectOptions(screen.getByRole("combobox", { name: "Active tenant" }), tenants[1].id);
    expect(screen.queryByText(userMessage.content)).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue("North private draft")).not.toBeInTheDocument();
    expect(screen.getByPlaceholderText("New conversation title")).toHaveValue("Ops review");

    await act(async () => pendingSouthList.resolve({ items: [southConversation] }));
    expect(await screen.findByText(southMessage.content)).toBeVisible();
    expect(screen.getByPlaceholderText(composerPlaceholder)).toHaveValue("");
    for (const request of requests.filter((request) => request.path === northDetailPath)) {
      expectTenantRequest(request, tenants[0].id);
    }
    for (const request of requests.filter((request) => request.path === southDetailPath)) {
      expectTenantRequest(request, tenants[1].id);
    }
    expect(requests.some((request) => request.path === southDetailPath)).toBe(true);
  });

  it.each(["success", "error"] as const)(
    "keeps new-tenant conversation drafts independent of late mutation %s",
    async (outcome) => {
      const user = userEvent.setup();
      const pendingCreate = deferredResponse();
      const pendingSend = deferredResponse();
      const createdNorth = { ...conversation, id: "conversation-created-north", title: "North only" };
      const { requests } = mockTenantConversations({
        [`POST ${collectionPath}`]: () => pendingCreate.promise,
        [`POST ${northDetailPath}/messages`]: () => pendingSend.promise,
        [`GET ${collectionPath}/${createdNorth.id}`]: () => jsonResponse({
          conversation: createdNorth,
          messages: []
        })
      });
      restoreSession(tenants[0].id);
      const { client } = renderApp();
      await user.click(await screen.findByRole("button", { name: "Assistant" }));
      await screen.findByText(userMessage.content);
      await user.clear(screen.getByPlaceholderText("New conversation title"));
      await user.type(screen.getByPlaceholderText("New conversation title"), createdNorth.title);
      await user.click(screen.getByRole("button", { name: "New" }));
      await user.type(screen.getByPlaceholderText(composerPlaceholder), "North pending message");
      await user.click(screen.getByRole("button", { name: "Send" }));
      expect(screen.getByRole("button", { name: "New" })).toBeDisabled();
      expect(screen.getByRole("button", { name: "Sending..." })).toBeDisabled();

      await user.selectOptions(screen.getByRole("combobox", { name: "Active tenant" }), tenants[1].id);
      expect(await screen.findByText(southMessage.content)).toBeVisible();
      expect(screen.getByRole("button", { name: "New" })).toBeEnabled();
      expect(screen.getByPlaceholderText(composerPlaceholder)).toHaveValue("");
      await user.clear(screen.getByPlaceholderText("New conversation title"));
      await user.type(screen.getByPlaceholderText("New conversation title"), "South new title");
      await user.type(screen.getByPlaceholderText(composerPlaceholder), "South new message");
      const southRequestCount = requests.filter((request) => request.headers.get("X-Tenant-Id") === tenants[1].id).length;

      await act(async () => {
        pendingCreate.resolve(outcome === "success" ? createdNorth : { detail: "North creation failed" },
          outcome === "success" ? 201 : 503);
        pendingSend.resolve(outcome === "success" ? assistantReply : { detail: "North sending failed" },
          outcome === "success" ? 201 : 503);
      });
      await waitFor(() => expect(client.isMutating()).toBe(0));

      expect(screen.getByPlaceholderText("New conversation title")).toHaveValue("South new title");
      expect(screen.getByPlaceholderText(composerPlaceholder)).toHaveValue("South new message");
      expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();
      expect(screen.getByText(southMessage.content)).toBeVisible();
      expect(screen.queryByText(/North (creation|sending) failed/)).not.toBeInTheDocument();
      expect(requests.filter((request) => request.headers.get("X-Tenant-Id") === tenants[1].id)).toHaveLength(southRequestCount);
      for (const request of requests.filter((request) => request.method === "POST")) {
        expectTenantRequest(request, tenants[0].id);
      }
    }
  );

  it.each(["success", "error"] as const)(
    "clears an ingestion draft and its previous %s when switching tenants",
    async (outcome) => {
      const user = userEvent.setup();
      mockBackend({
        "POST /jobs/ingest": () => outcome === "success"
          ? jsonResponse(ingestJob, 202)
          : jsonResponse({ detail: "North ingestion failed" }, 503)
      });
      restoreSession(tenants[0].id);
      renderApp();
      await user.click(await screen.findByRole("button", { name: "Ingestions" }));
      await user.clear(screen.getByRole("textbox", { name: "Source" }));
      await user.type(screen.getByRole("textbox", { name: "Source" }), "north-private-source");
      await user.type(screen.getByRole("textbox", { name: "Artifact URI" }), "s3://north/private.txt");
      await user.type(screen.getByRole("textbox", { name: "Text content" }), "North private document");
      await user.click(screen.getByRole("button", { name: "Queue ingestion" }));
      await screen.findByText(outcome === "success" ? ingestJob.job_id : /North ingestion failed/);

      await user.selectOptions(screen.getByRole("combobox", { name: "Active tenant" }), tenants[1].id);
      expect(screen.getByRole("textbox", { name: "Source" })).toHaveValue("aws-cur");
      expect(screen.getByRole("textbox", { name: "Artifact URI" })).toHaveValue("");
      expect(screen.getByRole("textbox", { name: "Text content" })).toHaveValue("");
      expect(screen.queryByRole("heading", { name: "Job accepted" })).not.toBeInTheDocument();
      expect(screen.queryByText(/North ingestion failed/)).not.toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Queue ingestion" })).toBeEnabled();
    }
  );

  it.each(["success", "error"] as const)(
    "keeps a new-tenant ingestion independent of the previous tenant's pending %s",
    async (outcome) => {
      const user = userEvent.setup();
      const pendingNorth = deferredResponse();
      const pendingSouth = deferredResponse();
      const southJob = { ...ingestJob, job_id: "job-south-document" };
      const { requests } = mockBackend({
        "POST /jobs/ingest": ({ headers }) => headers.get("X-Tenant-Id") === tenants[0].id
          ? pendingNorth.promise
          : pendingSouth.promise
      });
      restoreSession(tenants[0].id);
      const { client } = renderApp();
      await user.click(await screen.findByRole("button", { name: "Ingestions" }));
      await user.type(screen.getByRole("textbox", { name: "Text content" }), "North document");
      await user.click(screen.getByRole("button", { name: "Queue ingestion" }));
      expect(screen.getByRole("button", { name: "Queueing job..." })).toBeDisabled();

      await user.selectOptions(screen.getByRole("combobox", { name: "Active tenant" }), tenants[1].id);
      expect(screen.getByRole("textbox", { name: "Text content" })).toHaveValue("");
      expect(screen.getByRole("button", { name: "Queue ingestion" })).toBeEnabled();
      await user.type(screen.getByRole("textbox", { name: "Text content" }), "South document");
      await user.click(screen.getByRole("button", { name: "Queue ingestion" }));
      await act(async () => pendingSouth.resolve(southJob, 202));
      expect(await screen.findByText(southJob.job_id)).toBeVisible();

      await act(async () => pendingNorth.resolve(
        outcome === "success" ? ingestJob : { detail: "North ingestion failed late" },
        outcome === "success" ? 202 : 503
      ));
      await waitFor(() => expect(client.isMutating()).toBe(0));
      expect(screen.getByText(southJob.job_id)).toBeVisible();
      expect(screen.queryByText(ingestJob.job_id)).not.toBeInTheDocument();
      expect(screen.queryByText(/North ingestion failed late/)).not.toBeInTheDocument();
      expect(screen.getByRole("textbox", { name: "Text content" })).toHaveValue("South document");
      const submitted = requests.filter((request) => request.method === "POST" && request.path === "/jobs/ingest");
      expect(submitted).toHaveLength(2);
      for (const [index, request] of submitted.entries()) {
        expectTenantRequest(request, tenants[index].id);
        expect(request.body).toMatchObject({
          tenant_id: tenants[index].id,
          text_content: index === 0 ? "North document" : "South document"
        });
      }
    }
  );
});
