# Inventario del frontend origen — Economicon (JUP-091)

JUP: JUP-091
Trello: https://trello.com/c/pVfcfvhu/83-jup-091-inventariar-dependencias-y-endpoints-del-frontend-economicon-origen
OpenSpec change: `openspec/changes/jup-091-inventory-economicon-frontend/`
Rama: `docs/JUP-091-inventory-economicon-frontend`
Commit base de este repo: `b0c11f9`

## Snapshot del origen

- Ruta: `../Economicon/frontend` (carpeta hermana, **fuera** de este repo).
- Paquete: `finops-dashboard-frontend` (generado con Figma Make).
- Rama: `main` · Commit: `1fe0030c054d81787bfd0c410f238a6f87a688f6`.

Es el **mismo commit** que inspeccionó JUP-083, así que los 7 supuestos confirmados allí siguen
vigentes y este inventario los extiende en lugar de revisarlos.

## Alcance

Este documento completa las dos tareas de inventario del **origen** que el spike
[docs/spikes/frontend-migration.md](../spikes/frontend-migration.md) dejó abiertas en F1:

1. **Dependencias** clasificadas como `MANTENER` / `SUSTITUIR` / `DESCARTAR`.
2. **Pantallas → contratos** del backend de este repo, o `SIN EQUIVALENTE`.

Significado de las etiquetas de dependencia, fijado para que F2 no las reinterprete:

| Etiqueta | Significado |
| --- | --- |
| `MANTENER` | Entra al monorepo tal cual; el destino no tiene equivalente y la función es necesaria. |
| `SUSTITUIR` | El destino ya cubre esa función con otra librería, o exige cambio de versión mayor. |
| `DESCARTAR` | No aplica aquí: mock, dependencia sin uso real en el código, o función que la migración no porta. |

**Fuera de inventario:** `../Economicon/frontend/node_modules/**` y cualquier artefacto generado del
origen. Tampoco se inventaría el destino: eso es la
[línea base de JUP-090](JUP-090-frontend-migration-baseline.md).

## Clasificación de dependencias

<!-- Se completa en las tareas 2.1-2.4 -->

## Mapeo de pantallas a contratos del backend

<!-- Se completa en las tareas 3.1-3.3 -->

## Hallazgos

<!-- Se completa en la tarea 4.3 -->
