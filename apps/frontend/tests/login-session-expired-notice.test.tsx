// JUP-098, grupo 4: el aviso de sesion expirada en /login.
//
// El grupo 3 (ya commiteado) garantiza que un 401 fuera de /me en cualquier
// operacion autenticada (o el 401 de /me al arrancar) invalida la sesion con
// motivo "expired" y que `SessionGate` redirige a /login con
// `state={{ sessionExpired: true }}` (ver session-expiry-notice.test.tsx).
// Este grupo (4) cubre la CAPA DE PRESENTACION que todavia no existe:
// `LoginPage` debe leer esa marca una sola vez, mostrar una region
// `role="status"` con el texto exacto de la decision 5 del design, ocultarla
// en cuanto el operador reintenta el acceso, y no dejar ningun rastro
// persistente de la marca (ni en el historial de navegacion ni en storage).
//
// Fase Red (tareas 4.1-4.5): hoy `src/pages/LoginPage.tsx` no renderiza
// ningun `role="status"`, asi que las aserciones que esperan verlo (4.1, 4.2,
// la mitad "el aviso desaparece" de 4.3) fallan genuinamente con "Unable to
// find role='status'". Ademas, el grupo 3 YA deja la marca
// `{ sessionExpired: true }` en el estado de navegacion para el escenario de
// 4.1/4.4 (no solo para el 401 de /me al arrancar que cubre
// session-expiry-notice.test.tsx) -- por eso la asercion de no-persistencia
// de 4.4a tambien es Red genuino hoy, no caracterizacion: la marca todavia
// no se sustituye sin estado porque ese es exactamente el trabajo de la fase
// Green (4.6). El resto de 4.4 (storage y montaje directo en /login) y todo
// 4.5 ya los garantiza el comportamiento heredado de JUP-085/097 y del grupo
// 3, y se documentan aqui como caracterizacion/regresion (igual que se hizo
// en 3.2), para que la fase Green no los rompa por accidente.
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { mockBackend, renderApp, restoreSession, SESSION_KEY } from "./test-support";

// Texto exacto exigido por la decision 5 del design de JUP-098. Se fija como
// constante para no repetir el literal en cada asercion y para que un typo
// futuro en el codigo de produccion (o en el propio test) se note como un
// diff de string, no como un "casi coincide".
const SESSION_EXPIRED_MESSAGE = "Your session has expired. Sign in again to continue.";

// Replica local de la utilidad `failure` de auth-session.test.tsx / grupo 3
// (session-expiry-notice.test.tsx): no esta exportada desde ninguno de los
// dos, y tasks.md prohibe tocar archivos ya commiteados de esta tarjeta.
// Construye una respuesta HTTP fallida por status, o lanza un fallo de red
// simulado.
function failure(kind: number | "network"): Response {
  if (kind === "network") throw new TypeError("Synthetic connection failure");
  return new Response("Synthetic HTTP failure", { status: kind });
}

describe("JUP-098 aviso de sesion expirada en /login", () => {
  it("tarea 4.1: una invalidacion en vuelo por 401 de /billing/summary muestra el aviso de sesion expirada en el acceso", async () => {
    // Escenario: sesion valida navegando a /overview-legacy, pero la peticion
    // autenticada de esa pantalla (GET /billing/summary, no /me) responde
    // 401. El grupo 3 ya garantiza que esto termina en /login con la marca
    // de expiracion en el estado de navegacion; esta prueba exige ademas que
    // la marca se traduzca en un aviso VISIBLE -- lo que hoy no ocurre
    // (Red genuino: LoginPage no renderiza ningun role="status").
    mockBackend({ "GET /billing/summary": () => failure(401) });
    restoreSession();
    renderApp(["/overview-legacy"]);

    await screen.findByRole("button", { name: "Sign in" });

    expect(screen.getByRole("status")).toHaveTextContent(SESSION_EXPIRED_MESSAGE);
  });

  it("tarea 4.2: una invalidacion en vuelo por 401 de la mutacion de ingesta muestra el mismo aviso", async () => {
    // Mismo motivo de expiracion, pero disparado desde una mutacion (POST
    // /jobs/ingest) en vez de una query -- ambos extremos comparten el mismo
    // camino de invalidacion en services/api.ts (fetchJson/discardResponse),
    // por lo que el aviso debe aparecer igual. Red genuino por el mismo
    // motivo que 4.1.
    const user = userEvent.setup();
    mockBackend({ "POST /jobs/ingest": () => failure(401) });
    restoreSession();
    renderApp(["/ingest"]);

    await user.type(await screen.findByLabelText("Text content"), "synthetic cost data");
    await user.click(screen.getByRole("button", { name: "Queue ingestion" }));

    await screen.findByRole("button", { name: "Sign in" });

    expect(screen.getByRole("status")).toHaveTextContent(SESSION_EXPIRED_MESSAGE);
  });

  it("tarea 4.3: el aviso desaparece al iniciar un nuevo intento de acceso, y un intento fallido solo muestra su propio error de credenciales", async () => {
    // Precondicion: reproduce el escenario 4.1 hasta que el aviso este
    // visible (esa espera con `getByRole` sincrono es, hoy, la parte Red de
    // este test: lanza "Unable to find role='status'" porque LoginPage aun
    // no lo renderiza). A partir de ahi, el operador escribe una
    // contrasena y pulsa "Sign in" -- el intento falla con un 401 de
    // /auth/login (un motivo deliberadamente distinto al de expiracion, para
    // comprobar que ambos errores no se mezclan). En cuanto la mutacion de
    // login deja de estar idle, el aviso de expiracion debe desaparecer; si
    // el intento falla, solo debe quedar visible el parrafo rojo de error de
    // credenciales ya existente.
    const user = userEvent.setup();
    mockBackend({
      "GET /billing/summary": () => failure(401),
      "POST /auth/login": () => failure(401)
    });
    restoreSession();
    renderApp(["/overview-legacy"]);

    await screen.findByRole("button", { name: "Sign in" });
    // Precondicion explicita: el aviso esta presente antes del reintento.
    expect(screen.getByRole("status")).toHaveTextContent(SESSION_EXPIRED_MESSAGE);

    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    // El intento falla con el mismo cuerpo sintetico que usan
    // auth-session.test.tsx y session-expiry-notice.test.tsx para un 401 de
    // /auth/login: "Synthetic HTTP failure". Esperar a que aparezca es la
    // señal de que la mutacion ya dejo de estar idle (isError).
    await screen.findByText("Synthetic HTTP failure");

    // El aviso de expiracion ya no debe estar -- solo el error de
    // credenciales del intento fallido.
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("tarea 4.4a: tras llegar a /login desde una invalidacion en vuelo, la entrada de historial ya no deberia llevar la marca de expiracion", async () => {
    // Mismo criterio empirico que session-expiry-notice.test.tsx: la marca
    // vive en el estado de navegacion de react-router, no en storage. El
    // grupo 3 (ya commiteado) hace que este MISMO escenario (401 de
    // /billing/summary) llegue a /login con
    // `state={{ sessionExpired: true }}` -- eso es justo lo que la fase
    // Green de este grupo (4.6) debe corregir: LoginPage debe sustituir esa
    // entrada del historial sin estado en cuanto la lee, para que no
    // sobreviva a una recarga. Por eso esta asercion es Red genuino HOY (no
    // caracterizacion): `router.state.location.state` todavia es
    // `{ sessionExpired: true }`, no `null`.
    mockBackend({ "GET /billing/summary": () => failure(401) });
    restoreSession();
    const { router } = renderApp(["/overview-legacy"]);

    // Se espera a que la navegacion a /login se complete usando una señal
    // que no depende del aviso (que hoy no existe): el propio formulario de
    // acceso ya identifica que la redireccion ocurrio.
    await screen.findByRole("button", { name: "Sign in" });

    expect(router.state.location.pathname).toBe("/login");
    expect(router.state.location.state).toBeNull();
  });

  it("tarea 4.4b: llegar a /login desde una invalidacion no introduce ninguna marca nueva en localStorage ni sessionStorage", async () => {
    // El unico soporte que el design permite para la marca es el estado de
    // navegacion (cubierto por 4.4a). Esta prueba descarta que una
    // implementacion futura de LoginPage decida persistir la marca en
    // storage como mecanismo alternativo -- lo que romperia la garantia de
    // "no persistencia" (una recarga en /login no debe volver a mostrar el
    // aviso). Caracterizacion: ya pasa hoy, porque hoy no existe ningun
    // mecanismo de aviso que pudiera escribir en storage.
    mockBackend({ "GET /billing/summary": () => failure(401) });
    restoreSession();
    renderApp(["/overview-legacy"]);

    await screen.findByRole("button", { name: "Sign in" });

    const localKeys = Object.keys(window.localStorage);
    const sessionKeys = Object.keys(window.sessionStorage);
    expect(localKeys.some((key) => /expired/i.test(key))).toBe(false);
    expect(sessionKeys.some((key) => /expired/i.test(key))).toBe(false);
    // Caracterizacion heredada del grupo 3: la invalidacion ya limpia la
    // sesion persistida (no queda ninguna clave de sesion residual).
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
  });

  it("tarea 4.4c: montar /login directamente sin ninguna invalidacion previa no muestra el aviso desde el principio", async () => {
    // Caso base sin ninguna marca de expiracion en juego: no hay sesion
    // previa ni redireccion, /login es la primera y unica entrada del
    // historial. El aviso nunca deberia aparecer. Caracterizacion: ya pasa
    // hoy porque LoginPage no renderiza ningun role="status" en absoluto
    // todavia; debe seguir pasando tras el Green, donde la ausencia de marca
    // en `location.state` (nunca hubo redireccion) debe seguir sin activar
    // el aviso.
    mockBackend();
    renderApp(["/login"]);

    await screen.findByRole("button", { name: "Sign in" });

    expect(screen.queryByRole("status")).toBeNull();
  });

  it.each([403, 503, "network"] as const)(
    "tarea 4.5: un fallo %s de /billing/summary nunca muestra el aviso de expiracion y conserva la sesion",
    async (kind) => {
      // Caracterizacion heredada de JUP-085/097 (el grupo 3 no cambia esto):
      // un fallo que no es 401 no invalida la sesion, por lo que nunca se
      // navega a /login y, por tanto, LoginPage ni siquiera se monta -- el
      // aviso de expiracion no puede aparecer en ningun momento. Ya pasa hoy.
      mockBackend({ "GET /billing/summary": () => failure(kind) });
      restoreSession();
      const { router } = renderApp(["/overview-legacy"]);

      await screen.findByRole("heading", { name: "Backend unavailable" });

      expect(window.localStorage.getItem(SESSION_KEY)).not.toBeNull();
      expect(router.state.location.pathname).not.toBe("/login");
      expect(screen.queryByRole("status")).toBeNull();
    }
  );
});
