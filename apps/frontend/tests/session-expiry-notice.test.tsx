// JUP-098, grupo 3: la marca de expiracion (`{ sessionExpired: true }`) en el
// estado de navegacion de `/login` solo debe aparecer cuando el motivo real
// de fin de sesion es un `401` de `GET /me` al arrancar. Cualquier otro
// motivo (errores no-401 de `/me`, contrato invalido, logout manual o "Reset
// session" tras un fallo de tenants) debe terminar en `/login` SIN marca.
//
// Tarea 3.1 fija el Red genuino: hoy `SessionGate` no propaga ningun motivo
// a `<Navigate>`, asi que la marca nunca llega.
// Tarea 3.2 son pruebas de caracterizacion/regresion: el comportamiento sin
// marca ya es el actual (no cambia con este grupo), pero se fijan aqui para
// que la fase Green (3.3) no las rompa por accidente.
//
// Nota empirica sobre el "ausente" del enunciado: react-router (createLocation,
// chunk-JZWAC4HX.mjs:210, `state = null` como valor por defecto del parametro)
// normaliza SIEMPRE un `state` no proporcionado (o `undefined`) a `null`, nunca
// a `undefined` -- tanto hoy como tras el Green, ya que <Navigate> sin la prop
// `state` (o con `state={undefined}`) pasa por el mismo default. Por eso estas
// aserciones usan `toBeNull()`, no `toBeUndefined()`: es el unico valor que el
// "ausente" puede tomar en la practica con esta libreria.
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { operator } from "./fixtures";
import { jsonResponse, mockBackend, renderApp, restoreSession } from "./test-support";

// Replica local de la utilidad `failure` de auth-session.test.tsx (no
// exportada desde alli, y tasks.md prohibe tocar ese archivo): construye una
// respuesta HTTP fallida por status, o lanza un fallo de red simulado.
function failure(kind: number | "network"): Response {
  if (kind === "network") throw new TypeError("Synthetic connection failure");
  return new Response("Synthetic HTTP failure", { status: kind });
}

// Espera a que el router termine en /login y devuelve el estado de
// navegacion de esa ubicacion, tal como lo expone react-router v7 en
// `router.state.location.state`.
async function waitForLoginState(router: { state: { location: { pathname: string; state: unknown } } }) {
  await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
  return router.state.location.state;
}

describe("JUP-098 marca de expiracion de sesion en /login", () => {
  it("un 401 de /me al arrancar con sesion persistida termina en /login con la marca de expiracion", async () => {
    // Red genuino (tarea 3.1): hoy SessionGate desloguea via handleLogout()
    // pero <Navigate> nunca pasa `state`, asi que este expect falla.
    mockBackend({ "GET /me": () => failure(401) });
    restoreSession();
    const { router } = renderApp(["/"]);
    const state = await waitForLoginState(router);
    expect(state).toEqual({ sessionExpired: true });
  });

  it.each([403, 503, "network"] as const)(
    "un error %s de /me al arrancar termina en /login sin marca de expiracion",
    async (kind) => {
      // Caracterizacion (tarea 3.2): el comportamiento sin marca ya es el
      // actual hoy; se fija para que la fase Green no lo rompa.
      mockBackend({ "GET /me": () => failure(kind) });
      restoreSession();
      const { router } = renderApp(["/"]);
      const state = await waitForLoginState(router);
      expect(state).toBeNull();
    }
  );

  it.each([
    ["null", null],
    ["missing-id", { email: operator.email, full_name: operator.full_name, role: operator.role }]
  ])(
    "un contrato de perfil invalido (%s) en /me termina en /login sin marca de expiracion",
    async (_name, profile) => {
      // Caracterizacion (tarea 3.2): un 200 con contrato invalido no es un
      // 401, por lo que nunca debe dejar la marca de expiracion.
      mockBackend({ "GET /me": () => jsonResponse(profile) });
      restoreSession();
      const { router } = renderApp(["/"]);
      const state = await waitForLoginState(router);
      expect(state).toBeNull();
    }
  );

  it("el cierre de sesion manual (boton Cerrar sesion) termina en /login sin marca de expiracion", async () => {
    // Caracterizacion (tarea 3.2): logout manual usa el motivo neutro por
    // defecto de invalidateSession, nunca "expired".
    const user = userEvent.setup();
    mockBackend();
    restoreSession();
    const { router } = renderApp(["/"]);
    await screen.findByRole("button", { name: "Cerrar sesion" });
    await user.click(screen.getByRole("button", { name: "Cerrar sesion" }));
    const state = await waitForLoginState(router);
    expect(state).toBeNull();
  });

  it('el boton "Reset session" tras un 403 de /tenants termina en /login sin marca de expiracion', async () => {
    // Caracterizacion (tarea 3.2): un fallo de tenants no relacionado con
    // /me tampoco debe dejar la marca de expiracion al desloguear.
    const user = userEvent.setup();
    mockBackend({ "GET /tenants": () => failure(403) });
    restoreSession();
    const { router } = renderApp(["/"]);
    await user.click(await screen.findByRole("button", { name: "Reset session" }));
    const state = await waitForLoginState(router);
    expect(state).toBeNull();
  });
});
