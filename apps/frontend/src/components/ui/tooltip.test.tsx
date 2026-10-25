// Prueba de los wrappers `Tooltip`, `TooltipTrigger` y `TooltipContent`
// sobre `@radix-ui/react-tooltip`.
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `Tooltip` envuelve Radix `TooltipPrimitive.Root`, pero ademas lo envuelve
// internamente en su propio `TooltipProvider` (delayDuration=0 por
// defecto) -- el test NO necesita anadir su propio <TooltipProvider>
// alrededor. `TooltipContent` usa `Portal` y, como en Dialog, no se monta
// en el DOM hasta que el tooltip se muestra (hover/focus).
import { Tooltip, TooltipContent, TooltipTrigger } from "./tooltip";

describe("Tooltip", () => {
  it("monta el disparador pero no el contenido mientras no hay interaccion", () => {
    render(
      <Tooltip>
        <TooltipTrigger>Pasa el raton</TooltipTrigger>
        <TooltipContent>Informacion</TooltipContent>
      </Tooltip>,
    );

    // El disparador si esta presente de entrada: es el elemento visible
    // con el que el usuario interactua para revelar el tooltip.
    expect(screen.getByText("Pasa el raton")).toBeInTheDocument();

    // El contenido del tooltip usa Portal + Presence en Radix: sin hover
    // ni focus, Radix no lo monta en el DOM en absoluto (no es solo un
    // "display: none", el nodo no existe). Verificar `queryByText` en vez
    // de `getByText` es deliberado: `getByText` lanzaria si no lo
    // encuentra, mientras que aqui la ausencia es el comportamiento
    // esperado a comprobar. Si el wrapper montase el contenido siempre
    // (sin envolver Portal/Presence correctamente), este test fallaria.
    expect(screen.queryByText("Informacion")).toBeNull();
  });
});
