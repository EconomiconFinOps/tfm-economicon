JUP: JUP-114
Trello: https://trello.com/c/F492abeY

## Why

JUP-030 detecta candidatas bajo demanda sin guardar nada: su `id` cambia con el periodo y las reglas, no hay criticidad, ni estado, ni nada que el panel `/anomalies` (JUP-057, que sigue con una lista fija de ejemplo) o el asistente (JUP-038) puedan leer y seguir. La tarjeta pide que las anomalías se conserven por cliente, se prioricen por criticidad e impacto y se pueda seguir su estado. Este change es la primera etapa en el backend; el panel conectado y la ejecución periódica son changes posteriores de la misma tarjeta.

## What Changes

- Un **episodio de anomalía** guardado por cliente: se abre cuando un servicio salta la regla de negocio diaria de JUP-019 (`relative_delta > 20 % AND absolute_delta > 100` por día, en la moneda del episodio) y sigue siendo el mismo registro mientras vuelva a saltar dentro de una tolerancia de 3 días; pasada la tolerancia queda «ya no se observa» y lo cierra una persona. Si el servicio vuelve a saltar después, se abre un episodio nuevo enlazado al anterior.
- **Lo esperado** de cada día es el gasto medio diario de los 7 días anteriores; con un episodio abierto, la **referencia anclada** al inicio del episodio (la media de los 7 días previos a su inicio), tanto para detectar como para acumular impacto.
- **Impacto acumulado** (suma del exceso diario sobre la referencia, sin negativos) y **criticidad** P1/P2/P3 de JUP-019 calculada sobre ese impacto, con umbrales nominales en EUR y USD; otras monedas no se evalúan y se informan.
- **Estados** Nueva, Investigando, Resuelta y Falso positivo, con motivo obligatorio al cerrar; se guarda quién y cuándo cambió el estado, la fecha del primer cambio desde Nueva y la de cierre (para MTTA y MTTR).
- **API autenticada** del cliente activo: detectar ahora (recorre día a día los días completos pendientes, como máximo 7, idempotente), listar episodios, ver uno y cambiar su estado. Ids ajenos o inexistentes dan el mismo 404.
- **Migración 002 del backend** con las tablas de episodios y del estado de detección por cliente.
- **ADR-0019** del modelo de anomalías: regla, referencia, episodio, criticidad, monedas, estados, limitaciones y trabajo futuro (puesta al día obligatoria en la etapa 2, línea base predictiva, conversión de monedas, responsable, permisos por rol, archivado automático).
- Enmiendas de contrato: la evaluación de JUP-030 queda como **consulta de prueba sin guardar** (no se toca su comportamiento) y el contrato del agente de JUP-084 aclara qué es lo esperado, la criticidad por impacto acumulado, las reglas versionadas y que la fuente de JUP-038 son los episodios.

Fuera de alcance: el panel `/anomalies` y los datos de demostración (change 2, `jup-114-anomalies-panel-live`), la ejecución periódica y los avisos (change 3), la explicación con el agente (JUP-038), el documento de reglas del corpus del asistente (fijado por huella en las evaluaciones de JUP-022, JUP-069 y JUP-070; se registra un hallazgo para actualizarlo con JUP-038), conversión de moneda, detección estadística o predictiva, causa raíz y permisos por rol.

## Capabilities

### New Capabilities

- `cost-anomaly-episodes`: detección diaria con la regla de negocio, episodios guardados por cliente con referencia anclada, impacto acumulado, criticidad, estados con trazabilidad y su API.

### Modified Capabilities

- `cost-anomaly-detection`: la evaluación de JUP-030 se declara consulta de prueba sin guardar, distinta de los episodios; JUP-038 consume episodios y no candidatas de la consulta de prueba.
- `finops-agent-tool-contract`: el requisito de anomalías candidatas define lo esperado, la criticidad por impacto acumulado, la versión de las reglas y la fuente persistida.

## Impact

Backend: migración 002, acceso a datos (lectura diaria de costes por servicio con las protecciones de billing v2, y escritura de episodios), esquemas, servicio de detección, rutas nuevas bajo `/billing/anomalies/` y pruebas, incluidas pruebas con CockroachDB real. Documentación: `docs/api/cost-anomalies.md`, nueva `docs/api/anomaly-episodes.md`, `docs/adr/ADR-0019-…`, nota de continuidad y hallazgos. Sin cambios en el frontend, el processor, el corpus del asistente, los conjuntos de evaluación ni el comportamiento de `POST /billing/anomalies/evaluate`.

La interpretación de la criticidad sobre el impacto acumulado está pendiente de confirmar con la responsable de las reglas de negocio; si cambia, se ajusta antes de archivar.
