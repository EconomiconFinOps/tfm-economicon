import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AnomalyExplanationFields } from "../src/components/AnomalyExplanationFields";
import { MessageComposer } from "../src/components/MessageComposer";
import { episode, episodeList } from "../src/test/anomalyFixtures";
import { assistantReply, conversation, session, tenants } from "./fixtures";
import { expectTenantRequest, jsonResponse, mockBackend, renderApp, restoreSession } from "./test-support";

// JUP-038 tarea 6.6 (remediacion de mutantes del modo «Explicar una anomalia» del redactor).
// Cada caso indica que mutante de Stryker mata y por que el comportamiento observable lo delata. Los
// mutantes equivalentes (queryKey, clases CSS, `isError || !options`, `instanceof ApiError` y los controles
// de tipo dentro de `anomalyErrorText`, `if (event.target.checked)` de la casilla de propiedad) NO se
// atacan: no existe prueba que los distinga del codigo real.
// Se duplican aqui los ayudantes de los archivos de pruebas existentes porque no se importan entre si.

const collection = "/assistant/conversations";
const detail = `${collection}/${conversation.id}`;
const messagePath = `${detail}/messages`;
const episodesPath = "/billing/anomalies/episodes";

const ID_A = `anomaly-${"a".repeat(64)}`;
const ID_B = `anomaly-${"b".repeat(64)}`;
const ID_C = `anomaly-${"c".repeat(64)}`;
const ID_D = `anomaly-${"d".repeat(64)}`;

const episodeA = episode({
  id: ID_A, currency: "EUR", service: "Compute", start_date: "2026-09-08", last_seen_date: "2026-09-09",
  severity: "P3", status: "new"
});
const episodeB = episode({
  id: ID_B, currency: "USD", service: null, start_date: "2026-09-10", last_seen_date: "2026-09-12",
  severity: "P1", status: "investigating"
});
const episodeC = episode({
  id: ID_C, currency: "EUR", service: "Storage", start_date: "2026-09-09", last_seen_date: "2026-09-11",
  severity: "P2", status: "resolved", closed_at: "2026-09-12T10:00:00Z", closure_reason: "Revisada"
});
const episodeD = episode({ id: ID_D, currency: "EUR", service: "Network", start_date: "2026-09-02" });

const PROPOSED_QUESTION = "¿Por qué se ha marcado esta anomalía?";
const PLACEHOLDER_DOCUMENTS = "Pregunta sobre los documentos ingeridos del cliente.";
const PLACEHOLDER_OWNERSHIP = "Pregunta sobre los costes de la selección.";
const PLACEHOLDER_ANOMALY = "Pregunta sobre la anomalía elegida.";
const UNAVAILABLE_TEXT = "Esta anomalía no se puede explicar con las reglas actuales.";
const UNAVAILABLE_BODY = { detail: { code: "anomaly_explanation_unavailable" } };

type Recorded = ReturnType<typeof mockBackend>["requests"][number];
type User = ReturnType<typeof userEvent.setup>;

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

// Espera un instante real para poder afirmar que ALGO NO ocurrio (ninguna peticion, ningun aviso).
async function settle() {
  await act(async () => { await new Promise<void>((resolve) => setTimeout(resolve, 40)); });
}

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

async function chooseAnomaly(user: User, id: string) {
  await user.selectOptions(await screen.findByRole("combobox", { name: "Anomalía" }), id);
}

function questionBox() {
  return screen.getByRole("textbox", { name: "Pregunta" });
}

function propertyBox() {
  return screen.getByRole("checkbox", { name: "Consultar costes por propiedad" });
}

// Formulario del redactor: el ancestro del cuadro «Pregunta». Se obtiene sin aserciones no nulas.
function composerForm(): HTMLFormElement {
  const form = questionBox().closest("form");
  if (!form) throw new Error("El cuadro Pregunta debe estar dentro de un formulario");
  return form;
}

function newClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity }, mutations: { retry: false } } });
}

// Los clientes de consultas de los montajes directos se vacian al terminar cada prueba.
const directClients: QueryClient[] = [];
afterEach(() => {
  for (const client of directClients.splice(0)) client.clear();
});

function renderDirect(ui: React.ReactElement) {
  const client = newClient();
  directClients.push(client);
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("JUP-038 6.6 AnomalyExplanationFields: la consulta solo se hace con token y cliente", () => {
  // Mata `enabled: Boolean(token && tenantId)` -> `true` y -> `Boolean(token || tenantId)`.
  // El backend simulado NO define la ruta de anomalias: cualquier peticion queda registrada y ademas
  // hace fallar la prueba (peticion no interceptada).
  it.each([
    ["sin cliente (tenantId vacío)", "token-valido", ""],
    ["sin token (token vacío)", "", tenants[0].id]
  ])("%s no pide la lista de anomalías", async (_name, token, tenantId) => {
    const { requests } = mockBackend();
    renderDirect(<AnomalyExplanationFields token={token} tenantId={tenantId} selected="" onSelect={vi.fn()}
      linkedId="" disabled={false} />);
    await settle();
    expect(episodeRequests(requests)).toHaveLength(0);
    expect(requests).toHaveLength(0);
    // Al no haber consulta, el componente se queda en el estado de carga y no muestra error ni selector.
    expect(screen.getByText("Cargando anomalías...")).toBeVisible();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("control positivo: con token y cliente sí se pide la lista, con sus cabeceras", async () => {
    const { requests } = mockBackend({
      [`GET ${episodesPath}`]: () => jsonResponse(episodeList({ episodes: [episodeA] }))
    });
    renderDirect(<AnomalyExplanationFields token={session.accessToken} tenantId={tenants[0].id} selected=""
      onSelect={vi.fn()} linkedId="" disabled={false} />);
    expect(await screen.findByRole("combobox", { name: "Anomalía" })).toBeVisible();
    expect(episodeRequests(requests)).toHaveLength(1);
    expectTenantRequest(episodeRequests(requests)[0]);
  });
});

describe("JUP-038 6.6 AnomalyExplanationFields: la preselección del enlace se aplica una sola vez", () => {
  // Mata `linkApplied.current = true` -> `false`. Con la mutacion, cada vez que la lista cambia el efecto
  // vuelve a imponer la anomalia del enlace. Se provoca ese cambio de lista de forma real: una segunda
  // lectura del backend devuelve una anomalia mas (los datos distintos rompen el compartido estructural
  // de TanStack Query y `options` pasa a ser otro array).
  it("si la persona vuelve a 'Elige una anomalía' y la lista se refresca, no se le reimpone la del enlace", async () => {
    let reads = 0;
    const { requests } = backend({
      [`GET ${episodesPath}`]: () => {
        reads += 1;
        return jsonResponse(episodeList({ episodes: reads === 1 ? [episodeA, episodeB, episodeC] : [episodeA, episodeB, episodeC, episodeD] }));
      }
    });
    restoreSession();
    const { client } = renderApp([`/assistant?episode=${ID_B}`]);
    const user = userEvent.setup();
    const select = await screen.findByRole("combobox", { name: "Anomalía" });
    // La primera lista preselecciona B (comportamiento correcto que no debe romperse).
    await waitFor(() => expect(select).toHaveValue(ID_B));

    // La persona decide no explicar ninguna: vuelve a la opcion neutra y el envio queda bloqueado.
    await user.selectOptions(select, "");
    expect(select).toHaveValue("");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();

    // Se fuerza una nueva lectura con datos distintos y se espera a que la lista nueva se pinte.
    await act(async () => { await client.invalidateQueries(); });
    await screen.findByRole("option", { name: /^Network ·/ });
    expect(episodeRequests(requests).length).toBeGreaterThanOrEqual(2);
    // Se deja tiempo a que un efecto mal escrito reimponga B antes de comprobar nada.
    await settle();
    expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue("");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  });
});

describe("JUP-038 6.6 MessageComposer: el envío forzado sin anomalía no sale", () => {
  // Mata `if (!episodeId) return;` -> `if (false)`. El boton ya esta deshabilitado, pero un envio del
  // formulario (Intro en el cuadro, extensiones del navegador...) no pasa por el boton: la guarda del
  // manejador es la ultima barrera y no debe mandarse un `episode_id` vacio.
  it("con el modo activo y sin anomalía elegida, un submit forzado no hace ningún POST", async () => {
    const { requests } = backend();
    await activateMode();
    await screen.findByRole("combobox", { name: "Anomalía" });
    expect(questionBox()).toHaveValue(PROPOSED_QUESTION);
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();

    fireEvent.submit(composerForm());
    await settle();
    expect(posts(requests)).toHaveLength(0);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("control positivo: con anomalía elegida el mismo submit forzado sí envía anomaly_query", async () => {
    const { requests } = backend();
    const { user } = await activateMode();
    await chooseAnomaly(user, ID_B);
    fireEvent.submit(composerForm());
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    expect(posts(requests)[0].body).toEqual({ content: PROPOSED_QUESTION, anomaly_query: { episode_id: ID_B } });
  });
});

describe("JUP-038 6.6 MessageComposer: reinicio de la elección al cambiar de modo", () => {
  // Mata la eliminacion de `setEpisodeId("")` en la casilla de propiedad (lineas 108-110): la anomalia
  // elegida no puede sobrevivir a un paso por el modo de propiedad.
  it("elegir B, pasar por costes por propiedad y volver deja 'Elige una anomalía' y Enviar bloqueado", async () => {
    backend();
    const { user, anomalyBox } = await activateMode();
    await chooseAnomaly(user, ID_B);
    expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue(ID_B);

    await user.click(propertyBox());
    expect(anomalyBox).not.toBeChecked();
    await user.click(anomalyBox);
    const select = await screen.findByRole("combobox", { name: "Anomalía" });
    expect(select).toHaveValue("");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  });

  // Mata la eliminacion de `setEpisodeId("")` de la rama `else` de la casilla de anomalia (linea 125).
  it("elegir B, apagar el modo y volver a activarlo deja 'Elige una anomalía' y Enviar bloqueado", async () => {
    backend();
    const { user, anomalyBox } = await activateMode();
    await chooseAnomaly(user, ID_B);

    await user.click(anomalyBox);
    expect(screen.queryByRole("combobox", { name: "Anomalía" })).not.toBeInTheDocument();
    await user.click(anomalyBox);
    const select = await screen.findByRole("combobox", { name: "Anomalía" });
    expect(select).toHaveValue("");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  });

  // Mata los mutantes que hacen que apagar el modo (rama `else`) ejecute tambien la propuesta de pregunta,
  // o que la propongan sin comprobar el cuadro: si la persona vacio la pregunta a proposito, apagar el modo
  // no debe volver a escribirsela.
  it("apagar el modo con la pregunta vacía no vuelve a proponer la pregunta", async () => {
    backend();
    const { user, anomalyBox } = await activateMode();
    expect(questionBox()).toHaveValue(PROPOSED_QUESTION);
    await user.clear(questionBox());
    expect(questionBox()).toHaveValue("");

    await user.click(anomalyBox);
    expect(anomalyBox).not.toBeChecked();
    expect(questionBox()).toHaveValue("");
    expect(questionBox()).toHaveAttribute("placeholder", PLACEHOLDER_DOCUMENTS);
  });

  // Mata `!message.trim()` -> `!message`: un cuadro con solo espacios cuenta como vacio y se sustituye.
  it("con el cuadro solo con espacios al activar el modo se propone la pregunta", async () => {
    backend();
    const { user, anomalyBox } = await openComposer();
    await user.type(questionBox(), "   ");
    expect(questionBox()).toHaveValue("   ");
    await user.click(anomalyBox);
    expect(questionBox()).toHaveValue(PROPOSED_QUESTION);
  });

  // Control complementario: con texto real la propuesta no lo pisa (la condicion debe ser `trim` y no
  // una constante verdadera).
  it("con texto real al activar el modo no se pisa lo escrito", async () => {
    backend();
    const { user, anomalyBox } = await openComposer();
    await user.type(questionBox(), "Mi pregunta");
    await user.click(anomalyBox);
    expect(questionBox()).toHaveValue("Mi pregunta");
  });
});

describe("JUP-038 6.6 MessageComposer: el cambio de casilla limpia el error del envío", () => {
  // Mata la eliminacion de `sendMutation.reset()` en la casilla de anomalia (linea 129). Un error de un
  // envio anterior no debe seguir en pantalla cuando la persona cambia de modo: ya no se refiere a lo
  // que va a enviar. (`handleSend` tambien hace reset, pero solo al enviar, no al cambiar de casilla.)
  it("tras un 409 visible, apagar el modo anomalía hace desaparecer el aviso", async () => {
    backend({ [`POST ${messagePath}`]: () => jsonResponse(UNAVAILABLE_BODY, 409) });
    const { user, anomalyBox } = await activateMode();
    await chooseAnomaly(user, ID_B);
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect((await screen.findByRole("alert")).textContent).toBe(UNAVAILABLE_TEXT);

    await user.click(anomalyBox);
    expect(anomalyBox).not.toBeChecked();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("tras un 409 visible, volver a activar el modo anomalía desde otro modo tampoco arrastra el aviso", async () => {
    backend({ [`POST ${messagePath}`]: () => jsonResponse(UNAVAILABLE_BODY, 409) });
    const { user, anomalyBox } = await activateMode();
    await chooseAnomaly(user, ID_B);
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect((await screen.findByRole("alert")).textContent).toBe(UNAVAILABLE_TEXT);

    // Pasar por propiedad ya limpiaba el error; al volver a activar la anomalia no debe reaparecer ni quedar.
    await user.click(propertyBox());
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    await user.click(anomalyBox);
    await screen.findByRole("combobox", { name: "Anomalía" });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("JUP-038 6.6 MessageComposer: marcador del cuadro Pregunta", () => {
  // Mata los cambios de literal en las tres ramas del marcador (linea 176 incluida: el de propiedad).
  it("el marcador cambia con cada modo: documentos, propiedad, anomalía y de nuevo documentos", async () => {
    backend();
    const { user, anomalyBox } = await openComposer();
    expect(questionBox()).toHaveAttribute("placeholder", PLACEHOLDER_DOCUMENTS);

    await user.click(propertyBox());
    expect(questionBox()).toHaveAttribute("placeholder", PLACEHOLDER_OWNERSHIP);

    await user.click(anomalyBox);
    expect(questionBox()).toHaveAttribute("placeholder", PLACEHOLDER_ANOMALY);

    await user.click(anomalyBox);
    expect(questionBox()).toHaveAttribute("placeholder", PLACEHOLDER_DOCUMENTS);
  });
});

describe("JUP-038 6.6 MessageComposer usado sin las props opcionales", () => {
  function composer() {
    return renderDirect(<MessageComposer token={session.accessToken} tenantId={tenants[0].id}
      conversationId={conversation.id} />);
  }

  // Mata el valor por defecto `initialEpisodeId = ""` -> otro valor: sin la prop, el modo nace apagado y
  // no se pide ninguna anomalia.
  it("sin initialEpisodeId el modo anomalía nace apagado, sin selector ni petición de anomalías", async () => {
    const { requests } = backend();
    composer();
    const anomalyBox = await screen.findByRole("checkbox", { name: "Explicar una anomalía" });
    expect(anomalyBox).not.toBeChecked();
    expect(propertyBox()).not.toBeChecked();
    expect(screen.queryByRole("combobox", { name: "Anomalía" })).not.toBeInTheDocument();
    expect(questionBox()).toHaveValue("");
    expect(questionBox()).toHaveAttribute("placeholder", PLACEHOLDER_DOCUMENTS);
    await settle();
    expect(episodeRequests(requests)).toHaveLength(0);
  });

  // Mata `onSent?.()` -> `onSent()`: sin la prop, llamarla lanza un TypeError dentro de `onSuccess`, la
  // mutacion pasa a error y aparece un `alert` tras un envio que el servidor acepto.
  it("un envío documental correcto sin onSent no produce ningún error", async () => {
    const { requests } = backend();
    composer();
    const user = userEvent.setup();
    await user.type(await screen.findByRole("textbox", { name: "Pregunta" }), "Consulta documental");
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    expect(posts(requests)[0].body).toEqual({ content: "Consulta documental" });
    await waitFor(() => expect(questionBox()).toHaveValue(""));
    await settle();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  });

  it("un envío de anomalía correcto sin onSent no produce ningún error", async () => {
    const { requests } = backend();
    composer();
    const user = userEvent.setup();
    await user.click(await screen.findByRole("checkbox", { name: "Explicar una anomalía" }));
    await chooseAnomaly(user, ID_A);
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    expect(posts(requests)[0].body).toEqual({ content: PROPOSED_QUESTION, anomaly_query: { episode_id: ID_A } });
    await waitFor(() => expect(questionBox()).toHaveValue(""));
    await settle();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("JUP-038 6.6 ConversationsPage: la dirección tras un envío correcto", () => {
  async function sendFromLink(search: string) {
    const { requests } = backend();
    restoreSession();
    const app = renderApp([`/assistant${search}`]);
    const user = userEvent.setup();
    await screen.findByRole("checkbox", { name: "Explicar una anomalía" });
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Anomalía" })).toHaveValue(ID_B));
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(posts(requests)).toHaveLength(1));
    return app;
  }

  // Mata los mutantes de `onSent` que reconstruyen mal los parametros o borran otro distinto: solo
  // `episode` debe desaparecer; el resto de la cadena de consulta se conserva.
  it("quita solo el parámetro episode y conserva los demás", async () => {
    const { router } = await sendFromLink(`?episode=${ID_B}&otro=1`);
    await waitFor(() => expect(router.state.location.search).toBe("?otro=1"));
    expect(router.state.location.pathname).toBe("/assistant");
  });

  // Mata `{ replace: true }` -> `{ replace: false }`/ausente: quitar el parametro no debe dejar una
  // entrada nueva en el historial (volver atras reabriria el enlace con el modo armado).
  it("la navegación es de reemplazo, no una entrada nueva en el historial", async () => {
    const { router } = await sendFromLink(`?episode=${ID_B}&otro=1`);
    // Se espera a que el parametro haya desaparecido: es el momento en que la navegacion ya se aplico.
    await waitFor(() => expect(router.state.location.search).toBe("?otro=1"));
    expect(router.state.historyAction).toBe("REPLACE");
    expect(router.state.historyAction).not.toBe("PUSH");
  });
});
