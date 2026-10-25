// JUP-098, remediacion de mutacion (tarea 3.5): mutante superviviente real en
// SessionGate.tsx:86 -- cambiar `useState(false)` por `useState(true)` en el
// valor inicial de `sessionExpired`.
//
// Intento inicial (descartado): un test que solo comprueba el ESTADO FINAL
// asentado de `router.state.location.state` tras `waitFor` NO mata este
// mutante. Motivo verificado empiricamente: cuando `session` es null desde
// el primer render, el propio efecto de `SessionGate` (linea 98) llama a
// `invalidateSession(generation)` SIN motivo explicito -> el default es
// "manual" (services/api.ts) -> el suscriptor pone `sessionExpired` a
// `false` de verdad DENTRO del mismo `act()` sincrono que usa
// `@testing-library/react` para montar. Esa correccion desencadena un
// segundo commit donde `<Navigate>` vuelve a llamar a `navigate()` con el
// `state` ya corregido, y `replace: true` sobrescribe la MISMA entrada de
// historial -- todo antes de que `render()` devuelva el control al test.
// Con o sin el mutante, el valor final que ve cualquier `waitFor` posterior
// es identico: el mutante se "autocura" en el mismo tick.
//
// Por eso este test no inspecciona solo el estado final: se suscribe al
// router ANTES del primer render/commit (via `router.subscribe`, expuesto
// por `createMemoryRouter`) para capturar TODAS las transiciones a /login
// que ocurren durante ese proceso de asentamiento, incluida la primera
// (la que <Navigate> dispara con el valor inicial de `sessionExpired` antes
// de que el efecto corrector de SessionGate tenga ocasion de correr). Esa
// primera transicion es exactamente lo que el mutante corrompe: con
// `useState(true)`, la marca de expiracion aparece ahi aunque se corrija
// enseguida; con el codigo real, nunca aparece porque el valor inicial ya es
// `false`.
//
// Este caso corresponde al escenario "The session ends without server
// rejection" de specs/demo-auth-session/spec.md: un arranque con sesion
// ausente (no invalida, genuinamente ausente desde el principio) nunca debe
// mostrar la marca de expiracion -- ni siquiera transitoriamente.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";
import { routeConfig } from "../src/routes";
import { mockBackend, SESSION_KEY } from "./test-support";

describe("JUP-098 marca de expiracion de sesion en /login (montaje en frio)", () => {
  it("un arranque sin ninguna sesion persistida nunca marca /login como expirado, ni siquiera transitoriamente", async () => {
    // Verificacion explicita de la premisa del caso: no hay sesion alguna en
    // localStorage antes de renderizar (a diferencia de todos los tests de
    // session-expiry-notice.test.tsx, que llaman a restoreSession()).
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();

    // Sin overrides: con `enabled: Boolean(session?.accessToken)` en falso
    // desde el primer render, ninguna peticion autenticada deberia salir
    // (test-support falla el test si llega una peticion no interceptada).
    mockBackend();

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: Infinity },
        mutations: { retry: false }
      }
    });
    const router = createMemoryRouter(routeConfig, { initialEntries: ["/"] });

    // Se suscribe ANTES de montar: es la unica forma de observar el primer
    // valor que <Navigate> paso a `navigate()`, antes de que el efecto
    // autocorrector de SessionGate (que corre en el mismo `act()` sincrono
    // del montaje) lo tape.
    const observedLoginStates: unknown[] = [];
    const unsubscribe = router.subscribe((state) => {
      if (state.location.pathname === "/login") observedLoginStates.push(state.location.state);
    });

    render(
      <QueryClientProvider client={client}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    );

    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));

    unsubscribe();
    client.clear();

    // Ni siquiera transitoriamente /login debe haber recibido la marca de
    // expiracion: esta es la asercion que el mutante (useState(true)) rompe
    // -- con el, `observedLoginStates` contiene `{ sessionExpired: true }`
    // en su primera entrada, aunque un commit posterior la corrija.
    expect(observedLoginStates).not.toContainEqual({ sessionExpired: true });

    // Mismo criterio empirico documentado en session-expiry-notice.test.tsx:
    // react-router normaliza el `state` ausente a `null`, nunca a
    // `undefined`. El estado final, tras asentarse, tambien debe ser nulo.
    expect(router.state.location.state).toBeNull();
  });
});
