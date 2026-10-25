import { describe, expect, it } from "vitest";
import { episode } from "../test/anomalyFixtures";
import { exportRows, filterEpisodes, openingExcess, runCounts, validClosingReason } from "./anomalyPanel";

describe("JUP-114 funciones del panel de anomalías", () => {
  const open = episode();
  const ended = episode({ id: "e2", service: null, observation: "no_longer_observed", no_longer_observed_on: "2026-09-14", severity: "P3" });
  const closed = episode({ id: "e3", status: "false_positive", closure_reason: "=cmd", severity: "P2" });

  it("exporta las columnas acordadas, con el origen y la naturaleza de candidata", () => {
    const [row] = exportRows([open], { tenantName: "Core Finance", synthetic: true, lastEvaluated: "2026-09-20" });
    expect(Object.keys(row)).toEqual(["Cliente", "Origen", "Criticidad", "Servicio", "Moneda", "Impacto acumulado",
      "Días con impacto", "Inicio", "Última vez vista", "Observación", "Estado", "Motivo de cierre", "Revisado hasta",
      "Reglas", "Naturaleza"]);
    expect(row).toMatchObject({ Cliente: "Core Finance", Origen: "Sintéticos", Criticidad: "Alta (P1)", Moneda: "EUR",
      "Impacto acumulado": "2807.71", "Revisado hasta": "2026-09-20", Naturaleza: "Candidata: causa no establecida" });
    const [ingested] = exportRows([ended], { tenantName: "Core Finance", synthetic: false, lastEvaluated: null });
    expect(ingested).toMatchObject({ Origen: "Ingesta de costes", Servicio: "(sin servicio)",
      Observación: "Ya no se observa desde 14/09/2026", "Revisado hasta": "" });
    expect(JSON.stringify(ingested)).not.toMatch(/real/i);
  });

  it("filtra por criticidad, estado y observación combinados", () => {
    const all = [open, ended, closed];
    expect(filterEpisodes(all, "all", "open", "all").map((e) => e.id)).toEqual(["anomaly-1", "e2"]);
    expect(filterEpisodes(all, "P3", "open", "no_longer_observed").map((e) => e.id)).toEqual(["e2"]);
    expect(filterEpisodes(all, "P2", "false_positive", "all").map((e) => e.id)).toEqual(["e3"]);
    expect(filterEpisodes(all, "P1", "resolved", "all")).toEqual([]);
  });

  it("calcula el exceso del día de apertura con céntimos exactos", () => {
    expect(openingExcess(episode({ opening_observed_cost: "377.00", reference_daily_cost: "142.86" }))).toBe("234.14");
    expect(openingExcess(episode({ opening_observed_cost: "18014398509481986.05", reference_daily_cost: "9007199254740993.01" })))
      .toBe("9007199254740993.04");
  });

  it.each([
    ["Escalado revertido", true], ["  ok  ", true], ["ñandú — 42", true], ["😀", true],
    ["", false], ["   ", false], ["\u200b", false], ["\u3164", false], ["\u2800", false], ["\u0301", false],
    ["a\u0007b", false], ["ok\u0085", true], ["\u001fok\u001c", true], ["\u0085", false], ["a\u202eb", false], ["a\u2028b", false], ["x".repeat(501), false],
  ])("valida el motivo %j como el backend", (reason, valid) => {
    expect(validClosingReason(reason)).toBe(valid);
  });

  it("resume los recuentos de una detección en singular y plural", () => {
    const base = { status: "completed" as const, rules_version: "v", last_complete_day: "2026-09-20", evaluated_days: [],
      skipped_days: [], unsupported_currencies: [] };
    expect(runCounts({ ...base, opened: 1, continued: 1, no_longer_observed: 1 }))
      .toBe("1 anomalía nueva · 1 sigue activa · 1 ya no se observa");
    expect(runCounts({ ...base, opened: 0, continued: 2, no_longer_observed: 2 }))
      .toBe("0 anomalías nuevas · 2 siguen activas · 2 ya no se observan");
  });
});
