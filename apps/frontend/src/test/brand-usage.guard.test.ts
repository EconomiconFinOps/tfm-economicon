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

describe("el violeta de marca es exclusivo de botones", () => {
  it("ninguna gráfica ni texto ni borde usa `primary` como color", () => {
    const offenders = SOURCES.filter(({ file }) => !PRIMARY_EXCEPTIONS.includes(file)).flatMap(({ file, text }) =>
      text
        .split("\n")
        .flatMap((line, index) => {
          const found = [
            ...line.matchAll(/var\(--primary\)|(?<![\w-])(?:text|border|ring|outline|fill|stroke|from|to|via|shadow)-primary(?![\w-])/g)
          ];
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
    const sample = '<Bar fill="var(--primary)" /> <p className="text-primary">';
    expect([...sample.matchAll(/var\(--primary\)|(?<![\w-])(?:text|fill)-primary(?![\w-])/g)]).toHaveLength(2);
  });
});

describe("el relleno suave de un estado se mantiene dentro de la opacidad comprobada", () => {
  it("ninguna clase de relleno o borde de estado supera el 30 %", () => {
    const offenders = SOURCES.flatMap(({ file, text }) =>
      [...text.matchAll(/(?<![\w-])(?:bg|border|from|to|via)-(?:success|danger|info|warning|neutral)-tint\/(\d+)/g)]
        .filter((match) => Number(match[1]) > 30)
        .map((match) => `${file} ${match[0]}`),
    );
    expect(offenders).toEqual([]);
  });
});
