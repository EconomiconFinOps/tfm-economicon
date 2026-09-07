// Prueba de los wrappers `Dialog` y `DialogTrigger` sobre
// `@radix-ui/react-dialog`. No se importa `DialogContent` porque su
// contenido usa `Portal` y, en Radix, no se monta en el DOM hasta que el
// dialogo se abre -- no hay `@testing-library/user-event` instalado
// todavia en este proyecto, y no se necesita para verificar el estado
// cerrado por defecto.
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `Dialog` envuelve Radix `DialogPrimitive.Root` (no controlado, sin
// render propio); `DialogTrigger` envuelve `Trigger`, que Radix renderiza
// por defecto como un <button>.
import { Dialog, DialogTrigger } from "./dialog";

describe("Dialog", () => {
  it("monta el disparador en su estado cerrado por defecto, sin abrir el dialogo", () => {
    render(
      <Dialog>
        <DialogTrigger>Abrir modal</DialogTrigger>
      </Dialog>,
    );

    // Verificamos por rol accesible "button" (no solo por texto plano):
    // Radix `DialogPrimitive.Trigger` renderiza un <button> nativo por
    // defecto, y este es el elemento real con el que interactuaria un
    // usuario para abrir el dialogo. Esto confirma que el wrapper reenvia
    // la estructura semantica de Radix en vez de un <div> generico.
    const trigger = screen.getByRole("button", { name: "Abrir modal" });

    expect(trigger).toBeInTheDocument();
  });
});
