// Casos adicionales (remediacion de mutation testing, JUP-095 grupo 4, tarea
// 4.3) complementarios a separator.test.tsx, que ya esta commiteado y
// bloqueado por el hook del harness. Ese archivo verifica el rol ARIA segun
// `decorative`; aqui se cubren dos mutantes distintos sobre `orientation` y
// el string de clases, que no son observables via `getByRole` porque con
// `decorative` por defecto (true) Radix oculta el elemento del arbol de
// accesibilidad (role="none") y `getByRole("separator")` no lo encuentra.
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import { Separator } from "./separator";

describe("Separator (mutaciones: default de orientation y string de clases)", () => {
  it("fija data-orientation='horizontal' cuando no se pasa la prop orientation explicita", () => {
    // Verifica el comportamiento por defecto observable de `orientation`.
    // NO mata el mutante StringLiteral de separator.tsx:10 (que cambia
    // `orientation = "horizontal"` a `orientation = ""`): confirmado por
    // codigo fuente y por ejecucion real de Stryker, ese mutante es
    // equivalente. `@radix-ui/react-separator`'s `Root` valida el prop
    // `orientation` internamente (`isValidOrientation`, ver
    // node_modules/@radix-ui/react-separator/dist/index.mjs) y si el valor
    // recibido no es "horizontal" ni "vertical" (incluida la cadena vacia
    // "" del mutante) usa su propio `DEFAULT_ORIENTATION = "horizontal"`
    // para fijar `data-orientation`. Por tanto el DOM renderizado es
    // identico con el default real ("horizontal") y con el mutado (""): no
    // existe aserción posible sobre el render que distinga ambos casos.
    // Se documenta aqui en vez de eliminar el caso porque sigue verificando
    // un comportamiento real (el default efectivo es "horizontal").
    const { container } = render(<Separator />);

    const separator = container.querySelector('[data-slot="separator-root"]');

    expect(separator).toHaveAttribute("data-orientation", "horizontal");
  });

  it("aplica las clases base del wrapper al elemento renderizado", () => {
    // Mata el mutante StringLiteral de separator.tsx:20, que colapsa el
    // string de clases de `Separator` (`"bg-border shrink-0 ..."`) a `""`.
    // "shrink-0" es una clase literal estable del string original, no
    // condicionada por `orientation` (esa parte del string usa selectores
    // `data-[orientation=...]`, no interpolacion de JS).
    const { container } = render(<Separator />);

    const separator = container.querySelector('[data-slot="separator-root"]');

    expect(separator).toHaveClass("shrink-0");
  });
});
