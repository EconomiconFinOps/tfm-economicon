# JUP-097 — Mapa de carencias de datos por pantalla

Entregable de la tarea 6.3 de [`jup-097-reconcile-api-layer`](../../openspec/changes/jup-097-reconcile-api-layer/).
Enumera, para cada una de las 5 pantallas de coste portadas en JUP-095, qué dato concreto pinta y qué
capacidad de backend le falta para dejar de ser demostración. No decide nada nuevo: consolida y
traduce a las pantallas ya portadas el trabajo de análisis que ya hizo
[JUP-091](JUP-091-economicon-source-inventory.md) (sección "Mapeo de pantallas a contratos del
backend"), sirviendo de insumo directo para la decisión de épica sobre `RF-091-003`.

Esta tarjeta **no construye ninguna de estas capacidades** (decisión de alcance tomada antes de
proponer, ver `proposal.md`): el backend expone hoy exactamente los mismos 10 endpoints que
[JUP-091](JUP-091-economicon-source-inventory.md) ya había catalogado sin cambio.

## Tabla: pantalla → dato → capacidad ausente → finding

| Pantalla (componente) | Ruta | Módulo de demostración | Dato | Capacidad ausente | Finding |
| --- | --- | --- | --- | --- | --- |
| `ExecutiveCostDashboard` | `/` (index) | `executiveCostDashboard.ts` | `kpiData[0]` "Coste Total Mensual" | Ninguna — **PARCIAL**: `GET /billing/summary` → `monthly_spend` existe, pero devuelve un valor codificado a mano | `RF-091-004` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` | `kpiData[2]` "Ahorro Potencial" | Ninguna — **PARCIAL**: `GET /billing/summary` → `savings_identified`, mismo caso | `RF-091-004` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` | `kpiData[3]` "Recursos Activos" | **C7** — inventario de recursos activos | `RF-091-003` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` | `monthlyData` (serie mensual compute/storage/network) | **C1** — serie temporal de costes | `RF-091-003` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` | `serviceData` (reparto % por servicio) | **C2** — desglose por dimensión | `RF-091-003` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` | `kpiData[1]` "Coste por Servicio" | **C2** — desglose por dimensión | `RF-091-003` |
| `OperationalCostDashboard` | `/operational` | `operationalCostDashboard.ts` | `detailedData` (servicio, proyecto, coste, uso, proveedor) | **C2 + C3** — desglose por dimensión y multi-cloud AWS/GCP | `RF-091-003` |
| `OperationalCostDashboard` | `/operational` | `operationalCostDashboard.ts` | `hourlyData` (coste por franja horaria) | **C1** — serie temporal (granularidad horaria) | `RF-091-003` |
| `OperationalCostDashboard` | `/operational` | `operationalCostDashboard.ts` | `providerData` (AWS / Azure / GCP) | **C3** — multi-cloud AWS/GCP | `RF-091-003` |
| `ExecutiveCutDashboard` | `/cuts` | `executiveCutDashboard.ts` | `savingsData` (objetivo vs. alcanzado vs. pendiente) | **C4** — objetivos y acciones de recorte | `RF-091-003` |
| `ExecutiveCutDashboard` | `/cuts` | `executiveCutDashboard.ts` | `cutActions` (acción, impacto, estado, responsable, fecha) | **C4** — objetivos y acciones de recorte | `RF-091-003` |
| `ExecutiveCutDashboard` | `/cuts` | `executiveCutDashboard.ts` | `kpiData` (ahorro total, objetivo mensual, alcanzado, acciones activas) | **C4** — objetivos y acciones de recorte | `RF-091-003` |
| `AnomaliesPanel` | `/anomalies` | `anomaliesPanel.ts` | `anomalies` (tipo, servicio, severidad, descripción, agente) | **C5** — detección de anomalías | `RF-091-003` |
| `AnomaliesPanel` | `/anomalies` | `anomaliesPanel.ts` | `trendData` + `stats` | **C5** — detección de anomalías | `RF-091-003` |
| `RecommendationsPanel` | `/recommendations` | `recommendationsPanel.ts` | `recommendations` (título, categoría, ahorro estimado, agente) | **C6** — motor de recomendaciones | `RF-091-003` |
| `RecommendationsPanel` | `/recommendations` | `recommendationsPanel.ts` | `savingsByCategory` + `stats` | **C6** — motor de recomendaciones | `RF-091-003` |

## Resumen por capacidad (referencia: `RF-091-003`)

Mismas 7 capacidades que catalogó JUP-091, con las pantallas ya portadas que las necesitarían hoy:

| # | Capacidad ausente | Pantallas afectadas (ya portadas) | Dato ya en BD |
| --- | --- | --- | --- |
| C1 | Serie temporal de costes (mensual y por hora) | `ExecutiveCostDashboard`, `OperationalCostDashboard` | Sí — registros normalizados con fecha (JUP-072 a JUP-077) |
| C2 | Desglose por dimensión (servicio, proyecto, recurso) | `ExecutiveCostDashboard`, `OperationalCostDashboard` | Parcial — dimensiones Azure normalizadas |
| C3 | Multi-cloud AWS / GCP | `OperationalCostDashboard` | No — solo se ingesta Azure |
| C4 | Objetivos y acciones de recorte (impacto, estado, responsable, fecha) | `ExecutiveCutDashboard` | No — entidad de gestión inexistente |
| C5 | Detección de anomalías | `AnomaliesPanel` | No — requiere lógica de detección |
| C6 | Motor de recomendaciones | `RecommendationsPanel` | No — requiere lógica de análisis |
| C7 | Inventario de recursos activos | `ExecutiveCostDashboard` | No |

## Qué hacer cuando una capacidad se construya

Cuando una tarjeta futura construya alguna de estas capacidades (`C1`-`C7`), le corresponde a **esa**
tarjeta:

1. Retirar de este documento (o marcar resuelta) la fila correspondiente.
2. Retirar el nombre de esa capacidad del comentario "DATOS DE DEMOSTRACION (sustituibles)" del
   módulo `src/data/demo/*.ts` afectado, sustituyendo el dato estático por la llamada real vía
   `services/api.ts`.
3. Actualizar `RF-095-002` en `openspec/findings/backlog.md`: si esa era la última capacidad
   pendiente de una pantalla, esa pantalla deja de aparecer en el finding.

Este documento no envejece por sí mismo: envejece porque una tarjeta lo actualiza al construir la
capacidad que describe.

## Fuentes

- [docs/planning/JUP-091-economicon-source-inventory.md](JUP-091-economicon-source-inventory.md),
  sección "Mapeo de pantallas a contratos del backend" — análisis original, sobre el código del
  origen (`Economicon`) antes de portar.
- `apps/frontend/src/data/demo/*.ts` — los 5 módulos ya portados en JUP-095, verificados variable a
  variable en esta tarjeta.
- `openspec/findings/backlog.md` — `RF-091-003` (7 capacidades ausentes), `RF-091-004`
  (`/billing/summary` parcialmente hardcodeado), `RF-095-002` (mock data in production path).
