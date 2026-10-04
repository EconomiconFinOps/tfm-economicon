import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { AnomaliesPanel } from "./AnomaliesPanel";

const exportSpy = vi.hoisted(() => vi.fn());
vi.mock("@/components/ExportButton", () => ({
  ExportButton: (props: { data: Record<string, string | number>[]; filename: string }) => {
    exportSpy(props);
    return <button>Exportar Resultados</button>;
  },
}));
afterEach(() => vi.clearAllMocks());
const change = (label: string, value: string) => fireEvent.change(screen.getByRole("combobox", { name: label }), { target: { value } });
const services = () => screen.getAllByRole("rowheader").map(cell => cell.querySelector("p")?.textContent);
const exported = () => exportSpy.mock.lastCall?.[0] as { data: Record<string, string | number>[]; filename: string };

describe("AnomaliesPanel", () => {
  it("shows honest sample provenance, computed global metrics and only open alerts by default", () => {
    render(<AnomaliesPanel />);
    expect(screen.getByRole("heading", { name: "Panel de Anomalías y Alertas" })).toBeInTheDocument();
    expect(screen.getByLabelText("Datos de demostración")).toHaveTextContent("18–19 de abril de 2026");
    expect(screen.getByLabelText("Datos de demostración")).toHaveTextContent("sin conexión a detección real");
    const summary = screen.getByRole("region", { name: "Resumen del conjunto de muestra" });
    expect(within(summary).getByText("Impacto de anomalías abiertas").nextElementSibling).toHaveTextContent("30.700");
    expect(within(summary).getByText("Anomalías abiertas").nextElementSibling).toHaveTextContent("3");
    expect(within(summary).getByText("Criticidad alta · abiertas").nextElementSibling).toHaveTextContent("2");
    expect(within(summary).getByText("Anomalías resueltas").nextElementSibling).toHaveTextContent("2");
    expect(services()).toEqual(["EC2 - us-east-1", "CloudFront", "EBS Volumes"]);
    expect(screen.queryByText("RDS Database")).not.toBeInTheDocument();
    expect(screen.queryByText("Azure Storage")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Mostrando 3 de 5");
    expect(screen.getByText("2026-04-19 03:24")).toHaveAttribute("datetime", "2026-04-19T03:24");
  });

  it("combines severity and status filters while keeping global metrics unchanged", () => {
    render(<AnomaliesPanel />);
    change("Criticidad", "Media");
    change("Estado", "Resuelto");
    expect(services()).toEqual(["RDS Database", "Azure Storage"]);
    expect(screen.getByRole("status")).toHaveTextContent("Mostrando 2 de 5");
    expect(screen.getByText("Impacto de anomalías abiertas").nextElementSibling).toHaveTextContent("30.700");
    change("Criticidad", "Baja");
    change("Estado", "Pendiente");
    expect(services()).toEqual(["EBS Volumes"]);
    change("Criticidad", "Alta");
    change("Estado", "Investigando");
    expect(services()).toEqual(["EC2 - us-east-1", "CloudFront"]);
  });

  it("provides an empty state with disabled export and a working reset", () => {
    render(<AnomaliesPanel />);
    change("Criticidad", "Media");
    expect(screen.getByRole("heading", { name: "No hay alertas con estos filtros" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Exportar Resultados" })).toBeDisabled();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Mostrando 0 de 5");
    fireEvent.click(screen.getByRole("button", { name: "Ver anomalías abiertas" }));
    expect(screen.getByLabelText("Criticidad")).toHaveValue("Todas");
    expect(screen.getByLabelText("Estado")).toHaveValue("Abiertas");
    expect(services()).toHaveLength(3);
    expect(screen.getByRole("button", { name: "Exportar Resultados" })).toBeEnabled();
    change("Estado", "Todos");
    fireEvent.click(screen.getByRole("button", { name: "Restablecer filtros" }));
    expect(screen.queryByRole("combobox", { name: "Ordenar por" })).not.toBeInTheDocument();
    expect(services()).toHaveLength(3);
  });

  it("sorts all rows by severity then impact", () => {
    render(<AnomaliesPanel />);
    change("Estado", "Todos");
    expect(services()).toEqual(["EC2 - us-east-1", "CloudFront", "RDS Database", "Azure Storage", "EBS Volumes"]);
    expect(exported().data.map(row => row["Impacto estimado (EUR)"])).toEqual([15800, 12500, 8200, 5600, 2400]);
  });

  it("passes only the displayed ordered rows to export with demonstration provenance", () => {
    render(<AnomaliesPanel />);
    expect(exported().data.map(row => row.Servicio)).toEqual(services());
    expect(exported().filename).toContain("demo-2026-04-18_19");
    change("Estado", "Todos");
    change("Criticidad", "Media");
    const { data } = exported();
    expect(data.map(row => row.Servicio)).toEqual(["RDS Database", "Azure Storage"]);
    expect(data.map(row => row.Servicio)).toEqual(services());
    for (const row of data) {
      expect(row.Origen).toBe("Datos de demostración");
      expect(row.Periodo).toBe("18–19 de abril de 2026");
      expect(row.Estado).toBe("Resuelto");
    }
  });
});
