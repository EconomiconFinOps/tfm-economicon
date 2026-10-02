# JUP-097 — Mapa de carencias de datos por pantalla

Entregable de la tarea 6.3 de [`jup-097-reconcile-api-layer`](../../openspec/changes/jup-097-reconcile-api-layer/).
Enumera, para cada una de las 5 pantallas de coste portadas en JUP-095, qué dato concreto pinta y qué
capacidad de backend le falta para dejar de ser demostración. No decide nada nuevo: consolida y
traduce a las pantallas ya portadas el trabajo de análisis que ya hizo
[JUP-091](JUP-091-economicon-source-inventory.md) (sección "Mapeo de pantallas a contratos del
backend"), sirviendo de insumo directo para la decisión de épica sobre `RF-091-003`.

Esta tarjeta **no construye ninguna de estas capacidades** (decisión de alcance tomada antes de
proponer, ver `proposal.md`): en la instantánea inicial de JUP-097, el backend exponía los mismos 10 endpoints que
[JUP-091](JUP-091-economicon-source-inventory.md) ya había catalogado sin cambio.

Actualización técnica local — **27/09/2026**: [JUP-026](../../openspec/changes/jup-026-azure-cost-kpis/proposal.md)
implementa agregados reales en `GET /billing/summary`, consumidos por `/` y `/overview-legacy`,
con [15 comprobaciones TEMP en navegador contra la API real PASS](../evidence/JUP-026-validation.md)
y [revisión técnica REVIEW_PASS](../../openspec/changes/jup-026-azure-cost-kpis/review.md), con la limitación móvil heredada
[RF-026-002](../../openspec/findings/backlog.md#rf-026-002). Paris aprobó el 27/09/2026 aplazar RF-026-002 fuera de JUP-026,
con revisión antes del paso de P0 a P1. El estado efectivo de QA consta en [review.md](../../openspec/changes/jup-026-azure-cost-kpis/review.md);
la aprobación final posterior a QA y la integración siguen pendientes. Las filas ejecutivas de total, ahorro y C2
indican este estado; sus referencias a constantes identifican la instantánea histórica de JUP-097.
Los gráficos mensuales, la exportación y el inventario siguen siendo demostración.
`RF-091-003` y `RF-095-002` permanecen abiertos; esto no modifica el estado operativo de las tarjetas.

## Tabla: pantalla → dato → capacidad ausente → finding

| Pantalla (componente) | Ruta | Módulo de demostración | Dato | Capacidad ausente | Finding |
| --- | --- | --- | --- | --- | --- |
| `ExecutiveCostDashboard` | `/` (index) | `executiveCostDashboard.ts` (origen histórico) | Antes: `kpiData[0]` "Coste Total Mensual"; ahora: total del periodo | **Implementado localmente en JUP-026, pendiente de integración**: `GET /billing/summary` → `totals`, agregados reales como cadenas decimales exactas por moneda y periodo UTC seleccionable; antes codificado a mano | `RF-091-004` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` (origen histórico) | Antes: `kpiData[2]` "Ahorro Potencial"; ahora: no disponible | **Ahorro NO implementado**: JUP-026 retira el valor ficticio; `savings_identified: null` y ahorro no disponible en ejecutiva y legacy. Cambio local pendiente de integración; falta el motor de ahorro | `RF-091-004` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` | `kpiData[3]` "Recursos Activos" | **C7** — inventario de recursos activos | `RF-091-003` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` | `monthlyData` (serie mensual compute/storage/network) | **C1** — serie temporal de costes | `RF-091-003` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` (origen histórico) | Antes: `serviceData` (reparto % por servicio); ahora: tabla de importes | **C2 — implementado localmente en JUP-026, pendiente de integración**: tabla real seleccionable por suscripción, grupo de recursos, servicio, proyecto o etiqueta; importes exactos por moneda, sin gráfico porcentual | `RF-091-003` |
| `ExecutiveCostDashboard` | `/` | `executiveCostDashboard.ts` (origen histórico) | Antes: `kpiData[1]` "Coste por Servicio"; ahora: tabla de importes | **C2 — implementado localmente en JUP-026, pendiente de integración**: mismo desglose real del periodo UTC; dimensiones ausentes y cobertura parcial explícitas | `RF-091-003` |
| `OperationalCostDashboard` | `/operational` | `operationalCostDashboard.ts` | `detailedData` (servicio, proyecto, coste, uso, proveedor) | **C2 + C3** — desglose por dimensión y multi-cloud AWS/GCP | `RF-091-003` |
| `OperationalCostDashboard` | `/operational` | `operationalCostDashboard.ts` | `hourlyData` (coste por franja horaria) | **C1** — serie temporal (granularidad horaria) | `RF-091-003` |
| `OperationalCostDashboard` | `/operational` | `operationalCostDashboard.ts` | `providerData` (AWS / Azure / GCP) | **C3** — multi-cloud AWS/GCP | `RF-091-003` |
| `ExecutiveCutDashboard` | `/cuts` | `executiveCutDashboard.ts` | `savingsData` (objetivo vs. alcanzado vs. pendiente) | **C4** — objetivos y acciones de recorte | `RF-091-003` |
| `ExecutiveCutDashboard` | `/cuts` | `executiveCutDashboard.ts` | `cutActions` (acción, impacto, estado, responsable, fecha) | **C4** — objetivos y acciones de recorte | `RF-091-003` |
| `ExecutiveCutDashboard` | `/cuts` | `executiveCutDashboard.ts` | `kpiData` (ahorro total, objetivo mensual, alcanzado, acciones activas) | **C4** — objetivos y acciones de recorte | `RF-091-003` |
| `AnomaliesPanel` | `/anomalies` | `anomaliesPanel.ts` | `anomalies` (tipo, servicio, severidad, descripción, agente) | **C5** — detección de anomalías | `RF-091-003` |
| `AnomaliesPanel` | `/anomalies` | `anomaliesPanel.ts` | Indicadores derivados de `anomalies` (abiertas, altas abiertas, impacto abierto y resueltas); JUP-057 retira `trendData` y `stats` ficticios | **C5** — detección de anomalías; los indicadores siguen basados en fixtures | `RF-091-003` |
| `RecommendationsPanel` | `/recommendations` | `recommendationsPanel.ts` | `recommendations` (título, categoría, ahorro estimado, agente) | **C6** — motor de recomendaciones | `RF-091-003` |
| `RecommendationsPanel` | `/recommendations` | `recommendationsPanel.ts` | `savingsByCategory` + `stats` | **C6** — motor de recomendaciones | `RF-091-003` |

## Resumen por capacidad (referencia: `RF-091-003`)

Mismas 7 capacidades que catalogó JUP-091, con las pantallas ya portadas que las necesitarían hoy:

| # | Capacidad ausente | Pantallas afectadas (ya portadas) | Dato ya en BD |
| --- | --- | --- | --- |
| C1 | Serie temporal de costes (mensual y por hora) | `ExecutiveCostDashboard`, `OperationalCostDashboard` | Sí — registros normalizados con fecha (JUP-072 a JUP-077) |
| C2 | Desglose por dimensión: JUP-026 implementado localmente, pendiente de integración (27/09/2026); C2 + C3 operativo sigue sin resolver | `ExecutiveCostDashboard`: tabla real por suscripción, grupo de recursos, servicio, proyecto o etiqueta; `OperationalCostDashboard`: pendiente | Dimensiones Azure normalizadas agregadas por periodo UTC y moneda; cobertura parcial explícita cuando faltan dimensiones |
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
