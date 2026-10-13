import { describe, expect, it } from "vitest";
import { isAnomalyEvidence } from "./contracts";
import { episode } from "../test/anomalyFixtures";

// JUP-038 tarea 5.1: validador de la evidencia guardada de una explicación de anomalía.
// La evidencia es la fotografía de un solo episodio que genera el backend (ejemplo A de la explicación:
// Compute, EUR, apertura 2026-09-08, referencia 400.00, observado 550.00, impacto 400.00 en 2 días, P3).
// El validador es la frontera de confianza del frontend: ante cualquier duda debe devolver false para
// que la interfaz no pinte cifras que no entiende.

const LIMITATIONS = [
  "Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.",
  "No se verifica que los datos de coste estén completos; un día puede evaluarse antes de que lleguen registros tardíos.",
];

// Evidencia válida base. Los operandos llevan 12 decimales, como los guarda la base de datos en la práctica.
function evidenceA(): Record<string, any> {
  return {
    schema_version: "1.0",
    adapter_version: "anomaly-explanation-1.0",
    id: `anomaly-explanation:${"a".repeat(64)}`,
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

// Devuelve una copia de la evidencia base tras aplicar una única mutación: cada caso de rechazo rompe
// una sola regla para que el motivo del rechazo sea inequívoco.
function mutated(change: (copy: Record<string, any>) => void): Record<string, any> {
  const copy = structuredClone(evidenceA());
  change(copy);
  return copy;
}

describe("JUP-038 isAnomalyEvidence: casos válidos", () => {
  it("acepta la evidencia completa del ejemplo A", () => {
    expect(isAnomalyEvidence(evidenceA())).toBe(true);
  });

  it("acepta la hora de la explicación con Z y con +00:00 (el mismo instante)", () => {
    // El backend escribe +00:00, pero la API de episodios usa Z: ambas formas son ISO 8601 válidas.
    expect(isAnomalyEvidence(mutated((e) => { e.explained_at = "2026-10-12T18:30:00Z"; }))).toBe(true);
    expect(isAnomalyEvidence(mutated((e) => { e.explained_at = "2026-10-12T18:30:00+00:00"; }))).toBe(true);
    expect(isAnomalyEvidence(mutated((e) => { e.explained_at = "2026-10-12T18:30:00.123456+00:00"; }))).toBe(true);
  });

  it("acepta las horas del episodio con Z (la API de episodios las escribe así)", () => {
    expect(isAnomalyEvidence(mutated((e) => {
      e.episode.created_at = "2026-09-10T03:00:00Z"; e.episode.updated_at = "2026-09-10T03:00:00Z";
    }))).toBe(true);
  });

  it.each([
    ["12 decimales", "2800.000000000000"],
    ["2 decimales", "2800.00"],
    ["1 decimal", "2800.5"],
    ["sin decimales", "2800"],
    ["negativo", "-12.50"],
  ])("acepta operandos exactos con %s: el número de decimales no se restringe", (_nombre, valor) => {
    // La base de datos conserva la escala de la columna; el validador no debe imponer 2 decimales aquí.
    expect(isAnomalyEvidence(mutated((e) => {
      e.operands = { reference_seven_day_total: valor, opening_observed_cost: valor, accumulated_impact_times_seven: valor };
    }))).toBe(true);
  });

  it("acepta un servicio nulo, otra criticidad coherente y un impacto de 0 días", () => {
    expect(isAnomalyEvidence(mutated((e) => {
      e.episode.service = null;
      e.episode.severity = "P1"; e.impact.severity = "P1"; e.impact.severity_band = "> 2000.00";
      e.episode.impact_day_count = 0; e.impact.day_count = 0;
    }))).toBe(true);
  });

  it("acepta las tres notas de redondeo conocidas y datos sintéticos", () => {
    expect(isAnomalyEvidence(mutated((e) => {
      e.rounding_notes = ["absolute_increase", "relative_increase", "accumulated_impact"];
      e.includes_synthetic_data = true;
    }))).toBe(true);
  });

  it("acepta importes enormes que Number no podría representar con exactitud", () => {
    // Se valida el texto, nunca se convierte a número: 9007199254740993.01 es mayor que MAX_SAFE_INTEGER.
    expect(isAnomalyEvidence(mutated((e) => {
      const big = "9007199254740993.01";
      e.episode.accumulated_impact = big; e.impact.accumulated_impact = big;
      e.episode.reference_daily_cost = big; e.opening.reference_daily_cost = big;
    }))).toBe(true);
  });
});

describe("JUP-038 isAnomalyEvidence: valores que no son un objeto de evidencia", () => {
  it.each([
    ["null", null],
    ["undefined", undefined],
    ["una cadena", "anomaly-explanation"],
    ["una lista vacía", []],
    ["una lista con la evidencia dentro", [evidenceA()]],
    ["un número", 42],
    ["un booleano", true],
    ["un objeto vacío", {}],
  ])("rechaza %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(valor)).toBe(false);
  });
});

describe("JUP-038 isAnomalyEvidence: versiones, identificador y estado", () => {
  it.each([
    ["schema_version distinta", (e: Record<string, any>) => { e.schema_version = "2.0"; }],
    ["schema_version numérica", (e: Record<string, any>) => { e.schema_version = 1; }],
    ["sin schema_version", (e: Record<string, any>) => { delete e.schema_version; }],
    ["adapter_version distinta", (e: Record<string, any>) => { e.adapter_version = "anomaly-explanation-2.0"; }],
    ["adapter_version de costes", (e: Record<string, any>) => { e.adapter_version = "ownership-1.0"; }],
    ["sin adapter_version", (e: Record<string, any>) => { delete e.adapter_version; }],
    ["id sin prefijo", (e: Record<string, any>) => { e.id = "a".repeat(64); }],
    ["id con prefijo de costes", (e: Record<string, any>) => { e.id = `cost:${"a".repeat(64)}`; }],
    ["id con 63 hex", (e: Record<string, any>) => { e.id = `anomaly-explanation:${"a".repeat(63)}`; }],
    ["id con 65 hex", (e: Record<string, any>) => { e.id = `anomaly-explanation:${"a".repeat(65)}`; }],
    ["id con hex en mayúscula", (e: Record<string, any>) => { e.id = `anomaly-explanation:${"A".repeat(64)}`; }],
    ["id con carácter no hex", (e: Record<string, any>) => { e.id = `anomaly-explanation:${"g".repeat(64)}`; }],
    ["id con salto de línea final", (e: Record<string, any>) => { e.id = `anomaly-explanation:${"a".repeat(64)}\n`; }],
    ["id con texto antes", (e: Record<string, any>) => { e.id = `x anomaly-explanation:${"a".repeat(64)}`; }],
    ["id numérico", (e: Record<string, any>) => { e.id = 7; }],
    ["sin id", (e: Record<string, any>) => { delete e.id; }],
    ["status partial", (e: Record<string, any>) => { e.status = "partial"; }],
    ["status no_data", (e: Record<string, any>) => { e.status = "no_data"; }],
    ["sin status", (e: Record<string, any>) => { delete e.status; }],
  ])("rechaza: %s", (_nombre, cambio) => {
    expect(isAnomalyEvidence(mutated(cambio))).toBe(false);
  });
});

describe("JUP-038 isAnomalyEvidence: fuente", () => {
  it.each([
    ["source ausente", (e: Record<string, any>) => { delete e.source; }],
    ["source nulo", (e: Record<string, any>) => { e.source = null; }],
    ["source como cadena de costes", (e: Record<string, any>) => { e.source = "azure_cost_records/completed"; }],
    ["kind distinto", (e: Record<string, any>) => { e.source.kind = "azure_cost_records"; }],
    ["sin kind", (e: Record<string, any>) => { delete e.source.kind; }],
    ["rules_version vacío", (e: Record<string, any>) => { e.source.rules_version = ""; }],
    ["rules_version solo espacios", (e: Record<string, any>) => { e.source.rules_version = "   "; }],
    ["rules_version numérico", (e: Record<string, any>) => { e.source.rules_version = 1; }],
    ["sin rules_version", (e: Record<string, any>) => { delete e.source.rules_version; }],
    ["data_as_of imposible", (e: Record<string, any>) => { e.source.data_as_of = "2026-02-30"; }],
    ["data_as_of con hora", (e: Record<string, any>) => { e.source.data_as_of = "2026-09-09T00:00:00Z"; }],
    ["data_as_of nulo", (e: Record<string, any>) => { e.source.data_as_of = null; }],
    ["sin data_as_of", (e: Record<string, any>) => { delete e.source.data_as_of; }],
  ])("rechaza: %s", (_nombre, cambio) => {
    expect(isAnomalyEvidence(mutated(cambio))).toBe(false);
  });
});

describe("JUP-038 isAnomalyEvidence: episodio", () => {
  it.each([
    ["episodio ausente", (e: Record<string, any>) => { delete e.episode; }],
    ["episodio nulo", (e: Record<string, any>) => { e.episode = null; }],
    ["episodio como lista", (e: Record<string, any>) => { e.episode = []; }],
    ["criticidad desconocida (P4)", (e: Record<string, any>) => { e.episode.severity = "P4"; }],
    ["estado desconocido", (e: Record<string, any>) => { e.episode.status = "acknowledged"; }],
    ["importe del episodio sin dos decimales", (e: Record<string, any>) => { e.episode.reference_daily_cost = "400.0"; }],
    ["fecha de inicio imposible", (e: Record<string, any>) => { e.episode.start_date = "2026-02-30"; }],
    ["moneda vacía", (e: Record<string, any>) => { e.episode.currency = ""; }],
    ["causa del episodio establecida", (e: Record<string, any>) => { e.episode.cause_status = "established"; }],
  ])("rechaza, vía isAnomalyEpisode: %s", (_nombre, cambio) => {
    expect(isAnomalyEvidence(mutated(cambio))).toBe(false);
  });
});

describe("JUP-038 isAnomalyEvidence: operandos exactos", () => {
  const claves = ["reference_seven_day_total", "opening_observed_cost", "accumulated_impact_times_seven"];

  it("rechaza que falte el bloque operands o que no sea un objeto", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.operands; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.operands = null; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.operands = ["2800.00", "550.00", "2800.00"]; }))).toBe(false);
  });

  it.each(claves)("rechaza que falte el operando %s", (clave) => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.operands[clave]; }))).toBe(false);
  });

  // Cada valor malformado se prueba en cada una de las tres claves para que ninguna quede sin validar.
  const malos: [string, unknown][] = [
    ["un número en lugar de cadena", 2800],
    ["nulo", null],
    ["notación científica", "2.8e3"],
    ["notación científica sin decimales", "1e3"],
    ["coma decimal", "2800,00"],
    ["cadena vacía", ""],
    ["punto final sin decimales", "2800."],
    ["sin parte entera", ".5"],
    ["espacios alrededor", " 2800.00 "],
    ["signo más", "+2800.00"],
    ["texto no numérico", "NaN"],
    ["salto de línea final", "2800.00\n"],
  ];
  for (const clave of claves) {
    it.each(malos)(`rechaza ${clave} con %s`, (_nombre, valor) => {
      expect(isAnomalyEvidence(mutated((e) => { e.operands[clave] = valor; }))).toBe(false);
    });
  }
});

describe("JUP-038 isAnomalyEvidence: apertura", () => {
  const importes = ["absolute_increase", "relative_increase_percent"];
  const importesMalos: [string, unknown][] = [
    ["un solo decimal", "150.0"],
    ["tres decimales", "150.000"],
    ["sin decimales", "150"],
    ["coma decimal", "150,00"],
    ["notación científica", "1.5e2"],
    ["un número en lugar de cadena", 150],
    ["nulo", null],
    ["cero negativo", "-0.00"],
  ];

  it("rechaza que falte el bloque opening o que no sea un objeto", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.opening; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.opening = null; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.opening = []; }))).toBe(false);
  });

  for (const clave of importes) {
    it.each(importesMalos)(`rechaza ${clave} con %s`, (_nombre, valor) => {
      expect(isAnomalyEvidence(mutated((e) => { e.opening[clave] = valor; }))).toBe(false);
    });
    it(`rechaza que falte ${clave}`, () => {
      expect(isAnomalyEvidence(mutated((e) => { delete e.opening[clave]; }))).toBe(false);
    });
  }

  // reference_daily_cost y observed_cost también deben ser importes de 2 decimales; además deben coincidir
  // con el episodio (coherencia, más abajo), así que aquí solo se prueba el rechazo de la forma.
  it.each(["reference_daily_cost", "observed_cost"])("rechaza %s con un solo decimal o numérico", (clave) => {
    expect(isAnomalyEvidence(mutated((e) => { e.opening[clave] = "400.0"; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.opening[clave] = 400; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { delete e.opening[clave]; }))).toBe(false);
  });

  it.each(["absolute_threshold", "relative_threshold_percent"])("rechaza %s mal formado", (clave) => {
    for (const malo of ["1e2", "2e1", "", "100,00", "20 %", 20, null, " 20", "20."]) {
      expect(isAnomalyEvidence(mutated((e) => { e.opening[clave] = malo; })), `valor ${String(malo)}`).toBe(false);
    }
    expect(isAnomalyEvidence(mutated((e) => { delete e.opening[clave]; }))).toBe(false);
  });

  it.each(["absolute_threshold", "relative_threshold_percent"])("acepta %s con cualquier número de decimales", (clave) => {
    // Los umbrales salen tal cual de las reglas del episodio: "20" o "100.00" son igual de válidos.
    for (const bueno of ["20", "100.00", "0.5", "12.123456"]) {
      expect(isAnomalyEvidence(mutated((e) => { e.opening[clave] = bueno; })), `valor ${bueno}`).toBe(true);
    }
  });

  it.each([
    ["conditions_met falso", false],
    ["conditions_met como cadena", "true"],
    ["conditions_met como 1", 1],
    ["conditions_met nulo", null],
  ])("rechaza %s: solo se guarda evidencia de aperturas que cumplieron la regla", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.opening.conditions_met = valor; }))).toBe(false);
  });

  it("rechaza que falte conditions_met", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.opening.conditions_met; }))).toBe(false);
  });
});

describe("JUP-038 isAnomalyEvidence: impacto", () => {
  it("rechaza que falte el bloque impact o que no sea un objeto", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.impact; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.impact = null; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.impact = "400.00"; }))).toBe(false);
  });

  it.each([
    ["un decimal", "400.0"],
    ["tres decimales", "400.000"],
    ["notación científica", "4e2"],
    ["número", 400],
    ["nulo", null],
  ])("rechaza accumulated_impact con %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.impact.accumulated_impact = valor; }))).toBe(false);
  });

  it("rechaza que falte accumulated_impact", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.impact.accumulated_impact; }))).toBe(false);
  });

  it.each([
    ["negativo", -1],
    ["decimal", 1.5],
    ["cadena", "2"],
    ["NaN", Number.NaN],
    ["infinito", Number.POSITIVE_INFINITY],
    ["nulo", null],
    ["no seguro", 9007199254740993],
  ])("rechaza day_count %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.impact.day_count = valor; }))).toBe(false);
  });

  it("rechaza que falte day_count", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.impact.day_count; }))).toBe(false);
  });

  it.each([
    ["imposible", "2026-02-30"],
    ["con hora", "2026-09-09T00:00:00Z"],
    ["formato europeo", "09/09/2026"],
    ["nula", null],
  ])("rechaza through_date %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.impact.through_date = valor; }))).toBe(false);
  });

  it("rechaza que falte through_date", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.impact.through_date; }))).toBe(false);
  });

  it.each([
    ["P4", "P4"],
    ["minúscula", "p3"],
    ["Alta", "Alta (P1)"],
    ["nula", null],
  ])("rechaza severity %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.impact.severity = valor; }))).toBe(false);
  });

  it.each([
    ["vacío", ""],
    ["solo espacios", "  "],
    ["número", 500],
    ["nulo", null],
  ])("rechaza severity_band %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.impact.severity_band = valor; }))).toBe(false);
  });

  it("rechaza que falte severity o severity_band", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.impact.severity; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { delete e.impact.severity_band; }))).toBe(false);
  });
});

describe("JUP-038 isAnomalyEvidence: coherencia interna con el episodio", () => {
  // La evidencia es la fotografía de un solo episodio: si el bloque de apertura o de impacto no coincide
  // con el episodio embebido, la evidencia mezcla datos de dos momentos y no se debe mostrar.
  it("rechaza una criticidad del impacto distinta de la del episodio", () => {
    expect(isAnomalyEvidence(mutated((e) => { e.impact.severity = "P1"; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.episode.severity = "P2"; }))).toBe(false);
  });

  it("rechaza un impacto acumulado distinto del del episodio", () => {
    expect(isAnomalyEvidence(mutated((e) => { e.impact.accumulated_impact = "401.00"; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.episode.accumulated_impact = "399.99"; }))).toBe(false);
  });

  it("rechaza una referencia diaria de la apertura distinta de la del episodio", () => {
    expect(isAnomalyEvidence(mutated((e) => { e.opening.reference_daily_cost = "399.00"; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.episode.reference_daily_cost = "401.00"; }))).toBe(false);
  });

  it("rechaza un observado de la apertura distinto del observado de apertura del episodio", () => {
    expect(isAnomalyEvidence(mutated((e) => { e.opening.observed_cost = "551.00"; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.episode.opening_observed_cost = "549.99"; }))).toBe(false);
  });

  it("la coherencia compara importes exactos: una diferencia de un céntimo basta", () => {
    expect(isAnomalyEvidence(mutated((e) => { e.impact.accumulated_impact = "400.01"; }))).toBe(false);
    expect(isAnomalyEvidence(mutated((e) => { e.opening.observed_cost = "550.01"; }))).toBe(false);
  });
});

describe("JUP-038 isAnomalyEvidence: notas, sintéticos, causa, supuestos y limitaciones", () => {
  it.each([
    ["no es una lista", "absolute_increase"],
    ["nulo", null],
    ["objeto", {}],
    ["nota desconocida", ["otra_nota"]],
    ["una conocida y una desconocida", ["absolute_increase", "otra_nota"]],
    ["elemento numérico", ["absolute_increase", 1]],
    ["elemento nulo", [null]],
    ["nombre con mayúsculas", ["Absolute_Increase"]],
    ["cadena vacía", [""]],
  ])("rechaza rounding_notes: %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.rounding_notes = valor; }))).toBe(false);
  });

  it("rechaza que falte rounding_notes", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.rounding_notes; }))).toBe(false);
  });

  it.each([
    ["cadena", "false"],
    ["número", 0],
    ["nulo", null],
  ])("rechaza includes_synthetic_data %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.includes_synthetic_data = valor; }))).toBe(false);
  });

  it("rechaza que falte includes_synthetic_data", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.includes_synthetic_data; }))).toBe(false);
  });

  it.each([
    ["causa establecida", "established"],
    ["vacío", ""],
    ["nulo", null],
  ])("rechaza cause_status con %s: la causa nunca está establecida", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.cause_status = valor; }))).toBe(false);
  });

  it("rechaza que falte cause_status", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.cause_status; }))).toBe(false);
  });

  it.each([
    ["cadena", "supuesto"],
    ["nulo", null],
    ["objeto", {}],
  ])("rechaza assumptions que no es una lista (%s)", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.assumptions = valor; }))).toBe(false);
  });

  it("rechaza que falte assumptions", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.assumptions; }))).toBe(false);
  });

  it.each([
    ["una cadena", "Limitación"],
    ["nulo", null],
    ["objeto", {}],
    ["elemento numérico", ["ok", 1]],
    ["elemento nulo", [null]],
  ])("rechaza limitations: %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.limitations = valor; }))).toBe(false);
  });

  it("rechaza que falte limitations", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.limitations; }))).toBe(false);
  });

  it("acepta una lista de limitaciones vacía", () => {
    expect(isAnomalyEvidence(mutated((e) => { e.limitations = []; }))).toBe(true);
  });
});

describe("JUP-038 isAnomalyEvidence: explained_at", () => {
  it.each([
    ["solo fecha", "2026-10-12"],
    ["sin zona horaria", "2026-10-12T18:30:00"],
    ["texto", "ayer"],
    ["mes imposible", "2026-13-01T00:00:00Z"],
    ["día imposible", "2026-02-30T00:00:00Z"],
    ["nulo", null],
    ["número (epoch)", 1760293800],
    ["cadena vacía", ""],
  ])("rechaza %s", (_nombre, valor) => {
    expect(isAnomalyEvidence(mutated((e) => { e.explained_at = valor; }))).toBe(false);
  });

  it("rechaza que falte explained_at", () => {
    expect(isAnomalyEvidence(mutated((e) => { delete e.explained_at; }))).toBe(false);
  });
});
