// Prueba de la utilidad `cn`, el helper de composicion de clases que usa
// todo el patron shadcn/ui: `twMerge(clsx(inputs))`. Es la primera pieza
// portada del grupo 4 (JUP-095) y la consumen los 5 wrappers de Radix.
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `cn(...inputs)` acepta los mismos argumentos que `clsx` y devuelve una
// cadena de clases ya deduplicada por `tailwind-merge`.
import { cn } from "./utils";

describe("cn", () => {
  it("concatena varias clases simples en una sola cadena", () => {
    // Caso base: sin conflicto entre utilidades de Tailwind, `cn` debe
    // comportarse como una simple concatenacion (via clsx) e incluir ambas.
    const result = cn("a", "b");

    expect(result).toContain("a");
    expect(result).toContain("b");
  });

  it("deduplica clases de Tailwind en conflicto, quedandose con la ultima", () => {
    // Este es el caso que justifica usar `tailwind-merge` en vez de un
    // `join`/`clsx` a secas: "p-2" y "p-4" son ambas utilidades de padding
    // que compiten por la misma propiedad CSS. Sin `twMerge`, un `clsx`
    // simple concatenaria "p-2 p-4" y el navegador aplicaria la ultima por
    // orden de cascada, pero el string resultante seguiria conteniendo la
    // clase muerta "p-2" -- lo cual rompe herramientas que inspeccionan la
    // cadena de clases (p.ej. tests de snapshot, linters de Tailwind).
    // `twMerge` debe resolver el conflicto y devolver exactamente "p-4".
    const result = cn("p-2", "p-4");

    expect(result).toBe("p-4");
  });
});
