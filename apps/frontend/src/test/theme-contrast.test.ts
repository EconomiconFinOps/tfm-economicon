// Contraste de los pares texto/fondo del tema en cada paleta (JUP-112, decisión 5
// de design.md; requisitos de estados, gráficas y botones de frontend-brand-identity).
// Lee theme.css con `node:fs`, resuelve los alias `var(--x)` y calcula la razón
// de contraste WCAG: 4,5:1 para texto y 3:1 para elementos gráficos.
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const THEME_CSS = readFileSync(path.resolve(__dirname, "..", "styles", "theme.css"), "utf-8").replace(
  /\/\*[\s\S]*?\*\//g,
  "",
);

type Palette = Record<string, string>;

function blockOf(header: string): string {
  const start = THEME_CSS.indexOf(`${header} {`);
  if (start < 0) throw new Error(`theme.css no tiene el bloque ${header}`);
  return THEME_CSS.slice(THEME_CSS.indexOf("{", start) + 1, THEME_CSS.indexOf("}", start));
}

function readPalette(header: string): Palette {
  const palette: Palette = {};
  for (const match of blockOf(header).matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    palette[match[1]] = match[2].trim();
  }
  return palette;
}

const LIGHT = readPalette(":root");
const DARK = { ...LIGHT, ...readPalette('[data-theme="dark"]') };

function resolve(palette: Palette, token: string): string {
  let value = palette[`--${token}`];
  for (let depth = 0; value !== undefined && value.startsWith("var("); depth += 1) {
    if (depth > 5) throw new Error(`alias circular en --${token}`);
    value = palette[value.slice(4, -1).trim()];
  }
  if (!value || !/^#[0-9a-f]{6}$/i.test(value)) throw new Error(`--${token} no resuelve a un color hexadecimal: ${value}`);
  return value;
}

const channels = (hex: string): number[] => [1, 3, 5].map((index) => parseInt(hex.slice(index, index + 2), 16));

function mix(foreground: string, background: string, alpha: number): string {
  const front = channels(foreground);
  const back = channels(background);
  const result = front.map((value, index) => Math.round(value * alpha + back[index] * (1 - alpha)));
  return `#${result.map((value) => value.toString(16).padStart(2, "0")).join("")}`;
}

function luminance(hex: string): number {
  const [red, green, blue] = channels(hex).map((value) => {
    const unit = value / 255;
    return unit <= 0.03928 ? unit / 12.92 : ((unit + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

export function contrast(first: string, second: string): number {
  const [light, dark] = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (light + 0.05) / (dark + 0.05);
}

const SURFACES = ["background", "card", "accent"];
const STATES = ["success", "danger", "info", "warning"];
// Opacidad máxima con la que las pantallas pintan el relleno suave de un estado.
const TINT_ALPHA = 0.3;

describe("contraste - cálculo (en memoria)", () => {
  it("negro sobre blanco es 21:1 y un color sobre sí mismo 1:1", () => {
    expect(contrast("#000000", "#ffffff")).toBeCloseTo(21, 5);
    expect(contrast("#5b4fe8", "#5b4fe8")).toBeCloseTo(1, 5);
  });

  it("el coral con texto blanco no llega a 4,5:1 (por eso el texto sobre coral es casi negro)", () => {
    expect(contrast("#ffffff", "#ff8a5b")).toBeLessThan(4.5);
  });

  it("detecta un token que no resuelve a un color", () => {
    expect(() => resolve({ "--a": "var(--b)" }, "a")).toThrow(/no resuelve/);
  });
});

describe.each([
  ["clara", LIGHT],
  ["oscura", DARK],
] as const)("contraste de la paleta %s", (_name, palette) => {
  const color = (token: string) => resolve(palette, token);

  it.each(SURFACES)("el texto principal y el secundario se leen sobre %s (≥4,5:1)", (surface) => {
    expect(contrast(color("foreground"), color(surface))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(color("subtle-foreground"), color(surface))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(color("muted-foreground"), color(surface))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(color("highlight"), color(surface))).toBeGreaterThanOrEqual(4.5);
  });

  it.each(STATES.flatMap((state) => SURFACES.map((surface) => [state, surface] as const)))(
    "el texto de estado %s se lee sobre su relleno suave y sobre %s (≥4,5:1)",
    (state, surface) => {
      const surfaceColor = color(surface);
      const softFill = mix(color(`${state}-tint`), surfaceColor, TINT_ALPHA);
      expect(contrast(color(`${state}-foreground`), softFill)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(color(state), surfaceColor)).toBeGreaterThanOrEqual(4.5);
    },
  );

  it.each(STATES)("el relleno de estado %s se distingue de la tarjeta (≥3:1)", (state) => {
    expect(contrast(color(`${state}-tint`), color("card"))).toBeGreaterThanOrEqual(3);
  });

  it("los textos sobre violeta, coral e índigo de marca se leen (≥4,5:1)", () => {
    expect(contrast(color("primary-foreground"), color("primary"))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(color("saving-foreground"), color("saving"))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(color("brand-foreground"), color("brand"))).toBeGreaterThanOrEqual(4.5);
  });

  it.each(["chart-1", "chart-2", "chart-3", "chart-4", "chart-5"])(
    "la serie %s se distingue de la tarjeta (≥3:1)",
    (series) => {
      expect(contrast(color(series), color("card"))).toBeGreaterThanOrEqual(3);
    },
  );

  it("el violeta y el coral de marca son los de la guía en ambas paletas", () => {
    expect(color("primary").toLowerCase()).toBe("#5b4fe8");
    expect(color("saving").toLowerCase()).toBe("#ff8a5b");
    expect(color("brand").toLowerCase()).toBe("#2b2359");
  });

  it("las series de gráfica no usan el violeta de botones ni el coral", () => {
    const series = ["chart-1", "chart-2", "chart-3", "chart-4", "chart-5"].map((token) => color(token).toLowerCase());
    expect(series).not.toContain(color("primary").toLowerCase());
    expect(series).not.toContain(color("saving").toLowerCase());
  });
});

describe("la paleta clara es la de la guía de marca", () => {
  it("fondo, texto y tarjeta suave son los de la guía", () => {
    expect(resolve(LIGHT, "background").toLowerCase()).toBe("#fafafc");
    expect(resolve(LIGHT, "foreground").toLowerCase()).toBe("#14121f");
    expect(resolve(LIGHT, "accent").toLowerCase()).toBe("#e4e1fb");
  });
});
