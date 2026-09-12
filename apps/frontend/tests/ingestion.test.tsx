import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ingestJob, tenants } from "./fixtures";
import {
  deferredResponse,
  expectTenantRequest,
  jsonResponse,
  mockBackend,
  renderApp,
  restoreSession
} from "./test-support";

describe("ingestion creation", () => {
  it("queues a document for the selected tenant and displays the accepted job", async () => {
    const user = userEvent.setup();
    const pending = deferredResponse();
    const { requests } = mockBackend({ "POST /jobs/ingest": () => pending.promise });
    restoreSession(tenants[1].id);
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Ingestions" }));

    await user.clear(screen.getByLabelText("Source"));
    await user.type(screen.getByLabelText("Source"), "azure-cost-export");
    await user.type(screen.getByLabelText("Artifact URI"), "s3://test-billing/september.csv");
    await user.type(screen.getByLabelText("Text content"), "Compute usage total: 9876 USD.");
    await user.click(screen.getByRole("button", { name: "Queue ingestion" }));
    expect(screen.getByRole("button", { name: "Queueing job..." })).toBeDisabled();
    expect(screen.queryByRole("heading", { name: "Job accepted" })).not.toBeInTheDocument();

    const submitted = requests.find((request) => request.path === "/jobs/ingest");
    expect(submitted).toBeDefined();
    expectTenantRequest(submitted!, tenants[1].id);
    expect(submitted?.body).toEqual({
      tenant_id: tenants[1].id,
      source: "azure-cost-export",
      artifact_uri: "s3://test-billing/september.csv",
      text_content: "Compute usage total: 9876 USD.",
      metadata: {}
    });

    await act(async () => pending.resolve(ingestJob, 202));
    expect(await screen.findByRole("heading", { name: "Job accepted" })).toBeVisible();
    expect(screen.getByText(ingestJob.job_id)).toBeVisible();
    expect(screen.getByText(ingestJob.status)).toBeVisible();
    expect(screen.getByText(ingestJob.queue)).toBeVisible();
  });

  it("keeps the document after queue rejection and permits a successful retry", async () => {
    const user = userEvent.setup();
    let attempts = 0;
    const { requests } = mockBackend({
      "POST /jobs/ingest": () => {
        attempts += 1;
        return attempts === 1
          ? jsonResponse({ detail: "Unable to publish the job into RabbitMQ." }, 503)
          : jsonResponse(ingestJob, 202);
      }
    });
    restoreSession();
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Ingestions" }));
    await user.type(screen.getByLabelText("Text content"), "Idle compute instances cost 678 USD.");
    await user.click(screen.getByRole("button", { name: "Queue ingestion" }));

    expect(await screen.findByText(/Unable to publish the job into RabbitMQ/)).toBeVisible();
    expect(screen.getByLabelText("Text content")).toHaveValue("Idle compute instances cost 678 USD.");
    expect(screen.queryByRole("heading", { name: "Job accepted" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Queue ingestion" })).toBeEnabled();
    const submitted = requests.find((request) => request.path === "/jobs/ingest");
    expect(submitted?.body).toMatchObject({ artifact_uri: null, tenant_id: tenants[0].id });

    await user.click(screen.getByRole("button", { name: "Queue ingestion" }));
    expect(await screen.findByRole("heading", { name: "Job accepted" })).toBeVisible();
    expect(screen.queryByText(/Unable to publish the job into RabbitMQ/)).not.toBeInTheDocument();
  });
});
