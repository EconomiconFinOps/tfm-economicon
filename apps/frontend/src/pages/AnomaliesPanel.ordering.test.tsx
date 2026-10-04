import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import type { DemoAnomaly } from "@/data/demo/anomaliesPanel";
import { AnomaliesPanel } from "./AnomaliesPanel";

// Input order and impact order differ from severity priority. Include a high
// resolved record so counting all high records cannot pass as high open count.
vi.mock("@/data/demo/anomaliesPanel", () => {
  const row = (id: number, servicio: string, severidad: DemoAnomaly["severidad"], estado: DemoAnomaly["estado"], coste: number): DemoAnomaly =>
    ({ id, servicio, severidad, estado, coste, tipo: "Tipo", descripcion: "Descripción", detectado: "2026-04-18 10:00", agente: "n/a" });
  return {
    demoPeriod: "18–19 de abril de 2026",
    anomalies: [
      row(1, "Baja pendiente 9000", "Baja", "Pendiente", 9000),
      row(2, "Alta investigando 1000", "Alta", "Investigando", 1000),
      row(3, "Alta pendiente 5000", "Alta", "Pendiente", 5000),
      row(4, "Alta resuelta 7000", "Alta", "Resuelto", 7000),
      row(5, "Media resuelta 3000", "Media", "Resuelto", 3000),
    ],
  };
});
vi.mock("@/components/ExportButton", () => ({ ExportButton: () => <button>Exportar Resultados</button> }));

const change = (label: string, value: string) => fireEvent.change(screen.getByRole("combobox", { name: label }), { target: { value } });
const services = () => screen.getAllByRole("rowheader").map(cell => cell.querySelector("p")?.textContent);
const indicator = (label: string) => within(screen.getByRole("region", { name: "Resumen del conjunto de muestra" })).getByText(label).nextElementSibling?.textContent;

describe("AnomaliesPanel with adversarial priorities and statuses", () => {
  it("prioritizes severity and breaks same-severity ties by impact rather than input order", () => {
    render(<AnomaliesPanel />);
    expect(services()).toEqual(["Alta pendiente 5000", "Alta investigando 1000", "Baja pendiente 9000"]);
    change("Estado", "Todos");
    expect(services()).toEqual(["Alta resuelta 7000", "Alta pendiente 5000", "Alta investigando 1000", "Media resuelta 3000", "Baja pendiente 9000"]);
  });

  it("excludes resolved high alerts from high open count and preserves all global indicators through filters and empty results", () => {
    render(<AnomaliesPanel />);
    expect(screen.getByLabelText("Datos de demostración")).toHaveTextContent("independientes del cliente seleccionado");
    const expected = () => {
      expect(indicator("Impacto de anomalías abiertas")).toContain("15.000");
      expect(indicator("Anomalías abiertas")).toBe("3");
      expect(indicator("Criticidad alta · abiertas")).toBe("2");
      expect(indicator("Anomalías resueltas")).toBe("2");
      expect(screen.getByText(/El resumen no cambia con los filtros/)).toBeInTheDocument();
    };
    expected();
    change("Criticidad", "Alta");
    change("Estado", "Resuelto");
    expect(services()).toEqual(["Alta resuelta 7000"]);
    expected();
    change("Criticidad", "Baja");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expected();
  });
});
