// Tema claro/oscuro: arranque según el sistema, elección explícita que prevalece
// y persiste, almacenamiento no disponible y alternancia sin recargar (JUP-112,
// requisitos "El tema oscuro deriva de la marca y es opcional" y "El usuario
// puede cambiar de tema desde el armazón").
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
    expect(screen.getByRole("button", { name: "Tema oscuro" }).getAttribute("aria-pressed")).toBe("false");
  });

  it("arranca en oscuro cuando el sistema lo prefiere y no hay elección guardada", () => {
    mockSystemTheme(true);
    render(<ThemeToggle />);

    expect(currentTheme()).toBe("dark");
    expect(screen.getByRole("button", { name: "Tema oscuro" }).getAttribute("aria-pressed")).toBe("true");
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
    const button = screen.getByRole("button", { name: "Tema oscuro" });

    await user.click(button);
    expect(currentTheme()).toBe("dark");
    expect(button.getAttribute("aria-pressed")).toBe("true");
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("dark");

    await user.click(button);
    expect(currentTheme()).toBeNull();
    expect(button.getAttribute("aria-pressed")).toBe("false");
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("light");
  });

  it("una elección explícita clara se conserva al volver a montar con el sistema en oscuro", async () => {
    mockSystemTheme(true);
    const user = userEvent.setup();
    const first = render(<ThemeToggle />);
    await user.click(screen.getByRole("button", { name: "Tema oscuro" }));
    expect(currentTheme()).toBeNull();
    first.unmount();

    render(<ThemeToggle />);
    expect(currentTheme()).toBeNull();
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
  });

  it("sin matchMedia en el navegador arranca en claro", () => {
    vi.stubGlobal("matchMedia", undefined);
    render(<ThemeToggle />);

    expect(currentTheme()).toBeNull();
  });
});
