## Context

La épica de migración del frontend (Economicon → tfm-economicon) está diseñada en el spike
[docs/spikes/frontend-migration.md](../../../docs/spikes/frontend-migration.md) con estrategia de
**reemplazo completo** y **adopción de TypeScript**. El spike deja 6 supuestos `[ASUNCION]` sobre el
frontend de Economicon que no se pueden confirmar sin inspeccionar el repositorio origen. Economicon
está disponible como **carpeta hermana fuera del repo** (`../Economicon`).

Esta HU (`jup-083`, carril `light`, doc-only) resuelve esos supuestos mediante inspección en solo
lectura y documenta los hallazgos, sin tocar código de producto.

## Goals / Non-Goals

**Goals:**
- Confirmar con datos reales cada `[ASUNCION]` del spike: versión de React/Vite, routing, librería
  de datos/estado, auth/sesión, sistema de estilos, assets, variables `VITE_*`.
- Reemplazar cada `[ASUNCION]` en el spike por el dato confirmado y actualizar el checklist.
- Dejar un **inventario detallado** del frontend de Economicon en este `design.md`.

**Non-Goals:**
- Migrar, copiar o commitear código de Economicon en tfm-economicon (eso es F3 de la épica).
- Instalar dependencias, adoptar TypeScript o crear el ADR de TS (HU posterior de tooling, F2).
- Modificar el backend o los contratos de API.

## Decisions

- **Inspección en solo lectura, fuera del repo.** Economicon se lee desde `../Economicon`; nada suyo
  entra en el árbol de git de tfm-economicon. Alternativa descartada: clonarlo dentro con `.gitignore`
  (más riesgo de commitearlo por error).
- **Doble registro de hallazgos.** El dato corto y confirmado va al spike (reemplaza el `[ASUNCION]`);
  el detalle e evidencia va al inventario de este `design.md`. Da trazabilidad sin ensuciar el spike.
- **Un commit por supuesto.** Cada tarea de `tasks.md` resuelve un supuesto y se commitea aparte,
  para historial limpio y revisión granular.
- **Sin ADR.** No hay decisión de arquitectura nueva aquí; la adopción de TypeScript (con su ADR)
  pertenece a una HU posterior. Se declarará "ADR no aplicable" en la review.
- **Doc-only → archivar con `--skip-specs`.** No hay capability de producto; el spec de esta HU es
  un spec mínimo de proceso que no se promociona a `openspec/specs/`.
- **Snapshot del origen.** Se anota el commit hash de `../Economicon` inspeccionado, para que el
  inventario sea reproducible aunque Economicon cambie después.

## Risks / Trade-offs

- [Economicon expone endpoints que el backend de este repo no tiene] → Registrar como *finding* en
  `review.md` y en `openspec/findings/backlog.md`; no se resuelve aquí, alimenta la épica.
- [Un supuesto confirmado cambia el alcance de la épica (ej. no es React 18, o usa otro bundler)]
  → Documentar el impacto en el spike y avisar; puede requerir replanificar HUs posteriores.
- [El inventario queda obsoleto si Economicon evoluciona] → Mitigado anotando el commit hash del
  origen inspeccionado.

## Inventario del frontend de Economicon

> Esta sección se rellena durante `/opsx:apply` (una entrada por tarea). Estructura a completar:

- **Snapshot del origen:** ruta `../Economicon`, commit hash `<pendiente>`.
- **T1 · React / Vite:** `<pendiente>` (versiones exactas de `package.json`).
- **T2 · Routing:** `<pendiente>` (librería y versión; dependencias nuevas).
- **T3 · Librería de datos/estado:** `<pendiente>` (TanStack Query / Redux / SWR / otro).
- **T4 · Auth / sesión:** `<pendiente>` (mecanismo; encaje con `Bearer` + `X-Tenant-Id`).
- **T5 · Sistema de estilos:** `<pendiente>` (CSS plano / Modules / Tailwind / styled-components).
- **T6 · Assets:** `<pendiente>` (fuentes, imágenes, iconos; licencias).
- **T7 · Variables de entorno `VITE_*`:** `<pendiente>`.
