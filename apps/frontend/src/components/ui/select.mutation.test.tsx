// Casos adicionales (remediacion de mutation testing, JUP-095 grupo 4, tarea
// 4.3) complementarios a select.test.tsx, que ya esta commiteado y bloqueado
// por el hook del harness. Ese archivo verifica el placeholder visible en el
// combobox; aqui se cubren dos mutantes distintos en `SelectTrigger`, ambos
// invisibles para esa asercion.
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { Select, SelectTrigger, SelectValue } from "./select";

describe("SelectTrigger (mutaciones: default de size y string de clases)", () => {
  it("fija data-size='default' cuando no se pasa la prop size explicita", () => {
    // Mata el mutante StringLiteral de select.tsx:33, que cambia el default
    // de la prop `size` de `SelectTrigger` (`size = "default"`) a `size = ""`.
    // El wrapper reenvia `size` como `data-size` al elemento de Radix; sin
    // esta asercion, un default vacio no rompia el placeholder visible (el
    // otro test de este componente) y el mutante sobrevivia.
    render(
      <Select>
        <SelectTrigger>
          <SelectValue placeholder="Elige una opcion" />
        </SelectTrigger>
      </Select>,
    );

    const trigger = screen.getByRole("combobox");

    expect(trigger).toHaveAttribute("data-size", "default");
  });

  it("aplica las clases base del wrapper al trigger", () => {
    // Mata el mutante StringLiteral de select.tsx:44, que colapsa el string
    // de clases de `SelectTrigger` (`"border-input ... rounded-md ..."`) a
    // `""`. Se elige "rounded-md" por ser una clase literal, estable y
    // presente tal cual en el string original (no depende de `data-size` ni
    // de interpolaciones condicionales del string).
    render(
      <Select>
        <SelectTrigger>
          <SelectValue placeholder="Elige una opcion" />
        </SelectTrigger>
      </Select>,
    );

    const trigger = screen.getByRole("combobox");

    expect(trigger).toHaveClass("rounded-md");
  });
});
