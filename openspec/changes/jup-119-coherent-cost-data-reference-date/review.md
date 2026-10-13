# Revisión de jup-119-coherent-cost-data-reference-date

JUP: JUP-119 · [Trello](https://trello.com/c/HtjtmPaJ) · ADR: [ADR-0021](../../../docs/adr/ADR-0021-demo-cost-data-single-path-and-reference-date.md) · Evidencia: [JUP-119-validation.md](../../../docs/evidence/JUP-119-validation.md)

## Resumen

Los datos de demostración entran por una sola ruta (generador → API simulada de demo → ingesta del processor, con `scripts/demo_data.py`), en una ventana común del 1 de julio al 30 de octubre de 2026, solo con servicio y etiqueta `Project`; un servicio del backend decide el «hoy» (`COST_REFERENCE_DATE`) y el frontend lo lee de `GET /billing/reference-date`. El paquete de demo se rehízo y los scripts antiguos de carga se retiraron.

## Decisiones

- Ruta única con dos agrupaciones y los casos raros de JUP-106 como pruebas (sondeo con CockroachDB real; ver el ADR-0021).
- La carga usa una llamada a la CLI por pareja: una primera medida de 133 s por llamada era un artefacto de usar `localhost` en el DSN en Windows (espera de IPv6), no la inicialización de la base; con `127.0.0.1` la carga completa tarda 23,9 s.
- Episodios ocultos al retroceder la fecha (visibles solo si el último día de su impacto es anterior a la referencia); confirmado por Lucia.
- Ventana común del 1/7 al 30/10 para todo; carga opt-in con el perfil `demo` de Compose.
- La referencia que reproduce JUP-107 es el 21/9 (último día evaluado: 20/9); la del final de los datos es el 30/10 (último día evaluado: 29/10), porque el último día con datos nunca se da por completo.

## Validación

Ver [la evidencia](../../../docs/evidence/JUP-119-validation.md): batería completa (backend con CockroachDB real, processor, API simulada, frontend, scripts, Compose y comprobaciones del repositorio), stack aislado real con la receta de navegador (12 pasos `pass` y control positivo) y las tres pantallas con campos ausentes vistas en la interfaz real.

Fallos de entorno que no son de este change: las cuatro suites de salud del proveedor del backend (`ProactorEventLoop`, `RF-119-004`), un reinicio del CockroachDB del Compose por lentitud de disco (`RF-119-008`) y una prueba del frontend con tiempo de espera ajustado (`quality-gates`) que falla bajo carga de CPU y pasa en solitario.

## Adversarial Review (pass 1)

Revisor independiente (agente `adversarial-reviewer`), sobre `bfaf3983..c998e3ee`. Veredicto: **changes-requested**; sin BLOCKING, 1 HIGH, 3 MEDIUM, 2 LOW.

| ID | Severidad | Descripción | Resolución |
| --- | --- | --- | --- |
| ADV-1 | HIGH | La prueba de cobertura de la ventana no nombraba la suscripción y solo vigilaba lo de fuera de la ventana para filas `synthetic-` (una fila pública fuera de ventana pasaba). | Corregido: `coverage_gaps` nombra el tenant, sus suscripciones y el día, y vigila todas las filas sea cual sea su origen; pruebas con una fila pública del 2026-06-01 y del 2026-11-15. |
| ADV-2 | MEDIUM | `demo_data.py` solo se negaba con `RUNTIME_ENVIRONMENT == "production"` exacto; `Production`, `prod`, `staging` o vacío cargaban. | Corregido con lista blanca (`development` o `test`, valor exacto); prueba con nueve valores para `apply` y `remove` y spec actualizada. |
| ADV-3 | MEDIUM | El manifiesto no nombraba una definición de ingesta por suscripción. | Corregido: cada pareja lleva `definition`, el cargador usa la de cada pareja y una prueba lo exige. |
| ADV-4 | MEDIUM | Una ingesta original del dataset público de una suscripción que la demo también usa no se veía como ajena y `remove` la borraría. | Reproducido con CockroachDB real y corregido: una ingesta es de la demo solo si su petición guardada es una de las definiciones de la demo; lo demás es `other-data`, `apply` se niega y `remove` no lo borra. Prueba extremo a extremo y de unidad. |
| ADV-5 | LOW | `COST_REFERENCE_DATE=9999-12-31` o `0001-01-01` se aceptaba y fallaba con `OverflowError` en la primera lectura. | Corregido: el validador acepta de 1900-01-02 a 9998-12-29; pruebas con los extremos. |
| ADV-6 | LOW | La guía de JUP-106 seguía listando comandos de inserción directa del script retirado. | Corregido: los comandos se sustituyen por una nota de que son históricos y por la ruta actual. |

Ataques que resistieron (resumen del revisor): fecha de referencia inválida, ninguna otra lectura del reloj para decidir el día, los siete caminos de lectura de coste, el día de referencia incluido y el siguiente excluido, los registros sin fecha, la regla de ambigüedad sobre el periodo recortado, los episodios (lista, detalle y cambio de estado comparten el filtro y dan el mismo 404), el indicador sintético, el validador del frontend y los números del conjunto de datos recalculados sin el código del change.

Fuera de su alcance: no tenía CockroachDB ni el stack real, así que las pruebas con base de datos real, la detección de extremo a extremo y la receta de navegador no se revisaron por ejecución; esas están cubiertas por la evidencia.

## Adversarial Review (pass 2)

Mismo revisor, sobre `bfaf3983..ce075b7f`. Veredicto: **changes-requested**; sin BLOCKING, 2 HIGH, 2 MEDIUM, 3 LOW. Los cuatro puntos nuevos que se le pidieron atacar (distinción de ingestas propias y ajenas, lista blanca de entorno, definición por pareja y rango del validador) resistieron.

| ID | Severidad | Descripción | Resolución |
| --- | --- | --- | --- |
| ADV-1 | HIGH | La spec decía que el panel ejecutivo abre en el mes de la fecha de referencia, pero abre (desde antes de este change) los seis meses completos anteriores. | La spec era la que se pasaba: corregida para fijar lo que el panel hace y la prueba de frontend ya comprobaba (con la referencia en 2026-10-15, abril a septiembre de 2026). El compositor del asistente enseña el mes de referencia, y eso también queda dicho. No cambia el código. |
| ADV-2 | HIGH | La guía mandaba ejecutar `remove` ante `other-data`, pero `remove` no retira datos ajenos: bucle sin salida. | Corregida: `partial` se arregla con `remove`; `other-data` exige retirar las filas a mano o recrear el stack con volúmenes nuevos. |
| ADV-3 | MEDIUM | Los stacks cargados con los scripts retirados dejaban filas `synthetic-jup106-*` y `synthetic-jup107-*` como datos ajenos sin aviso de migración. | Añadida la nota en la preparación y en la guía de datos (`down -v` o SQL). |
| ADV-4 | MEDIUM | El cuerpo de la guía de JUP-106 seguía describiendo la herramienta antigua sin marcarlo como histórico. | El apartado queda titulado «histórico: describe la herramienta retirada», con la nota de comandos no ejecutables. |
| ADV-5 | LOW | La spec decía que el mensaje nombra `COST_REFERENCE_DATE` y el mensaje nombra el campo `cost_reference_date`. | Spec ajustada a «nombra el ajuste (`cost_reference_date`)». |
| ADV-6 | LOW | `run_ingestion` no tenía tiempo límite y descartaba la causa del fallo. | Corregido con prueba primero: tiempo límite de 600 s y causa (código de error de la CLI o «se agotó el tiempo») sin imprimir nunca el entorno ni stderr. |
| ADV-7 | LOW | «Idempotente bajo concurrencia» no está comprobado para dos `apply` simultáneos. | Se quita la afirmación de la guía y se registra como `RF-119-009`. |

Además, el revisor señaló que `.claude/skills/economicon-stack/scripts/cargar_demo.py` (local, no versionado) usaba una lista negra de `production`; se pasó a lista blanca, igual que `demo_data.py`. No pudo construir un episodio cuyo `no_longer_observed_on` quede más allá de la referencia con `impact_through_date` anterior: queda como `RF-119-010`.

## Adversarial Review (pass 3)

Mismo revisor, sobre `bfaf3983..d89cf402`, con CockroachDB real. Veredicto: **accept**; sin BLOCKING ni HIGH, 3 MEDIUM, 5 LOW. Se atendieron todos con prueba primero salvo ADV-8, que queda como observación en el backlog.

| ID | Severidad | Descripción | Resolución |
| --- | --- | --- | --- |
| ADV-1 | MEDIUM | Con la referencia igual a `no_longer_observed_on`, un episodio se listaba como «ya no observado» desde un día incompleto (el filtro solo miraba `impact_through_date`). | Reproducido con CockroachDB real y corregido: el episodio es visible si `impact_through_date` y `no_longer_observed_on` son anteriores a la referencia. Una prueba lo cubre (y sustituye la anterior, que fijaba la regla vieja); spec, diseño y guía actualizados; `RF-119-010` queda resuelto. |
| ADV-2 | MEDIUM | El texto de la pregunta de responsables decía «no se muestran datos posteriores» (sugiere que existen) y no indicaba el tramo contado. | Reproducido y corregido: el texto ya no lo dice y añade «Solo se cuentan los días hasta el ..., inclusive» cuando el periodo pedido pasa de la referencia; un mes futuro no añade nada. Pruebas ajustadas y guía de la API actualizada. |
| ADV-3 | MEDIUM | Un refresco fallido de la fecha de referencia, con el dato ya cargado, sustituía el panel ejecutivo por el error. | Reproducido con una prueba de componente (foco de ventana + fallo del segundo GET) y corregido: el error solo sustituye al panel si no hay dato. Mismo patrón en el compositor del asistente. |
| ADV-4 | LOW | Diseño y tareas citaban un `_clamp_end` único que no existe. | Texto corregido: el tope se aplica en los puntos de lectura con el helper único `visible_end`. |
| ADV-5 | LOW | La guarda del reloj no veía `now.date()` ni el reloj de SQL. | Nueva guarda sobre `.date()`, `CURRENT_DATE`, `current_date` y `now()` con un control positivo. |
| ADV-6 | LOW | El manifiesto de la demo no declaraba que los datos son sintéticos o desplazados. | Campo `notice` en el manifiesto con prueba; la propuesta ya no habla de una etiqueta por fila. |
| ADV-7 | LOW | `apply` con un tenant presente y otro ausente decía «partial en tenant-core (present)». | El mensaje lista cada tenant con su estado; prueba nueva. |
| ADV-8 | LOW | `COST_REFERENCE_DATE` no se limita por entorno. | Observación sin requisito: `RF-119-011`. |

Ataques que resistieron (resumen del revisor): fechas inválidas y sus extremos, las siete lecturas con el tope, episodios ocultos con el mismo 404 y detección con la referencia retrocedida, cifras de las guías recalculadas desde el CSV, cuatro mutaciones del generador, cargador con la API equivocada y con DSN rotos, lista blanca de entorno y Compose.

Fuera de su alcance: receta de navegador y UI con otra referencia, dos `apply` a la vez (`RF-119-009`) y el perfil `demo` levantado de verdad.

## Barrido de patrones

- Comparación exacta de `RUNTIME_ENVIRONMENT` (ADV-2): `scripts/demo_data.py` (corregido); el Compose usa `${RUNTIME_ENVIRONMENT:-production}`, que trata el vacío como producción; `cargar_demo.py` de la skill local no se versiona.
- Comprobaciones de la ventana que dependían de un prefijo de origen (ADV-1): solo `test_demo_dataset.py`.
- Aritmética de fecha sin límites (ADV-5): `reference_date.py` y `fetch_anomaly_episode_list`, cubiertos por el rango del validador.
- Datos de una suscripción de la demo escritos por otra ingesta (ADV-4): `SqlStore` en `scripts/demo_data.py`.
- Lecturas del reloj para decidir el día visible: dos pruebas barren `apps/backend/app` (ninguna fuera del servicio de fecha de referencia); el processor no lee fechas de billing.
- Menciones a los scripts retirados: barrido registrado en la tarea 7.4; los registros históricos (`docs/evidence/JUP-106|107|114|047`, `docs/contributions/JUP-064-*`) se dejan como estaban.

## Riesgos

- El tope por fecha es de lectura, no de acceso: los datos posteriores existen en la base (`RF-119-007`). Probado en lo que cubre (11 + 4 pruebas con CockroachDB real) y documentado.
- Sin ensayo humano de la demo: la receta de navegador es una ejecución automatizada.
- La interfaz con una referencia distinta de 2026-10-30 solo se recorrió en la guía de anomalías con 2026-09-21 (tres episodios, «Revisado hasta el 20/09/2026»); las pantallas de costes y el asistente con otra fecha, y el retroceso de la fecha con episodios ya detectados, los cubren las pruebas de backend y de frontend.
- Hallazgos del change registrados en `openspec/findings/backlog.md` (`RF-119-001` a `RF-119-011`).

## ADR

Sí aplica: ADR-0021 (nuevo). Enlaza ADR-0001 (la API simulada pasa a servir también un CSV de demo) y ADR-0020 (los episodios obedecen a la fecha de referencia).
