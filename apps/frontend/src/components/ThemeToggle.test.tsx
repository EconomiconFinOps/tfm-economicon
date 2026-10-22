// Etiqueta del selector de tema (JUP-134, requisito "El usuario puede cambiar de
// tema desde el armazón"): el texto visible nombra el tema ACTIVO («Tema claro» o
// «Tema oscuro»), el nombre accesible es exactamente ese texto (sin aria-label ni
// aria-pressed) y el `title` describe la acción que ocurre al pulsar. La lógica de
// useTheme (atributo data-theme, persistencia) no cambia y se fija aquí solo como
// guarda de no regresión.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeToggle } from "@/components/ThemeToggle";

const STORAGE_KEY = "economicon-theme";

// Simula la preferencia del sistema: solo las consultas "dark" devuelven `matches`.
function mockSystemTheme(dark: boolean) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches: dark && query.includes("dark"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn()
    }))
  );
}

const currentTheme = () => document.documentElement.getAttribute("data-theme");

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("ThemeToggle: texto, icono y título según el tema activo", () => {
  it("con el tema claro activo muestra «Tema claro», el icono del sol y el título «Cambiar a tema oscuro»", () => {
    mockSystemTheme(false);
    const { container } = render(<ThemeToggle />);

    // El texto debe nombrar el tema en uso, no una acción ni un valor fijo.
    const button = screen.getByRole("button", { name: "Tema claro" });
    expect(button.textContent?.trim()).toBe("Tema claro");
    expect(button.getAttribute("title")).toBe("Cambiar a tema oscuro");
    expect(container.querySelector("svg.lucide-sun")).not.toBeNull();
    expect(container.querySelector("svg.lucide-moon")).toBeNull();
  });

  it("con el tema oscuro activo (por el sistema) muestra «Tema oscuro», el icono de la luna y el título «Cambiar a tema claro»", () => {
    mockSystemTheme(true);
    const { container } = render(<ThemeToggle />);

    const button = screen.getByRole("button", { name: "Tema oscuro" });
    expect(button.textContent?.trim()).toBe("Tema oscuro");
    expect(button.getAttribute("title")).toBe("Cambiar a tema claro");
    expect(container.querySelector("svg.lucide-moon")).not.toBeNull();
    expect(container.querySelector("svg.lucide-sun")).toBeNull();
  });

  it("con el tema claro activo no existe ningún botón llamado «Tema oscuro»", () => {
    // Escenario "no muestra el texto «Tema oscuro»": evita que el texto fijo antiguo siga presente.
    mockSystemTheme(false);
    render(<ThemeToggle />);

    expect(screen.queryByRole("button", { name: "Tema oscuro" })).toBeNull();
    expect(screen.queryByText("Tema oscuro")).toBeNull();
  });

  it("con el tema oscuro activo no existe ningún botón llamado «Tema claro»", () => {
    mockSystemTheme(true);
    render(<ThemeToggle />);

    expect(screen.queryByRole("button", { name: "Tema claro" })).toBeNull();
    expect(screen.queryByText("Tema claro")).toBeNull();
  });
});

describe("ThemeToggle: semántica accesible", () => {
  it.each([
    ["claro", false, "Tema claro"],
    ["oscuro", true, "Tema oscuro"]
  ])("con el tema %s el botón no tiene aria-pressed ni aria-label y su nombre accesible es su texto visible", (_tema, dark, texto) => {
    mockSystemTheme(dark);
    render(<ThemeToggle />);
    const button = screen.getByRole("button");

    // `null` (atributo ausente) y no "false": ya no es un botón de alternancia, porque el nombre cambia con el estado.
    expect(button.hasAttribute("aria-pressed")).toBe(false);
    expect(button.hasAttribute("aria-label")).toBe(false);
    expect(button.textContent?.trim()).toBe(texto);
    // Nombre accesible exacto (no una coincidencia parcial): getByRole con cadena exige igualdad.
    expect(screen.getByRole("button", { name: texto })).toBe(button);
  });

  it.each([
    ["claro", false, "svg.lucide-sun"],
    ["oscuro", true, "svg.lucide-moon"]
  ])("el icono del tema %s está oculto a las tecnologías de apoyo", (_tema, dark, selector) => {
    mockSystemTheme(dark);
    const { container } = render(<ThemeToggle />);

    // El icono es decorativo: el texto ya dice el estado, así que no debe duplicarse en el nombre.
    expect(container.querySelector(selector)?.getAttribute("aria-hidden")).toBe("true");
  });
});

describe("ThemeToggle: el texto sigue al tema", () => {
  it("al alternar ida y vuelta el texto, el icono y el título cambian sin recargar", async () => {
    mockSystemTheme(false);
    const user = userEvent.setup();
    const { container } = render(<ThemeToggle />);

    await user.click(screen.getByRole("button", { name: "Tema claro" }));
    // Tras el clic el nombre cambia: se vuelve a buscar el botón por el nombre del nuevo estado.
    const dark = screen.getByRole("button", { name: "Tema oscuro" });
    expect(currentTheme()).toBe("dark");
    expect(dark.getAttribute("title")).toBe("Cambiar a tema claro");
    expect(dark.hasAttribute("aria-pressed")).toBe(false);
    expect(container.querySelector("svg.lucide-moon")).not.toBeNull();
    expect(screen.queryByRole("button", { name: "Tema claro" })).toBeNull();

    await user.click(dark);
    const light = screen.getByRole("button", { name: "Tema claro" });
    expect(currentTheme()).toBeNull();
    expect(light.getAttribute("title")).toBe("Cambiar a tema oscuro");
    expect(container.querySelector("svg.lucide-sun")).not.toBeNull();
    expect(screen.queryByRole("button", { name: "Tema oscuro" })).toBeNull();
  });

  it("alternar desde oscuro (sistema oscuro) pasa a «Tema claro» y vuelve a «Tema oscuro»", async () => {
    mockSystemTheme(true);
    const user = userEvent.setup();
    render(<ThemeToggle />);

    await user.click(screen.getByRole("button", { name: "Tema oscuro" }));
    await user.click(screen.getByRole("button", { name: "Tema claro" }));
    expect(screen.getByRole("button", { name: "Tema oscuro" })).toBeTruthy();
  });

  it("una elección oscura guardada fija «Tema oscuro» al volver a montar aunque el sistema sea claro", async () => {
    mockSystemTheme(false);
    const user = userEvent.setup();
    const first = render(<ThemeToggle />);
    await user.click(screen.getByRole("button", { name: "Tema claro" }));
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("dark");
    first.unmount();

    // Equivale a recargar la página: el texto lo decide la elección guardada, no el sistema.
    render(<ThemeToggle />);
    expect(screen.getByRole("button", { name: "Tema oscuro" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Tema claro" })).toBeNull();
  });

  it("una elección clara guardada fija «Tema claro» al volver a montar aunque el sistema sea oscuro", async () => {
    mockSystemTheme(true);
    window.localStorage.setItem(STORAGE_KEY, "light");
    render(<ThemeToggle />);

    expect(screen.getByRole("button", { name: "Tema claro" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Tema oscuro" })).toBeNull();
    expect(currentTheme()).toBeNull();
  });

  it("un valor guardado inválido se ignora y el texto sigue la preferencia del sistema", () => {
    mockSystemTheme(true);
    window.localStorage.setItem(STORAGE_KEY, "sepia");
    render(<ThemeToggle />);

    expect(screen.getByRole("button", { name: "Tema oscuro" })).toBeTruthy();
  });
});

describe("ThemeToggle: entornos degradados arrancan en claro", () => {
  it("con el almacenamiento bloqueado y el sistema claro muestra «Tema claro» y alterna a «Tema oscuro»", async () => {
    // Regresión: sin localStorage el texto debe seguir el estado en memoria, no quedar fijo.
    mockSystemTheme(false);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    const user = userEvent.setup();
    render(<ThemeToggle />);

    await user.click(screen.getByRole("button", { name: "Tema claro" }));
    expect(screen.getByRole("button", { name: "Tema oscuro" })).toBeTruthy();
    expect(currentTheme()).toBe("dark");
  });

  it("con el almacenamiento bloqueado y el sistema oscuro muestra «Tema oscuro»", () => {
    mockSystemTheme(true);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    render(<ThemeToggle />);

    expect(screen.getByRole("button", { name: "Tema oscuro" })).toBeTruthy();
  });

  it("si matchMedia lanza una excepción arranca en claro con el texto «Tema claro»", () => {
    vi.stubGlobal("matchMedia", () => {
      throw new Error("matchMedia roto");
    });
    render(<ThemeToggle />);

    expect(screen.getByRole("button", { name: "Tema claro" })).toBeTruthy();
    expect(currentTheme()).toBeNull();
  });

  it("sin matchMedia en el navegador arranca en claro con el texto «Tema claro»", () => {
    vi.stubGlobal("matchMedia", undefined);
    render(<ThemeToggle />);

    expect(screen.getByRole("button", { name: "Tema claro" })).toBeTruthy();
    expect(currentTheme()).toBeNull();
  });
});

describe("ThemeToggle: la lógica de useTheme no cambia", () => {
  it("data-theme=dark solo existe en oscuro y la elección se persiste en cada alternancia", async () => {
    // Guarda de no regresión: este caso ya pasa antes del cambio y debe seguir pasando.
    mockSystemTheme(false);
    const user = userEvent.setup();
    render(<ThemeToggle />);
    expect(currentTheme()).toBeNull();

    await user.click(screen.getByRole("button"));
    expect(currentTheme()).toBe("dark");
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("dark");

    await user.click(screen.getByRole("button"));
    expect(currentTheme()).toBeNull();
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("light");
  });
});
