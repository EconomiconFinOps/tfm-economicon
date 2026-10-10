// El texto de la leyenda de las gráficas usa tokens de texto, no el color de la serie
// (JUP-112, requisito "Las gráficas usan una paleta propia coherente con la marca").
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { chartLegendFormatter, chartTooltipStyle } from "./chartTheme";

describe("chartTheme", () => {
  it("la leyenda pinta su texto con el color de texto secundario del tema", () => {
    render(<>{chartLegendFormatter("Compute")}</>);

    expect(screen.getByText("Compute").style.color).toBe("var(--muted-foreground)");
  });

  it("el tooltip usa solo variables del tema", () => {
    expect(Object.values(chartTooltipStyle).filter((value) => String(value).includes("#"))).toEqual([]);
    expect(chartTooltipStyle.backgroundColor).toBe("var(--card)");
  });
});
