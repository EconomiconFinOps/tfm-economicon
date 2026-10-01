import { describe, expect, it, vi } from "vitest";
import { getSessionGeneration, invalidateSession, subscribeSessionInvalidation } from "./api";

// Archivo nuevo (no `api.test.ts`) porque ese archivo ya esta commiteado y
// estaba protegido contra edicion en el entorno local. Este test remedia un mutante superviviente
// de Stryker sobre `services/api.ts` (tarea 2.4): no toca `api.test.ts` ni
// ningun archivo de producto.

describe("JUP-098 invalidateSession avanza la generacion internamente (remediacion mutacion 2.4)", () => {
  it("una segunda llamada con la generacion original ya invalidada no vuelve a notificar", () => {
    // Mutante Stryker superviviente (CallExpression, api.ts linea 50):
    // eliminar la llamada a `advanceSessionGeneration()` dentro de
    // `invalidateSession` no hace fallar ningun test existente. Si esa
    // llamada no ocurriera de verdad, `sessionGeneration` no cambiaria tras
    // la primera invalidacion, y una segunda llamada con la MISMA generacion
    // original volveria a pasar el guard `generation !== sessionGeneration` y
    // notificaria otra vez -- cuando esa generacion ya deberia estar muerta.
    const generation = getSessionGeneration();
    const listener = vi.fn();
    const unsubscribe = subscribeSessionInvalidation(listener);
    try {
      // Primera invalidacion: comportamiento ya cubierto por otros tests,
      // pero se reafirma aqui para dejar clara la secuencia del escenario.
      invalidateSession(generation, "expired");
      expect(listener).toHaveBeenCalledExactlyOnceWith("expired");

      // Si `advanceSessionGeneration()` se ejecuto de verdad, la generacion
      // interna ya no coincide con el valor capturado al principio.
      expect(getSessionGeneration()).not.toBe(generation);

      listener.mockClear();
      // Clave del test: se reusa deliberadamente la variable `generation`
      // capturada al principio (no `getSessionGeneration()` recalculado).
      // Con `advanceSessionGeneration()` presente, ese `generation` ya es una
      // generacion vieja y el guard debe bloquear la notificacion. Si el
      // mutante (que elimina esa llamada) estuviera vivo, este `generation`
      // seguiria coincidiendo con la generacion actual y el listener volveria
      // a ser invocado -- haciendo fallar esta asercion.
      invalidateSession(generation, "expired");
      expect(listener).not.toHaveBeenCalled();
    } finally {
      unsubscribe();
    }
  });
});
