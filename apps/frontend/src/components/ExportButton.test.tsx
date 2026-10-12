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

  it("solo ofrece los formatos pedidos", () => {
    render(<ExportButton data={[{ columna: "valor" }]} filename="prueba" formats={["csv"]} />);
    fireEvent.click(screen.getByText("Exportar Resultados"));
    expect(screen.getByText("Exportar CSV")).toBeInTheDocument();
    expect(screen.queryByText("Exportar PDF")).toBeNull();
  });
});

describe("ExportButton con texto escrito por usuarios", () => {
  const hostile = { Servicio: "<img src=x onerror=alert(1)>", Motivo: "=HYPERLINK(\"http://x\")", Dias: 0, Nota: "+1", Menos: "-2+3", Arroba: "@SUM(A1)", Importe: "-300.00" };

  it("escapa el HTML del informe PDF", () => {
    let written = "";
    const fakeWindow = { document: { write: (html: string) => { written = html; }, close: () => undefined }, print: () => undefined };
    const original = window.open;
    window.open = (() => fakeWindow) as unknown as typeof window.open;
    try {
      render(<ExportButton data={[hostile]} filename={"<b>informe</b>"} />);
      fireEvent.click(screen.getByText("Exportar Resultados"));
      fireEvent.click(screen.getByText("Exportar PDF"));
    } finally {
      window.open = original;
    }
    expect(written).not.toContain("<img");
    expect(written).not.toContain("<b>informe</b>");
    expect(written).toContain("&lt;img src=x onerror=alert(1)&gt;");
    expect(written).toContain("<td>0</td>");
  });

  it("neutraliza fórmulas y conserva los ceros en el CSV", async () => {
    let blob: Blob | undefined;
    const originalCreate = URL.createObjectURL;
    URL.createObjectURL = ((value: Blob) => { blob = value; return "blob:x"; }) as typeof URL.createObjectURL;
    try {
      render(<ExportButton data={[hostile]} filename="informe" />);
      fireEvent.click(screen.getByText("Exportar Resultados"));
      fireEvent.click(screen.getByText("Exportar CSV"));
    } finally {
      URL.createObjectURL = originalCreate;
    }
    const text = await (blob as Blob).text();
    const [, row] = text.split("\n");
    expect(row).toContain("\"'=HYPERLINK(\\\"http://x\\\")\"");
    expect(row).toContain("\"'+1\"");
    expect(row).toContain("\"'-2+3\"");
    expect(row).toContain("\"-300.00\"");
    expect(row).toContain("\"'@SUM(A1)\"");
    expect(row).toContain(",\"0\",");
  });
});
