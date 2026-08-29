# Línea base de migración del frontend (JUP-090)

JUP: JUP-090
Trello: https://trello.com/c/DtlNd0u0/82-jup-090-inventariar-frontend-actual
OpenSpec change: `openspec/changes/jup-090-inventory-current-frontend/`
Rama: `docs/JUP-090-inventory-current-frontend`
Commit base del inventario: `0967692`

## Alcance

Este documento es la línea base de la épica *Migrar frontend del repositorio Economicon* para el
**destino** (`apps/frontend` en este repo). Clasifica cada archivo y punto de integración como:

- **PRESERVAR** — se mantiene sin cambios funcionales al reemplazar el frontend.
- **REEMPLAZAR** — se sustituye por completo por el código/config de Economicon.
- **RECONCILIAR** — requiere fusión dirigida: parte del origen, parte del destino.

Fuera de este inventario quedan los artefactos generados y no versionados:
`apps/frontend/node_modules/**` y cualquier caché de build (`node_modules/.vite`).

El inventario del **origen** (Economicon) no es objeto de este documento: ya está cubierto por
JUP-083 ([docs/spikes/frontend-migration.md](../spikes/frontend-migration.md)) y por la tarjeta
`jup-0xx-inventariar-frontend-economicon` de F1.

## Qué se preserva del destino

<!-- Se completa en la tarea 2.2/2.3 -->

## Clasificación archivo a archivo

<!-- Se completa en las tareas 2.1-2.3 -->

## Contratos del backend consumidos por el frontend

<!-- Se completa en la tarea 2.4 -->

## Criterios de paridad funcional (login → tenant → dashboard)

<!-- Se completa en la tarea 3.1 -->

## Rollback

<!-- Se completa en la tarea 3.2 -->
