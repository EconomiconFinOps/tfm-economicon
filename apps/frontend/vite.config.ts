// `defineConfig` de "vitest/config" reexporta el de Vite con el campo `test`
// tipado: evita el pragma de referencia triple-slash sin perder los tipos de
// vite.config para `dev`/`build`/`preview` (JUP-095, grupo 2).
import { configDefaults, defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    // `test.exclude` reemplaza el array por defecto en vez de fusionarse con
    // el; se parte de `configDefaults.exclude` para no perder sus patrones
    // (node_modules, dist...) y se suma `.stryker-tmp`, la carpeta temporal
    // que deja el mutation testing (`.claude/harness/mutation.md`). Sin esta
    // exclusion, Vitest la recoge como archivos de test propios si queda en
    // disco, contaminando en silencio el conteo de la suite (detectado en
    // QA de la tarea 2.3, reproducible corriendo Stryker y relanzando test).
    exclude: [...configDefaults.exclude, "**/.stryker-tmp/**"]
  }
});

