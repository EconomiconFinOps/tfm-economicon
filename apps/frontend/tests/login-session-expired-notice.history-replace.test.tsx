// JUP-098, remediacion de mutacion (tarea 4.7): mutantes supervivientes en
// `LoginPage.tsx` linea 57, dentro del efecto que sustituye la entrada de
// historial que trae la marca `sessionExpired`.
//
// Stryker reporto dos mutantes vivos sobre esa llamada a `navigate`:
//   1. `ObjectLiteral` (57:33): `navigate(location.pathname, {})` -- borra
//      `replace: true` y `state: null` por completo.
//   2. `BooleanLiteral` (57:44): `navigate(location.pathname, { replace:
//      false, state: null })` -- conserva `state: null` pero invierte el
//      modo de REPLACE a PUSH.
//
// Ambos mutantes comparten el mismo efecto observable que este test explota:
// sin `replace: true`, esa llamada hace un PUSH en vez de un REPLACE. El
// test 4.4a (ya commiteado, en login-session-expired-notice.test.tsx) solo
// comprueba el estado ACTUAL de la navegacion (`router.state.location.state
// === null`), que un PUSH tambien deja en `null` -- por eso no mata a estos
// mutantes. Lo que un PUSH rompe es la PROFUNDIDAD de la pila de historial:
// en vez de sustituir la unica entrada de /login (la que dejo el `<Navigate
// replace>` de SessionGate), añade una segunda entrada encima.
//
// Hallazgo empirico (confirmado ejecutando este test contra el mutante antes
// de escribir la aserción final): un simple "atras" con `router.navigate(-1)`
// SI expone, momentaneamente, la entrada vieja con `{ sessionExpired: true }`
// -- pero como `LoginPage` sigue montado, su propio efecto (que escucha
// cambios de `location`) se vuelve a disparar de inmediato al ver la marca
// otra vez, y la corrige con OTRA navegacion (por el mismo codigo mutado,
// otro PUSH), dejando el estado FINAL en `null` de nuevo antes de que
// `await act(...)` devuelva el control. Por eso comprobar solo el estado
// final tras el "atras" NO mata a los mutantes: el auto-arreglo del propio
// efecto lo enmascara. Lo que si distingue REPLACE de PUSH de forma robusta
// es la secuencia COMPLETA de transiciones de historial que ocurre durante
// el "atras": este test se suscribe al router ANTES de navegar para grabar
// cada ubicacion por la que pasa (incluidas las transitorias que un efecto
// posterior podria borrar) y comprueba que ninguna de ellas trae la marca de
// expiracion. Con el codigo real (pila de una sola entrada), "atras" no
// tiene a donde ir (el indice se clampa) y no se emite ninguna transicion.
import { act, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mockBackend, renderApp, restoreSession } from "./test-support";

// Replica local de `failure`, igual que en login-session-expired-notice.test.tsx:
// no esta exportada desde ningun archivo commiteado y tasks.md prohibe
// tocarlos para añadir una exportacion nueva.
function failure(kind: number | "network"): Response {
  if (kind === "network") throw new TypeError("Synthetic connection failure");
  return new Response("Synthetic HTTP failure", { status: kind });
}

describe("JUP-098 remediacion de mutacion: replace de historial en LoginPage", () => {
  it("tarea 4.7: ir hacia atras en el historial tras la correccion de LoginPage no expone la marca de sesion expirada en ninguna transicion", async () => {
    // Mismo escenario que 4.1/4.4a: una invalidacion en vuelo por 401 de
    // /billing/summary navegando a /overview-legacy. El grupo 3 hace que
    // SessionGate llegue a /login con `state={{ sessionExpired: true }}`
    // mediante un REPLACE (no un PUSH) de la unica entrada inicial, por lo
    // que la pila de historial en este punto tiene una sola entrada.
    mockBackend({ "GET /billing/summary": () => failure(401) });
    restoreSession();
    const { router } = renderApp(["/overview-legacy"]);

    // Se espera a que LoginPage ya haya corregido el estado de navegacion
    // (tarea 4.6 / 4.4a): la marca se lee una vez y la entrada de historial
    // se sustituye sin estado.
    await screen.findByRole("button", { name: "Sign in" });
    // La presencia del boton acredita el render, pero el efecto de limpieza
    // del historial puede no haber terminado todavia. Esperar al estado del
    // router antes de observar las transiciones de la navegacion hacia atras.
    await waitFor(() => expect(router.state.location.state).toBeNull());

    // Se suscribe ANTES de navegar hacia atras para grabar cada ubicacion
    // por la que pasa el router durante esa navegacion, incluidas las
    // transitorias (ver comentario superior sobre el auto-arreglo del
    // efecto de LoginPage).
    const visitedLocationStates: unknown[] = [];
    const unsubscribe = router.subscribe((state) => {
      visitedLocationStates.push(state.location.state);
    });

    // El operador pulsa "atras". Con el codigo real, la pila de historial
    // sigue teniendo una sola entrada (LoginPage tambien usa REPLACE, no
    // PUSH), asi que no hay ninguna entrada previa a la que volver y no se
    // emite ninguna transicion con la marca puesta. Se envuelve en `act`
    // porque `router.navigate(-1)` dispara actualizaciones de estado de
    // React.
    await act(async () => {
      await router.navigate(-1);
    });
    unsubscribe();

    // Aserción que mata a ambos mutantes: si el efecto de LoginPage hiciera
    // un PUSH en vez de un REPLACE (cualquiera de los dos mutantes), la pila
    // tendria dos entradas y "atras" pasaria, aunque fuera transitoriamente,
    // por la entrada vieja con `{ sessionExpired: true }` todavia puesta --
    // capturado aqui aunque el propio efecto la corrija enseguida despues.
    // Con el codigo real, ninguna transicion trae esa marca.
    expect(visitedLocationStates).not.toContainEqual({ sessionExpired: true });
    // Y el estado final, tras cualquier auto-correccion, sigue sin persistir
    // la marca (comportamiento ya cubierto por 4.4a, reafirmado aqui).
    expect(router.state.location.state).toBeNull();
  });
});
