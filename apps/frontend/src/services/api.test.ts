import { afterEach, describe, expect, it, vi } from "vitest";
import {
  advanceSessionGeneration,
  checkHealthProvider,
  fetchSystemHealth,
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


describe("JUP-047 provider API information is separate from functional validity", () => {
  const stamp = "2026-10-06T12:00:00Z";
  function observation(extra: Record<string, unknown> = {}) {
    return { id: "openrouter", status: "ok", reason_code: "none", source_kind: "live",
      checked_at: stamp, latency_ms: 12, verified_at: stamp, last_attempt_at: stamp,
      expires_at: "2026-10-06T12:01:00Z", check_id: "synthetic-check",
      reported_model: "economicon-chat", model_identity: "unconfirmed",
      reported_cost_usd: "0.00002", cost_status: "gateway_reported", cost_confirmation: "unconfirmed", ...extra };
  }
  function response(payload: unknown, status = 200) {
    const mocked = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify(payload),
      { status, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", mocked);
    return mocked;
  }
  function checkProvider() {
    return checkHealthProvider("synthetic-token", "tenant-a", "opening", new AbortController().signal);
  }
  afterEach(() => { vi.unstubAllGlobals(); });

  it.each([
    { label: "valid exact information", extra: {}, model: "economicon-chat", cost: "0.00002", costStatus: "gateway_reported" },
    { label: "absent information", extra: { reported_model: undefined, model_identity: undefined,
      reported_cost_usd: undefined, cost_status: undefined, cost_confirmation: undefined }, model: null, cost: null, costStatus: "unavailable" },
    { label: "unsafe and falsely certified information", extra: { reported_model: "unsafe://private?token=synthetic-secret",
      model_identity: "verified", reported_cost_usd: "NaN", cost_confirmation: "verified" }, model: null, cost: null, costStatus: "invalid" }
  ])("normalizes GET $label without changing functional validity", async ({ extra, model, cost, costStatus }) => {
    const snapshot = {
      status: "ok", tenant_id: "tenant-a", checked_at: stamp,
      window: { start: "2026-10-05T12:00:00Z", end: stamp },
      components: ["backend", "database", "rabbitmq", "processor", "vector_store", "azure_cost_api", "litellm"].map(id => ({
        id, status: "ok", reason_code: "none", source_kind: "live", checked_at: stamp, latency_ms: 0
      })).concat([observation(extra)]),
      jobs: { data_status: "empty", counts: { publish_pending: 0, publish_failed: 0, publish_unknown: 0,
        queued: 0, running: 0, completed: 0, failed: 0, other: 0 }, failed_last_24h: 0, last_updated_at: null },
      ingestion: { data_status: "empty", counts: { running: 0, completed: 0, failed: 0, other: 0 },
        failed_last_24h: 0, last_completed_at: null }
    };
    const mocked = response(snapshot);
    const result = await fetchSystemHealth("synthetic-token", "tenant-a", new AbortController().signal);
    expect(result.tenant_id).toBe("tenant-a");
    expect(result.components.find(component => component.id === "openrouter")).toMatchObject({
      status: "ok", verified_at: stamp, reported_model: model, model_identity: "unconfirmed",
      reported_cost_usd: cost, cost_status: costStatus, cost_confirmation: "unconfirmed"
    });
    expect(JSON.stringify(result)).not.toContain("synthetic-secret");
    expect(mocked).toHaveBeenCalledTimes(1);
    expect(mocked.mock.calls[0][0]).toContain("/health/status");
    const init = mocked.mock.calls[0][1]!;
    expect(init.method ?? "GET").toBe("GET");
    expect(init.body).toBeUndefined();
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer synthetic-token");
    expect(new Headers(init.headers).get("X-Tenant-Id")).toBe("tenant-a");
  });


  it.each(["economicon-chat", "openrouter/z-ai/glm-5.2", "z-ai/glm-5.2-20260616", "other-model"])(
    "preserves reported %s as unconfirmed information without changing request model", async (reported_model) => {
      const mocked = response(observation({ reported_model }));
      await expect(checkProvider()).resolves.toMatchObject({
        status: "ok", verified_at: stamp, reported_model, model_identity: "unconfirmed", cost_confirmation: "unconfirmed"
      });
      const init = mocked.mock.calls[0][1]!;
      expect(JSON.parse(String(init.body))).toEqual({ idempotency_key: "opening" });
      expect(new Headers(init.headers).get("Authorization")).toBe("Bearer synthetic-token");
      expect(new Headers(init.headers).get("X-Tenant-Id")).toBe("tenant-a");
    }
  );

  it("normalizes absent information while retaining valid functionality", async () => {
    const payload = observation();
    const { reported_model, model_identity, reported_cost_usd, cost_status, cost_confirmation, ...legacy } = payload;
    void reported_model; void model_identity; void reported_cost_usd; void cost_status; void cost_confirmation;
    response(legacy);
    await expect(checkProvider()).resolves.toMatchObject({
      status: "ok", verified_at: stamp, reported_model: null, model_identity: "unconfirmed",
      reported_cost_usd: null, cost_status: "unavailable", cost_confirmation: "unconfirmed"
    });
  });

  it.each([42, { name: "different-model" }, "x".repeat(257), "unsafe://private?token=synthetic-secret"])(
    "normalizes unusable model information without invalidating a functional response", async (reported_model) => {
      response(observation({ reported_model, model_identity: "verified" }));
      const result = await checkProvider();
      expect(result).toMatchObject({ status: "ok", reported_model: null, model_identity: "unconfirmed" });
      expect(JSON.stringify(result)).not.toContain("synthetic-secret");
    }
  );

  it.each(["NaN", "Infinity", "-1", { amount: 1 }])(
    "normalizes malformed cost information and never certifies upstream billing", async (reported_cost_usd) => {
      response(observation({ reported_cost_usd, cost_confirmation: "verified" }));
      await expect(checkProvider()).resolves.toMatchObject({
        status: "ok", verified_at: stamp, reported_cost_usd: null, cost_status: "invalid", cost_confirmation: "unconfirmed"
      });
    }
  );

  it("cannot certify identity or cost just because server fields claim verified", async () => {
    response(observation({ reported_model: "openrouter/z-ai/glm-5.2", model_identity: "verified", cost_confirmation: "verified" }));
    await expect(checkProvider()).resolves.toMatchObject({ status: "ok", model_identity: "unconfirmed", cost_confirmation: "unconfirmed" });
  });

  it.each([{ status: "invented-green" }, { verified_at: "invalid-date" }, { source_kind: "mock" }, { check_id: null }])(
    "still rejects an invalid functional observation despite informational data", async (extra) => {
      response(observation(extra));
      await expect(checkProvider()).rejects.toThrow();
    }
  );

  it("HTTP401 expires the current session and discards its response", async () => {
    response(observation(), 401);
    const expired = vi.fn();
    const unsubscribe = subscribeSessionInvalidation(expired);
    let settled = false;
    try {
      void checkProvider().then(() => { settled = true; }, () => { settled = true; });
      await vi.waitFor(() => expect(expired).toHaveBeenCalledExactlyOnceWith("expired"));
      await Promise.resolve();
      expect(settled).toBe(false);
    } finally { unsubscribe(); }
  });

  it.each([403, 500])("still rejects HTTP%s even when model/cost look valid", async (status) => {
    response(observation(), status);
    await expect(checkProvider()).rejects.toThrow();
  });
});
