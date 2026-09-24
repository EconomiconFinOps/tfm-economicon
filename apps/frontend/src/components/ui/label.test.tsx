// Prueba del wrapper `Label` sobre `@radix-ui/react-label`'s `Root`.
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `Label` acepta las props de Radix `LabelPrimitive.Root` (incluida
// `htmlFor`) mas `className`, y renderiza el elemento <label> de Radix
// pasandole esas props tal cual (misma API publica que el origen).
import { Label } from "./label";

describe("Label", () => {
  it("renderiza un elemento label asociado al campo indicado via htmlFor", () => {
    render(<Label htmlFor="campo">Texto</Label>);

    // Radix LabelPrimitive.Root renderiza un <label> nativo con el texto
    // como hijo directo, por lo que `getByText` ya devuelve el propio
    // elemento label. Verificamos el atributo `for` (no solo que el texto
    // este presente) porque es el comportamiento observable real que
    // justifica pasar `htmlFor` a traves del wrapper: la asociacion
    // accesible label->campo, sin la cual un lector de pantalla no podria
    // vincular el texto con el control de formulario.
    const label = screen.getByText("Texto");

    expect(label).toBeInTheDocument();
    expect(label).toHaveAttribute("for", "campo");
  });
});
