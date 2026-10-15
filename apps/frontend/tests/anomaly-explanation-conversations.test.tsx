import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { episode, episodeList } from "../src/test/anomalyFixtures";
import { assistantMessage, assistantReply, conversation, userMessage } from "./fixtures";
import { deferredResponse, expectTenantRequest, jsonResponse, mockBackend, renderApp, restoreSession } from "./test-support";

// JUP-038 tareas 6.1 y 6.2: modo «Explicar una anomalía» del redactor del asistente (design.md, decision 9).
// Son pruebas de integracion: se monta la aplicacion entera en /assistant y solo se simula el backend HTTP.
// `mockBackend` hace fallar cualquier peticion no prevista, asi que "no se pide nada" se comprueba de verdad.
// Mientras el modo no exista, cada prueba falla por el mismo motivo: no hay casilla «Explicar una anomalia».

const collection = "/assistant/conversations";
const detail = `${collection}/${conversation.id}`;
const messagePath = `${detail}/messages`;
const episodesPath = "/billing/anomalies/episodes";

// Identificadores con el formato real del backend: "anomaly-" + 64 hexadecimales en minuscula.
// (El fixture por defecto, "anomaly-1", NO tiene ese formato y el modo debe ignorarlo.)
const ID_A = `anomaly-${"a".repeat(64)}`;
const ID_B = `anomaly-${"b".repeat(64)}`;
const ID_C = `anomaly-${"c".repeat(64)}`;

// Tres episodios en un orden que no coincide con ningun orden natural (fecha, criticidad, servicio ni id):
// asi la prueba de orden demuestra que se respeta el que da el backend y no uno calculado en el cliente.
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
const labelA = "Compute · EUR · desde 2026-09-08 · Baja (P3) · Nueva";
const labelB = "(sin servicio) · USD · desde 2026-09-10 · Alta (P1) · Investigando";
const labelC = "Storage · EUR · desde 2026-09-09 · Media (P2) · Resuelta";
const PLACEHOLDER_OPTION = "Elige una anomalía";
const PROPOSED_QUESTION = "¿Por qué se ha marcado esta anomalía?";
const NOT_FOUND_TEXT = "No se ha encontrado esa anomalía en el cliente activo. Actualiza la lista y elige otra.";
const UNAVAILABLE_TEXT = "Esta anomalía no se puede explicar con las reglas actuales.";
const LOAD_ERROR_TEXT = "No se han podido cargar las anomalías.";
const EMPTY_TEXT = "Este cliente no tiene anomalías guardadas. Se detectan desde el panel de Anomalías.";

type Recorded = ReturnType<typeof mockBackend>["requests"][number];

// Evidencia valida y coherente con `episodeA` (adaptada del ejemplo A de src/services/anomalyEvidence.test.ts):
// el validador exige que apertura e impacto coincidan con el episodio embebido.
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
const EVIDENCE_SUMMARY = "Evidencia de la anomalía — Baja (P3)";

function explanationMessage(question: string) {
  return [
    { ...userMessage, content: question },
    { ...assistantMessage, content: "Explicación de la anomalía de Compute.", metadata: { citations: [], anomaly_evidence: evidenceForA() } }
  ];
}

// Backend por defecto: una conversacion vacia, tres anomalias validas y un envio que responde 201.
function backend(overrides: Parameters<typeof mockBackend>[0] = {}) {
  return mockBackend({
    [`GET ${collection}`]: () => jsonResponse({ items: [conversation] }),
    [`GET ${detail}`]: () => jsonResponse({ conversation, messages: [] }),
    [`GET ${episodesPath}`]: () => jsonResponse(episodeList({ episodes: [episodeA, episodeB, episodeC] })),
    [`POST ${messagePath}`]: () => jsonResponse(assistantReply, 201),
    ...overrides
  });
}

function posts(requests: Recorded[]) {
  return requests.filter((request) => request.method === "POST" && request.path === messagePath);
}

function episodeRequests(requests: Recorded[]) {
  return requests.filter((request) => request.path === episodesPath);
}

// Monta /assistant y espera a que el redactor ofrezca la casilla nueva. Que la espera sea por la casilla
// (y no por otra cosa) es lo que hace que el Red falle por el motivo correcto: el modo no existe.
async function openComposer() {
  restoreSession();
  const app = renderApp(["/assistant"]);
  const user = userEvent.setup();
  const anomalyBox = await screen.findByRole("checkbox", { name: "Explicar una anomalía" });
  return { ...app, user, anomalyBox };
}

async function activateMode() {
  const context = await openComposer();
  await context.user.click(context.anomalyBox);
  return context;
}

async function chooseAnomaly(user: ReturnType<typeof userEvent.setup>, id: string) {
  await user.selectOptions(await screen.findByRole("combobox", { name: "Anomalía" }), id);
}

function questionBox() {
  return screen.getByRole("textbox", { name: "Pregunta" });
}

describe("JUP-038 modo Explicar una anomalía: carga de la lista", () => {
  it("con el modo apagado no se pide ninguna anomalía y al activarlo se pide la lista del cliente activo", async () => {
    const { requests } = backend();
    const { user, anomalyBox } = await openComposer();
    // Control: la casilla existe, esta apagada y la de propiedad sigue como hoy.
    expect(anomalyBox).not.toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Consultar costes por propiedad" })).not.toBeChecked();
    // Con el modo apagado el redactor no debe tocar el endpoint de anomalias (aunque este simulado).
    expect(episodeRequests(requests)).toHaveLength(0);

    await user.click(anomalyBox);
    await screen.findByRole("combobox", { name: "Anomalía" });
    // Al activarlo: una sola lectura de todas las anomalias (abiertas y cerradas) con token y cliente.
    const listRequests = episodeRequests(requests);
    expect(listRequests).toHaveLength(1);
    expect(listRequests[0].method).toBe("GET");
    expect(listRequests[0].search.get("scope")).toBe("all");
    expectTenantRequest(listRequests[0]);
  });

  it("muestra 'Cargando anomalías...' mientras llega la lista y no permite enviar", async () => {
    const pending = deferredResponse();
    backend({ [`GET ${episodesPath}`]: () => pending.promise });
    await activateMode();
    expect(await screen.findByText("Cargando anomalías...")).toBeVisible();
    // Con la pregunta propuesta pero sin anomalia elegida, enviar sigue bloqueado durante la carga.
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    await act(async () => pending.resolve(episodeList({ episodes: [episodeA] })));
    // Al llegar la lista el aviso desaparece y aparece el selector.
    expect(await screen.findByRole("combobox", { name: "Anomalía" })).toBeVisible();
    expect(screen.queryByText("Cargando anomalías...")).not.toBeInTheDocument();
  });

  it("apagar el modo oculta el selector y vuelve al envio documental sin anomaly_query", async () => {
    const { requests } = backend();
    const { user, anomalyBox } = await activateMode();
    await chooseAnomaly(user, ID_A);
    await user.click(anomalyBox);
    expect(anomalyBox).not.toBeChecked();
    expect(screen.queryByRole("combobox", { name: "Anomalía" })).not.toBeInTheDocument();
    // Fuera del modo, la pregunta escrita se envia como consulta documental normal.
    await user.clear(questionBox());
    await user.type(questionBox(), "Consulta documental");
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    expect(posts(requests)[0].body).toEqual({ content: "Consulta documental" });
  });
});

describe("JUP-038 modo Explicar una anomalía: opciones del selector", () => {
  it("ofrece 'Elige una anomalía' sin nada elegido y una opción por episodio en el orden del backend", async () => {
    backend();
    await activateMode();
    const select = await screen.findByRole("combobox", { name: "Anomalía" });
    const options = within(select).getAllByRole("option");
    // Primera opcion neutra con valor vacio, luego los episodios tal cual los da el backend (A, B, C).
    expect(options.map((option) => option.textContent)).toEqual([PLACEHOLDER_OPTION, labelA, labelB, labelC]);
    expect(options.map((option) => option.getAttribute("value"))).toEqual(["", ID_A, ID_B, ID_C]);
    // Nada elegido por defecto: el usuario debe decidir, no se cuela la primera.
    expect(select).toHaveValue("");
  });

  it("solo ofrece los episodios con id anomaly-<64 hex en minúscula>", async () => {
    const hostile = (id: string, service: string) => episode({ id, service });
    backend({
      [`GET ${episodesPath}`]: () => jsonResponse(episodeList({
        episodes: [
          hostile("anomaly-1", "Fixture corto"),
          hostile(`anomaly-${"A".repeat(64)}`, "Mayusculas"),
          hostile(`anomaly-${"a".repeat(63)}`, "Sesenta y tres"),
          hostile(`anomaly-${"a".repeat(65)}`, "Sesenta y cinco"),
          hostile(`${ID_C}\n`, "Salto de linea"),
          hostile(`anomaly-${"g".repeat(64)}`, "No hexadecimal"),
          hostile(`x${ID_C}`, "Prefijo extra"),
          episodeA,
          episodeB
        ]
      }))
    });
    await activateMode();
    const select = await screen.findByRole("combobox", { name: "Anomalía" });
    // Control positivo: las dos validas estan; todas las demas quedan fuera, sin dejar opciones huerfanas.
    expect(within(select).getAllByRole("option").map((option) => option.textContent))
      .toEqual([PLACEHOLDER_OPTION, labelA, labelB]);
  });
});

describe("JUP-038 modo Explicar una anomalía: pregunta propuesta", () => {
  it("propone la pregunta con el cuadro vacío, se puede cambiar y elegir una anomalía no la sobrescribe", async () => {
    backend();
    const { user } = await activateMode();
    // Con el modo activo y la pregunta vacia se propone el texto y cambia el marcador del cuadro.
    expect(questionBox()).toHaveValue(PROPOSED_QUESTION);
    expect(questionBox()).toHaveAttribute("placeholder", "Pregunta sobre la anomalía elegida.");
    await user.clear(questionBox());
    await user.type(questionBox(), "Explícame el pico de Compute");
    await chooseAnomaly(user, ID_A);
    expect(questionBox()).toHaveValue("Explícame el pico de Compute");
  });

  it("si ya había texto al activar el modo no se sobrescribe", async () => {
    backend();
    restoreSession();
    renderApp(["/assistant"]);
    const user = userEvent.setup();
    // Control previo: el cuadro acepta texto antes de activar el modo (comportamiento actual).
    await user.type(await screen.findByRole("textbox", { name: "Pregunta" }), "Mi pregunta previa");
    await user.click(await screen.findByRole("checkbox", { name: "Explicar una anomalía" }));
    await screen.findByRole("combobox", { name: "Anomalía" });
    expect(questionBox()).toHaveValue("Mi pregunta previa");
  });
});

describe("JUP-038 modo Explicar una anomalía: envio", () => {
  it("Enviar queda deshabilitado hasta elegir anomalía y también si se borra la pregunta", async () => {
    backend();
    const { user } = await activateMode();
    const send = screen.getByRole("button", { name: "Enviar" });
    await screen.findByRole("combobox", { name: "Anomalía" });
    // Hay pregunta propuesta pero ninguna anomalia: no se puede enviar.
    expect(questionBox()).toHaveValue(PROPOSED_QUESTION);
    expect(send).toBeDisabled();
    // Control: con anomalia elegida y pregunta, ya se puede enviar.
    await chooseAnomaly(user, ID_B);
    expect(send).toBeEnabled();
    // Sin pregunta tampoco (regla existente del redactor, que el modo no debe romper).
    await user.clear(questionBox());
    expect(send).toBeDisabled();
  });

  it("envía el cuerpo exacto con anomaly_query y sin ownership_query, y el cliente activo", async () => {
    const { requests } = backend();
    const { user } = await activateMode();
    await chooseAnomaly(user, ID_B);
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    const request = posts(requests)[0];
    expect(request.body).toEqual({ content: PROPOSED_QUESTION, anomaly_query: { episode_id: ID_B } });
    // Una sola seleccion por mensaje: ni rastro de la consulta por propiedad.
    expect(Object.keys(request.body as Record<string, unknown>).sort()).toEqual(["anomaly_query", "content"]);
    expectTenantRequest(request);
  });

  it("tras un éxito limpia la pregunta, recarga la conversación y muestra el bloque de evidencia", async () => {
    let sent = false;
    const question = "Explícame la anomalía de Compute";
    const { requests } = backend({
      [`GET ${detail}`]: () => jsonResponse({ conversation, messages: sent ? explanationMessage(question) : [] }),
      [`POST ${messagePath}`]: () => {
        sent = true;
        return jsonResponse({ ...assistantReply, assistant_message: explanationMessage(question)[1] }, 201);
      }
    });
    const { user } = await activateMode();
    await user.clear(questionBox());
    await user.type(questionBox(), question);
    await chooseAnomaly(user, ID_A);
    // Control previo: antes de enviar no hay ningun bloque de evidencia en pantalla.
    expect(screen.queryByText(EVIDENCE_SUMMARY)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText(EVIDENCE_SUMMARY)).toBeVisible();
    // La pregunta guardada aparece como mensaje y el cuadro queda vacio.
    expect(screen.getByText(question)).toBeVisible();
    await waitFor(() => expect(questionBox()).toHaveValue(""));
    // Recarga de la conversacion: la lectura del detalle se repite despues del envio.
    expect(requests.filter((request) => request.method === "GET" && request.path === detail).length).toBeGreaterThanOrEqual(2);
  });
});

describe("JUP-038 modo Explicar una anomalía: sin anomalías o con la lista rota", () => {
  it.each([
    ["ninguna anomalía", () => episodeList({ episodes: [] })],
    ["solo anomalías con id de formato inválido", () => episodeList({ episodes: [episode({ id: "anomaly-1" })] })]
  ])("con %s lo dice, indica el panel y no permite enviar", async (_name, list) => {
    backend({ [`GET ${episodesPath}`]: () => jsonResponse(list()) });
    await activateMode();
    expect(await screen.findByText(EMPTY_TEXT)).toBeVisible();
    // Hay pregunta (propuesta) y aun asi el boton esta bloqueado: no hay nada que explicar.
    expect(questionBox()).toHaveValue(PROPOSED_QUESTION);
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    expect(screen.queryByRole("combobox", { name: "Anomalía" })).not.toBeInTheDocument();
  });

  it.each([
    ["un 500", () => jsonResponse({ detail: "boom interno del servidor" }, 500)],
    ["una respuesta con forma inválida", () => jsonResponse({ contract_version: 2, episodes: "no es una lista" })]
  ])("si la lista falla por %s muestra un aviso fijo y no permite enviar", async (_name, response) => {
    backend({ [`GET ${episodesPath}`]: response });
    await activateMode();
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe(LOAD_ERROR_TEXT);
    // El aviso es el texto fijo del modo, no el cuerpo crudo del servidor.
    expect(screen.queryByText(/boom interno/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    expect(screen.queryByRole("combobox", { name: "Anomalía" })).not.toBeInTheDocument();
  });
});

describe("JUP-038 modo Explicar una anomalía: exclusión con costes por propiedad", () => {
  it("activar uno desactiva el otro en los dos sentidos", async () => {
    backend();
    const { user, anomalyBox } = await openComposer();
    const property = screen.getByRole("checkbox", { name: "Consultar costes por propiedad" });
    await user.click(property);
    expect(property).toBeChecked();
    expect(screen.getByLabelText("Agrupar por")).toBeVisible();
    // Propiedad -> anomalia: la de propiedad se apaga y sus campos desaparecen.
    await user.click(anomalyBox);
    expect(anomalyBox).toBeChecked();
    expect(property).not.toBeChecked();
    expect(screen.queryByLabelText("Agrupar por")).not.toBeInTheDocument();
    expect(await screen.findByRole("combobox", { name: "Anomalía" })).toBeVisible();
    // Anomalia -> propiedad: el selector de anomalias se va y vuelven los campos de costes.
    await user.click(property);
    expect(property).toBeChecked();
    expect(anomalyBox).not.toBeChecked();
    expect(screen.queryByRole("combobox", { name: "Anomalía" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Agrupar por")).toBeVisible();
  });

  it("cada modo envía solo lo suyo: ownership_query sin anomaly_query y al revés", async () => {
    const { requests } = backend();
    const { user, anomalyBox } = await openComposer();
    const property = screen.getByRole("checkbox", { name: "Consultar costes por propiedad" });
    // Modo propiedad (comportamiento existente): solo ownership_query.
    await user.click(property);
    await user.type(questionBox(), "Coste por aplicación");
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    expect(posts(requests)[0].body).toEqual({ content: "Coste por aplicación", ownership_query: { group_by: "application" } });
    // Modo anomalia tras haber usado el de propiedad: solo anomaly_query, sin restos de ownership_query.
    // Tras el exito la pregunta quedo vacia, asi que al activar el modo se propone el texto por defecto.
    await waitFor(() => expect(questionBox()).toHaveValue(""));
    await user.click(anomalyBox);
    await chooseAnomaly(user, ID_C);
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(2));
    expect(posts(requests)[1].body).toEqual({ content: PROPOSED_QUESTION, anomaly_query: { episode_id: ID_C } });
  });

  it("volver al modo propiedad tras elegir una anomalía no arrastra la anomalía al mensaje", async () => {
    const { requests } = backend();
    const { user, anomalyBox } = await activateMode();
    await chooseAnomaly(user, ID_A);
    // Control: con el modo de anomalia el envio habria llevado anomaly_query (probado en otra prueba).
    expect(anomalyBox).toBeChecked();
    await user.click(screen.getByRole("checkbox", { name: "Consultar costes por propiedad" }));
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    expect(posts(requests)[0].body).toEqual({ content: PROPOSED_QUESTION, ownership_query: { group_by: "application" } });
  });
});

// Errores del servidor al enviar. Cada caso arranca con un fallo y, tras comprobarlo, el mismo servidor pasa
// a responder 201: ese reintento es el control positivo (demuestra que la pregunta y la anomalia elegidas
// se conservaron y que el fallo venia de la respuesta, no de un redactor roto).
const failures: { name: string; status: number; body: unknown; expectedText: string }[] = [
  {
    name: "404 de anomalía", status: 404, body: { detail: { code: "anomaly_episode_not_found" } },
    expectedText: NOT_FOUND_TEXT
  },
  {
    name: "409 de anomalía no explicable", status: 409, body: { detail: { code: "anomaly_explanation_unavailable" } },
    expectedText: UNAVAILABLE_TEXT
  },
  {
    // El 404 de conversacion lleva `detail` como cadena: no es un codigo de anomalia y no debe confundirse.
    name: "404 de conversación", status: 404, body: { detail: "Conversation not found." },
    expectedText: JSON.stringify({ detail: "Conversation not found." })
  },
  {
    name: "422 genérico", status: 422,
    body: { detail: [{ loc: ["body", "anomaly_query"], msg: "Field required", type: "missing" }] },
    expectedText: JSON.stringify({ detail: [{ loc: ["body", "anomaly_query"], msg: "Field required", type: "missing" }] })
  },
  {
    name: "503 genérico", status: 503, body: { detail: "Assistant unavailable" },
    expectedText: JSON.stringify({ detail: "Assistant unavailable" })
  }
];

describe("JUP-038 modo Explicar una anomalía: errores al enviar", () => {
  it.each(failures)("ante un $name muestra el texto exacto, conserva pregunta y elección y no añade mensajes", async (failure) => {
    let failing = true;
    let sent = false;
    const question = "Explícame esta anomalía otra vez";
    const { requests } = backend({
      [`GET ${detail}`]: () => jsonResponse({ conversation, messages: sent ? explanationMessage(question) : [] }),
      [`POST ${messagePath}`]: () => {
        if (failing) return jsonResponse(failure.body, failure.status);
        sent = true;
        return jsonResponse({ ...assistantReply, assistant_message: explanationMessage(question)[1] }, 201);
      }
    });
    const { user } = await activateMode();
    await user.clear(questionBox());
    await user.type(questionBox(), question);
    await chooseAnomaly(user, ID_B);
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    // Texto exacto en un unico role="alert" (los dos textos de anomalia son fijos; el resto es el generico de hoy).
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe(failure.expectedText);
    // Se conservan la pregunta y la anomalia, y se puede volver a enviar.
    expect(questionBox()).toHaveValue(question);
    expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue(ID_B);
    expect(screen.getByRole("button", { name: "Enviar" })).toBeEnabled();
    // Ningun mensaje nuevo en la conversacion y ninguna recarga del detalle por un envio fallido.
    expect(screen.queryAllByRole("article")).toHaveLength(0);
    expect(screen.queryByText(EVIDENCE_SUMMARY)).not.toBeInTheDocument();
    expect(requests.filter((request) => request.method === "GET" && request.path === detail)).toHaveLength(1);

    // Control positivo: el reintento identico funciona, borra el aviso y muestra la evidencia.
    failing = false;
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText(EVIDENCE_SUMMARY)).toBeVisible();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(posts(requests)).toHaveLength(2);
    expect(posts(requests)[1].body).toEqual(posts(requests)[0].body);
    expect(posts(requests)[0].body).toEqual({ content: question, anomaly_query: { episode_id: ID_B } });
  });
});
