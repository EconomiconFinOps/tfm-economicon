# Review: jup-090-inventory-current-frontend

## Result

Accepted

## Scope Reviewed

- `apps/frontend/**` (excepto `node_modules` y cachés de build), en solo lectura.
- `docker-compose.yml` (servicio `frontend`), `turbo.json`, `pnpm-workspace.yaml`.
- `docs/spikes/frontend-migration.md` (corrección de un hecho verificado).
- `openspec/changes/jup-090-inventory-current-frontend/{proposal,design,specs,tasks}.md`.
- Entregable: `docs/planning/JUP-090-frontend-migration-baseline.md`.

## Checklist

- [x] Cada archivo no generado de `apps/frontend/**` tiene una clasificación PRESERVAR/REEMPLAZAR/RECONCILIAR con evidencia de línea.
- [x] El guion de paridad login → tenant → dashboard nombra endpoint y resultado observable en cada paso.
- [x] La regla de rollback queda registrada en la línea base.
- [x] Toda divergencia encontrada (README vs. código vs. spike) queda registrada como finding, no resuelta en esta HU.
- [x] Checks del carril ejecutados y en verde (tarea 4.4).
- [x] Tasks.md marcado 11/11.

ADR no aplicable. Esta HU es inventario/documentación sobre el estado ya existente del destino; no
introduce ninguna decisión de arquitectura nueva. La adopción de TypeScript (con su propio ADR)
corresponde a la tarjeta `jup-0xx-adr-adopcion-typescript` de F1.

## Validation

```txt
corepack pnpm openspec:validate -> PASS: 17 items validated strictly (3 specs, 14 changes)
corepack pnpm jup:check -- --change jup-090-inventory-current-frontend -> PASS: enlazado con Trello y completo
test / lint / build -> N/A (doc-only, sin código de producto; harness TDD omitido: sin tester/coder/mutación)
```

## Review Findings

| ID | Tipo | Severidad | Scope | Descripcion | Accion | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-090-001 | Platform/build reproducibility | Medium | Out of scope | `apps/frontend/Dockerfile` instala con `pnpm install --no-frozen-lockfile` sin copiar `pnpm-lock.yaml` ni `pnpm-workspace.yaml` de la raíz: construye fuera del lockfile reproducible que exige el spike. | Resolver en la tarjeta F4 `verificar-docker-compose` | Open |
| RF-090-002 | Documentation accuracy | Low | Out of scope | El spike afirmaba `env_file: .env` en el servicio `frontend` de `docker-compose.yml`; esa clave no existe — `VITE_API_BASE_URL` viaja como `environment:` inline. | Corregido directamente en `docs/spikes/frontend-migration.md` dentro de esta HU | Fixed |
| RF-090-003 | API contract drift | Medium | Out of scope | `GET /me` (`fetchProfile`, `api.js:31`) está documentado en el README y contratado con el backend, pero el frontend nunca lo invoca: `App.jsx` toma `user` del payload de `POST /auth/login`. | Decidir en la tarjeta F3 `reconciliar-capa-api` si se conecta o se retira | Open |

## Risks / Follow-Ups

- F4 (`verificar-docker-compose`) debe resolver `RF-090-001` antes de dar por buena la imagen Docker
  con el build TS.
- F3 (`reconciliar-capa-api`) debe decidir `RF-090-003` al portar `services/api.js` a TS.
- Las páginas `IngestPage.jsx` y `ConversationsPage.jsx` quedan marcadas RECONCILIAR sin confirmar aún
  qué pantalla del origen recibe su lógica; a confirmar en F3 (`portar-codigo-fuente`) contra el
  inventario de Economicon de JUP-083.
