import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// Actual theme values, including aliases, rather than a duplicate test palette.
const theme = readFileSync(path.resolve(__dirname, "../styles/theme.css"), "utf8");
const root = theme.match(/:root\s*\{([\s\S]*?)\}/)![1];
const tokens = new Map([...root.matchAll(/(--[\w-]+):\s*([^;]+);/g)].map((match) => [match[1], match[2]]));
type Color = [number, number, number];

function color(name: string, seen: string[] = []): Color {
  if (seen.includes(name)) throw new Error(`Circular color alias: ${name}`);
  const value = tokens.get(`--${name}`)?.trim();
  const alias = value?.match(/^var\(--([\w-]+)\)$/)?.[1];
  if (alias) return color(alias, [...seen, name]);
  if (!value || !/^#[\da-f]{6}$/i.test(value)) throw new Error(`Unsupported or missing color: ${name}`);
  return [1, 3, 5].map((offset) => parseInt(value.slice(offset, offset + 2), 16)) as Color;
}

function mix(foreground: Color, background: Color, opacity: number): Color {
  return foreground.map((channel, index) => channel * opacity + background[index] * (1 - opacity)) as Color;
}

function luminance(value: Color): number {
  const linear = value.map((channel) => {
    const srgb = channel / 255;
    return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
  });
  return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722;
}

function contrast(foreground: Color, background: Color): number {
  const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

describe("JUP-112 readable Economicon brand", () => {
  it("uses the approved light brand palette and a separate white CTA label", () => {
    expect(tokens.get("--background")).toBe("#FAFAFC");
    expect(tokens.get("--brand")).toBe("#2B2359");
    expect(tokens.get("--primary")).toBe("#5B4FE8");
    expect(tokens.get("--accent")).toBe("#E4E1FB");
    expect(tokens.get("--insight")).toBe("#FF8A5B");
    expect(contrast(color("primary-foreground"), color("primary"))).toBeGreaterThanOrEqual(4.5);
    // Hover uses primary/90 on the card, where contrast is lower than the solid CTA.
    expect(contrast(color("primary-foreground"), mix(color("primary"), color("card"), 0.9))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(color("insight-foreground"), color("insight"))).toBeGreaterThanOrEqual(4.5);
  });

  const textTokens = ["foreground", "brand", "muted-foreground", "subtle-foreground", "neutral", "success", "danger", "info", "warning", "warning-text", "positive", "chart-axis"];
  it.each(textTokens)("%s supports normal text on the light page and card", (name) => {
    for (const surface of ["background", "card"]) {
      expect(contrast(color(name), color(surface)), `${name} on ${surface}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it.each(["success", "danger", "info", "warning", "attention"])("%s labels remain readable on their translucent badge", (state) => {
    for (const surface of ["background", "card", "accent"]) {
      expect(contrast(color(`${state}-foreground`), mix(color(`${state}-tint`), color(surface), 0.2))).toBeGreaterThanOrEqual(4.5);
    }
  });

  it.each(["chart-1", "chart-2", "chart-3", "chart-4", "chart-5", "chart-negative", "chart-baseline"])("%s remains visible on a chart surface", (name) => {
    expect(contrast(color(name), color("card"))).toBeGreaterThanOrEqual(3);
  });

  it("has a visible keyboard focus color and accessible field borders", () => {
    expect(contrast(color("ring"), color("background"))).toBeGreaterThanOrEqual(3);
    expect(contrast(color("input"), color("card"))).toBeGreaterThanOrEqual(3);
  });
});
