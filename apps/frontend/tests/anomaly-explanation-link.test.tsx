import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { episode, episodeList } from "../src/test/anomalyFixtures";
import { assistantMessage, assistantReply, conversation, tenants } from "./fixtures";
import { deferredResponse, jsonResponse, mockBackend, renderApp, restoreSession } from "./test-support";

// JUP-038 tarea 6.4: entrada al modo «Explicar una anomalía» desde la dirección /assistant?episode=<id>
// (design.md, decision 10). Son pruebas de integracion: se monta la aplicacion en una dirección concreta
// con el enrutador en memoria y solo se simula el backend HTTP. `router.state.location.search` es la
// fuente de verdad de que el parametro siga o no en la dirección.

const collection = "/assistant/conversations";
const detail = `${collection}/${conversation.id}`;
const messagePath = `${detail}/messages`;
const episodesPath = "/billing/anomalies/episodes";

// Identificadores con el formato real del backend ("anomaly-" + 64 hexadecimales en minuscula).
const ID_A = `anomaly-${"a".repeat(64)}`;
const ID_B = `anomaly-${"b".repeat(64)}`;
const ID_C = `anomaly-${"c".repeat(64)}`;
const ID_OTHER_TENANT = `anomaly-${"d".repeat(64)}`;

const episodeA = episode({
  id: ID_A, currency: "EUR", service: "Compute", start_date: "2026-09-08", last_seen_date: "2026-09-09",
  reference_daily_cost: "400.00", opening_observed_cost: "550.00", accumulated_impact: "400.00",
  impact_day_count: 2, impact_through_date: "2026-09-09", severity: "P3", status: "new"
});
const episodeB = episode({
  id: ID_B, currency: "USD", service: null, start_date: "2026-09-10", last_seen_date: "2026-09-12",
  severity: "P1", status: "investigating"
});
const episodeC = episode({
  id: ID_C, currency: "EUR", service: "Storage", start_date: "2026-09-09", last_seen_date: "2026-09-11",
  severity: "P2", status: "resolved", closed_at: "2026-09-12T10:00:00Z", closure_reason: "Revisada"
});
const episodeD = episode({ id: ID_OTHER_TENANT, currency: "EUR", service: "Network", start_date: "2026-09-02" });

// Texto esperado de la opcion de un episodio en el selector (se escribe aqui con las palabras del panel,
// sin importar `severityLabels`, para que un cambio de etiquetas en el producto haga fallar la prueba).
function labelOf(item: ReturnType<typeof episode>): string {
  const severity = { P1: "Alta (P1)", P2: "Media (P2)", P3: "Baja (P3)" }[item.severity];
  const status = { new: "Nueva", investigating: "Investigando", resolved: "Resuelta", false_positive: "Falso positivo" }[item.status];
  return `${item.service ?? "(sin servicio)"} · ${item.currency} · desde ${item.start_date} · ${severity} · ${status}`;
}

const WARNING_TEXT ="La anomalía indicada en el enlace no está entre las de este cliente.";
const EMPTY_TEXT = "Este cliente no tiene anomalías guardadas. Se detectan desde el panel de Anomalías.";
const PROPOSED_QUESTION = "¿Por qué se ha marcado esta anomalía?";
const NOT_EXPLAINABLE = { detail: { code: "anomaly_explanation_unavailable" } };

type Recorded = ReturnType<typeof mockBackend>["requests"][number];

// Evidencia valida y coherente con `episodeA` (adaptada del ejemplo A de src/services/anomalyEvidence.test.ts).
function evidenceForA(): Record<string, unknown> {
  return {
    schema_version: "1.0", adapter_version: "anomaly-explanation-1.0",
    id: `anomaly-explanation:${"a".repeat(64)}`, status: "ok",
    source: { kind: "anomaly_episodes", rules_version: "jup019-daily-v1", data_as_of: "2026-09-09" },
    episode: episodeA,
    operands: {
      reference_seven_day_total: "2800.000000000000", opening_observed_cost: "550.000000000000",
      accumulated_impact_times_seven: "2800.000000000000"
    },
    opening: {
      reference_daily_cost: "400.00", observed_cost: "550.00", absolute_increase: "150.00",
      relative_increase_percent: "37.50", absolute_threshold: "100.00", relative_threshold_percent: "20",
      conditions_met: true
    },
    impact: {
      accumulated_impact: "400.00", day_count: 2, through_date: "2026-09-09", severity: "P3", severity_band: "< 500.00"
    },
    rounding_notes: [], includes_synthetic_data: false, cause_status: "not_established", assumptions: [],
    limitations: ["Es un candidato para investigar, no una causa demostrada."],
    explained_at: "2026-10-12T18:30:00+00:00"
  };
}

const explainedReply = {
  ...assistantReply,
  assistant_message: { ...assistantMessage, metadata: { citations: [], anomaly_evidence: evidenceForA() } }
};

// Backend por defecto: una conversacion vacia, tres anomalias validas y un envio que responde 201.
function backend(overrides: Parameters<typeof mockBackend>[0] = {}) {
  return mockBackend({
    [`GET ${collection}`]: () => jsonResponse({ items: [conversation] }),
    [`GET ${detail}`]: () => jsonResponse({ conversation, messages: [] }),
    [`GET ${episodesPath}`]: () => jsonResponse(episodeList({ episodes: [episodeA, episodeB, episodeC] })),
    [`POST ${messagePath}`]: () => jsonResponse(explainedReply, 201),
    ...overrides
  });
}

function posts(requests: Recorded[]) {
  return requests.filter((request) => request.method === "POST" && request.path === messagePath);
}

function episodeRequests(requests: Recorded[]) {
  return requests.filter((request) => request.path === episodesPath);
}

function openLink(id: string, tenantId?: string) {
  restoreSession(tenantId);
  const app = renderApp([`/assistant?episode=${id}`]);
  return { ...app, user: userEvent.setup() };
}

// La casilla del modo es lo primero que debe aparecer ya activada: si no existe, el Red falla por ese motivo.
async function activeAnomalyBox() {
  const box = await screen.findByRole("checkbox", { name: "Explicar una anomalía" });
  expect(box).toBeChecked();
  return box;
}

describe("JUP-038 enlace /assistant?episode=<id>: preselección", () => {
  it.each([[ID_B, labelOf(episodeB)], [ID_C, labelOf(episodeC)]])(
    "con %s en la lista abre el modo activado con esa anomalía elegida y no otra", async (id, label) => {
      backend();
      openLink(id);
      await activeAnomalyBox();
      // La de propiedad queda apagada y no hay aviso: el enlace es de este cliente.
      expect(screen.getByRole("checkbox", { name: "Consultar costes por propiedad" })).not.toBeChecked();
      const select = await screen.findByRole("combobox", { name: "Anomalía" });
      // Se comprueba un id que NO es el primero de la lista (A) para descartar "elegir la primera".
      await waitFor(() => expect(select).toHaveValue(id));
      expect(within(select).getByRole("option", { name: label })).toHaveProperty("selected", true);
      expect(screen.queryByText(WARNING_TEXT)).not.toBeInTheDocument();
      // Con la anomalia elegida y la pregunta propuesta, ya se puede enviar.
      expect(screen.getByRole("textbox", { name: "Pregunta" })).toHaveValue(PROPOSED_QUESTION);
      expect(screen.getByRole("button", { name: "Enviar" })).toBeEnabled();
    });

  it("enviar desde el enlace manda exactamente la anomalía del enlace", async () => {
    const { requests } = backend();
    const { user } = openLink(ID_C);
    await activeAnomalyBox();
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue(ID_C));
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    expect(posts(requests)[0].body).toEqual({ content: PROPOSED_QUESTION, anomaly_query: { episode_id: ID_C } });
  });

  it.each([["está en la lista", true], ["no está en la lista", false]])(
    "no avisa mientras la lista carga y, cuando llega, avisa solo si el id %s", async (_name, present) => {
      const pending = deferredResponse();
      backend({ [`GET ${episodesPath}`]: () => pending.promise });
      openLink(ID_B);
      await activeAnomalyBox();
      // Aun no se sabe si el id es del cliente: un aviso ahora seria falso.
      expect(await screen.findByText("Cargando anomalías...")).toBeVisible();
      expect(screen.queryByText(WARNING_TEXT)).not.toBeInTheDocument();
      await act(async () => pending.resolve(episodeList({ episodes: present ? [episodeA, episodeB] : [episodeA, episodeC] })));
      const select = await screen.findByRole("combobox", { name: "Anomalía" });
      if (present) {
        await waitFor(() => expect(select).toHaveValue(ID_B));
        expect(screen.queryByText(WARNING_TEXT)).not.toBeInTheDocument();
      } else {
        expect(await screen.findByText(WARNING_TEXT)).toBeVisible();
        expect(select).toHaveValue("");
      }
    });
});

describe("JUP-038 enlace /assistant?episode=<id>: anomalía que no es del cliente", () => {
  it.each([
    ["id con formato válido que no está en la lista", ID_OTHER_TENANT, [episodeA, episodeB]],
    ["id de formato inválido aunque aparezca en la lista", "anomaly-1", [episodeA, episode({ id: "anomaly-1" })]],
    ["id con mayúsculas en lugar del de la lista", `anomaly-${"A".repeat(64)}`, [episodeA, episodeB]],
    ["texto que no es un identificador", "cualquier-cosa", [episodeA, episodeB]]
  ])("%s: avisa, deja el modo activo y ninguna anomalía elegida", async (_name, id, episodes) => {
    backend({ [`GET ${episodesPath}`]: () => jsonResponse(episodeList({ episodes })) });
    openLink(id);
    await activeAnomalyBox();
    expect(await screen.findByText(WARNING_TEXT)).toBeVisible();
    // El aviso se anuncia como estado (no como error): es informativo, no un fallo de la peticion.
    expect(screen.getByRole("status")).toHaveTextContent(WARNING_TEXT);
    const select = screen.getByRole("combobox", { name: "Anomalía" });
    expect(select).toHaveValue("");
    // Sin anomalia elegida no se puede enviar, aunque la pregunta propuesta este escrita.
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    // Control positivo del mismo escenario: el usuario si puede elegir una de las del cliente y entonces envia.
    await userEvent.setup().selectOptions(select, ID_A);
    expect(screen.getByRole("button", { name: "Enviar" })).toBeEnabled();
  });

  it("con la lista vacía avisa del enlace, dice que no hay anomalías y no permite enviar", async () => {
    backend({ [`GET ${episodesPath}`]: () => jsonResponse(episodeList({ episodes: [] })) });
    openLink(ID_B);
    await activeAnomalyBox();
    expect(await screen.findByText(WARNING_TEXT)).toBeVisible();
    expect(screen.getByText(EMPTY_TEXT)).toBeVisible();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  });
});

describe("JUP-038 enlace /assistant?episode=<id>: la dirección tras enviar", () => {
  it("un envío correcto quita el parámetro de la dirección y deja la ruta", async () => {
    const { requests } = backend();
    const { user, router } = openLink(ID_B);
    await activeAnomalyBox();
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue(ID_B));
    // Control previo: antes de enviar el parametro sigue en la dirección.
    expect(router.state.location.search).toBe(`?episode=${ID_B}`);
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    await waitFor(() => expect(router.state.location.search).toBe(""));
    expect(router.state.location.pathname).toBe("/assistant");
  });

  it("un envío fallido conserva el parámetro y el reintento correcto lo quita", async () => {
    let failing = true;
    const { requests } = backend({
      [`POST ${messagePath}`]: () => failing ? jsonResponse(NOT_EXPLAINABLE, 409) : jsonResponse(explainedReply, 201)
    });
    const { user, router } = openLink(ID_B);
    await activeAnomalyBox();
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue(ID_B));
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Esta anomalía no se puede explicar con las reglas actuales.");
    // Tras el fallo el parametro se conserva y la anomalia sigue elegida.
    expect(router.state.location.search).toBe(`?episode=${ID_B}`);
    expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue(ID_B);
    // Control positivo: el mismo envio, ahora correcto, si quita el parametro.
    failing = false;
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(2));
    await waitFor(() => expect(router.state.location.search).toBe(""));
  });
});

describe("JUP-038 enlace /assistant?episode=<id>: sin enlace nada cambia", () => {
  it("sin parámetro el redactor aparece apagado y no se pide ninguna anomalía", async () => {
    const { requests } = backend();
    restoreSession();
    const { router } = renderApp(["/assistant"]);
    const box = await screen.findByRole("checkbox", { name: "Explicar una anomalía" });
    expect(box).not.toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Consultar costes por propiedad" })).not.toBeChecked();
    expect(screen.queryByText(WARNING_TEXT)).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Anomalía" })).not.toBeInTheDocument();
    expect(episodeRequests(requests)).toHaveLength(0);
    expect(router.state.location.search).toBe("");
    // Control: al activar el modo a mano si se pide la lista y no hay aviso de enlace.
    await userEvent.setup().click(box);
    await screen.findByRole("combobox", { name: "Anomalía" });
    expect(episodeRequests(requests)).toHaveLength(1);
    expect(screen.queryByText(WARNING_TEXT)).not.toBeInTheDocument();
  });

  it("un parámetro episode vacío se trata como si no estuviera", async () => {
    const { requests } = backend();
    restoreSession();
    renderApp(["/assistant?episode="]);
    const box = await screen.findByRole("checkbox", { name: "Explicar una anomalía" });
    expect(box).not.toBeChecked();
    expect(screen.queryByText(WARNING_TEXT)).not.toBeInTheDocument();
    expect(episodeRequests(requests)).toHaveLength(0);
  });
});

describe("JUP-038 enlace /assistant?episode=<id>: cliente y conversación", () => {
  it("al cambiar de cliente con el parámetro puesto avisa y no deja ninguna elegida", async () => {
    const southConversation = { ...conversation, id: "conversation-south", tenant_id: tenants[1].id, title: "South cost review" };
    const { requests } = backend({
      [`GET ${collection}`]: ({ headers }) => jsonResponse({
        items: headers.get("X-Tenant-Id") === tenants[0].id ? [conversation] : [southConversation]
      }),
      [`GET ${collection}/${southConversation.id}`]: () => jsonResponse({ conversation: southConversation, messages: [] }),
      // El cliente norte tiene las anomalias A y B; el sur solo la D: B no existe alli.
      [`GET ${episodesPath}`]: ({ headers }) => jsonResponse(episodeList({
        episodes: headers.get("X-Tenant-Id") === tenants[0].id ? [episodeA, episodeB] : [episodeD]
      }))
    });
    const { user, router } = openLink(ID_B, tenants[0].id);
    await activeAnomalyBox();
    // Control positivo: en el cliente norte el id del enlace se elige sin aviso.
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue(ID_B));
    expect(screen.queryByText(WARNING_TEXT)).not.toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: "Ámbito de cliente" }), tenants[1].id);
    expect(await screen.findByText(WARNING_TEXT)).toBeVisible();
    expect(await activeAnomalyBox()).toBeChecked();
    expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue("");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    // La lista del nuevo cliente se pidio con su cabecera y el parametro sigue en la dirección.
    const southList = episodeRequests(requests).filter((request) => request.headers.get("X-Tenant-Id") === tenants[1].id);
    expect(southList.length).toBeGreaterThanOrEqual(1);
    expect(router.state.location.search).toBe(`?episode=${ID_B}`);
  });

  it("sin conversación seleccionada el parámetro no se pierde y arma el modo al crear la primera", async () => {
    const created = { ...conversation, id: "conversation-created", title: "Revisión operativa" };
    let published = false;
    backend({
      [`GET ${collection}`]: () => jsonResponse({ items: published ? [created] : [] }),
      [`POST ${collection}`]: () => {
        published = true;
        return jsonResponse(created, 201);
      },
      [`GET ${collection}/${created.id}`]: () => jsonResponse({ conversation: created, messages: [] })
    });
    const { user, router } = openLink(ID_B);
    // Sin conversaciones no hay redactor: el parametro debe sobrevivir a ese estado.
    expect(await screen.findByText("Crea una conversación para empezar a usar el asistente.")).toBeVisible();
    expect(screen.queryByRole("checkbox", { name: "Explicar una anomalía" })).not.toBeInTheDocument();
    expect(router.state.location.search).toBe(`?episode=${ID_B}`);

    await user.click(screen.getByRole("button", { name: "Nueva" }));
    // En cuanto hay conversacion seleccionada, el redactor nace con el modo activado y la anomalia del enlace.
    await activeAnomalyBox();
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue(ID_B));
    expect(router.state.location.search).toBe(`?episode=${ID_B}`);
  });
});
