import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { episode } from "../test/anomalyFixtures";
import { AnswerEvidence } from "./AnswerEvidence";

// JUP-038 tarea 5.2: rama nueva de AnswerEvidence para metadata.anomaly_evidence.
// Orden de prioridad esperado: citas documentales válidas, luego cost_evidence, luego anomaly_evidence y,
// al final, el texto «Sin fuentes documentales utilizadas.».

const NO_DISPONIBLE = "La evidencia de esta explicación no está disponible.";
const SIN_FUENTES = "Sin fuentes documentales utilizadas.";
const SUMMARY = "Evidencia de la anomalía — Baja (P3)";
const LIMITACION = "Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.";

// Texto determinista de la explicación: incluye líneas de viñeta «- ...» que NO son citas.
const CONTENIDO = [
  "Servicio: Compute (EUR).",
  "Impacto acumulado: 400.00 EUR en 2 días, hasta el 2026-09-09.",
  `- ${LIMITACION}`,
  "- No se verifica que los datos de coste estén completos.",
].join("\n");

// Evidencia JSON que las pruebas mutan a mano: cada nivel anidado es otro objeto laxo. Se tipa asi y no con
// `any` (lint) para conservar la comprobacion de tipos; las mutaciones anidadas usan un cast puntual a `Mut`.
type Mut = { [key: string]: unknown };

function evidenceA(): Mut {
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
      rules_version: "jup019-daily-v1", limitations: [LIMITACION],
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
    limitations: [LIMITACION],
    explained_at: "2026-10-12T18:30:00+00:00",
  };
}

const citation = {
  evidence_id: "chunk-1", kind: "corpus", document_id: "doc-1", title: "Guía Azure",
  source: "FinOps", reference: "document:doc-1/chunk:0", section: "Costes", page: 4, excerpt: "Texto original",
};

describe("JUP-038 AnswerEvidence: rama de evidencia de anomalía", () => {
  it("muestra el bloque de evidencia de la anomalía y no el aviso de 'sin fuentes documentales'", () => {
    // La explicación de una anomalía no usa documentos: su evidencia es propia, así que advertir de que
    // no hay fuentes documentales sería engañoso.
    render(<AnswerEvidence content={CONTENIDO} metadata={{ citations: [], anomaly_evidence: evidenceA() }} />);
    expect(screen.getByText(SUMMARY).tagName).toBe("SUMMARY");
    expect(screen.queryByText(SIN_FUENTES)).not.toBeInTheDocument();
    expect(screen.queryByText(NO_DISPONIBLE)).not.toBeInTheDocument();
  });

  it("el bloque trae las cifras guardadas al abrirlo", () => {
    render(<AnswerEvidence content={CONTENIDO} metadata={{ citations: [], anomaly_evidence: evidenceA() }} />);
    fireEvent.click(screen.getByText(SUMMARY));
    expect(screen.getByText("Servicio: Compute · Moneda: EUR")).toBeVisible();
    expect(screen.getByText("Impacto acumulado: 400.00 EUR en 2 días, hasta 2026-09-09.")).toBeVisible();
  });

  it("las viñetas del texto de la explicación no se convierten en enlaces de fuente", () => {
    // Solo las líneas '- [N] ' pueden ser citas; las viñetas '- Es un candidato…' se quedan como texto.
    render(<AnswerEvidence content={CONTENIDO} metadata={{ citations: [], anomaly_evidence: evidenceA() }} />);
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText(`- ${LIMITACION}`)).toBeInTheDocument();
    expect(screen.getByText("- No se verifica que los datos de coste estén completos.")).toBeInTheDocument();
    expect(screen.getByText("Servicio: Compute (EUR).")).toBeInTheDocument();
  });

  it("también se muestra cuando 'citations' trae referencias que no se pueden respaldar con fuentes válidas", () => {
    // La rama de anomalía va antes del aviso 'La evidencia de esta respuesta no está disponible.' de las
    // citas rotas: la explicación de anomalías no depende de citas documentales.
    render(<AnswerEvidence content={CONTENIDO} metadata={{ citations: ["missing"], anomaly_evidence: evidenceA() }} />);
    expect(screen.getByText(SUMMARY)).toBeInTheDocument();
    expect(screen.queryByText("La evidencia de esta respuesta no está disponible.")).not.toBeInTheDocument();
    expect(screen.queryByText(SIN_FUENTES)).not.toBeInTheDocument();
  });

  it.each([
    ["schema_version futura", () => ({ ...evidenceA(), schema_version: "2.0" })],
    ["id con otro formato", () => ({ ...evidenceA(), id: "anomaly-explanation:xyz" })],
    ["conditions_met falso", () => { const e = evidenceA(); (e.opening as Mut).conditions_met = false; return e; }],
    ["incoherente con el episodio", () => { const e = evidenceA(); (e.impact as Mut).severity = "P1"; return e; }],
    ["null", () => null],
    ["una cadena", () => "anomaly-explanation"],
    ["una lista", () => []],
  ])("con una evidencia no válida (%s) avisa y no muestra ninguna cifra", (_nombre, crear) => {
    const { container } = render(<AnswerEvidence content="Texto de la respuesta." metadata={{ citations: [], anomaly_evidence: crear() }} />);
    expect(screen.getByText(NO_DISPONIBLE)).toBeInTheDocument();
    expect(screen.queryByText(SIN_FUENTES)).not.toBeInTheDocument();
    expect(container.querySelector("details")).toBeNull();
    for (const cifra of ["550.00", "400.00", "150.00", "37.50", "Compute", "2800"]) {
      expect(container.textContent).not.toContain(cifra);
    }
  });

  it("una clave anomaly_evidence presente pero con valor undefined se trata como evidencia no disponible", () => {
    // La rama se decide por la presencia de la clave ('in'), no por que el valor sea verdadero.
    render(<AnswerEvidence content="Texto." metadata={{ citations: [], anomaly_evidence: undefined }} />);
    expect(screen.getByText(NO_DISPONIBLE)).toBeInTheDocument();
    expect(screen.queryByText(SIN_FUENTES)).not.toBeInTheDocument();
  });

  it("las citas documentales válidas siguen teniendo prioridad sobre la evidencia de anomalía", () => {
    // Comportamiento existente que la rama nueva no debe cambiar.
    render(<AnswerEvidence content={"- [1] FinOps: Texto original"}
      metadata={{ citations: ["chunk-1"], source_citations: [citation], anomaly_evidence: evidenceA() }} />);
    expect(screen.getByRole("region", { name: "Fuentes utilizadas" })).toBeInTheDocument();
    expect(screen.queryByText(SUMMARY)).not.toBeInTheDocument();
    expect(screen.queryByText(NO_DISPONIBLE)).not.toBeInTheDocument();
  });

  it("cost_evidence sigue teniendo prioridad sobre la evidencia de anomalía", () => {
    // Una cost_evidence ilegible muestra su propio aviso y la evidencia de anomalía no se pinta.
    render(<AnswerEvidence content="Texto." metadata={{ cost_evidence: { schema_version: "future" }, anomaly_evidence: evidenceA() }} />);
    expect(screen.getByText("La evidencia de costes de esta respuesta no está disponible.")).toBeInTheDocument();
    expect(screen.queryByText(SUMMARY)).not.toBeInTheDocument();
    expect(screen.queryByText(NO_DISPONIBLE)).not.toBeInTheDocument();
  });

  it("sin anomaly_evidence ni citas se mantiene el aviso de 'sin fuentes documentales'", () => {
    // La rama nueva solo actúa cuando la clave existe; el texto final no cambia para el resto de respuestas.
    render(<AnswerEvidence content="Texto." metadata={{ citations: [] }} />);
    expect(screen.getByText(SIN_FUENTES)).toBeInTheDocument();
    expect(screen.queryByText(NO_DISPONIBLE)).not.toBeInTheDocument();
  });
});
