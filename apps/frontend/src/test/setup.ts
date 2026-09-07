// Extiende `expect` de Vitest con los matchers de accesibilidad/DOM de
// jest-dom (toBeInTheDocument, toHaveTextContent...). Se carga una vez por
// proceso de test vía `test.setupFiles` en vite.config.ts (JUP-095, grupo 2).
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Testing Library registra su limpieza automática (desmontar cada árbol
// renderizado tras cada test) enganchándose al `afterEach` global si existe.
// Este proyecto usa `globals: false` en vite.config.ts (importa
// describe/it/expect explícitos en cada test, grupo 2): sin un `afterEach`
// global, ese auto-cleanup nunca se registra y el DOM montado por un test
// se filtra al siguiente `it()` del mismo archivo (detectado en el grupo 4:
// dos tests de Separator en el mismo describe se contaminaban entre sí).
// Registrarlo aquí, explícito, es el patrón oficial documentado por
// Testing Library para proyectos sin `globals: true`.
afterEach(cleanup);
