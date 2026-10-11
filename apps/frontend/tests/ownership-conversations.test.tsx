import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { assistantMessage, assistantReply, billing, conversation, tenants } from "./fixtures";
import { deferredResponse, expectTenantRequest, jsonResponse, mockBackend, renderApp, restoreSession } from "./test-support";

const collection = "/assistant/conversations";
const detail = `${collection}/${conversation.id}`;
const messagePath = `${detail}/messages`;
const second = { ...conversation, id: "second-conversation", title: "Second conversation" };
const evidence = {
  schema_version: "1.0", adapter_version: "ownership-1.0", id: `cost:${"a".repeat(64)}`,
  source: "azure_cost_records/completed", status: "partial", data_environment: "unknown",
  provenance: { ingestion_ids: ["ingestion-demo-1"], observed_day_count: 2, first_usage_date: "2026-09-01", last_usage_date: "2026-09-02" },
  selected_groups: [{ value: "App-A", cost: "10.00", currency: "EUR", record_count: 1 }],
  summary: {
    ...billing, group_by: "tag", tag_key: "application", data_status: "partial", missing_dimension_count: 1,
    period: { start_date: "2026-09-01", end_date: "2026-10-01", timezone: "UTC" },
    totals: [{ cost: "12.00", currency: "EUR", record_count: 2 }],
    groups: [
      { value: "App-A", subscription_id: null, cost: "10.00", currency: "EUR", record_count: 1 },
      { value: null, subscription_id: null, cost: "2.00", currency: "EUR", record_count: 1 }
    ], monthly_spend: "12.00", currency: "EUR"
  }
};
const costMessage = {
  ...assistantMessage,
  content: "Coste registrado por aplicación: App-A.\nGasto de la selección: 10.00 EUR.\nSin aplicación: 2.00 EUR.",
  metadata: { citations: [], source_citations: [], cost_evidence: evidence }
};

function backend(overrides: Parameters<typeof mockBackend>[0] = {}) {
  return mockBackend({
    [`GET ${collection}`]: () => jsonResponse({ items: [conversation, second] }),
    [`GET ${detail}`]: () => jsonResponse({ conversation, messages: [] }),
    [`GET ${collection}/${second.id}`]: () => jsonResponse({ conversation: second, messages: [] }),
    [`POST ${messagePath}`]: () => jsonResponse(assistantReply, 201),
    ...overrides
  });
}

async function start() {
  restoreSession();
  const app = renderApp(["/assistant"]);
  const user = userEvent.setup();
  await user.click(await screen.findByRole("checkbox", { name: "Consultar costes por propiedad" }));
  await user.type(screen.getByRole("textbox", { name: "Pregunta" }), "¿Cuál es el coste registrado?");
  return { ...app, user };
}

describe("JUP-037 ownership conversations", () => {
  it("keeps a newly created conversation selected after refreshing the existing list", async () => {
    const created = { ...conversation, id: "created-ownership", title: "New ownership" };
    const refreshed = deferredResponse();
    let published = false;
    const { requests } = backend({
      [`GET ${collection}`]: () => published ? refreshed.promise : jsonResponse({ items: [conversation] }),
      [`POST ${collection}`]: () => {
        published = true;
        return jsonResponse(created, 201);
      },
      [`GET ${collection}/${created.id}`]: () => jsonResponse({ conversation: created, messages: [] }),
      [`POST ${collection}/${created.id}/messages`]: () => jsonResponse({ ...assistantReply, conversation: created }, 201)
    });
    const { user } = await start();
    await user.click(screen.getByRole("button", { name: /^New$/ }));
    await waitFor(() => expect(requests.filter((request) => request.method === "GET"
      && request.path === collection)).toHaveLength(2));
    await act(async () => refreshed.resolve({ items: [conversation, created] }));
    await screen.findByRole("button", { name: /New ownership/ });
    await waitFor(() => expect(screen.getByRole("textbox", { name: "Pregunta" })).toHaveValue(""));
    await user.click(screen.getByRole("checkbox", { name: "Consultar costes por propiedad" }));
    await user.type(screen.getByRole("textbox", { name: "Pregunta" }), "Coste del nuevo hilo");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(requests.some((request) => request.method === "POST"
      && request.path === `${collection}/${created.id}/messages`)).toBe(true));
    expect(requests.some((request) => request.method === "POST" && request.path === messagePath)).toBe(false);
  });

  it("sends an exact custom-tag selection and displays the persisted cost evidence", async () => {
    let sent = false;
    const { requests } = backend({
      [`GET ${detail}`]: () => jsonResponse({ conversation, messages: sent ? [costMessage] : [] }),
      [`POST ${messagePath}`]: () => {
        sent = true;
        return jsonResponse({ ...assistantReply, assistant_message: costMessage }, 201);
      }
    });
    const { user } = await start();
    await user.selectOptions(screen.getByRole("combobox", { name: "Agrupar por" }), "tag");
    await user.type(screen.getByRole("textbox", { name: "Clave de etiqueta" }), "BusinessUnit");
    await user.type(screen.getByRole("textbox", { name: "Valor exacto (opcional)" }), "App-A");
    await user.type(screen.getByRole("textbox", { name: "Moneda (opcional)" }), "EUR");
    fireEvent.change(screen.getByLabelText("Inicio UTC (incluido)"), { target: { value: "2026-09-01" } });
    fireEvent.change(screen.getByLabelText("Fin UTC (excluido)"), { target: { value: "2026-10-01" } });
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByText("Gasto de la selección: 10.00 EUR.")).toBeVisible();
    expect(screen.getByText("Sin aplicación: 2.00 EUR.")).toBeVisible();
    const summary = screen.getByText("Evidencia de costes — Datos parciales");
    await user.click(summary);
    expect(screen.getByText(`Identificador: ${evidence.id}`)).toBeVisible();
    expect(screen.getByText("ingestion-demo-1")).toBeVisible();
    expect(screen.getByText("Días con registros observados: 2.")).toBeVisible();
    expect(screen.getByText("Primera fecha de uso: 2026-09-01.")).toBeVisible();
    expect(screen.getByText("Última fecha de uso: 2026-09-02.")).toBeVisible();
    expect(screen.getByText(/Entorno de datos no confirmado/)).toBeVisible();
    expect(screen.queryByText("Sin fuentes documentales utilizadas.")).not.toBeInTheDocument();
    const request = requests.find((item) => item.path === messagePath);
    expect(request?.body).toEqual({
      content: "¿Cuál es el coste registrado?",
      ownership_query: {
        group_by: "tag", tag_key: "BusinessUnit", value: "App-A", currency: "EUR",
        start_date: "2026-09-01", end_date: "2026-10-01"
      }
    });
    expectTenantRequest(request!);
  });

  it.each(["application", "owner", "project", "cost_center"])(
    "sends %s independently without tag aliases or implicit dates",
    async (group) => {
      const { requests } = backend();
      const { user } = await start();
      await user.selectOptions(screen.getByRole("combobox", { name: "Agrupar por" }), "tag");
      await user.type(screen.getByRole("textbox", { name: "Clave de etiqueta" }), "org");
      await user.selectOptions(screen.getByRole("combobox", { name: "Agrupar por" }), group);
      await user.type(screen.getByRole("textbox", { name: "Valor exacto (opcional)" }), "Team-A");
      await user.click(screen.getByRole("button", { name: "Send" }));
      await waitFor(() => expect(requests.find((item) => item.path === messagePath)?.body).toEqual({
        content: "¿Cuál es el coste registrado?", ownership_query: { group_by: group, value: "Team-A" }
      }));
    }
  );

  it("rejects incomplete or reversed dates, a missing tag key and an invalid currency before sending", async () => {
    const { requests } = backend();
    const { user } = await start();
    fireEvent.change(screen.getByLabelText("Inicio UTC (incluido)"), { target: { value: "2026-09-01" } });
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Indica ambas fechas");
    fireEvent.change(screen.getByLabelText("Fin UTC (excluido)"), { target: { value: "2026-09-01" } });
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(screen.getByRole("alert")).toHaveTextContent("posterior");
    fireEvent.change(screen.getByLabelText("Inicio UTC (incluido)"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("Fin UTC (excluido)"), { target: { value: "" } });
    await user.type(screen.getByRole("textbox", { name: "Moneda (opcional)" }), "eUr");
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(screen.getByRole("alert")).toHaveTextContent("tres letras mayúsculas");
    await user.clear(screen.getByRole("textbox", { name: "Moneda (opcional)" }));
    await user.selectOptions(screen.getByRole("combobox", { name: "Agrupar por" }), "tag");
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(screen.getByRole("alert")).toHaveTextContent("clave de la etiqueta");
    expect(requests.filter((item) => item.method === "POST")).toHaveLength(0);
  });

  it("retains a failed selection for retry and clears fields and errors on conversation change", async () => {
    backend({ [`POST ${messagePath}`]: () => jsonResponse({ detail: "Ownership unavailable" }, 503) });
    const { user } = await start();
    await user.type(screen.getByRole("textbox", { name: "Valor exacto (opcional)" }), "Private application");
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Ownership unavailable");
    expect(screen.getByRole("textbox", { name: "Valor exacto (opcional)" })).toHaveValue("Private application");
    expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();
    await user.click(screen.getByRole("button", { name: /Second conversation/ }));
    const checkbox = await screen.findByRole("checkbox", { name: "Consultar costes por propiedad" });
    expect(checkbox).not.toBeChecked();
    expect(screen.getByRole("textbox", { name: "Pregunta" })).toHaveValue("");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    await user.click(checkbox);
    expect(screen.getByRole("textbox", { name: "Valor exacto (opcional)" })).toHaveValue("");
  });

  it.each(["success", "error"])("isolates delayed %s when another conversation is selected", async (outcome) => {
    const pending = deferredResponse();
    backend({ [`POST ${messagePath}`]: () => pending.promise });
    const { user, client } = await start();
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(screen.getByRole("button", { name: "Sending..." })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: /Second conversation/ }));
    await user.click(await screen.findByRole("checkbox", { name: "Consultar costes por propiedad" }));
    await user.type(screen.getByRole("textbox", { name: "Pregunta" }), "New question");
    await user.type(screen.getByRole("textbox", { name: "Valor exacto (opcional)" }), "New value");
    await act(async () => pending.resolve(outcome === "success" ? assistantReply : { detail: "Old request failed" }, outcome === "success" ? 201 : 503));
    await waitFor(() => expect(client.isMutating()).toBe(0));
    expect(screen.getByRole("textbox", { name: "Pregunta" })).toHaveValue("New question");
    expect(screen.getByRole("textbox", { name: "Valor exacto (opcional)" })).toHaveValue("New value");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();
  });

  it("clears ownership fields and validation errors when changing tenant", async () => {
    backend();
    const { user } = await start();
    await user.type(screen.getByRole("textbox", { name: "Valor exacto (opcional)" }), "Private value");
    fireEvent.change(screen.getByLabelText("Inicio UTC (incluido)"), { target: { value: "2026-09-01" } });
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(screen.getByRole("alert")).toBeVisible();
    await user.selectOptions(screen.getByRole("combobox", { name: "Ambito de cliente" }), tenants[1].id);
    const checkbox = await screen.findByRole("checkbox", { name: "Consultar costes por propiedad" });
    expect(checkbox).not.toBeChecked();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Pregunta" })).toHaveValue("");
    await user.click(checkbox);
    expect(screen.getByRole("textbox", { name: "Valor exacto (opcional)" })).toHaveValue("");
    expect(screen.getByLabelText("Inicio UTC (incluido)")).toHaveValue("");
  });
});
