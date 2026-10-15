import { describe, expect, it } from "vitest";
import { isAnomalyEvidence } from "./contracts";
import { episode } from "../test/anomalyFixtures";

// JUP-038 tarea 5.4: remediación de mutantes supervivientes de isAnomalyEvidence (contracts.ts).
// Las pruebas de anomalyEvidence.test.ts están commiteadas y bloqueadas, así que estos casos van aparte.

const LIMITATIONS = [
  "Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.",
  "No se verifica que los datos de coste estén completos; un día puede evaluarse antes de que lleguen registros tardíos.",
];

const VALID_ID = `anomaly-explanation:${"a".repeat(64)}`;

// Evidencia JSON laxa que las pruebas mutan a mano (sin `any`): los niveles anidados se castean a `Mut`.
type Mut = { [key: string]: unknown };

// Duplicado de evidenceA de anomalyEvidence.test.ts (un test no puede importarse desde otro):
// ejemplo A, Compute, EUR, apertura 2026-09-08, impacto 400.00 en 2 días, P3.
function evidenceA(): Mut {
  return {
    schema_version: "1.0",
    adapter_version: "anomaly-explanation-1.0",
    id: VALID_ID,
    status: "ok",
    source: { kind: "anomaly_episodes", rules_version: "jup019-daily-v1", data_as_of: "2026-09-09" },
    episode: episode({
      id: "ep-a", currency: "EUR", service: "Compute", start_date: "2026-09-08", last_seen_date: "2026-09-09",
      reference_daily_cost: "400.00", opening_observed_cost: "550.00", accumulated_impact: "400.00",
      impact_day_count: 2, impact_through_date: "2026-09-09", severity: "P3", status: "new",
      rules_version: "jup019-daily-v1", limitations: LIMITATIONS,
      created_at: "2026-09-10T03:00:00+00:00", updated_at: "2026-09-10T03:00:00+00:00",
    }),
    operands: {
      reference_seven_day_total: "2800.000000000000",
      opening_observed_cost: "550.000000000000",
      accumulated_impact_times_seven: "2800.000000000000",
    },
    opening: {
      reference_daily_cost: "400.00", observed_cost: "550.00", absolute_increase: "150.00",
      relative_increase_percent: "37.50", absolute_threshold: "100.00", relative_threshold_percent: "20",
      conditions_met: true,
    },
    impact: {
      accumulated_impact: "400.00", day_count: 2, through_date: "2026-09-09", severity: "P3", severity_band: "< 500.00",
    },
    rounding_notes: [],
    includes_synthetic_data: false,
    cause_status: "not_established",
    assumptions: [],
    limitations: LIMITATIONS,
    explained_at: "2026-10-12T18:30:00+00:00",
  };
}

function mutated(change: (copy: Mut) => void): Mut {
  const copy = structuredClone(evidenceA());
  change(copy);
  return copy;
}

describe("JUP-038 isAnomalyEvidence: el id debe ser una cadena de verdad (mutante typeof value.id !== 'string' -> false)", () => {
  it("control positivo: el id como cadena con el patrón correcto se acepta", () => {
    expect(isAnomalyEvidence(mutated((e) => { e.id = VALID_ID; }))).toBe(true);
  });

  it("rechaza un id que es un array de un elemento cuya conversión a texto cumple el patrón", () => {
    // Sin el typeof, RegExp.test convertiría el array con String() a exactamente un id válido y lo aceptaría.
    // Mata el mutante que sustituye la comprobación de tipo por false.
    expect(isAnomalyEvidence(mutated((e) => { e.id = [VALID_ID]; }))).toBe(false);
  });

  it("rechaza un id que es un objeto cuyo toString() devuelve un id válido", () => {
    // Mismo hueco por otra vía: la coerción a texto usa toString() del objeto y daría un id válido.
    expect(isAnomalyEvidence(mutated((e) => { e.id = { toString: () => VALID_ID }; }))).toBe(false);
  });
});

describe("JUP-038 isAnomalyEvidence: acepta cada criticidad coherente (mutante ['P1','P2','P3'] -> ['P1','','P3'])", () => {
  // Ninguna prueba previa usaba una evidencia válida con P2. La severidad debe coincidir entre el impacto y
  // el episodio (regla de coherencia) y los importes de 2 decimales deben coincidir entre episodio e impacto.
  it.each([
    ["P1", "> 2000.00", "2500.00"],
    ["P2", "500.00 to 2000.00", "1200.00"],
    ["P3", "< 500.00", "400.00"],
  ])("acepta la criticidad %s con su tramo %s", (severity, tramo, impacto) => {
    expect(isAnomalyEvidence(mutated((e) => {
      (e.episode as Mut).severity = severity;
      (e.episode as Mut).accumulated_impact = impacto;
      (e.impact as Mut).severity = severity;
      (e.impact as Mut).severity_band = tramo;
      (e.impact as Mut).accumulated_impact = impacto;
    }))).toBe(true);
  });

  it("sigue rechazando una criticidad de impacto fuera de P1, P2 y P3 aunque coincida con el episodio", () => {
    // Evita que el caso de aceptación se cumpla por un validador demasiado permisivo.
    expect(isAnomalyEvidence(mutated((e) => {
      (e.episode as Mut).severity = "P4"; (e.impact as Mut).severity = "P4";
    }))).toBe(false);
  });
});
