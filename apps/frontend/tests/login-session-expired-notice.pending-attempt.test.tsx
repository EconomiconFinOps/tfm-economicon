// JUP-098, remediacion de revision del PR #50: el aviso de sesion expirada
// debe desaparecer en cuanto EMPIEZA un nuevo intento de acceso (la spec dice
// "SHALL disappear once a new sign-in attempt starts"), no solo cuando ese
// intento ya ha fallado.
//
// Hueco detectado: la tarea 4.3 (login-session-expired-notice.test.tsx)
// comprueba el aviso ANTES del reintento y DESPUES de que el reintento falle,
// pero nunca MIENTRAS la mutacion de login esta pendiente. Con eso, un
// mutante que sustituye `mutation.isIdle` por `!mutation.isError` en
// `LoginPage` dejaba el aviso visible junto al boton "Signing in..." y toda
// la bateria de JUP-098 seguia en verde. Este archivo fija justo esa ventana
// intermedia: la respuesta de POST /auth/login se retiene con un
// `deferredResponse` para observar el estado pendiente de forma determinista
// (sin temporizadores ni esperas arbitrarias).
import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { deferredResponse, mockBackend, renderApp, restoreSession } from "./test-support";

// Texto exacto de la decision 5 del design (mismo literal que en
// login-session-expired-notice.test.tsx; se duplica porque ese archivo no lo
// exporta y los tests commiteados no se pueden editar).
const SESSION_EXPIRED_MESSAGE = "Your session has expired. Sign in again to continue.";

// Replica local de la utilidad `failure` de login-session-expired-notice.test.tsx
// (no exportada): respuesta HTTP fallida por status, o fallo de red simulado.
function failure(kind: number | "network"): Response {
  if (kind === "network") throw new TypeError("Synthetic connection failure");
  return new Response("Synthetic HTTP failure", { status: kind });
}

describe("JUP-098 aviso de sesion expirada durante un intento de acceso pendiente", () => {
  it("el aviso desaparece en cuanto el nuevo intento de acceso esta en vuelo, sin esperar a que falle", async () => {
    // Se retiene la respuesta de /auth/login para que la mutacion quede
    // pendiente (ni idle ni en error) todo el tiempo que haga falta observarla.
    const pending = deferredResponse();
    const user = userEvent.setup();
    mockBackend({
      "GET /billing/summary": () => failure(401),
      "POST /auth/login": () => pending.promise
    });
    restoreSession();
    renderApp(["/overview-legacy"]);

    await screen.findByRole("button", { name: "Sign in" });
    // Precondicion sobre el aviso VISIBLE, no sobre `router.state.location.state`:
    // LoginPage borra la marca del historial en cuanto la lee (tarea 4.4a), asi
    // que consultarla aqui seria una carrera con ese efecto.
    expect(screen.getByRole("status")).toHaveTextContent(SESSION_EXPIRED_MESSAGE);

    await user.type(screen.getByLabelText("Password"), "any-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    // Senal observable de que la mutacion esta pendiente: el boton cambia su
    // etiqueta. En este punto la respuesta sigue retenida, asi que no puede
    // haber ni exito ni error todavia.
    await screen.findByRole("button", { name: "Signing in..." });

    // Nucleo del caso: el intento ya ha empezado, luego el aviso de
    // expiracion no debe convivir con el "Signing in...".
    expect(screen.queryByRole("status")).toBeNull();

    // Limpieza: se libera la respuesta retenida dentro de `act` para que la
    // mutacion termine antes del siguiente test. El error resultante ya lo
    // cubre la tarea 4.3; aqui no se comprueba.
    await act(async () => pending.resolve({ detail: "late" }, 401));
  });
});
