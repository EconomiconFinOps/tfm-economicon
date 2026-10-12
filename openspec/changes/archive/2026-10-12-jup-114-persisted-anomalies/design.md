JUP: JUP-114 · ADR: [ADR-0019](../../../../docs/adr/ADR-0019-cost-anomaly-episodes.md) (nuevo en este change)

## Context

Ver `proposal.md` (Why) y la spec `cost-anomaly-episodes`. Estado de partida:

- `POST /billing/anomalies/evaluate` (JUP-030) compara agregados de dos periodos con reglas que manda quien llama y no guarda nada. No se toca.
- `Database.fetch_billing_summary` ya aplica las protecciones de billing v2 (ingestas completadas, predicados de tenant, rechazo de fuentes solapadas con `AmbiguousCostSource`) en una transacción `SERIALIZABLE`, pero solo devuelve agregados de periodo, no días.
- Las tablas de coste (`azure_cost_records`, `azure_cost_ingestion_runs`) son del processor; el backend tiene sus propias migraciones (`schema_migrations`, hoy solo `001_initial`) y crea ahí `jobs`, `conversations` y `messages`.
- La regla de negocio diaria y los tramos P1/P2/P3 están en `docs/assistant-corpus/business-rules/economicon-mvp-rules.md`, fijado por sha256 en los conjuntos de evaluación de JUP-022, JUP-069 y JUP-070: este change no lo modifica.
- Solo existe el usuario demo y ningún endpoint comprueba roles.

## Goals / Non-Goals

**Goals:** aplicar la regla diaria de JUP-019 sobre el coste diario real por servicio, guardar episodios por tenant con referencia anclada, impacto acumulado, criticidad y estado trazable, y exponerlos por API para el change 2 (panel) y JUP-038.

**Non-Goals:** frontend, datos de demostración y su limpieza (change 2), ejecución periódica, puesta al día completa y avisos (change 3), otras dimensiones distintas de servicio, conversión de moneda, responsable asignado, permisos por rol, histórico completo de cambios de estado, modificar el corpus del asistente o los conjuntos de evaluación.

## Decisions

**D1. Regla diaria de JUP-019 tal cual, sobre coste diario observado.** Alternativa descartada: regla semanal (más de 20 % y más de 700 en la semana). Era más barata antes de decidir la referencia anclada y el impacto acumulado, que ya obligan a leer días; con la lectura diaria hecha, la regla diaria evita una regla nueva, deja los tramos P1/P2/P3 alcanzables (con la semanal el impacto mínimo era 700 y P3 era imposible) y coincide con el contrato de JUP-084 y con las preguntas JUP-069-016 a 019. Cumple lo que dejó escrito JUP-030 para una adaptación diaria: granularidad (suma real por `usage_date`, nunca dividir agregados), cobertura (días evaluables), igualdad (estrictas) y combinación (las dos condiciones).

**D2. Lo esperado: media de 7 días; referencia anclada con episodio abierto.** Comparar con el día anterior es muy sensible a un día raro; la media de 7 días amortigua eso. Mientras un episodio está siguiéndose (`new` o `investigating` y `observed`), se compara con su referencia anclada (la media de los 7 días previos a su inicio), para que una subida que se queda no deje de verse cuando la media la alcanza. Alternativa futura: línea base predictiva (ADR, trabajo futuro).

**D3. Episodio con tolerancia de 3 días.** Con la regla diaria, una subida real puede saltar un día sí y otro no; la tolerancia la mantiene en un único episodio. Pasada la tolerancia, `no_longer_observed`: el ciclo de vida (estado) lo decide una persona, la observación la decide el sistema. Son dos campos separados para no cerrar nada automáticamente.

**D4. Días evaluables y último día completo.** El último día con datos del tenant se trata como posiblemente incompleto (las fuentes de coste llegan con retraso), así que el último día completo es el anterior. Un día solo se evalúa si él y sus 7 días previos tienen algún registro del tenant; si no, se salta y se informa. Un servicio sin registros en un día con datos del tenant cuenta 0,00.

**D5. Ejecución con marca de agua por tenant.** Tabla `anomaly_detection_state (tenant_id PK, last_evaluated_date, rules_version, updated_at)`. Cada ejecución evalúa los días posteriores a la marca hasta el último día completo, como máximo 7 (los más recientes), y deja la marca en el último día completo. Así repetir la pulsación no vuelve a procesar días (idempotente) y el impacto suma cada día una vez. Alternativa descartada: recalcular los episodios desde cero en cada pulsación; daría duplicados al mezclar episodios terminados con días ya vistos, y obliga a leer toda la historia.

**D6. Atomicidad y concurrencia.** Una ejecución es una sola transacción `SERIALIZABLE`: lee la marca de agua, los costes diarios y los episodios en seguimiento y el último de cada grupo, y escribe episodios y marca. No hace falta `SELECT … FOR UPDATE`: con `SERIALIZABLE`, dos ejecuciones que leen y escriben la misma marca de agua chocan y una aborta. Si CockroachDB aborta por conflicto (`40001`) o falla cualquier paso, no queda nada escrito y la API devuelve 409 `detection_conflict` (la siguiente pulsación ve el estado ya actualizado y responde `up_to_date`). Refuerzos en el esquema: id determinista como clave primaria e índice único parcial sobre `(tenant_id, currency, service_key)` donde `observation = 'observed' AND status IN ('new','investigating')`.

**D7. Lectura diaria con las protecciones de billing.** Nuevo método de `Database` que reutiliza el mismo filtrado que `fetch_billing_summary` (ingestas completadas, tenant en las dos tablas, conflicto por suscripción y día dentro del rango leído → `AmbiguousCostSource`) y devuelve `(usage_date, currency, service, sum(pretax_cost), count)` más la lista de días observados del tenant. Rango leído: desde 7 días antes del primer día a evaluar hasta el último día completo. Se ejecuta dentro de la transacción de D6.

**D8. Modelo de datos (migración `002_anomaly_episodes` del backend).** `anomaly_episodes`: `id` (`anomaly-` + sha256 de `[1, tenant_id, rules_version, currency, service, start_date]`), `tenant_id`, `currency`, `service` (nulo permitido) y `service_key` (clave no nula para el índice único), `start_date`, `last_seen_date`, `observation`, `no_longer_observed_on`, `reference_daily_cost`, `opening_observed_cost`, `accumulated_impact`, `impact_day_count`, `impact_through_date`, `severity`, `status`, `status_changed_by`, `status_changed_at`, `first_reviewed_at`, `first_reviewed_by`, `closed_at`, `closure_reason`, `previous_episode_id`, `rules_version`, `rules` (JSONB con umbrales), `created_at`, `updated_at`. Importes como `DECIMAL` sin escala fija y expuestos como cadenas de dos decimales. Todas las consultas llevan `tenant_id`.

**D9. API bajo `/billing/anomalies/`.** `POST /detect` (sin cuerpo), `GET /episodes?scope=open|all` (por defecto `open`), `GET /episodes/{id}` y `PATCH /episodes/{id}` con `{status, reason?}`. Códigos de estado en inglés como en JUP-019 (`new`, `investigating`, `resolved`, `false_positive`); las etiquetas en español son del panel. Mismo 404 para ajeno o inexistente, como pide JUP-086 para endpoints con ids opacos. El cambio de estado usa un `UPDATE … WHERE id AND tenant_id AND status = :esperado` para que dos cambios simultáneos no se pisen. Alternativa descartada: nuevo prefijo `/anomalies`; se mantiene junto a la consulta de JUP-030.

**D10. Reglas versionadas.** `rules_version = "jup019-daily-v1"` con un objeto de reglas (porcentaje, incremento, días de referencia, tolerancia, tramos y monedas) definido en un único sitio del servicio y copiado en cada episodio.

**D11. Lo que no se toca y dónde queda escrito.** La consulta de JUP-030 sigue con `>=` y reglas independientes; la diferencia se documenta en `docs/api/cost-anomalies.md`, en `docs/api/anomaly-episodes.md` y en el ADR, con una prueba del límite exacto del 20 %. El documento de reglas del corpus no se modifica; se registra un hallazgo para incorporar las aclaraciones (lo esperado, criticidad por acumulado, estados del MVP) con JUP-038, regenerando las huellas en cadena.

## Risks / Trade-offs

- [Datos que llegan tarde a un día ya evaluado] → se excluye el último día con datos; el resto queda como limitación documentada.
- [Pulsaciones separadas más de 7 días dejan días sin evaluar] → la respuesta informa del rango no evaluado; la puesta al día completa es obligatoria en la etapa 2 (ADR).
- [Ciclos semanales y media inflada tras un pico] → candidatas, no anomalías confirmadas; una persona las marca como falso positivo; línea base predictiva como trabajo futuro.
- [Cerrar como resuelta con el gasto aún alto] → la media de 7 días puede no volver a saltar; limitación en el ADR y en la API.
- [Criticidad por impacto acumulado es una interpretación de "EUR/mes"] → pendiente de confirmar con la responsable de las reglas antes de archivar; el cambio sería solo de la función de tramos y de los textos.
- [Umbrales nominales en USD] → 1 USD se trata como 1 EUR a efectos de umbral; otras monedas no se evalúan; conversión como trabajo futuro.
- [Conflictos 40001 en CockroachDB] → 409 sin escrituras parciales y prueba con dos ejecuciones simultáneas contra CockroachDB real.
- [Pruebas con CockroachDB real no corren en CI (RF-107-002)] → se ejecutan en local con nodo desechable y se registra en la evidencia.

## Migration Plan

La migración `002` solo crea tablas e índices nuevos; se aplica al arrancar el backend como la `001`. No modifica datos existentes. Rollback: desplegar la versión anterior deja las tablas sin usar; borrarlas no afecta a nada más.

## Open Questions

- Confirmación de la responsable de las reglas de negocio sobre la criticidad por impacto acumulado (no cambia la estructura del change, solo los tramos si dijera otra cosa).
