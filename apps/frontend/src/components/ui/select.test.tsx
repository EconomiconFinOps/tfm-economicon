// Prueba de los wrappers `Select`, `SelectTrigger` y `SelectValue` sobre
// `@radix-ui/react-select`. No se importa `SelectContent`/`SelectItem`
// porque el contenido de un Select de Radix solo se monta en el DOM (via
// Portal) cuando esta abierto -- no hace falta abrirlo para probar el
// render del disparador en su estado cerrado por defecto.
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `Select` envuelve Radix `SelectPrimitive.Root` (no controlado, sin
// render propio); `SelectTrigger` envuelve `Trigger` (Radix le asigna
// role="combobox" automaticamente); `SelectValue` envuelve `Value` y
// acepta `placeholder`.
import { Select, SelectTrigger, SelectValue } from "./select";

describe("Select", () => {
  it("renderiza un combobox que muestra el placeholder cuando no hay valor seleccionado", () => {
    render(
      <Select>
        <SelectTrigger>
          <SelectValue placeholder="Elige una opcion" />
        </SelectTrigger>
      </Select>,
    );

    // Radix asigna role="combobox" al disparador del Select de forma
    // automatica (no es una prop que el wrapper tenga que fijar a mano):
    // consultar por ese rol verifica que `SelectTrigger` efectivamente
    // reenvia sus props/estructura a `SelectPrimitive.Trigger` en vez de
    // renderizar un elemento generico sin semantica.
    const trigger = screen.getByRole("combobox");

    expect(trigger).toBeInTheDocument();
    // Sin valor seleccionado, Radix `Value` muestra el `placeholder` como
    // contenido visible dentro del trigger -- es el comportamiento
    // observable que demuestra que `SelectValue` reenvia esa prop a Radix.
    expect(trigger).toHaveTextContent("Elige una opcion");
  });
});
