JUP: JUP-057
Trello: https://trello.com/c/29e5Pisa

## Why

El responsable FinOps necesita priorizar anomalías abiertas por criticidad e
impacto. El panel existente muestra cinco ejemplos, pero anuncia 23 detecciones,
87% de resolución y actividad en tiempo real sin una fuente real.

## What Changes

- Mostrar explícitamente datos de prueba y su periodo fijo.
- Derivar indicadores de las mismas filas y distinguir el resumen global de los filtros.
- Mostrar abiertas inicialmente, filtrar por estado/criticidad y priorizar revisión.
- Mantener la exportación alineada con las filas visibles y su procedencia demo.
- Añadir pruebas funcionales, comprobación visual y evidencia reproducible.

## Capabilities

### New Capabilities

- `anomalies-panel`: priorización de anomalías de prueba, indicadores consistentes y filtros.

### Modified Capabilities

Ninguna capacidad de backend cambia.

## Impact

Frontend React existente en `/anomalies`, fixtures y pruebas. No añade dependencias,
endpoints, detección, notificaciones ni acciones persistentes. JUP-030 y la capacidad
C5 siguen pendientes; RF-091-003 y RF-095-002 no quedan resueltos por este trabajo.
La petición del usuario autoriza esta preparación con datos de prueba. Los roles
vigentes consultados en Trello el 01/10/2026 son Alejandro (liderazgo), Lucia
(pairing), Paris (revisión) y Victor (validación); no se atribuye participación
humana realizada ni aprobación a partir de esa asignación.
