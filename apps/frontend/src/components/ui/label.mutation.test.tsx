// Caso adicional (remediacion de mutation testing, JUP-095 grupo 4, tarea
// 4.3) complementario a label.test.tsx, que ya esta commiteado y bloqueado
// por el hook del harness. No se duplican sus aserciones (asociacion
// label->campo via htmlFor); este archivo cubre un mutante distinto.
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { Label } from "./label";

describe("Label (mutacion: string de clases)", () => {
  it("aplica las clases base del wrapper al elemento renderizado", () => {
    // Mata el mutante StringLiteral de label.tsx:16, que colapsa el string
    // de clases de `Label` (`"flex items-center gap-2 text-sm ..."`) a `""`.
    // Ninguna prueba existente verifica clases CSS en `Label`, por lo que
    // ese mutante sobrevivia: si el string se vacia, el elemento renderizado
    // deja de tener "text-sm" y este test lo detecta.
    render(<Label htmlFor="campo">Texto</Label>);

    const label = screen.getByText("Texto");

    // "text-sm" es una clase literal presente en el string original y
    // estable (no depende de la logica de `cn`/`twMerge`, que solo entra en
    // juego cuando se pasa `className` adicional).
    expect(label).toHaveClass("text-sm");
  });
});
