// Marca de Economicon en el armazón (JUP-112, requisitos "El armazón presenta
// la marca de Economicon" y "El monograma E identifica la aplicación").
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { Layout } from "./Layout";

const FRONTEND_DIR = path.resolve(__dirname, "..", "..");
const INDEX_HTML = readFileSync(path.join(FRONTEND_DIR, "index.html"), "utf-8");

describe("Layout - marca", () => {
  it("la cabecera muestra Economicon y no la identidad del prototipo", () => {
    const { container } = render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>
    );

    expect(screen.getByText("Economicon")).toBeTruthy();
    expect(container.querySelector("header img")).not.toBeNull();
    expect(container.textContent).not.toMatch(/FinOps AI Platform|FinOps Control Tower/);
  });

  it("el navegador recibe el título y el favicon de marca", () => {
    expect(INDEX_HTML).toMatch(/<title>[^<]*Economicon[^<]*<\/title>/);
    expect(INDEX_HTML).not.toMatch(/FinOps Control Tower/);
    expect(INDEX_HTML).toMatch(/<link[^>]+rel="icon"[^>]+href="\/favicon\.png"/);
  });

  it("el script de arranque fija el tema antes del primer pintado, con el almacenamiento protegido", () => {
    const script = INDEX_HTML.match(/<script>([\s\S]*?)<\/script>/)?.[1] ?? "";
    expect(script).toContain("prefers-color-scheme: dark");
    expect(script).toContain("data-theme");
    expect(script).toMatch(/try\s*{[\s\S]*localStorage[\s\S]*}\s*catch/);
  });

  it("los dos logotipos de marca están empaquetados con la aplicación sin modificar", () => {
    const primary = readFileSync(path.join(FRONTEND_DIR, "src", "assets", "brand", "economicon-primary.png"));
    const inverse = readFileSync(path.join(FRONTEND_DIR, "src", "assets", "brand", "economicon-inverse.png"));
    expect(primary.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
    expect(inverse.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
    expect(primary.equals(inverse)).toBe(false);
  });
});
