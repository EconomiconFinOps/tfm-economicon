// JUP-038 (tarea 7.1, fase Red): enlace «Explicar en el asistente» en el detalle de una anomalía del panel /anomalies.
// Contrato: el detalle ofrece un enlace a `/assistant?episode=<id>` solo cuando el id tiene el formato real
// `anomaly-<64 hex en minúscula>` (el asistente rechazaría cualquier otro), en cualquier estado del episodio, y el
// enlace únicamente navega: no lanza ninguna petición HTTP.
import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router";
import { focusManager, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AnomaliesPanel } from "./AnomaliesPanel";
import { episode, episodeList } from "../test/anomalyFixtures";
import type { AnomalyEpisode } from "../services/contracts";

const LINK_NAME = "Explicar en el asistente";

// Ids con el formato real del backend: "anomaly-" + 64 hex en minúscula.
const validId = (hex: string) => `anomaly-${hex.repeat(64)}`;
const ID_A = validId("a");
const ID_B = validId("b");
const ID_C = validId("c");

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

// Solo se sirve la lista; cualquier otra petición también recibe la lista para que, si el producto lanzara una
// petición nueva por error, la prueba la detecte por el conteo de llamadas y no por un fallo de red inventado.
function stubApi(episodes: AnomalyEpisode[]) {
  const fetchMock = vi.fn<typeof fetch>(() =>
    Promise.resolve(json(episodeList({ episodes, open_impact_by_currency: [{ currency: "EUR", amount: "100.00" }] }))));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function Layout() {
  return <Outlet context={{ token: "tok-1", activeTenant: { id: "tenant-core", name: "Core Finance" }, activeTenantId: "tenant-core" }} />;
}

// Se monta el panel con una segunda ruta /assistant que solo pinta un marcador: así se comprueba la navegación real.
function renderPanel() {
  const router = createMemoryRouter([
    { path: "/", Component: Layout, children: [{ index: true, Component: AnomaliesPanel }] },
    { path: "/assistant", Component: () => <p>Marcador del asistente</p> },
  ]);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
  return router;
}

// La tabla solo enseña las abiertas por defecto; «Todos los estados» deja ver también las cerradas.
async function showAllStatuses() {
  // Se espera al selector (no a la tabla): si no hay abiertas, la tabla no existe hasta cambiar el filtro.
  fireEvent.change(await screen.findByLabelText("Estado"), { target: { value: "all" } });
  await screen.findByRole("region", { name: /Lista de anomalías/ });
}

async function openDetail(service: string) {
  fireEvent.click(await screen.findByRole("button", { name: `Detalle de ${service}` }));
  const dialog = await screen.findByRole("dialog");
  // Se exige el título del servicio para asegurar que el diálogo abierto es el de la fila pedida.
  expect(dialog).toHaveTextContent(service);
  return dialog;
}

// El botón «Cerrar» (con la X) del diálogo es distinto de la acción «Cerrar…» de la anomalía.
async function closeDetail() {
  fireEvent.click(screen.getByRole("button", { name: "Cerrar" }));
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
}

afterEach(() => { vi.unstubAllGlobals(); focusManager.setFocused(undefined); });

describe("JUP-038 detalle de anomalía: enlace «Explicar en el asistente»", () => {
  // Cubre los cuatro estados y las dos observaciones: el requisito dice «en cualquier estado»,
  // incluidas las cerradas (que no tienen acciones de estado) y las que ya no se observan.
  const cases: { label: string; status: AnomalyEpisode["status"]; observation: AnomalyEpisode["observation"] }[] = [
    { label: "abierta y observada", status: "new", observation: "observed" },
    { label: "abierta y ya no observada", status: "new", observation: "no_longer_observed" },
    { label: "en investigación y observada", status: "investigating", observation: "observed" },
    { label: "resuelta y observada", status: "resolved", observation: "observed" },
    { label: "resuelta y ya no observada", status: "resolved", observation: "no_longer_observed" },
    { label: "falso positivo y observada", status: "false_positive", observation: "observed" },
    { label: "falso positivo y ya no observada", status: "false_positive", observation: "no_longer_observed" },
  ];

  it.each(cases)("ofrece el enlace con nombre y destino exactos en una anomalía $label", async ({ status, observation }) => {
    const closedFields = status === "resolved" || status === "false_positive"
      ? { closed_at: "2026-10-12T11:00:00Z", closure_reason: "Motivo de cierre" } : {};
    const noLongerFields = observation === "no_longer_observed" ? { no_longer_observed_on: "2026-09-14" } : {};
    stubApi([episode({ id: ID_A, service: "Compute", status, observation, ...closedFields, ...noLongerFields })]);
    renderPanel();
    await showAllStatuses();
    const dialog = await openDetail("Compute");
    // Nombre accesible exacto y rol de enlace (no botón): es navegación, no una acción.
    const link = await screen.findByRole("link", { name: LINK_NAME });
    expect(dialog).toContainElement(link);
    expect(link).toHaveAttribute("href", `/assistant?episode=${ID_A}`);
  });

  it("no cambia las acciones de estado: las abiertas las conservan junto al enlace y las cerradas siguen sin ellas", async () => {
    stubApi([
      episode({ id: ID_A, service: "Compute", status: "new" }),
      episode({ id: ID_B, service: "Database", status: "investigating" }),
      episode({ id: ID_C, service: "Storage", status: "resolved", closed_at: "2026-10-12T11:00:00Z", closure_reason: "Revertido" }),
    ]);
    renderPanel();
    await showAllStatuses();

    // Nueva: enlace + «Marcar en investigación» + «Cerrar…».
    await openDetail("Compute");
    expect(await screen.findByRole("link", { name: LINK_NAME })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Marcar en investigación" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cerrar…" })).toBeInTheDocument();
    await closeDetail();

    // En investigación: enlace + «Cerrar…», sin «Marcar en investigación».
    await openDetail("Database");
    expect(await screen.findByRole("link", { name: LINK_NAME })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Marcar en investigación" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cerrar…" })).toBeInTheDocument();
    await closeDetail();

    // Resuelta: el enlace aparece aunque ya no haya ninguna acción de estado.
    await openDetail("Storage");
    expect(await screen.findByRole("link", { name: LINK_NAME })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Marcar en investigación" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cerrar…" })).not.toBeInTheDocument();
  });

  // Ids que NO cumplen `^anomaly-[0-9a-f]{64}$`: el asistente los rechazaría, así que ofrecer el enlace llevaría
  // a un error. Cada uno se prueba junto a una anomalía válida de la misma lista (control positivo) para que la
  // ausencia no sea vacua (por ejemplo, por no haberse abierto el detalle o por no existir el enlace nunca).
  const invalidIds: { label: string; id: string }[] = [
    { label: "el id corto del fixture (anomaly-1)", id: "anomaly-1" },
    { label: "hexadecimal en mayúsculas", id: `anomaly-${"A".repeat(64)}` },
    { label: "63 caracteres hexadecimales", id: `anomaly-${"d".repeat(63)}` },
    { label: "65 caracteres hexadecimales", id: `anomaly-${"d".repeat(65)}` },
    { label: "un carácter no hexadecimal", id: `anomaly-${"d".repeat(63)}g` },
    { label: "sin el prefijo anomaly-", id: "d".repeat(64) },
    { label: "un espacio final", id: `anomaly-${"d".repeat(64)} ` },
    { label: "un salto de línea final", id: `anomaly-${"d".repeat(64)}\n` },
  ];

  it.each(invalidIds)("no ofrece el enlace cuando el id tiene $label, pero sí en la anomalía válida de la misma lista", async ({ id }) => {
    stubApi([
      episode({ id: ID_A, service: "Compute" }),
      episode({ id, service: "Database" }),
    ]);
    renderPanel();
    await showAllStatuses();

    // Control positivo: el mismo panel sí ofrece el enlace para el id válido.
    await openDetail("Compute");
    expect(await screen.findByRole("link", { name: LINK_NAME })).toHaveAttribute("href", `/assistant?episode=${ID_A}`);
    await closeDetail();

    // El detalle del id inválido se abre y se pinta completo (acción de estado presente), pero sin enlace.
    await openDetail("Database");
    expect(screen.getByRole("button", { name: "Cerrar…" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: LINK_NAME })).not.toBeInTheDocument();
    expect(screen.queryByText(LINK_NAME)).not.toBeInTheDocument();
  });

  it("solo navega: pulsar el enlace lleva a /assistant?episode=<id> sin lanzar ninguna petición nueva", async () => {
    const fetchMock = stubApi([episode({ id: ID_A, service: "Compute" })]);
    const router = renderPanel();
    await showAllStatuses();
    await screen.findByRole("button", { name: "Detalle de Compute" });
    // Tras cargar la lista se fija la línea base de peticiones: nada de lo siguiente debe añadir ninguna.
    const baseline = fetchMock.mock.calls.length;
    expect(baseline).toBeGreaterThan(0);

    await openDetail("Compute");
    const link = await screen.findByRole("link", { name: LINK_NAME });
    expect(fetchMock.mock.calls.length).toBe(baseline);

    fireEvent.click(link);
    expect(await screen.findByText("Marcador del asistente")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/assistant");
    expect(router.state.location.search).toBe(`?episode=${ID_A}`);
    // Ni lectura, ni POST, ni PATCH: el panel no crea conversaciones ni envía mensajes.
    expect(fetchMock.mock.calls.length).toBe(baseline);
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST" || init?.method === "PATCH")).toBe(false);
  });

  it("con varias anomalías, el enlace apunta al id de la anomalía cuyo detalle se abrió y no al de otra fila", async () => {
    stubApi([
      episode({ id: ID_A, service: "Compute", accumulated_impact: "900.00" }),
      episode({ id: ID_B, service: "Database", accumulated_impact: "500.00" }),
      episode({ id: ID_C, service: "Analytics", accumulated_impact: "100.00", severity: "P3" }),
    ]);
    renderPanel();
    await showAllStatuses();

    // Se abre la última fila (no la primera) para descartar que el enlace use siempre el primer episodio.
    await openDetail("Analytics");
    const link = await screen.findByRole("link", { name: LINK_NAME });
    expect(link).toHaveAttribute("href", `/assistant?episode=${ID_C}`);
    expect(screen.getAllByRole("link", { name: LINK_NAME })).toHaveLength(1);
  });

  it("al cerrar el detalle y abrir el de otra anomalía muestra el enlace de esa y no el de la anterior", async () => {
    stubApi([
      episode({ id: ID_A, service: "Compute" }),
      episode({ id: ID_B, service: "Database" }),
    ]);
    renderPanel();
    await showAllStatuses();

    await openDetail("Compute");
    expect(await screen.findByRole("link", { name: LINK_NAME })).toHaveAttribute("href", `/assistant?episode=${ID_A}`);
    await closeDetail();

    await openDetail("Database");
    expect(await screen.findByRole("link", { name: LINK_NAME })).toHaveAttribute("href", `/assistant?episode=${ID_B}`);
    await closeDetail();

    // Volver a la primera no debe conservar el destino de la segunda.
    await openDetail("Compute");
    expect(await screen.findByRole("link", { name: LINK_NAME })).toHaveAttribute("href", `/assistant?episode=${ID_A}`);
  });
});
