// El ahorro se destaca con el coral y nunca con el color de éxito (JUP-112, requisito
// "El coral es el único acento cálido y marca ahorro e insights").
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";

vi.mock("recharts", () => {
  const Passthrough = ({ children }: { children?: React.ReactNode }) => <div>{children}</div>;
  const Empty = () => null;
  return {
    ResponsiveContainer: Passthrough,
    BarChart: Passthrough,
    LineChart: Passthrough,
    AreaChart: Passthrough,
    Bar: Empty,
    Line: Empty,
    Area: Empty,
    XAxis: Empty,
    YAxis: Empty,
    CartesianGrid: Empty,
    Tooltip: Empty,
    Legend: Empty
  };
});

import { RecommendationsPanel } from "./RecommendationsPanel";
import { ExecutiveCutDashboard } from "./ExecutiveCutDashboard";

function cardOf(element: HTMLElement): HTMLElement {
  let current: HTMLElement | null = element;
  while (current && !/\brounded-lg\b/.test(current.className)) current = current.parentElement;
  if (!current) throw new Error("sin tarjeta contenedora");
  return current;
}

describe("el ahorro lleva el acento coral", () => {
  it("la tarjeta de ahorro potencial de Recomendaciones es coral y su texto casi negro", () => {
    render(
      <MemoryRouter>
        <RecommendationsPanel />
      </MemoryRouter>
    );

    const card = cardOf(screen.getByText("Ahorro Potencial Total"));
    expect(card.className).toContain("bg-saving");
    expect(card.className).toContain("text-saving-foreground");
    expect(card.innerHTML).not.toMatch(/text-success/);
  });

  it("la insignia de ahorro de cada recomendación es coral", () => {
    render(
      <MemoryRouter>
        <RecommendationsPanel />
      </MemoryRouter>
    );

    const badges = screen.getAllByText(/€\/mes$/).filter((element) => element.className.includes("font-semibold"));
    expect(badges.length).toBeGreaterThan(0);
    for (const badge of badges) expect(badge.parentElement?.className).toContain("bg-saving");
  });

  it("el KPI de ahorro total de Corte Global es coral y no usa el color de éxito", () => {
    render(
      <MemoryRouter>
        <ExecutiveCutDashboard />
      </MemoryRouter>
    );

    const card = cardOf(screen.getByText("Ahorro Total"));
    expect(card.className).toContain("bg-saving");
    expect(card.innerHTML).not.toMatch(/text-success/);
    // Las demás tarjetas no se pintan de coral: solo el ahorro.
    expect(cardOf(screen.getByText("Objetivo Mensual")).className).not.toContain("bg-saving");
  });
});
