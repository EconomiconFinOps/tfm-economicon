import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-pressed={isDark}
      aria-label="Tema oscuro"
      title={isDark ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
      className="flex items-center gap-2 rounded-lg border border-brand-foreground/30 px-3 py-2 text-sm text-brand-foreground hover:bg-brand-foreground/10"
    >
      {isDark ? <Moon className="size-4" aria-hidden="true" /> : <Sun className="size-4" aria-hidden="true" />}
      <span>{isDark ? "Oscuro" : "Claro"}</span>
    </button>
  );
}
