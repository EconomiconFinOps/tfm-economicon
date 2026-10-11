import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { billing } from "../../tests/fixtures";
import { CostEvidence } from "./CostEvidence";

const evidence = {
  schema_version: "1.0", adapter_version: "ownership-1.0", id: `cost:${"a".repeat(64)}`,
  source: "azure_cost_records/completed", status: "ok", summary: billing,
  selected_groups: [],
  provenance: { ingestion_ids: [], observed_day_count: 0, first_usage_date: null, last_usage_date: null }
};

describe("ownership cost evidence", () => {
  it("exposes every selected group beyond the 20-group text preview without rounding or currency conversion", () => {
    const groups = Array.from({ length: 21 }, (_, index) => ({
      value: `Application ${index + 1}`, currency: index === 20 ? "EUR" : "USD",
      cost: index === 20 ? "9007199254740993.01" : "-1.20", record_count: 1
    }));
    render(<CostEvidence evidence={{ ...evidence, selected_groups: groups }} />);
    fireEvent.click(screen.getByText("Evidencia de costes — Datos disponibles"));
    fireEvent.click(screen.getByText("Todos los grupos seleccionados (21)"));
    const row = screen.getByText("Application 21").closest("tr")!;
    expect(row).toBeVisible();
    expect(within(row).getByText("9007199254740993.01")).toBeVisible();
    expect(within(row).getByText("EUR")).toBeVisible();
    expect(screen.getAllByRole("row")).toHaveLength(22);
    expect(screen.getAllByText("-1.20")).toHaveLength(20);
  });

  it("does not turn an empty selected group set into zero spending", () => {
    render(<CostEvidence evidence={{ ...evidence, status: "no_data" }} />);
    fireEvent.click(screen.getByText("Evidencia de costes — Sin datos para la selección"));
    fireEvent.click(screen.getByText("Todos los grupos seleccionados (0)"));
    expect(screen.getByText("Sin grupos en la selección; no equivale a gasto cero.")).toBeVisible();
  });

  it("rejects malformed group and provenance fields while retaining understood evidence", () => {
    render(<CostEvidence evidence={{ ...evidence,
      selected_groups: [{ value: "Application", currency: "EUR", cost: 10, record_count: 1 }],
      provenance: { ingestion_ids: [null], observed_day_count: -1, first_usage_date: "2026-02-30", last_usage_date: null }
    }} />);
    fireEvent.click(screen.getByText("Evidencia de costes — Datos disponibles"));
    expect(screen.getByText("El desglose guardado no está disponible.")).toBeVisible();
    expect(screen.getByText("La procedencia detallada no está disponible.")).toBeVisible();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });
});
