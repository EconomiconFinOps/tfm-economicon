JUP: JUP-083
Trello: https://trello.com/c/GdGEHPvL

## Why

El spike [docs/spikes/frontend-migration.md](../../../docs/spikes/frontend-migration.md) contiene 6
supuestos marcados como `[ASUNCION]` sobre el frontend del repositorio **Economicon** (versión de
React/Vite, routing, librería de datos, auth/sesión, estilos y assets). Esos supuestos bloquean
arrancar la épica de migración porque las tareas técnicas dependen de datos que hoy no están
confirmados. Esta HU los resuelve inspeccionando Economicon en solo lectura.

## What Changes

- Inspeccionar **en solo lectura** el repositorio Economicon (`../Economicon`, carpeta hermana
  fuera del repo) para confirmar: versión de React/Vite, routing, librería de datos/estado,
  modelo de auth/sesión, sistema de estilos, assets y variables de entorno `VITE_*`.
- Reemplazar cada `[ASUNCION]` del spike por el dato confirmado, y actualizar el checklist de
  inspección del origen.
- Registrar el inventario detallado del frontend de Economicon en el `design.md` de esta HU.
- No se migra ni se copia código de Economicon, no se instalan dependencias y no se adopta
  TypeScript: eso corresponde a HUs posteriores de la épica.

## Capabilities

- `frontend-migration-assumptions`: capability de **proceso** (no de producto) que exige que cada
  supuesto del origen en el spike de migración esté confirmado contra Economicon y documentado.
  Es un spec mínimo requerido por OpenSpec para un cambio doc-only; se archiva con `--skip-specs`
  y no se promociona a `openspec/specs/`.

### Modified Capabilities

<!-- Ninguna. No cambian requisitos de comportamiento del producto; solo se actualiza
     documentación (el spike) y se produce un inventario. -->

## Impact

- `docs/spikes/frontend-migration.md` — se resuelven los `[ASUNCION]` y el checklist de inspección.
- `openspec/changes/jup-083-clarify-frontend-migration-assumptions/design.md` — alberga el
  inventario detallado del frontend de Economicon.
- **Sin código de producto, sin dependencias nuevas, sin `specs/` de producto.**
- Economicon se lee desde `../Economicon` (fuera del repo); nada suyo se commitea en tfm-economicon.

## Human Approval

- Change: jup-083-clarify-frontend-migration-assumptions
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-08-16
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: HU de solo lectura sobre `../Economicon`, sin código de producto; el riesgo principal es que un supuesto confirmado (p. ej. versión de React o bundler distinto) cambie el alcance de HUs posteriores de la épica, lo cual se documentará en el spike.
- Required changes before execution: none
- Notes: Inventario doc-only; se archivará con `--skip-specs`. ADR no aplicable en esta HU (la adopción de TypeScript, con su ADR, corresponde a una HU posterior de tooling).
