# Episodios de anomalias de coste

JUP-114 — [Trello](https://trello.com/c/F492abeY). Contrato HTTP version 1.
Decision: [ADR-0019](../adr/ADR-0019-cost-anomaly-episodes.md). Fuentes
ejecutables: [schema](../../apps/backend/app/schemas/anomaly_episodes.py),
[servicio](../../apps/backend/app/services/anomaly_episodes.py),
[acceso a datos](../../apps/backend/app/db/database.py),
[migracion](../../apps/backend/app/db/migrations/002_anomaly_episodes.py) y
[rutas](../../apps/backend/app/api/routes/billing.py).

Un episodio es una anomalia **candidata** guardada para un tenant, una moneda y
un servicio: se abre el dia en que salta la regla diaria de negocio de JUP-019 y
se sigue mientras vuelva a saltar. Se puede listar, priorizar por criticidad e
impacto y seguir su estado. No es una causa demostrada ni un ahorro, y no se
avisa a nadie (la ejecucion periodica y los avisos son de una etapa posterior).
La evaluacion de [cost-anomalies.md](cost-anomalies.md) sigue existiendo como
consulta de prueba sin guardar y no toca estos episodios.

## Acceso

Todas las rutas requieren el bearer de la sesion y `X-Tenant-Id` con
pertenencia comprobada, igual que `/billing/summary`. La autenticacion (401), la
cabecera (400) y la pertenencia (403) se resuelven antes de leer costes o
episodios. Cualquier miembro del tenant activo puede detectar y cambiar
estados; no hay permisos por rol.

| Ruta | Uso |
| --- | --- |
| `POST /billing/anomalies/detect` | «Detectar ahora». Sin cuerpo: un cuerpo no vacio da 422, despues de comprobar sesion, cabecera y pertenencia. |
| `GET /billing/anomalies/episodes?scope=open\|all` | Lista; por defecto `open` (`new` e `investigating`). Solo lee: nunca detecta. |
| `GET /billing/anomalies/episodes/{id}` | Un episodio del tenant activo. |
| `PATCH /billing/anomalies/episodes/{id}` | Cambio de estado con `{"status": ..., "reason": ...}`. |

Un `id` de otro tenant y un `id` inexistente devuelven el mismo
`404 {"detail":{"code":"anomaly_episode_not_found"}}`. Los `id` son
deterministas (`anomaly-` + SHA-256 de version, tenant, reglas, moneda, servicio
y dia de inicio), pero no autorizan nada: todas las consultas filtran por el
tenant activo.

## Regla y lo esperado

Para cada servicio y moneda del tenant, cada dia evaluable:

```text
esperado = media diaria de los 7 dias anteriores
           (o la referencia anclada del episodio en seguimiento)
salta si   esperado > 0
           AND observado - esperado > 100
           AND (observado - esperado) * 100 > esperado * 20
```

- **Coste diario observado:** suma exacta de los registros de ingestas
  completadas del tenant con esa `usage_date`, agrupados por moneda y servicio.
  Un servicio vacio o en blanco es un grupo propio (`service: null`); el
  servicio distingue mayusculas. Un servicio sin registros en un dia con datos
  del tenant cuenta 0,00. Nunca se divide un agregado de periodo entre dias.
- **Limites estrictos y las dos condiciones a la vez.** Una subida de
  exactamente 100 o exactamente el 20 % no salta (la consulta de prueba de
  JUP-030, con `>=` y reglas independientes, si la marcaria).
- **Comparacion exacta:** se compara contra la suma de los 7 dias (multiplicando
  el observado por 7), sin redondear la media.
- **Monedas:** umbrales nominales en EUR y USD, sin conversion. Otras monedas no
  se evaluan; la ejecucion las devuelve en `unsupported_currencies`.
- **Referencia anclada:** mientras un episodio esta en seguimiento (`new` o
  `investigating` y `observed`), su servicio se compara con la media de los 7
  dias previos a su inicio, para que una subida que se queda siga viendose.

## Dias evaluables y ejecucion

- El ultimo dia con datos del tenant se considera incompleto: el **ultimo dia
  completo** es el anterior, y nunca hoy (UTC) ni despues.
- Un dia es evaluable si el y sus 7 dias anteriores tienen algun registro del
  tenant en cualquier moneda. Si no, se salta con `not_observed` o
  `reference_incomplete` y no abre, extiende, termina ni suma impacto.
- Cada tenant guarda hasta que dia se evaluo. Una ejecucion evalua, en orden,
  los dias posteriores hasta el ultimo dia completo, como maximo los 7 mas
  recientes; en la primera, los 7 dias que terminan en el ultimo dia completo.
  Si quedan dias mas antiguos sin evaluar, la respuesta los devuelve en
  `unevaluated_range`.
- Repetir sin dias nuevos devuelve `up_to_date` y no cambia nada. Sin ningun
  dia evaluable devuelve `insufficient_data` y no guarda nada.
- La ejecucion es una sola transaccion: si dos coinciden, una devuelve
  `409 {"detail":{"code":"detection_conflict"}}` sin escribir nada; fuentes de
  coste solapadas en el rango leido devuelven
  `409 {"detail":{"code":"ambiguous_cost_source"}}` sin escribir nada.

Respuesta de `POST /billing/anomalies/detect`:

| Campo | Significado |
| --- | --- |
| `status` | `completed`, `up_to_date` o `insufficient_data`. |
| `rules_version` | `jup019-daily-v1`. |
| `last_complete_day` | Ultimo dia completo, o null sin datos. |
| `evaluated_days`, `skipped_days` | Dias evaluados y saltados con su motivo. |
| `unevaluated_range` | Dias pendientes que no se evaluaron por el limite de 7, o null. |
| `unsupported_currencies` | Monedas presentes en la ventana que no se evaluan. |
| `opened`, `continued`, `no_longer_observed` | Episodios abiertos, que volvieron a saltar y que dejaron de observarse en esta ejecucion. |

## Episodio, impacto y criticidad

- Se abre con estado `new` y observacion `observed` el primer dia que salta.
- Si vuelve a saltar dentro de **3 dias** desde la ultima vez, es el mismo
  episodio (`last_seen_date`). Si pasa un dia evaluado a mas de 3 dias sin
  saltar, pasa a `no_longer_observed` con `no_longer_observed_on`; el estado no
  cambia y lo cierra una persona.
- Un episodio cerrado o no observado no se reabre: si el servicio vuelve a
  saltar, se abre otro con `previous_episode_id` apuntando al anterior.
- **Impacto acumulado:** suma, en cada dia evaluado mientras esta en
  seguimiento, de `max(0, observado - referencia)`; `impact_day_count` y
  `impact_through_date` dicen que dias cuentan. Deja de crecer cuando ya no esta
  en seguimiento.
- **Criticidad** sobre el impacto acumulado, en la moneda del episodio:
  `P1` mayor que 2000, `P2` de 500 a 2000 (ambos incluidos), `P3` menor que 500.
  Se calcula con el impacto exacto, antes de redondear para mostrarlo: un
  impacto de 499,996 se muestra como `500.00` y es `P3`. Es la lectura de los
  tramos «EUR/mes» de JUP-019 como impacto del episodio; pendiente de
  confirmar con la responsable de las reglas de negocio.

La lista se ordena por criticidad (P1 a P3), impacto descendente, inicio mas
reciente e `id`. Cada episodio muestra su impacto en su moneda; no hay totales
entre monedas.

Campos de cada episodio: `id`, `kind: cost_anomaly_candidate`, `currency`,
`service`, `start_date`, `last_seen_date`, `observation`,
`no_longer_observed_on`, `reference_daily_cost`, `opening_observed_cost`,
`accumulated_impact`, `impact_day_count`, `impact_through_date`, `severity`,
`status`, `status_changed_by`, `status_changed_at`, `first_reviewed_at`,
`first_reviewed_by`,
`closed_at`, `closure_reason`, `previous_episode_id`, `rules_version`, `rules`
(umbrales con los que se abrio), `cause_status: not_established`,
`limitations`, `created_at` y `updated_at`. Los importes son cadenas con dos
decimales (HALF_UP); internamente se guardan exactos.

## Estados

| Desde | Hacia |
| --- | --- |
| `new` | `investigating`, `resolved`, `false_positive` |
| `investigating` | `resolved`, `false_positive` |
| `resolved`, `false_positive` | ninguno (409) |

- `resolved` y `false_positive` exigen `reason` de 1 a 500 caracteres tras
  quitar espacios, sin caracteres de control ni invisibles (categorias Unicode
  `C*`, `Zl` y `Zp`: por ejemplo U+0085, U+202E, U+2028 o un espacio de ancho
  cero) y con al menos un caracter visible (un motivo de solo rellenos como
  U+3164 o U+2800 o de marcas combinantes sueltas se rechaza); `investigating`
  no la admite.
  Peticiones invalidas o con campos extra dan 422 sin cambiar nada.
- Una transicion no permitida da
  `409 {"detail":{"code":"invalid_status_transition"}}`. Dos cambios
  simultaneos dejan exactamente uno; el que pierde la carrera recibe
  `409 {"detail":{"code":"invalid_status_transition"}}` si al releer ya no es
  valido, o `409 {"detail":{"code":"status_change_conflict"}}` si la base de
  datos abortó la transaccion: se puede reintentar.
- Se guarda quien (`status_changed_by`, id de usuario) y cuando
  (`status_changed_at`) hizo el ultimo cambio, quien y cuando hizo el primer
  cambio desde `new` (`first_reviewed_by` y `first_reviewed_at`, para el tiempo
  hasta reconocimiento, MTTA) y el cierre (`closed_at`, para el tiempo hasta
  resolucion, MTTR). No se guarda el historico completo de cambios.

## Ejemplo reproducible con doble explicito

Desde la raiz del repositorio, con las dependencias Python del backend. No
accede a Cockroach ni a HTTP: aplica la regla a una serie sintetica.

```python
import sys
sys.path.insert(0, "apps/backend")
from datetime import date, timedelta
from decimal import Decimal
from app.services.anomaly_episodes import detection_window, plan_detection

start = date(2026, 9, 1)
values = ["400.00"] * 7 + ["550.00", "650.00", "400.00"]
daily = {("EUR", "Compute"): {start + timedelta(days=i): Decimal(v) for i, v in enumerate(values)}}
window = detection_window(today=date(2026, 10, 12), last_evaluated=None,
                          latest_observed=date(2026, 9, 10))
plan = plan_detection(window, tenant_id="example-tenant", observed_days=set(daily[("EUR", "Compute")]),
                      daily=daily, episodes=[])
[episode] = plan.opened
print(plan.status, [d.isoformat() for d in plan.evaluated_days])
print(episode.start_date, episode.last_seen_date, episode.reference_daily_cost,
      episode.accumulated_impact, episode.impact_day_count, episode.severity)
```

Salida:

```text
completed ['2026-09-08', '2026-09-09']
2026-09-08 2026-09-09 400.00 400.00 2 P3
```

El 10 de septiembre es el ultimo dia con datos y no se evalua; del 3 al 7 se
saltan porque no tienen 7 dias previos con datos. El 8 sube 150 sobre 400 y abre
el episodio; el 9 sube 250 y lo continua; el impacto acumulado es 400.

## Consumo por JUP-038

JUP-038 explica episodios guardados: por que se abrieron (referencia, observado,
reglas y version), cuanto llevan (impacto acumulado y criticidad), en que estado
estan y sus limitaciones, sin recalcularlos ni atribuir causa o ahorro. La
adaptacion al envelope comun de herramientas (correlation ID, source, evidence
IDs, assumptions y limitations) corresponde al consumidor; estas rutas no
registran ninguna herramienta del agente.

## Limitaciones

- Un dia puede evaluarse antes de que lleguen datos tardios; no se reevalua.
- Si entre dos ejecuciones pasan mas de 7 dias, los anteriores no se evaluan
  (se devuelven en `unevaluated_range`). La ejecucion periodica de la etapa 2
  debe poner al dia todos los dias pendientes.
- Un gasto nuevo desde cero no abre episodio (no hay porcentaje).
- Los ciclos semanales pueden dar candidatas falsas y un pico reciente infla la
  media de 7 dias.
- Si se cierra un episodio con el gasto aun alto, la media puede no volver a
  saltar.
- Solo se vigila el servicio; solo EUR y USD, con umbrales nominales (1 USD
  cuenta como 1 EUR a efectos de umbral).
- Los nombres de servicio son datos del tenant: no publicarlos en logs o
  evidencia compartida indiscriminadamente.
