import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnomalyEvidence } from "./AnomalyEvidence";
import { isAnomalyEvidence } from "../services/contracts";
import { episode } from "../test/anomalyFixtures";

// JUP-038 tarea 5.4: remediación de mutantes supervivientes de AnomalyEvidence.tsx.
// Las pruebas de AnomalyEvidence.test.tsx están commiteadas y bloqueadas, así que estos casos van aparte.

const LIMITACION = "Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.";

// Evidencia JSON laxa que las pruebas mutan a mano (sin `any`).
type Mut = { [key: string]: unknown };

// Ejemplo A del backend (Compute, EUR, P3), con las limitaciones parametrizables.
function evidenceA(limitations: string[]): Mut {
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
      rules_version: "jup019-daily-v1", limitations,
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
    limitations,
    explained_at: "2026-10-12T18:30:00+00:00",
  };
}

// Renderiza el bloque real y abre el <details> principal con un clic en su resumen.
function renderOpen(evidence: unknown) {
  render(<AnomalyEvidence evidence={evidence} />);
  fireEvent.click(screen.getByText(/^Evidencia de la anomalía — /));
}

describe("JUP-038 AnomalyEvidence: lista de limitaciones (mutantes `length > 0` -> `true` y `>= 0`)", () => {
  it("una evidencia con limitations vacío sigue siendo válida para el validador", () => {
    // Condición previa: el caso vacío es un contrato legítimo, no un rechazo del validador.
    expect(isAnomalyEvidence(evidenceA([]))).toBe(true);
  });

  it("sin limitaciones no pinta ninguna lista «Limitaciones» pero sí el resto del bloque", () => {
    renderOpen(evidenceA([]));
    // El resto del bloque se muestra (el bloque no cayó en «no disponible»)...
    expect(screen.getByText("Candidata: causa no establecida.")).toBeVisible();
    expect(screen.getByText("Criticidad: Baja (P3) (tramo < 500.00).")).toBeVisible();
    // ...y no existe una <ul aria-label="Limitaciones"> vacía. Mata `true &&` y `>= 0 &&`, que la pintarían.
    expect(screen.queryByLabelText("Limitaciones")).toBeNull();
    expect(screen.queryByRole("list", { name: "Limitaciones" })).toBeNull();
  });

  it("control positivo: con una limitación la lista existe y la contiene", () => {
    renderOpen(evidenceA([LIMITACION]));
    const lista = screen.getByLabelText("Limitaciones");
    expect(lista.tagName).toBe("UL");
    expect(lista.querySelectorAll("li")).toHaveLength(1);
    expect(lista).toHaveTextContent(LIMITACION);
  });
});
