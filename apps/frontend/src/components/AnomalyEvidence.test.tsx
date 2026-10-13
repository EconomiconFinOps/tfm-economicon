import { fireEvent, render, screen, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import { episode } from "../test/anomalyFixtures";

// JUP-038 tarea 5.1: bloque desplegable con la evidencia guardada de una explicación de anomalía.
// Patrón de CostEvidence: si el contrato no se entiende no se muestra ninguna cifra, y lo que se muestra
// son exactamente las cadenas de la evidencia (el componente no suma, resta, redondea ni convierte).
// El componente se importa dentro de cada prueba para que, mientras no exista, falle cada prueba por
// separado y no con un único error de carga del archivo (ver renderEvidence).

const NO_DISPONIBLE = "La evidencia de esta explicación no está disponible.";
const NOTA_REDONDEO = "Algunas cifras se muestran redondeadas a dos decimales; los valores exactos cumplen la regla y están en los operandos.";
const AVISO_SINTETICO = "Los datos de este cliente incluyen datos sintéticos de demostración.";
const LIMITACIONES = [
  "Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.",
  "No se verifica que los datos de coste estén completos; un día puede evaluarse antes de que lleguen registros tardíos.",
  "Los ciclos semanales pueden dar candidatas falsas y un pico reciente sube la media de 7 días.",
];

// Ejemplo A del backend: Compute, EUR, apertura 2026-09-08, referencia 400.00, observado 550.00,
// subida 150.00 (37.50 %), impacto 400.00 en 2 días hasta 2026-09-09, P3, estado "new".
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
      rules_version: "jup019-daily-v1", limitations: LIMITACIONES,
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
    limitations: LIMITACIONES,
    explained_at: "2026-10-12T18:30:00+00:00",
  };
}

function mutated(change: (copy: Record<string, any>) => void): Record<string, any> {
  const copy = structuredClone(evidenceA());
  change(copy);
  return copy;
}

const SUMMARY_A = "Evidencia de la anomalía — Baja (P3)";

// Renderiza el componente real (importación diferida) y, si se pide, abre el bloque principal.
async function renderEvidence(evidence: unknown, open = true) {
  // La ruta va en una variable (con @vite-ignore) para que Vite no la resuelva al transformar el archivo:
  // así, mientras el módulo no exista, falla cada prueba por separado y no la carga de todo el archivo.
  const ruta = "./AnomalyEvidence";
  const { AnomalyEvidence } = await import(/* @vite-ignore */ ruta);
  const view = render((<AnomalyEvidence evidence={evidence} />) as ReactElement);
  if (open) fireEvent.click(screen.getByText(/^Evidencia de la anomalía — /));
  return view;
}

describe("JUP-038 AnomalyEvidence: evidencia válida", () => {
  it("muestra un details cuyo summary es exactamente 'Evidencia de la anomalía — Baja (P3)' y empieza cerrado", async () => {
    const { container } = await renderEvidence(evidenceA(), false);
    const summary = screen.getByText(SUMMARY_A);
    expect(summary.tagName).toBe("SUMMARY");
    const details = summary.closest("details")!;
    expect(details).not.toHaveAttribute("open");
    expect(container.querySelector("details")).toBe(details);
    // Cerrado, el contenido no es visible; al abrirlo con un clic sí lo es.
    expect(screen.getByText(`Identificador: anomaly-explanation:${"a".repeat(64)}`)).not.toBeVisible();
    fireEvent.click(summary);
    expect(screen.getByText(`Identificador: anomaly-explanation:${"a".repeat(64)}`)).toBeVisible();
  });

  it.each([
    ["P1", "Alta (P1)", "> 2000.00"],
    ["P2", "Media (P2)", "500.00 to 2000.00"],
    ["P3", "Baja (P3)", "< 500.00"],
  ])("usa la palabra del panel para la criticidad %s en el resumen y en la línea de criticidad", async (severity, etiqueta, tramo) => {
    // La criticidad se escribe con las mismas palabras que el panel /anomalies (severityLabels).
    await renderEvidence(mutated((e) => {
      e.episode.severity = severity; e.impact.severity = severity; e.impact.severity_band = tramo;
    }), false);
    fireEvent.click(screen.getByText(`Evidencia de la anomalía — ${etiqueta}`));
    expect(screen.getByText(`Criticidad: ${etiqueta} (tramo ${tramo}).`)).toBeVisible();
  });

  it.each([
    ["new", "Nueva"],
    ["investigating", "Investigando"],
    ["resolved", "Resuelta"],
    ["false_positive", "Falso positivo"],
  ])("escribe el estado %s con la palabra del panel", async (status, etiqueta) => {
    await renderEvidence(mutated((e) => { e.episode.status = status; }));
    expect(screen.getByText(`Estado: ${etiqueta}`)).toBeVisible();
  });

  it("muestra cada línea con su texto exacto para el ejemplo A", async () => {
    await renderEvidence(evidenceA());
    const textos = [
      `Identificador: anomaly-explanation:${"a".repeat(64)}`,
      "Fotografía tomada el 2026-10-12T18:30:00+00:00 (UTC).",
      "Servicio: Compute · Moneda: EUR",
      "Estado: Nueva",
      "Regla jup019-daily-v1: más de 100.00 EUR y más de un 20 % sobre la referencia, las dos a la vez.",
      "Día de apertura 2026-09-08: observado 550.00 EUR, referencia diaria 400.00 EUR. Subida 150.00 EUR (37.50 %).",
      "Impacto acumulado: 400.00 EUR en 2 días, hasta 2026-09-09.",
      "Criticidad: Baja (P3) (tramo < 500.00).",
      "Candidata: causa no establecida.",
    ];
    for (const texto of textos) expect(screen.getByText(texto), texto).toBeVisible();
  });

  it("muestra la hora de la fotografía tal como llega, también con Z", async () => {
    // El componente no reformatea fechas: lo que se guardó es lo que se muestra.
    await renderEvidence(mutated((e) => { e.explained_at = "2026-10-12T18:30:00Z"; }));
    expect(screen.getByText("Fotografía tomada el 2026-10-12T18:30:00Z (UTC).")).toBeVisible();
  });

  it("escribe '1 día' en singular y '0 días' y '2 días' en plural", async () => {
    // Edge case de concordancia: solo el 1 es singular; el 0 se escribe en plural.
    const { unmount } = await renderEvidence(mutated((e) => { e.impact.day_count = 1; e.episode.impact_day_count = 1; }));
    expect(screen.getByText("Impacto acumulado: 400.00 EUR en 1 día, hasta 2026-09-09.")).toBeVisible();
    unmount();
    const cero = await renderEvidence(mutated((e) => { e.impact.day_count = 0; e.episode.impact_day_count = 0; }));
    expect(screen.getByText("Impacto acumulado: 400.00 EUR en 0 días, hasta 2026-09-09.")).toBeVisible();
    cero.unmount();
    await renderEvidence(mutated((e) => { e.impact.day_count = 12; e.episode.impact_day_count = 12; }));
    expect(screen.getByText("Impacto acumulado: 400.00 EUR en 12 días, hasta 2026-09-09.")).toBeVisible();
  });

  it("dice 'sin servicio informado' cuando el servicio es nulo", async () => {
    await renderEvidence(mutated((e) => { e.episode.service = null; }));
    expect(screen.getByText("Servicio: sin servicio informado · Moneda: EUR")).toBeVisible();
    expect(screen.queryByText(/null/)).not.toBeInTheDocument();
  });

  it("pinta el servicio como texto: el HTML del nombre no crea ningún elemento", async () => {
    // El nombre del servicio viene de datos del cliente y no es de confianza (riesgo de XSS).
    const hostil = "<img src=x onerror=alert(1)>";
    const { container } = await renderEvidence(mutated((e) => { e.episode.service = hostil; }));
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText(`Servicio: ${hostil} · Moneda: EUR`)).toBeVisible();
  });

  it("usa la moneda del episodio (USD) en todas las líneas con importe y no menciona EUR", async () => {
    // Sin conversión: la moneda es la del episodio. Las limitaciones se sustituyen para que no citen EUR.
    const { container } = await renderEvidence(mutated((e) => {
      e.episode.currency = "USD"; e.episode.limitations = ["Limitación de prueba."]; e.limitations = ["Limitación de prueba."];
    }));
    expect(screen.getByText("Servicio: Compute · Moneda: USD")).toBeVisible();
    expect(screen.getByText("Regla jup019-daily-v1: más de 100.00 USD y más de un 20 % sobre la referencia, las dos a la vez.")).toBeVisible();
    expect(screen.getByText("Día de apertura 2026-09-08: observado 550.00 USD, referencia diaria 400.00 USD. Subida 150.00 USD (37.50 %).")).toBeVisible();
    expect(screen.getByText("Impacto acumulado: 400.00 USD en 2 días, hasta 2026-09-09.")).toBeVisible();
    expect(container.textContent).not.toContain("EUR");
  });

  it("muestra la regla con la versión y los umbrales que trae la evidencia", async () => {
    await renderEvidence(mutated((e) => {
      e.source.rules_version = "jup019-daily-v2"; e.episode.rules_version = "jup019-daily-v2";
      e.opening.absolute_threshold = "250.50"; e.opening.relative_threshold_percent = "35";
    }));
    expect(screen.getByText("Regla jup019-daily-v2: más de 250.50 EUR y más de un 35 % sobre la referencia, las dos a la vez.")).toBeVisible();
  });

  it("incluye la nota de redondeo cuando rounding_notes no está vacío y no la repite", async () => {
    await renderEvidence(mutated((e) => { e.rounding_notes = ["absolute_increase", "relative_increase"]; }));
    expect(screen.getAllByText(NOTA_REDONDEO)).toHaveLength(1);
    expect(screen.getByText(NOTA_REDONDEO)).toBeVisible();
  });

  it("no incluye la nota de redondeo cuando rounding_notes está vacío", async () => {
    await renderEvidence(evidenceA());
    expect(screen.queryByText(NOTA_REDONDEO)).not.toBeInTheDocument();
    expect(screen.queryByText(/redondead/)).not.toBeInTheDocument();
  });

  it("muestra el aviso de datos sintéticos solo cuando includes_synthetic_data es true", async () => {
    const con = await renderEvidence(mutated((e) => { e.includes_synthetic_data = true; }));
    expect(screen.getByText(AVISO_SINTETICO)).toBeVisible();
    con.unmount();
    await renderEvidence(evidenceA());
    expect(screen.queryByText(AVISO_SINTETICO)).not.toBeInTheDocument();
    expect(screen.queryByText(/sintétic/)).not.toBeInTheDocument();
  });

  it("lista cada limitación en una lista con nombre accesible 'Limitaciones'", async () => {
    await renderEvidence(evidenceA());
    const lista = screen.getByRole("list", { name: "Limitaciones" });
    expect(lista.tagName).toBe("UL");
    const items = within(lista).getAllByRole("listitem");
    expect(items.map((item) => item.textContent)).toEqual(LIMITACIONES);
  });

  it("toma las limitaciones de la evidencia y no las del episodio embebido", async () => {
    // Cada fuente tiene su texto; el bloque debe leer evidence.limitations.
    await renderEvidence(mutated((e) => {
      e.episode.limitations = ["Texto del episodio."]; e.limitations = ["Texto de la evidencia."];
    }));
    const lista = screen.getByRole("list", { name: "Limitaciones" });
    expect(within(lista).getAllByRole("listitem").map((item) => item.textContent)).toEqual(["Texto de la evidencia."]);
    expect(screen.queryByText("Texto del episodio.")).not.toBeInTheDocument();
  });

  it("pinta las limitaciones como texto, sin interpretar HTML", async () => {
    const { container } = await renderEvidence(mutated((e) => { e.limitations = ["<b>negrita</b> <img src=x onerror=alert(1)>"]; }));
    expect(container.querySelector("b")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText("<b>negrita</b> <img src=x onerror=alert(1)>")).toBeVisible();
  });
});

describe("JUP-038 AnomalyEvidence: operandos exactos", () => {
  it("anida un details 'Operandos exactos' dentro del bloque principal", async () => {
    await renderEvidence(evidenceA());
    const resumen = screen.getByText("Operandos exactos");
    expect(resumen.tagName).toBe("SUMMARY");
    const anidado = resumen.closest("details")!;
    const principal = screen.getByText(SUMMARY_A).closest("details")!;
    expect(anidado).not.toBe(principal);
    expect(principal.contains(anidado)).toBe(true);
  });

  it("muestra las tres líneas de operandos tal como llegan, con 12 decimales y sin recalcular", async () => {
    await renderEvidence(evidenceA());
    fireEvent.click(screen.getByText("Operandos exactos"));
    const anidado = screen.getByText("Operandos exactos").closest("details")!;
    for (const linea of [
      "Referencia de 7 días: 2800.000000000000",
      "Observado el día de apertura: 550.000000000000",
      "Impacto acumulado × 7: 2800.000000000000",
    ]) {
      const elemento = screen.getByText(linea);
      expect(anidado.contains(elemento), linea).toBe(true);
      expect(elemento).toBeVisible();
    }
  });

  it("muestra operandos con otra escala y valores distintos entre sí sin normalizarlos", async () => {
    // Los operandos son independientes de las cifras redondeadas: aquí difieren a propósito para detectar
    // que el componente los derive de otros campos en lugar de leerlos.
    await renderEvidence(mutated((e) => {
      e.operands = {
        reference_seven_day_total: "2800.5", opening_observed_cost: "550.004", accumulated_impact_times_seven: "2800",
      };
    }));
    fireEvent.click(screen.getByText("Operandos exactos"));
    expect(screen.getByText("Referencia de 7 días: 2800.5")).toBeVisible();
    expect(screen.getByText("Observado el día de apertura: 550.004")).toBeVisible();
    expect(screen.getByText("Impacto acumulado × 7: 2800")).toBeVisible();
  });
});

describe("JUP-038 AnomalyEvidence: sin aritmética propia", () => {
  it("muestra cifras 'raras' idénticas a las de la evidencia aunque no cuadren entre sí", async () => {
    // La evidencia es coherente para el validador (formato y coincidencia con el episodio) pero la
    // aritmética no cuadra a propósito (subida 7.77 con observado - referencia = 2.02): si el componente
    // restara, sumara, redondeara o convirtiera a Number, estas cifras saldrían distintas.
    const grande = "9007199254740993.01";
    const observado = "9007199254740995.03";
    await renderEvidence(mutated((e) => {
      e.episode.reference_daily_cost = grande; e.opening.reference_daily_cost = grande;
      e.episode.opening_observed_cost = observado; e.opening.observed_cost = observado;
      e.opening.absolute_increase = "7.77"; e.opening.relative_increase_percent = "999.99";
      e.episode.accumulated_impact = grande; e.impact.accumulated_impact = grande;
      e.operands = {
        reference_seven_day_total: "63050394783186951.070000000001",
        opening_observed_cost: "9007199254740995.030000000001",
        accumulated_impact_times_seven: "1.000000000000",
      };
    }));
    expect(screen.getByText(`Día de apertura 2026-09-08: observado ${observado} EUR, referencia diaria ${grande} EUR. Subida 7.77 EUR (999.99 %).`)).toBeVisible();
    expect(screen.getByText(`Impacto acumulado: ${grande} EUR en 2 días, hasta 2026-09-09.`)).toBeVisible();
    fireEvent.click(screen.getByText("Operandos exactos"));
    expect(screen.getByText("Referencia de 7 días: 63050394783186951.070000000001")).toBeVisible();
    expect(screen.getByText("Observado el día de apertura: 9007199254740995.030000000001")).toBeVisible();
    expect(screen.getByText("Impacto acumulado × 7: 1.000000000000")).toBeVisible();
  });

  it("no recalcula los días: usa day_count de la evidencia aunque el rango de fechas diga otra cosa", async () => {
    // Del 2026-09-08 al 2026-09-09 hay 2 días; la evidencia dice 5 y debe mostrarse 5, no un valor derivado.
    await renderEvidence(mutated((e) => { e.impact.day_count = 5; e.episode.impact_day_count = 5; }));
    expect(screen.getByText("Impacto acumulado: 400.00 EUR en 5 días, hasta 2026-09-09.")).toBeVisible();
  });

  it("no recalcula la subida a partir del observado y la referencia", async () => {
    await renderEvidence(mutated((e) => { e.opening.absolute_increase = "149.99"; e.opening.relative_increase_percent = "37.49"; }));
    expect(screen.getByText("Día de apertura 2026-09-08: observado 550.00 EUR, referencia diaria 400.00 EUR. Subida 149.99 EUR (37.49 %).")).toBeVisible();
  });
});

describe("JUP-038 AnomalyEvidence: evidencia no válida", () => {
  // Cada forma inválida debe dar un único <p> con el texto exacto y ninguna cifra ni bloque desplegable.
  const invalidas: [string, () => unknown][] = [
    ["null", () => null],
    ["undefined", () => undefined],
    ["una cadena", () => "anomaly-explanation"],
    ["una lista", () => [evidenceA()]],
    ["un número", () => 42],
    ["un objeto vacío", () => ({})],
    ["schema_version futura", () => mutated((e) => { e.schema_version = "2.0"; })],
    ["adapter_version distinta", () => mutated((e) => { e.adapter_version = "otro-1.0"; })],
    ["id con otro formato", () => mutated((e) => { e.id = "anomaly-explanation:xyz"; })],
    ["estado partial", () => mutated((e) => { e.status = "partial"; })],
    ["conditions_met falso", () => mutated((e) => { e.opening.conditions_met = false; })],
    ["operando con notación científica", () => mutated((e) => { e.operands.reference_seven_day_total = "2.8e3"; })],
    ["nota de redondeo desconocida", () => mutated((e) => { e.rounding_notes = ["otra"]; })],
    ["criticidad del impacto incoherente con el episodio", () => mutated((e) => { e.impact.severity = "P1"; })],
    ["importe de apertura incoherente con el episodio", () => mutated((e) => { e.opening.observed_cost = "551.00"; })],
    ["fecha imposible", () => mutated((e) => { e.impact.through_date = "2026-02-30"; })],
    ["causa establecida", () => mutated((e) => { e.cause_status = "established"; })],
  ];

  it.each(invalidas)("dice que no está disponible y no muestra ninguna cifra: %s", async (_nombre, crear) => {
    const { container } = await renderEvidence(crear(), false);
    const mensaje = screen.getByText(NO_DISPONIBLE);
    expect(mensaje.tagName).toBe("P");
    expect(container.querySelectorAll("p")).toHaveLength(1);
    expect(container.querySelector("details")).toBeNull();
    // Todo el contenido es el mensaje: ni identificador, ni importes, ni servicio, ni limitaciones.
    expect(container.textContent).toBe(NO_DISPONIBLE);
    for (const cifra of ["550.00", "400.00", "150.00", "37.50", "Compute", "2800", "P3", "Baja"]) {
      expect(container.textContent).not.toContain(cifra);
    }
  });
});
