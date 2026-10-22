// Tema claro/oscuro: arranque según el sistema, elección explícita que prevalece
// y persiste, almacenamiento no disponible y alternancia sin recargar (JUP-112,
// requisitos "El tema oscuro deriva de la marca y es opcional" y "El usuario
// puede cambiar de tema desde el armazón").
// JUP-134: el botón ya no tiene el texto fijo «Tema oscuro» ni `aria-pressed`: su
// texto visible nombra el tema ACTIVO («Tema claro» / «Tema oscuro») y ese texto
// es su nombre accesible. El estado se comprueba por el texto y por la ausencia
// del atributo; el resto de casos (arranque, persistencia, degradación) no cambia.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeToggle } from "@/components/ThemeToggle";

const STORAGE_KEY = "economicon-theme";

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

describe("ThemeToggle", () => {
  it("arranca en claro cuando el sistema no prefiere oscuro y no hay elección guardada", () => {
    mockSystemTheme(false);
    render(<ThemeToggle />);

    expect(currentTheme()).toBeNull();
    // En claro el texto es «Tema claro» y el estado ya no se expresa con aria-pressed.
    const button = screen.getByRole("button", { name: "Tema claro" });
    expect(button.textContent?.trim()).toBe("Tema claro");
    expect(button.hasAttribute("aria-pressed")).toBe(false);
  });

  it("arranca en oscuro cuando el sistema lo prefiere y no hay elección guardada", () => {
    mockSystemTheme(true);
    render(<ThemeToggle />);

    expect(currentTheme()).toBe("dark");
    const button = screen.getByRole("button", { name: "Tema oscuro" });
    expect(button.textContent?.trim()).toBe("Tema oscuro");
    expect(button.hasAttribute("aria-pressed")).toBe(false);
  });

  it("una elección guardada prevalece sobre la preferencia del sistema", () => {
    mockSystemTheme(true);
    window.localStorage.setItem(STORAGE_KEY, "light");
    render(<ThemeToggle />);

    expect(currentTheme()).toBeNull();
  });

  it("ignora un valor guardado que no es un tema válido", () => {
    mockSystemTheme(false);
    window.localStorage.setItem(STORAGE_KEY, "sepia");
    render(<ThemeToggle />);

    expect(currentTheme()).toBeNull();
  });

  it("alterna sin recargar, indica el tema activo y recuerda la elección", async () => {
    mockSystemTheme(false);
    const user = userEvent.setup();
    render(<ThemeToggle />);
    const button = screen.getByRole("button", { name: "Tema claro" });

    await user.click(button);
    expect(currentTheme()).toBe("dark");
    // La misma referencia al botón sigue viva y su texto pasó a nombrar el tema nuevo.
    expect(button.textContent?.trim()).toBe("Tema oscuro");
    expect(screen.getByRole("button", { name: "Tema oscuro" })).toBe(button);
    expect(button.hasAttribute("aria-pressed")).toBe(false);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("dark");

    await user.click(button);
    expect(currentTheme()).toBeNull();
    expect(button.textContent?.trim()).toBe("Tema claro");
    expect(screen.getByRole("button", { name: "Tema claro" })).toBe(button);
    expect(button.hasAttribute("aria-pressed")).toBe(false);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("light");
  });

  it("una elección explícita clara se conserva al volver a montar con el sistema en oscuro", async () => {
    mockSystemTheme(true);
    const user = userEvent.setup();
    const first = render(<ThemeToggle />);
    // Con el sistema en oscuro el botón arranca como «Tema oscuro»; pulsarlo elige claro.
    await user.click(screen.getByRole("button", { name: "Tema oscuro" }));
    expect(currentTheme()).toBeNull();
    first.unmount();

    render(<ThemeToggle />);
    expect(currentTheme()).toBeNull();
    expect(screen.getByRole("button", { name: "Tema claro" })).toBeTruthy();
  });

  it("sin almacenamiento disponible sigue funcionando con la preferencia del sistema y alterna", async () => {
    mockSystemTheme(true);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    const user = userEvent.setup();
    render(<ThemeToggle />);

    expect(currentTheme()).toBe("dark");
    await user.click(screen.getByRole("button", { name: "Tema oscuro" }));
    expect(currentTheme()).toBeNull();
    expect(screen.getByRole("button", { name: "Tema claro" })).toBeTruthy();
  });

  it("si matchMedia lanza una excepción arranca en claro sin romper", () => {
    vi.stubGlobal("matchMedia", () => {
      throw new Error("matchMedia roto");
    });
    expect(() => render(<ThemeToggle />)).not.toThrow();
    expect(currentTheme()).toBeNull();
    expect(screen.getByRole("button", { name: "Tema claro" })).toBeTruthy();
  });

  it.each([
    ["claro", false, "Tema claro"],
    ["oscuro", true, "Tema oscuro"]
  ])("el nombre accesible del botón con el tema %s contiene su texto visible (etiqueta en el nombre)", (_tema, dark, texto) => {
    // Se cubren ambos temas: el nombre accesible debe coincidir con el texto visible en los dos estados.
    mockSystemTheme(dark);
    render(<ThemeToggle />);
    const button = screen.getByRole("button", { name: texto });

    expect(button.textContent?.trim()).toBe(texto);
    expect(button.getAttribute("aria-label")).toBeNull();
  });

  it.each([
    ["claro", false, "Tema claro"],
    ["oscuro", true, "Tema oscuro"]
  ])("el botón con el tema %s tiene un indicador de foco propio visible sobre la cabecera índigo", (_tema, dark, texto) => {
    mockSystemTheme(dark);
    render(<ThemeToggle />);

    expect(screen.getByRole("button", { name: texto }).className).toContain("focus-visible:outline-brand-foreground");
  });

  it("sin matchMedia en el navegador arranca en claro", () => {
    vi.stubGlobal("matchMedia", undefined);
    render(<ThemeToggle />);

    expect(currentTheme()).toBeNull();
    expect(screen.getByRole("button", { name: "Tema claro" })).toBeTruthy();
  });
});
