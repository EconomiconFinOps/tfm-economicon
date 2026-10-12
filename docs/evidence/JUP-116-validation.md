# Evidencia JUP-116 — Ocultar del MVP las pantallas de maqueta

- Fecha: 2026-10-12.
- Trello: https://trello.com/c/IPB2nGxa
- Rama: `feat/JUP-116-hide-mockup-screens`, desde `origin/develop` en `3c6517b`.
- OpenSpec: `openspec/changes/jup-116-hide-mockup-screens/` (propuesta, spec delta de `frontend-navigation-shell`, diseño, tareas y `review.md`).
- Estado: evidencia técnica de esta sesión, tras dos pasadas de revisión adversarial. No sustituye la validación funcional de quien tenga ese rol en Trello.

## Qué se comprobó y cómo

| Comprobación | Resultado |
| --- | --- |
| `corepack pnpm test` en `apps/frontend` con `--maxWorkers=2` | 64 archivos y 801 pruebas pasan |
| Misma suite sin limitar el paralelismo, con el equipo al 100 % de CPU por el stack Docker | fallos por tiempo (5 s) en pruebas de formularios; los 4 archivos afectados pasan aislados (26 de 26) |
| `lint`, `typecheck` y `build` en `apps/frontend` | sin errores |
| `corepack pnpm openspec:validate`, `jup:check`, `jup:cleanup:check`, `synthetic-demo:test` | correctos (66 de 66 y 40 pruebas) |
| Pruebas nuevas en rojo antes de implementar | 8 de 12 fallaron por la razón esperada |
| Mutantes sobre el código y sobre el guardián de demostración | 6 de 6 detectados |
| Comprobación en navegador real | 16 comprobaciones PASS (ver abajo) |

## Comprobación en navegador

Edge con Playwright (`playwright-core`, fuera del repositorio) sobre el stack Docker del proyecto `tfm-economicon`, con Vite arrancado desde el worktree de esta rama en el puerto 5173 y los datos sintéticos de la demo en Growth Ops y Core Finance. Ventana de 1280 px.

| Comprobación | Resultado |
| --- | --- |
| El menú tiene cinco entradas en orden: Coste Global, Anomalías, Ingestions, Assistant, Salud del sistema | PASS |
| Sin separador en el menú | PASS |
| Las pestañas caben a 1280 px sin desplazamiento (`scrollWidth` 1280, `clientWidth` 1280) | PASS |
| Cargar directamente `/operational`, `/cuts`, `/recommendations` y una dirección inexistente lleva a `/` con el cliente intacto y sin error del enrutador | PASS (4) |
| Desde la app, ir a `/cuts` redirige a `/` y Atrás vuelve a `/anomalies` | PASS |
| `/overview-legacy` se abre por su dirección y no hay enlace «Overview» en el menú | PASS |
| Cada entrada del menú presenta su pantalla | PASS (5) |
| Coste Global sigue mostrando los totales reales | PASS |
| Sin errores de página durante el recorrido | PASS |

Las capturas y el resultado del script quedaron en la carpeta temporal de la sesión y no se versionan.

## Evidencia por requisito de la spec

| Requisito del delta | Dónde se comprueba |
| --- | --- |
| Una dirección no publicada lleva a la pantalla inicial | `routes.hidden-screens.test.tsx` (direcciones ocultas, inexistente, hostiles, ámbito conservado, Atrás) y el navegador |
| La vista heredada del resumen se alcanza solo por su dirección | `routes.hidden-screens.test.tsx` y el navegador |
| El menú no enlaza pantallas ocultas ni de demostración sin aviso | `Layout.test.tsx`, el guardián de demostración de `routes.hidden-screens.test.tsx` y el navegador |
| Las pantallas de demostración no tienen dirección | `routes.hidden-screens.test.tsx` |
| Ocultar no cambia las pantallas con datos reales | las pruebas existentes de cada pantalla, sin cambios, y el navegador |
| Una pantalla de demostración rotulada puede seguir publicada | el guardián de demostración y `AnomaliesPanel.test.tsx` |

## No validado

- El envío de mensajes en `/assistant`: el stack de IA no está levantado y el asistente devuelve 503 al enviar.
- El tema oscuro.
- La suite completa del frontend sin limitar el paralelismo, mientras el equipo está saturado; no se ha comparado con `develop` sin estos cambios.
- La validación funcional contra los criterios de la tarjeta por la persona con el rol de validación en Trello.
