// Requisitos de `frontend-brand-identity` que no tenían un test que fallara al
// romperlos (revisión de la PR #112): logotipo que corresponde a cada fondo,
// conmutador y foco en la cabecera, tooltips, coral fuera de los estados,
// base de la paleta oscura, fuentes empaquetadas, favicon, encabezado de nivel 1
// y anchura de las pestañas.
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { render, within } from "@testing-library/react";
import { Outlet, RouterProvider, createMemoryRouter } from "react-router";
import { Layout } from "@/layouts/Layout";
import { chartTooltipItemStyle } from "@/components/chartTheme";
import logoInverse from "@/assets/brand/economicon-inverse.png";

const FRONTEND_DIR = path.resolve(__dirname, "..", "..");
const read = (...parts: string[]) => readFileSync(path.join(FRONTEND_DIR, ...parts), "utf-8");

function SessionContext() {
  return (
    <Outlet
      context={{
        tenants: [{ id: "t1", name: "Acme" }],
        activeTenantId: "t1",
        onTenantChange: () => {},
        user: { full_name: "Ada Lovelace", email: "ada@example.com" },
        onLogout: () => {}
      }}
    />
  );
}

function renderLayout(): HTMLElement {
  const router = createMemoryRouter([{ path: "/", element: <SessionContext />, children: [{ index: true, Component: Layout }] }]);
  return render(<RouterProvider router={router} />).container;
}

const renderHeader = () => renderLayout().querySelector("header") as HTMLElement;

describe("armazón de marca", () => {
  it("la cabecera índigo usa el monograma inverso", () => {
    expect(renderHeader().querySelector("img")?.getAttribute("src")).toBe(logoInverse);
  });

  it("la cabecera ofrece el conmutador de tema", () => {
    expect(within(renderHeader()).getByRole("button", { name: "Tema oscuro" })).toBeTruthy();
  });

  it("cada control de la cabecera tiene un foco propio visible sobre el índigo", () => {
    const controls = [...renderHeader().querySelectorAll("button, select")];
    expect(controls).toHaveLength(3);
    for (const control of controls) expect(control.className).toContain("focus-visible:outline-brand-foreground");
  });

  it("el nombre de la marca es el encabezado de nivel 1 del armazón", () => {
    const headings = [...renderLayout().querySelectorAll("h1")];
    expect(headings.map((heading) => heading.textContent)).toEqual(["Economicon"]);
  });

  it("las pestañas de navegación caben a 1280 px con la barra de desplazamiento vertical", () => {
    // jsdom no mide el diseño: con 9 pestañas la fila medía 1242 px de 1265 en Chrome y con px-3 pasaba a 1314; se conserva el relleno compacto para que reactivar pantallas ocultas no desborde.
    const tabs = [...renderLayout().querySelectorAll("nav a")];
    expect(tabs).toHaveLength(5);
    for (const tab of tabs) {
      expect(tab.className).toContain("px-2");
      expect(tab.className).not.toContain("px-3");
    }
  });

  it("la pantalla de acceso muestra el monograma primario en claro y el inverso en oscuro", () => {
    const login = read("src", "pages", "LoginPage.tsx");
    expect(login).toMatch(/<img src=\{logoPrimary\}[^>]*\bdark:hidden\b/);
    expect(login).toMatch(/<img src=\{logoInverse\}[^>]*\bhidden\b[^>]*\bdark:block\b/);
  });

  it("el favicon declarado existe y es un PNG", () => {
    const favicon = path.join(FRONTEND_DIR, "public", "favicon.png");
    expect(existsSync(favicon)).toBe(true);
    expect(readFileSync(favicon).subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
  });
});

describe("tema de marca", () => {
  const theme = read("src", "styles", "theme.css");
  const dark = theme.slice(theme.indexOf('[data-theme="dark"] {'), theme.indexOf("@theme inline"));

  it("la paleta oscura usa el casi negro como fondo y el blanco roto como texto", () => {
    expect(dark).toMatch(/--background:\s*#14121f;/i);
    expect(dark).toMatch(/--foreground:\s*#fafafc;/i);
  });

  it("las fuentes de marca se empaquetan y los titulares usan Space Grotesk", () => {
    const main = read("src", "main.tsx");
    expect(main).toContain('import "@fontsource-variable/inter";');
    expect(main).toContain('import "@fontsource-variable/space-grotesk";');
    expect(theme).toMatch(/--font-heading:\s*"Space Grotesk Variable"/);
    expect(theme).toMatch(/h1,\s*h2,\s*h3,\s*h4\s*\{[^}]*font-family:\s*var\(--font-heading\)/);
  });

  it("los ítems del tooltip usan el color de texto del tema, no el de la serie", () => {
    expect(chartTooltipItemStyle.color).toBe("var(--foreground)");
  });
});

describe("el coral no indica estados", () => {
  // Únicas pantallas que muestran ahorro o insights.
  const SAVING_SCREENS = ["ExecutiveCutDashboard.tsx", "RecommendationsPanel.tsx"];
  const CORAL = /(?<![\w-])(?:bg|text|border|ring|outline|from|to|via|fill|stroke)-saving(?![\w])|var\(\s*--(?:color-)?saving/;

  it("ningún otro componente, layout o pantalla pinta con `saving`", () => {
    const offenders: string[] = [];
    for (const directory of ["components", "layouts", "pages"]) {
      for (const name of readdirSync(path.join(FRONTEND_DIR, "src", directory))) {
        if (!/\.tsx$/.test(name) || /\.test\.tsx$/.test(name) || SAVING_SCREENS.includes(name)) continue;
        if (CORAL.test(read("src", directory, name))) offenders.push(`${directory}/${name}`);
      }
    }
    expect(offenders).toEqual([]);
  });
});
