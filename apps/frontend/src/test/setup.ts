// Extiende `expect` de Vitest con los matchers de accesibilidad/DOM de
// jest-dom (toBeInTheDocument, toHaveTextContent...). Se carga una vez por
// proceso de test vía `test.setupFiles` en vite.config.ts (JUP-095, grupo 2).
import "@testing-library/jest-dom/vitest";
