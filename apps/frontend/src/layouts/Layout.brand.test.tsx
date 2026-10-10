// Marca de Economicon en el armazón (JUP-112, requisitos "El armazón presenta
// la marca de Economicon" y "El monograma E identifica la aplicación").
import { readFileSync } from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { describe, expect, it, vi } from "vitest";
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

  it("el script de arranque y el hook eligen el mismo tema con la misma matriz de entradas", async () => {
    const script = INDEX_HTML.match(/<script>([\s\S]*?)<\/script>/)?.[1] ?? "";
    const { useTheme } = await import("@/hooks/useTheme");
    const { renderHook } = await import("@testing-library/react");
    const matrix: Array<{ saved: string | null | "throws"; system: "dark" | "light" | "throws" | "absent" }> = [];
    for (const saved of [null, "light", "dark", "sepia", "throws"] as const) {
      for (const system of ["dark", "light", "throws", "absent"] as const) matrix.push({ saved, system });
    }

    for (const { saved, system } of matrix) {
      const stubs = () => ({
        getItem: () => {
          if (saved === "throws") throw new Error("blocked");
          return saved;
        }
      });
      const matchMedia =
        system === "absent"
          ? undefined
          : () => {
              if (system === "throws") throw new Error("broken");
              return { matches: system === "dark" };
            };

      let scriptTheme = "light";
      vm.runInNewContext(script, {
        window: { localStorage: stubs(), matchMedia },
        document: { documentElement: { setAttribute: (_name: string, value: string) => (scriptTheme = value) } }
      });

      vi.stubGlobal("matchMedia", matchMedia);
      const storage = vi.spyOn(Storage.prototype, "getItem").mockImplementation(stubs().getItem);
      document.documentElement.removeAttribute("data-theme");
      const { result, unmount } = renderHook(() => useTheme());
      unmount();
      storage.mockRestore();
      vi.unstubAllGlobals();

      expect(result.current.theme, JSON.stringify({ saved, system })).toBe(scriptTheme);
    }
  });

  it("los dos logotipos de marca están empaquetados con la aplicación sin modificar", () => {
    const primary = readFileSync(path.join(FRONTEND_DIR, "src", "assets", "brand", "economicon-primary.png"));
    const inverse = readFileSync(path.join(FRONTEND_DIR, "src", "assets", "brand", "economicon-inverse.png"));
    expect(primary.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
    expect(inverse.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
    expect(primary.equals(inverse)).toBe(false);
  });
});
