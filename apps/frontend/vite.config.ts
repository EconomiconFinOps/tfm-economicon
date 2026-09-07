// `defineConfig` de "vitest/config" reexporta el de Vite con el campo `test`
// tipado: evita el pragma de referencia triple-slash sin perder los tipos de
// vite.config para `dev`/`build`/`preview` (JUP-095, grupo 2).
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"]
  }
});

