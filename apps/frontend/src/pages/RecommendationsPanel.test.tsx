import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RecommendationsPanel, RecommendationsWorkbench } from "./RecommendationsPanel";
import { demoImpactReport, demoRecommendationReport as report, demoRecommendationTenant } from "@/data/demo/recommendationsPanel";
import * as model from "@/lib/recommendations";

const change = (name: string, value: string) => fireEvent.change(screen.getByRole("combobox", { name }), { target: { value } });
const actions = () => within(screen.getByRole("list", { name: "Recomendaciones priorizadas" })).getAllByRole("article").map(node => node.getAttribute("aria-label"));
const indicator = (name: string) => within(screen.getByRole("region", { name: "Resumen de la vista actual" })).getByText(name).nextElementSibling?.textContent;

describe("RecommendationsPanel", () => {
  it("makes the independent demo explicit and derives counts from the displayed report", () => {
    render(<RecommendationsPanel />);
    expect(screen.getByRole("heading", { name: "Panel de Recomendaciones" })).toBeVisible();
    expect(screen.getByLabelText("Datos de demostración")).toHaveTextContent("independientes del cliente seleccionado");
    expect(indicator("Recomendaciones visibles")).toBe("5");
    expect(indicator("Con estimación de ahorro")).toBe("4");
    expect(indicator("Ahorro sin estimar")).toBe("1");
    expect(screen.queryByRole("button", { name: "Implementar" })).not.toBeInTheDocument();
    expect(screen.queryByText(/ROI|Agentes IA Especializados Activos|106.000/)).not.toBeInTheDocument();
  });

  it("combines type and difficulty filters, updates summary, disables empty export and resets", async () => {
    const user = userEvent.setup();
    render(<RecommendationsPanel />);
    change("Tipo", "investigation");
    change("Dificultad", "low");
    expect(actions()).toEqual(["Investigar el consumo de Boreal"]);
    expect(indicator("Recomendaciones visibles")).toBe("1");
    expect(indicator("Dificultad baja")).toBe("1");
    change("Tipo", "tagging");
    change("Dificultad", "high");
    expect(screen.getByText("No hay recomendaciones con estos filtros")).toBeVisible();
    expect(indicator("Con estimación de ahorro")).toBe("0");
    expect(screen.getByRole("button", { name: "Exportar vista CSV" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Ver todas las recomendaciones" }));
    expect(actions()).toHaveLength(5);
    expect(screen.getByRole("combobox", { name: "Dificultad" })).toHaveValue("all");
  });

  it("sorts independent of fixture order, groups currencies, and uses received annual amounts", () => {
    const shuffled = { ...report, recommendations: [...report.recommendations].reverse() };
    render(<RecommendationsWorkbench report={shuffled} impact={demoImpactReport} tenantId={demoRecommendationTenant} source="Prueba" />);
    expect(actions()).toEqual([report.recommendations[1].action, report.recommendations[2].action, report.recommendations[0].action, report.recommendations[3].action, report.recommendations[4].action]);
    change("Ordenar por", "difficulty");
    expect(actions()).toEqual([report.recommendations[0].action, report.recommendations[3].action, report.recommendations[1].action, report.recommendations[2].action, report.recommendations[4].action]);
    change("Ahorro estimado", "annual");
    const atlas = screen.getByRole("article", { name: report.recommendations[1].action });
    expect(atlas).toHaveTextContent("10.800,00");
    expect(atlas).toHaveTextContent("Ahorro potencial · anual");
    expect(screen.getByRole("article", { name: report.recommendations[0].action })).toHaveTextContent("0,00");
    expect(screen.getByRole("article", { name: report.recommendations[4].action })).toHaveTextContent("No estimado");
  });

  it("exposes evidence, source, risk, confidence, limitations and human approval using keyboard details", async () => {
    const user = userEvent.setup();
    render(<RecommendationsPanel />);
    const article = screen.getByRole("article", { name: report.recommendations[2].action });
    const summary = within(article).getByText("Ver acción y evidencia");
    summary.closest("summary")?.focus();
    await user.keyboard("{Enter}");
    // jsdom does not emulate keyboard default actions for <summary>; use its
    // native click activation and verify the actual open property as well.
    if (!article.querySelector("details")?.open) await user.click(summary);
    expect(article.querySelector("details")?.open).toBe(true);
    expect(within(article).getByText(/Requiere aprobación humana/)).toBeVisible();
    expect(within(article).getByText("Evidencia de costes")).toBeVisible();
    expect(article).toHaveTextContent("6.200,00 EUR observados · 42 registros");
    expect(article).toHaveTextContent("Fuente: azure_cost_records");
    expect(article).toHaveTextContent("RiesgoAlta");
    expect(article).toHaveTextContent("ConfianzaBaja");
    expect(article).toHaveTextContent("Excluido del total por compartir alcance");
    expect(article).toHaveTextContent("Ninguna estimación es un ahorro realizado o garantizado");
  });

  it("exports only visible records and current period, preserving scenario assumptions", async () => {
    const download = vi.spyOn(model, "downloadRecommendations").mockImplementation(() => {});
    const user = userEvent.setup();
    render(<RecommendationsPanel />);
    change("Tipo", "tagging");
    change("Ahorro estimado", "annual");
    await user.click(screen.getByRole("button", { name: "Exportar vista CSV" }));
    const csv = download.mock.calls[0][0];
    expect(csv).toContain('"0.00","EUR","Anual"');
    expect(csv).toContain("Completar la atribución");
    expect(csv).not.toContain("Investigar el consumo de Boreal");
    expect(csv).toContain("mantiene las condiciones mensuales durante doce meses");
    expect(csv).toContain("no son aditivos");
    expect(csv).toContain("Demostración estática · datos simulados");
    download.mockRestore();
  });

  it("does not turn absent impact or empty reports into zero savings or proof of optimization", () => {
    render(<RecommendationsWorkbench report={{ ...report, recommendations: [], evidence: [], total_candidates: 0, status: "insufficient_data", data_status: "empty" }} source="Datos simulados" />);
    expect(screen.getByText("No hay recomendaciones para este periodo")).toBeVisible();
    expect(screen.getByText(/no confirma que el entorno esté optimizado/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Exportar vista CSV" })).toBeDisabled();
  });
});
