import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  // El texto muestra el tema activo y cambia con el estado, así que el nombre accesible no es
  // estable: por eso no es un botón de alternancia con aria-pressed (un lector diría "Tema claro,
  // no pulsado" y luego "Tema oscuro, pulsado"). El title describe la acción al pulsar y actúa como
  // descripción accesible, no como nombre, porque el botón ya tiene contenido de texto (sin aria-label).
  return (
    <button
      type="button"
      onClick={toggleTheme}
      title={isDark ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
      className="flex items-center gap-2 rounded-lg border border-brand-foreground/30 px-3 py-2 text-sm text-brand-foreground hover:bg-brand-foreground/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-foreground"
    >
      {isDark ? <Moon className="size-4" aria-hidden="true" /> : <Sun className="size-4" aria-hidden="true" />}
      <span>{isDark ? "Tema oscuro" : "Tema claro"}</span>
    </button>
  );
}
