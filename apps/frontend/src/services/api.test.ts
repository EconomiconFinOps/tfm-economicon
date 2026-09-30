import { describe, expect, it, vi } from "vitest";
import {
  advanceSessionGeneration,
  getSessionGeneration,
  invalidateSession,
  subscribeSessionInvalidation
} from "./api";

// `sessionGeneration` es estado de modulo compartido entre todos los tests de
// este archivo (y potencialmente con otros modulos que importen `./api` en el
// mismo proceso de Vitest). Por eso cada test lee la generacion actual con
// `getSessionGeneration()` en vez de asumir que empieza en 0 -- asumirlo
// acoplaria el resultado al orden de ejecucion de la suite completa.

describe("JUP-098 invalidateSession reason propagation (tarea 2.1)", () => {
  it("notifica 'expired' cuando invalidateSession se llama con ese motivo explicito", () => {
    const generation = getSessionGeneration();
    const listener = vi.fn();
    const unsubscribe = subscribeSessionInvalidation(listener);
    try {
      invalidateSession(generation, "expired");
      // El listener debe recibir exactamente el literal "expired", no un
      // booleano de exito ni un objeto envoltorio.
      expect(listener).toHaveBeenCalledExactlyOnceWith("expired");
    } finally {
      unsubscribe();
    }
  });

  it("notifica el motivo neutro 'manual' cuando no se pasa segundo argumento", () => {
    const generation = getSessionGeneration();
    const listener = vi.fn();
    const unsubscribe = subscribeSessionInvalidation(listener);
    try {
      // Sin segundo argumento: logout manual y demas casos sin motivo
      // especifico deben caer en el valor por defecto "manual".
      invalidateSession(generation);
      expect(listener).toHaveBeenCalledExactlyOnceWith("manual");
    } finally {
      unsubscribe();
    }
  });

  it("propaga el mismo motivo a todos los listeners suscritos en la misma llamada", () => {
    const generation = getSessionGeneration();
    const listenerA = vi.fn();
    const listenerB = vi.fn();
    const unsubscribeA = subscribeSessionInvalidation(listenerA);
    const unsubscribeB = subscribeSessionInvalidation(listenerB);
    try {
      invalidateSession(generation, "expired");
      expect(listenerA).toHaveBeenCalledExactlyOnceWith("expired");
      expect(listenerB).toHaveBeenCalledExactlyOnceWith("expired");
    } finally {
      unsubscribeA();
      unsubscribeB();
    }
  });

  it("deja de notificar a un listener despues de desuscribirlo", () => {
    const generation = getSessionGeneration();
    const listener = vi.fn();
    const unsubscribe = subscribeSessionInvalidation(listener);
    // Desuscribir antes de invalidar: la funcion devuelta por
    // subscribeSessionInvalidation debe romper la suscripcion de verdad, no
    // solo marcarla como inactiva.
    unsubscribe();
    invalidateSession(generation, "expired");
    expect(listener).not.toHaveBeenCalled();
  });
});

describe("JUP-098 invalidacion de generacion abandonada no notifica motivo (tarea 2.2)", () => {
  it("invalidateSession con una generacion vieja no invoca al listener en absoluto", () => {
    const oldGeneration = getSessionGeneration();
    const listener = vi.fn();
    const unsubscribe = subscribeSessionInvalidation(listener);
    try {
      // Avanzar la generacion actual simula que ya hubo una invalidacion (o
      // un logout) entre la captura de `oldGeneration` y esta llamada: la
      // peticion en curso quedo abandonada.
      advanceSessionGeneration();
      invalidateSession(oldGeneration, "expired");
      // El guard de generacion debe retornar antes del forEach: ni "expired"
      // ni "manual" ni ningun otro valor llega al listener.
      expect(listener).not.toHaveBeenCalled();
    } finally {
      unsubscribe();
    }
  });
});
