## 1. Preparación

- [x] 1.1 Crear `docs/planning/JUP-090-frontend-migration-baseline.md` con la cabecera de la línea
  base: JUP, enlace Trello, rama, **commit base** del inventario, y el alcance excluido
  (`node_modules`, `node_modules/.vite` y demás artefactos generados).

## 2. Inventario del destino (una tarea = un bloque = un commit)

- [x] 2.1 Inventariar `apps/frontend/src/**` (`App.jsx`, `main.jsx`, `components`, `hooks`, `layouts`,
  `pages`, `services`, `styles`) y clasificar cada archivo como `PRESERVAR` / `REEMPLAZAR` /
  `RECONCILIAR` con su justificación.
- [x] 2.2 Inventariar la configuración del paquete: `package.json` (nombre `@finops/frontend`,
  `type`, scripts, host/puerto 5173), `vite.config.js`, `eslint.config.js` e `index.html`; clasificar
  cada uno y anotar qué parte concreta debe sobrevivir a la fusión.
- [x] 2.3 Inventariar la integración de plataforma: `apps/frontend/Dockerfile`, servicio `frontend` de
  `docker-compose.yml` (puerto, `env_file`, dependencia de `backend`), `turbo.json`,
  `pnpm-workspace.yaml` y las variables `VITE_*` en uso; clasificar cada punto.
- [x] 2.4 Extraer de `apps/frontend/src/services/api.js` las llamadas HTTP reales (endpoint, método,
  headers `Authorization` y `X-Tenant-Id`) y contrastarlas con `apps/frontend/README.md`; volcar la
  tabla de contratos a la línea base.

## 3. Criterios de paridad y rollback

- [x] 3.1 Redactar el guion de paridad login → selección de tenant → dashboard: cada paso con acción,
  endpoint implicado y resultado observable, usando el seed `operator@example.com` / `secret`.
- [x] 3.2 Registrar en la línea base la regla de rollback: el scaffold actual no se borra hasta que la
  validación E2E de F5 pase, y qué se necesita para revertir.

## 4. Cierre y verificación

- [x] 4.1 Enlazar `docs/planning/JUP-090-frontend-migration-baseline.md` desde
  `docs/spikes/frontend-migration.md` y marcar como completada la tarjeta F1
  `inventariar-frontend-actual`.
- [x] 4.2 Verificar que ningún archivo no generado de `apps/frontend/**` queda sin etiqueta y que cada
  criterio de paridad nombra endpoint y resultado observable.
- [x] 4.3 Registrar en `review.md` y en `openspec/findings/backlog.md` (ID `RF-090-<secuencia>`) toda
  divergencia entre README, capa API y contratos del backend, sin resolverla aquí.
- [x] 4.4 Ejecutar `corepack pnpm openspec:validate` y
  `corepack pnpm jup:check -- --change jup-090-inventory-current-frontend`; registrar el resultado en
  `review.md` junto con la excepción doc-only del harness TDD (sin tester/coder/mutación).
