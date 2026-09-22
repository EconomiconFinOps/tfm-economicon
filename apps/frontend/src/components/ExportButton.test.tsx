// Prueba del boton de exportacion de resultados (menu CSV/PDF), portado tal
// cual del repositorio de origen (JUP-095, grupo 5).
//
// Importamos describe/it/expect explicitamente porque el proyecto NO usa
// `globals: true` en la config de Vitest (ver vite.config.ts).
import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

// Contrato esperado (a implementar por el agente coder en fase Green):
// `ExportButton` recibe `data` (array de objetos planos a exportar) y
// `filename` (nombre base del archivo generado). Renderiza un boton
// "Exportar Resultados" que, al pulsarse, despliega un menu con las
// opciones "Exportar CSV" y "Exportar PDF" (estado `isOpen` interno,
// cerrado por defecto).
import { ExportButton } from "./ExportButton";

describe("ExportButton", () => {
  it("empieza con el menu cerrado: no muestra las opciones de exportacion hasta que se interactua", () => {
    render(<ExportButton data={[{ columna: "valor" }]} filename="prueba" />);

    // El boton disparador siempre esta presente.
    expect(screen.getByText("Exportar Resultados")).toBeInTheDocument();

    // Antes de cualquier clic, el menu desplegable debe estar cerrado: las
    // opciones no deben existir en el documento (no basta con que esten
    // ocultas visualmente, queremos que el estado inicial del componente
    // sea "cerrado" de forma observable).
    expect(screen.queryByText("Exportar CSV")).toBeNull();
    expect(screen.queryByText("Exportar PDF")).toBeNull();
  });

  it("despliega las opciones CSV y PDF al pulsar el boton", () => {
    render(<ExportButton data={[{ columna: "valor" }]} filename="prueba" />);

    // Simulamos la interaccion real del usuario: un clic sobre el
    // disparador debe alternar el estado `isOpen` del componente y revelar
    // el menu.
    fireEvent.click(screen.getByText("Exportar Resultados"));

    expect(screen.getByText("Exportar CSV")).toBeInTheDocument();
    expect(screen.getByText("Exportar PDF")).toBeInTheDocument();
  });
});
