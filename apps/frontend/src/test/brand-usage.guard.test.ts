// Reglas de uso de la marca que el tema por sí solo no puede garantizar (JUP-112):
// el violeta es de botones, el relleno suave de un estado no supera la opacidad con la
// que se comprobó el contraste y el ahorro se destaca con el coral.
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const SRC_DIR = path.resolve(__dirname, "..");

function sources(): Array<{ file: string; text: string }> {
  const found: Array<{ file: string; text: string }> = [];
  const walk = (directory: string): void => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const absolute = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        if (entry.name !== "test" && entry.name !== "node_modules") walk(absolute);
      } else if (/\.tsx?$/.test(entry.name) && !/\.test\.tsx?$/.test(entry.name)) {
        found.push({ file: path.relative(SRC_DIR, absolute).split(path.sep).join("/"), text: readFileSync(absolute, "utf-8") });
      }
    }
  };
  walk(SRC_DIR);
  return found;
}

const SOURCES = sources();
// Primitivo de shadcn/ui copiado tal cual (ADR-0004) que ninguna pantalla importa.
const PRIMARY_EXCEPTIONS = ["components/ui/tooltip.tsx"];

// Utilidades de color de Tailwind (con variantes delante) y variables que consumen `primary`.
const PRIMARY_AS_COLOR =
  /var\(\s*--(?:color-)?primary\s*[,)]|(?<![\w-])(?:text|border(?:-[xytblrse])?|ring(?:-offset)?|outline|fill|stroke|from|to|via|shadow|divide|decoration|accent|caret|placeholder)-primary(?![\w-])/g;

describe("el violeta de marca es exclusivo de botones", () => {
  it("ninguna gráfica ni texto ni borde usa `primary` como color", () => {
    const offenders = SOURCES.filter(({ file }) => !PRIMARY_EXCEPTIONS.includes(file)).flatMap(({ file, text }) =>
      text
        .split("\n")
        .flatMap((line, index) => {
          const found = [...line.matchAll(PRIMARY_AS_COLOR)];
          return found.map((match) => `${file}:${index + 1} ${match[0]}`);
        }),
    );
    expect(offenders).toEqual([]);
  });

  it("todo fondo `bg-primary` es un botón con texto `text-primary-foreground`", () => {
    const offenders = SOURCES.filter(({ file }) => !PRIMARY_EXCEPTIONS.includes(file)).flatMap(({ file, text }) =>
      text
        .split("\n")
        .flatMap((line, index) =>
          /(?<![\w-])bg-primary(?![\w-])/.test(line) && !/text-primary-foreground/.test(line) ? [`${file}:${index + 1}`] : [],
        ),
    );
    expect(offenders).toEqual([]);
  });

  it("el detector marca un violeta fuera de su uso (en memoria)", () => {
    const sample = [
      '<Bar fill="var(--primary)" />',
      '<p className="text-primary">',
      '<i className="border-t-primary divide-primary decoration-primary accent-primary caret-primary placeholder-primary ring-offset-primary">',
      'stroke="var( --color-primary )"',
      '<i className="after:bg-primary-foreground hover:text-primary-foreground">'
    ].join(" ");
    expect([...sample.matchAll(PRIMARY_AS_COLOR)].map((match) => match[0])).toEqual([
      "var(--primary)",
      "text-primary",
      "border-t-primary",
      "divide-primary",
      "decoration-primary",
      "accent-primary",
      "caret-primary",
      "placeholder-primary",
      "ring-offset-primary",
      "var( --color-primary )"
    ]);
  });
});

// Rellenos de estado y de acento con opacidad: numérica (`/20`) o arbitraria (`/[60%]`, `/[0.6]`).
const TINT = /(?<![\w-])(?:bg|from|to|via)-(?:success|danger|info|warning|neutral|highlight)(?:-tint)?\/(?:(\d+)|\[([\d.]+)(%?)\])/g;

function tintOpacity(match: RegExpMatchArray): number {
  if (match[1] !== undefined) return Number(match[1]);
  return match[3] === "%" ? Number(match[2]) : Number(match[2]) * 100;
}

describe("el relleno suave de un estado se mantiene dentro de la opacidad comprobada", () => {
  it("ninguna clase de relleno de estado o de acento supera el 30 %", () => {
    const offenders = SOURCES.flatMap(({ file, text }) =>
      [...text.matchAll(TINT)].filter((match) => tintOpacity(match) > 30).map((match) => `${file} ${match[0]}`),
    );
    expect(offenders).toEqual([]);
  });

  it("el detector lee opacidades numéricas y arbitrarias (en memoria)", () => {
    const sample = "bg-neutral/60 bg-highlight/50 bg-danger/40 bg-warning-tint/[60%] bg-info-tint/[0.45] bg-success-tint/20";
    expect([...sample.matchAll(TINT)].map(tintOpacity)).toEqual([60, 50, 40, 60, 45, 20]);
  });
});

describe("el foco de los controles es visible", () => {
  it("ningún `outline-none` sin un indicador de foco propio en la misma línea", () => {
    const offenders = SOURCES.flatMap(({ file, text }) =>
      text
        .split(/\r?\n/)
        .flatMap((line, index) => (/(?<![\w-])outline-none/.test(line) && !/focus-visible:/.test(line) ? [`${file}:${index + 1}`] : [])),
    );
    expect(offenders).toEqual([]);
  });

  it("la regla base no atenúa el anillo de foco por debajo de 3:1", () => {
    const theme = readFileSync(path.join(SRC_DIR, "styles", "theme.css"), "utf-8");
    expect(theme).not.toMatch(/outline-ring\/\d+/);
  });
});

describe("los tooltips de las gráficas no heredan el color de la serie", () => {
  it("cada Tooltip que usa el estilo del tema fija también el color de sus ítems", () => {
    const offenders = SOURCES.flatMap(({ file, text }) => {
      const withStyle = text.match(/contentStyle=\{chartTooltipStyle\}/g)?.length ?? 0;
      const withItems = text.match(/itemStyle=\{chartTooltipItemStyle\}/g)?.length ?? 0;
      return withStyle === withItems ? [] : [`${file} (${withStyle} tooltips, ${withItems} con itemStyle)`];
    });
    expect(offenders).toEqual([]);
  });
});
