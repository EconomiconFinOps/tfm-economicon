// Prueba del wrapper `Separator` sobre `@radix-ui/react-separator`'s `Root`.
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `Separator` envuelve Radix `SeparatorPrimitive.Root` con props
// `orientation` (default "horizontal") y `decorative` (default true),
// pasando el resto de props (incluida `className`) tal cual.
import { Separator } from "./separator";

describe("Separator", () => {
  it("expone role=separator cuando decorative es false", () => {
    // Comportamiento ARIA real de Radix Separator: si `decorative` es
    // false, el separador es semanticamente significativo (p.ej. separa
    // secciones de contenido no relacionado) y Radix le asigna
    // role="separator" para que sea anunciado por lectores de pantalla.
    // Verificar esto -- en vez de solo comprobar que "algo se renderiza" --
    // es la unica forma de probar que el wrapper no rompe ese contrato de
    // accesibilidad al reenviar la prop `decorative` a Radix.
    render(<Separator decorative={false} />);

    expect(screen.getByRole("separator")).toBeInTheDocument();
  });

  it("no expone role=separator con el valor por defecto (decorative=true)", () => {
    // Caso complementario: por defecto Radix marca el separador como
    // puramente decorativo (role="none"), ocultandolo del arbol de
    // accesibilidad. Si el wrapper no reenviase correctamente el default
    // `decorative = true`, este test fallaria porque Radix expondria
    // role="separator" en vez de ocultarlo.
    render(<Separator />);

    expect(screen.queryByRole("separator")).toBeNull();
  });
});
