// `defineConfig` de "vitest/config" reexporta el de Vite con el campo `test`
// tipado: evita el pragma de referencia triple-slash sin perder los tipos de
// vite.config para `dev`/`build`/`preview` (JUP-095, grupo 2).
import path from "node:path";
import { configDefaults, defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  // Orden del array: react() primero, tailwindcss() despues -- mismo orden
  // que usa el origen. Tailwind v4 solo aporta un plugin de transformacion
  // de CSS, no compite con el de React por el pipeline de JSX (JUP-095,
  // grupo 3, decision de design.md sobre cablear el sistema de estilos).
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      // Alias que consumen los componentes de shadcn/ui copiados en el
      // grupo 4 (@/components/ui/..., @/lib/utils), convencion de ese
      // patron. Se declara aqui junto a `paths` en tsconfig.json (grupo 3,
      // decision 5 de design.md): declararlo solo en uno de los dos produce
      // el fallo de "compila pero no arranca", o el inverso.
      "@": path.resolve(__dirname, "./src")
    }
  },
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

