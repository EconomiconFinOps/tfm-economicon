# ADR-0019 — Episodios de anomalía de coste guardados con la regla diaria de negocio

- Status: Proposed
- Date: 2026-10-12
- Related JUP/OpenSpec: JUP-114, [jup-114-persisted-anomalies](../../openspec/changes/archive/2026-10-12-jup-114-persisted-anomalies/design.md)
- Trello: https://trello.com/c/F492abeY
- Supersedes: none
- Superseded by: none

## Context

JUP-030 evalúa candidatas bajo demanda con reglas que manda quien llama y no guarda nada: su `id` cambia con el periodo y las reglas, no hay criticidad ni estado. El panel `/anomalies` (JUP-057) muestra una lista fija de ejemplo y el asistente (JUP-038) necesita anomalías estables que explicar. Las reglas de negocio de JUP-019 (`docs/assistant-corpus/business-rules/economicon-mvp-rules.md`) definen una regla diaria (`relative_delta > 20 % AND absolute_delta > 100 EUR/day`), tramos de severidad P1/P2/P3 «EUR/mes» y estados sugeridos, sin decir contra qué se compara un día ni cómo se mide el impacto. Ese documento está fijado por sha256 en los conjuntos de evaluación de JUP-022, JUP-069 y JUP-070.

## Decision

1. **Una anomalía es un episodio guardado por tenant, moneda y servicio.** Se abre el día en que salta la regla y sigue siendo el mismo registro mientras vuelva a saltar dentro de una **tolerancia de 3 días**. Pasada la tolerancia, el sistema lo marca `no_longer_observed`; nunca lo cierra. Si el servicio vuelve a saltar, se abre un episodio nuevo enlazado al anterior.
2. **Regla diaria de JUP-019 tal cual**, sobre el coste diario realmente observado (suma de registros por `usage_date`, nunca un agregado dividido): salta si lo esperado es positivo, el día supera lo esperado en **más de 100** y en **más de un 20 %**. Las dos condiciones son estrictas y obligatorias.
3. **Lo esperado** es la media diaria de los 7 días anteriores. Con un episodio en seguimiento (`new` o `investigating`, y `observed`) es su **referencia anclada**: la media de los 7 días previos a su inicio. Así una subida que se queda sigue viéndose aunque la media la alcance.
4. **Días evaluables:** el último día con datos del tenant se considera incompleto; el último día completo es el anterior. Un día solo se evalúa si él y sus 7 días previos tienen algún registro del tenant.
5. **Impacto acumulado** = suma, cada día evaluado mientras el episodio está en seguimiento, de `max(0, observado − referencia)`. **Severidad** sobre ese impacto en la moneda del episodio: P1 > 2000, P2 de 500 a 2000, P3 < 500. Es la lectura de «EUR/mes» como impacto del episodio y no como proyección mensual (con una proyección ×30 casi todo sería P1); pendiente de confirmar con la responsable de las reglas.
6. **Monedas:** umbrales nominales en EUR y USD, sin conversión. Otras monedas no se evalúan y la ejecución las informa.
7. **Estados** `new`, `investigating`, `resolved`, `false_positive` (los de JUP-019 sin `acknowledged`), motivo obligatorio al cerrar, quién y cuándo cambió el estado, quién y cuándo hizo el primer cambio desde `new` (reconocimiento, para MTTA) y fecha de cierre (MTTR). Cualquier miembro del tenant puede cambiar el estado.
8. **Ejecución bajo demanda** («Detectar ahora»), idempotente, con una marca de agua por tenant: evalúa todos los días pendientes hasta el último día completo (en la primera, toda la historia) en una sola transacción. El límite inicial de 7 días por pulsación se quitó en el change `jup-114-anomalies-panel-live` (decisión de Lucia del 2026-10-12), porque impedía que la subida de Compute de la demo apareciera como episodio. Abrir el panel solo lee.
9. **Reglas versionadas** (`jup019-daily-v1`) copiadas en cada episodio.
10. **La consulta de JUP-030 no cambia** (límites `>=`, reglas independientes y configurables): queda como consulta de prueba sin guardar. Los episodios son la fuente para el panel y JUP-038.
11. **El documento de reglas del corpus no se modifica** en este cambio: la regla que aplicamos es la misma y las aclaraciones (lo esperado, criticidad por acumulado, estados del MVP) se incorporan con JUP-038, regenerando las huellas en cadena de las evaluaciones.

## Consequences

- El panel y el asistente leen episodios estables, priorizados y con estado trazable; los KPI MTTA y MTTR son calculables.
- Se detectan picos de un día y subidas sostenidas; P1, P2 y P3 son alcanzables.
- Limitaciones aceptadas: un día puede evaluarse antes de que lleguen datos tardíos; un gasto nuevo desde cero no abre episodio; los ciclos semanales pueden producir candidatas falsas; un pico reciente infla la media de 7 días; si se cierra un episodio con el gasto aún alto, la media puede no volver a saltar; solo se vigila el servicio; 1 USD se trata como 1 EUR a efectos de umbral.
- Son candidatas: no se afirma causa, ahorro, confianza estadística ni completitud de los datos.

## Alternatives Considered

- **Regla semanal** (la semana sube más de un 20 % y más de 700): descartada. Era más barata antes de decidir referencia anclada e impacto acumulado, que ya obligan a leer días; dejaba P3 inalcanzable (impacto mínimo 700) y obligaba a añadir una regla nueva a las de negocio.
- **Reutilizar la evaluación de JUP-030 y su `id`:** descartada. El `id` incluye periodo y reglas y no identifica un episodio; sus límites son inclusivos e independientes.
- **Recalcular todos los episodios desde cero en cada pulsación:** descartada. Leería toda la historia y mezclaría episodios terminados con días ya vistos; la marca de agua da idempotencia con lecturas acotadas.
- **Comparar con el día anterior:** descartada por sensible a un solo día raro.
- **Límite de 7 días por pulsación:** fue la decisión inicial para acotar cada ejecución; se descartó en el change 2 porque con una sola pulsación la demo no enseñaba la subida de Compute, y quitarlo costaba poco gracias a la marca de agua.

## Evidence And Follow-up

- Evidencia: [JUP-114-validation.md](../evidence/JUP-114-validation.md).
- **Etapa 2** (change `jup-114-anomaly-alerts-schedule`): la ejecución periódica llama a la misma detección, que ya pone al día todos los días pendientes aunque el entorno haya estado apagado.
- Trabajo futuro, registrado en `openspec/findings/backlog.md`: incorporar las aclaraciones al corpus del asistente con JUP-038; tabla de umbrales por moneda o conversión documentada; línea base predictiva (modelo que aprenda el patrón esperado, por ejemplo con ciclos semanales); responsable asignado y permisos por rol; archivado automático de episodios no observados; histórico completo de cambios de estado; otras dimensiones además del servicio.
