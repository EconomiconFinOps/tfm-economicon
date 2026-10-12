import { afterEach, describe, expect, it, vi } from "vitest";
import { changeAnomalyEpisodeStatus, detectAnomalies, fetchAnomalyEpisodes } from "./api";
import { isAnomalyDetectionRun, isAnomalyEpisodeList, type AnomalyEpisode } from "./contracts";

export function episode(overrides: Partial<AnomalyEpisode> = {}): AnomalyEpisode {
  return {
    id: "anomaly-1", kind: "cost_anomaly_candidate", currency: "EUR", service: "Compute",
    start_date: "2026-09-09", last_seen_date: "2026-09-20", observation: "observed", no_longer_observed_on: null,
    reference_daily_cost: "142.86", opening_observed_cost: "377.00", accumulated_impact: "2807.71",
    impact_day_count: 12, impact_through_date: "2026-09-20", severity: "P1", status: "new",
    status_changed_by: null, status_changed_at: null, first_reviewed_at: null, first_reviewed_by: null,
    closed_at: null, closure_reason: null, previous_episode_id: null, rules_version: "jup019-daily-v1",
    rules: { absolute_increase: "100.00" }, cause_status: "not_established", limitations: ["Candidata"],
    created_at: "2026-10-12T10:00:00Z", updated_at: "2026-10-12T10:00:00Z",
    ...overrides,
  };
}

export function episodeList(overrides: Record<string, unknown> = {}) {
  return {
    contract_version: 1, scope: "all", episodes: [episode()], last_evaluated_date: "2026-09-20",
    includes_synthetic_data: true, open_impact_by_currency: [{ currency: "EUR", amount: "2807.71" }],
    ...overrides,
  };
}

const run = {
  status: "completed", rules_version: "jup019-daily-v1", last_complete_day: "2026-09-20",
  evaluated_days: ["2026-09-08"], skipped_days: [{ date: "2026-09-07", reason: "reference_incomplete" }],
  unsupported_currencies: [], opened: 3, continued: 0, no_longer_observed: 1,
};

describe("JUP-114 contratos de episodios", () => {
  it("acepta una lista completa y una sin detecciones", () => {
    expect(isAnomalyEpisodeList(episodeList())).toBe(true);
    expect(isAnomalyEpisodeList(episodeList({ episodes: [], last_evaluated_date: null, open_impact_by_currency: [] }))).toBe(true);
    expect(isAnomalyEpisodeList(episodeList({ episodes: [episode({ service: null, status: "resolved",
      closed_at: "2026-10-12T11:00:00.123456Z", closure_reason: "ok", observation: "no_longer_observed",
      no_longer_observed_on: "2026-09-14" })] }))).toBe(true);
  });

  it.each([
    ["severidad desconocida", { episodes: [episode({ severity: "P4" as never })] }],
    ["estado desconocido", { episodes: [episode({ status: "acknowledged" as never })] }],
    ["importe sin dos decimales", { episodes: [episode({ accumulated_impact: "2807.7" })] }],
    ["importe numérico", { episodes: [episode({ accumulated_impact: 2807.71 as never })] }],
    ["cero negativo", { open_impact_by_currency: [{ currency: "EUR", amount: "-0.00" }] }],
    ["fecha inválida", { last_evaluated_date: "2026-02-30" }],
    ["sin indicador sintético", { includes_synthetic_data: undefined }],
    ["indicador como texto", { includes_synthetic_data: "true" }],
    ["moneda repetida en los totales", { open_impact_by_currency: [{ currency: "EUR", amount: "1.00" }, { currency: "EUR", amount: "2.00" }] }],
    ["causa establecida", { episodes: [episode({ cause_status: "established" as never })] }],
    ["versión de contrato distinta", { contract_version: 2 }],
  ])("rechaza %s", (_label, overrides) => {
    expect(isAnomalyEpisodeList(episodeList(overrides))).toBe(false);
  });

  it("valida el resultado de una detección", () => {
    expect(isAnomalyDetectionRun(run)).toBe(true);
    expect(isAnomalyDetectionRun({ ...run, status: "up_to_date", evaluated_days: [], skipped_days: [] })).toBe(true);
    expect(isAnomalyDetectionRun({ ...run, status: "done" })).toBe(false);
    expect(isAnomalyDetectionRun({ ...run, opened: -1 })).toBe(false);
    expect(isAnomalyDetectionRun({ ...run, skipped_days: [{ date: "2026-09-07", reason: "late" }] })).toBe(false);
  });
});

describe("JUP-114 cliente de episodios", () => {
  afterEach(() => vi.unstubAllGlobals());

  function stubFetch(body: unknown, status = 200) {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
  }

  it("lista todos los episodios del tenant activo", async () => {
    const fetchMock = stubFetch(episodeList());
    await expect(fetchAnomalyEpisodes("token-x", "tenant-core")).resolves.toEqual(episodeList());
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/billing\/anomalies\/episodes\?scope=all$/);
    expect(init.headers).toMatchObject({ Authorization: "Bearer token-x", "X-Tenant-Id": "tenant-core" });
  });

  it("rechaza una lista que no cumple el contrato", async () => {
    stubFetch(episodeList({ includes_synthetic_data: "yes" }));
    await expect(fetchAnomalyEpisodes("token-x", "tenant-core")).rejects.toThrow(/Invalid response/);
  });

  it("detecta sin enviar cuerpo", async () => {
    const fetchMock = stubFetch(run);
    await expect(detectAnomalies("token-x", "tenant-core")).resolves.toEqual(run);
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/billing\/anomalies\/detect$/);
    expect(init.method).toBe("POST");
    expect(init.body).toBeUndefined();
  });

  it("cambia el estado con PATCH y codifica el id", async () => {
    const fetchMock = stubFetch(episode({ status: "resolved" }));
    await changeAnomalyEpisodeStatus("token-x", "tenant-core", "anomaly-a/b", { status: "resolved", reason: "Escalado revertido" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/billing\/anomalies\/episodes\/anomaly-a%2Fb$/);
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body)).toEqual({ status: "resolved", reason: "Escalado revertido" });
  });

  it("propaga el código de conflicto del backend", async () => {
    stubFetch({ detail: { code: "status_change_conflict" } }, 409);
    await expect(changeAnomalyEpisodeStatus("token-x", "tenant-core", "anomaly-1", { status: "investigating" }))
      .rejects.toMatchObject({ status: 409, message: expect.stringContaining("status_change_conflict") });
  });
});
