JUP: JUP-090
Trello: https://trello.com/c/DtlNd0u0/82-jup-090-inventariar-frontend-actual

## Why

La épica *Migrar frontend del repositorio Economicon* sustituye por completo `apps/frontend` siguiendo
el spike [docs/spikes/frontend-migration.md](../../../../docs/spikes/frontend-migration.md). JUP-083 ya
inventarió el **origen** (Economicon) y confirmó un hecho que agrava el riesgo: el origen es un
dashboard estático **sin backend, sin auth y sin capa de datos**, así que todo el valor funcional del
frontend actual —capa API centralizada, sesión, tenant activo, TanStack Query— solo existe en el
**destino** y se perdería si se sobrescribe a ciegas.

Nadie ha inventariado el destino a nivel de archivo. Sin una lista escrita de qué se preserva y qué
se reemplaza, y sin criterios verificables de paridad, las tarjetas de tooling (F2) y de porte de
código (F3) decidirían caso a caso, con riesgo de romper el pegamento del monorepo (nombre de
paquete, scripts, puerto 5173, Docker, turbo, workspace pnpm) y de perder el recorrido
login → tenant → dashboard.

## What Changes

- Crear `docs/planning/JUP-090-frontend-migration-baseline.md` como **línea base** de la épica, con
  tres bloques:
  - **Qué se preserva del destino**, con evidencia por archivo: nombre `@finops/frontend`, scripts
    del monorepo, host/puerto `5173`, `Dockerfile`, servicio `frontend` de `docker-compose.yml`,
    `VITE_API_BASE_URL`, el patrón de capa API única, pipeline turbo y pertenencia al workspace pnpm.
  - **Clasificación archivo a archivo** de `apps/frontend/**` en `PRESERVAR` / `REEMPLAZAR` /
    `RECONCILIAR`, alineada con la tabla "Manejo de conflictos con archivos existentes" del spike.
  - **Criterios de aceptación de paridad funcional** del recorrido login → selección de tenant →
    dashboard, expresados como pasos verificables contra los contratos reales del backend
    (`POST /auth/login`, `GET /me`, `GET /tenants`, `GET /billing/summary`, `POST /jobs/ingest`,
    `/assistant/conversations…`) y el seed local `operator@example.com` / `secret`.
- Registrar la **regla de rollback**: el scaffold actual no se borra hasta que la validación E2E de
  F5 pase.
- Enlazar la línea base desde el spike para que las tarjetas F2–F5 la consuman como fuente única.
- Registrar como finding cualquier hueco detectado entre la UI del origen y los contratos del
  backend, sin resolverlo aquí.

Sin código de producto, sin dependencias nuevas, sin adopción de TypeScript: eso corresponde a
tarjetas posteriores de la épica.

## Capabilities

### New Capabilities

- `frontend-migration-baseline`: capability de **proceso** (no de producto) que exige que, antes de
  reemplazar el frontend, exista una línea base escrita que clasifique cada archivo del destino como
  preservar/reemplazar/reconciliar y que fije criterios de paridad verificables. Es el spec mínimo
  requerido por OpenSpec para un cambio doc-only; se archiva con `--skip-specs` y no se promociona a
  `openspec/specs/`.

### Modified Capabilities

<!-- Ninguna. No cambia ningún requisito de comportamiento del producto: esta HU solo produce
     documentación de planificación e inventario. -->

## Impact

- **Nuevo:** `docs/planning/JUP-090-frontend-migration-baseline.md` (línea base de la épica).
- **Modificado:** `docs/spikes/frontend-migration.md` — enlace a la línea base y marcado de la
  tarjeta F1 correspondiente.
- **Solo lectura:** `apps/frontend/**`, `docker-compose.yml`, `turbo.json`, `pnpm-workspace.yaml`,
  `apps/frontend/README.md` — se inspeccionan para producir el inventario; no se modifican.
- **Sin código de producto, sin cambios de dependencias, sin `specs/` de producto.**
- Consumidores posteriores: las tarjetas de F2 (tooling), F3 (porte), F4 (plataforma) y F5
  (validación E2E) usan esta línea base como referencia.

## Human Approval

- Change: jup-090-inventory-current-frontend
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-08-29
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: HU doc-only de solo lectura sobre `apps/frontend`, sin código de producto; los riesgos reales son que la línea base quede desactualizada si F2/F3 modifican el destino antes de consumirla (mitigado fijando el commit base del inventario) y que los criterios de paridad se redacten demasiado vagos para servir de guion E2E en F5 (mitigado exigiendo endpoint y resultado observable en cada criterio).
- Required changes before execution: none
- Notes: La línea base se publica en `docs/planning/JUP-090-frontend-migration-baseline.md`, no dentro del change, porque la consumen F2–F5 y debe sobrevivir al archivado. Doc-only: se omiten tester/coder/mutación del harness TDD y se documenta la excepción en `review.md`; se archivará con `--skip-specs`. ADR no aplicable en esta HU: no introduce decisiones de arquitectura duraderas, y la adopción de TypeScript conserva su propio ADR en la tarjeta de F1 correspondiente.
