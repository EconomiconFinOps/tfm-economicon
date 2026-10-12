# Deteccion de anomalias de coste — JUP-030

Verificacion: 2026-10-10; retomada el 2026-10-11 (ver el final). Encargo: «Implementa JUP-030 — Detectar anomalias de coste».
Origen conocido: despacho desde chat `01a1248a-4e9e-7963-a891-5d8cb49345a6`;
identificador del chat de implementacion no suministrado.

- [Tarjeta](https://trello.com/c/ScxJi1TO), P1 Valor FinOps. Descripcion y roles
  contrastados el 10/10 mediante `DockerServer:/home/danteadmin/economicon-collaboration`.
- Rama propia `feat/JUP-030-cost-anomalies`, worktree `tfm-economicon-jup030`,
  base `origin/develop` `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
  Checkout compartido y trabajo previo de otras tarjetas preservados.
- Contribucion publicada en [PR #91](https://github.com/EconomiconFinOps/tfm-economicon/pull/91),
  borrador contra develop; codigo verificado `0b35a72`. No se declara
  revision, validacion humana, merge ni cierre de tarjeta.
- Trello enlaza PR, contrato, evidencia y limites mediante comentario
  `6ac9ebeafa9f85a51f1b7647` del puente oficial. Se conserva columna Backlog;
  no se cambian roles, prioridades, criterios ni fechas.
- Liderazgo Lucia Mateo; pairing Paris Arcos Martin; revision Victor Mendez;
  validacion Alejandro Aguado. Asignaciones conservadas, sin acreditar participacion.
  La contribucion tecnica automatizada no sustituye ninguno de esos dictamenes.

## Alcance y decisiones

POST autenticado `/billing/anomalies/evaluate`: reglas configurables por
importe absoluto o aumento frente al periodo anterior de igual duracion,
con divisa explicita, grupos y pruebas. Reutiliza billing v2; no introduce
otra consulta SQL ni modifica el panel demo de JUP-057.

El resultado entrega candidatos y evidencia versionada para JUP-038:
costes, periodos, reglas, calidad, identificador estable y huella de evidencia.
La causa permanece `not_established`. Comparar agregados no demuestra anomalia
estadistica, causalidad, ahorro ni integridad temporal de la ingesta.
No se convierten divisas ni se rellenan datos ausentes con ceros.

Contrato y ejemplos: [cost-anomalies.md](../api/cost-anomalies.md).
OpenSpec: [jup-030-cost-anomalies](../../openspec/changes/archive/2026-10-11-jup-030-cost-anomalies/proposal.md).
La regla diaria del contrato JUP-084 (`>20%` y `>100 EUR/day`) es diferente:
no se declara implementada por este evaluador de periodos configurables.

## Verificacion y siguientes pasos

La evidencia tecnica por criterio se registra en
[JUP-030-validation.md](../evidence/JUP-030-validation.md).
150 pruebas focales pasaron sin omisiones, incluidas dos nuevas contra
CockroachDB v24.1.11. Regresion backend: 997 PASS, 21 integraciones externas
omitidas; compilacion PASS. OpenSpec 56/56; gobernanza 89 tests PASS.
CI del codigo `0b35a72`: siete checks tecnicos SUCCESS en run `38035032995`.
`JUP reviews` pendiente de review y validacion humanas, como corresponde al draft.
Entorno exclusivo Linux eliminado al terminar; los intentos Windows lentos
interrumpidos no se cuentan como evidencia favorable.
Pendientes: participacion real, review y validacion independientes, integracion
del consumidor JUP-038, alertas persistentes/notificaciones y conexion del panel.
Mantener esos limites al evaluar el cierre de la tarjeta; no marcarla Hecho
por la sola existencia de la contribucion tecnica. No se enviaron mensajes Discord.

## Retomada (2026-10-11)

El PR #91 se cerro el 10/10 sin integrar. La contribucion se retoma en la rama `feat/JUP-030-anomaly-evaluator`, desde `develop` y con los dos commits originales de Alejandro (autoria conservada). Se aplica la excepcion temporal: revision adversarial independiente (sin hallazgos graves, un hueco de test cerrado), validacion propia y aprobacion de Lucia en `review.md`; no se piden reviews de otras personas. Cuatro hallazgos menores quedan registrados y aceptados (`RF-030-001` a `004`). El panel `/anomalies` sigue con datos de demostracion y su conexion es un paso aparte; se repitio la validacion con Docker: 181 pruebas con CockroachDB real (cero omitidas) y 13 llamadas HTTP con el dataset publico, con importes iguales a los calculados con SQL independiente (ver `docs/evidence/JUP-030-validation.md`).

## Episodios guardados — JUP-114 (2026-10-12)

[Tarjeta JUP-114](https://trello.com/c/F492abeY), liderada por Lucia Mateo, se divide en tres changes en la misma rama y un solo PR al final (como JUP-107; decision de Lucia del 12/10). El primero, `jup-114-persisted-anomalies` (rama `feat/JUP-114-anomaly-circuit`), guarda **episodios** de anomalia por tenant, moneda y servicio con la regla diaria de negocio de JUP-019, referencia anclada, impacto acumulado, criticidad P1/P2/P3 y estados `new`, `investigating`, `resolved` y `false_positive`; API en [anomaly-episodes.md](../api/anomaly-episodes.md) y decision en [ADR-0020](../adr/ADR-0020-cost-anomaly-episodes.md). La evaluacion de JUP-030 no cambia y queda como consulta de prueba sin guardar.

- Decisiones de Lucia del 12/10, en el ADR: episodio con tolerancia de 3 dias, regla diaria (se descarto la semanal), referencia anclada, criticidad por impacto acumulado (pendiente de confirmar con Paris), umbrales nominales en EUR y USD, «Detectar ahora» con un maximo de 7 dias pendientes por pulsacion, cualquier miembro del tenant cambia estados.
- El documento de reglas del corpus no se toca: esta fijado por huella en las evaluaciones de JUP-022, JUP-069 y JUP-070 (`RF-114-001`, para JUP-038).
- Siguientes changes: `jup-114-anomalies-panel-live` (panel `/anomalies` y datos de demo, incluida la limpieza de episodios al retirarlos, `RF-114-007`) y la tarjeta [JUP-115](https://trello.com/c/0wQKN1yz), planeada antes como el change `jup-114-anomaly-alerts-schedule`, (ejecucion periodica y avisos; la puesta al dia completa ya la hace la deteccion desde el change 2, `RF-114-006` resuelto).
- JUP-038 (explicar anomalias en el chat) esta en espera hasta que se mergee el PR unico de JUP-114 (los tres changes), no al terminar el change 1.
- **Change 1 archivado el 12/10** (`openspec/changes/archive/2026-10-12-jup-114-persisted-anomalies/`) con dos pasadas de revision adversarial (la segunda `accept`), validacion con stack real (18/18) y aprobacion de Lucia; specs `cost-anomaly-episodes` (nueva), `cost-anomaly-detection` y `finops-agent-tool-contract` sincronizadas; evidencia en [JUP-114-validation.md](../evidence/JUP-114-validation.md); hallazgos `RF-114-001` a `RF-114-010`. Sin PR todavia: el PR unico se abre al terminar el change 3.
- **Change 2 archivado el 12/10** (`openspec/changes/archive/2026-10-12-jup-114-anomalies-panel-live/`, misma rama, sin PR): revision adversarial en dos pasadas (la segunda `accept`), validacion con stack real y aprobacion de Lucia; evidencia en [JUP-114-validation.md](../evidence/JUP-114-validation.md), hallazgos `RF-114-011` a `015` abiertos y `RF-114-012` aceptado como riesgo conocido del PR; specs `anomalies-panel`, `cost-anomaly-episodes`, `synthetic-anomaly-data` y `synthetic-cost-demo` sincronizadas. Contenido: deteccion sin limite de 7 dias (`RF-114-006` resuelto), lista con «Revisado hasta», indicador sintetico y total abierto exacto por moneda; panel `/anomalies` conectado (resumen, tabla, filtros, «Detectar ahora», detalle con cambio de estado y exportacion CSV/PDF con escape de HTML y de formulas); conjunto de demo diario (134 registros) con P1, P2 y P3 y `remove` que limpia episodios (`RF-114-007`); demo de 3 minutos con el paso D12. Decisiones de UX de Lucia del 12/10 recogidas en el diseño y las specs del change.

## Etapa 2 (ejecución periódica y avisos) fuera del MVP — 2026-10-12

Decisión de Lucia, con los hitos delante: el change 3 (la tarjeta [JUP-115](https://trello.com/c/0wQKN1yz), planeada antes como el change `jup-114-anomaly-alerts-schedule`,) **no se hace antes de la entrega**: el 12/10 la etapa 2 se separó de JUP-114 y pasó a «80 — Después del MVP». La congelación interna del código fue el 9/10, la de la memoria es el 16/10, el ensayo de la demo el 20/10 y la entrega el 23/10. El PR único de JUP-114 lleva los changes 1 y 2 (etapas 1 y 3 de la tarjeta, sin la etapa 2). El criterio «(Etapa 2) se avisa de las anomalías antes del cierre» queda **sin cumplir** en el MVP y la memoria debe contarlo como trabajo futuro, no como hecho. La división de la tarjeta en Trello la decide Lucia.

Exploración hecha el 12/10, para retomarla sin repetir la investigación:

- **Qué hay:** no existe ningún planificador en las apps (solo el timer de despliegue de `infra/cd`). El único precedente de avisos es JUP-045: regla de Grafana provisionada como código y **sin receptor externo**, por decisión del equipo para no reabrir la política de Discord solo lectura de JUP-081. No hay SMTP ni webhooks.
- **Qué ayuda:** la detección ya es idempotente, usa una marca de agua por tenant y lee los días de los datos, no del reloj, así que repetirla es barato y se pone al día sola. Las tablas de anomalías son del backend (ADR-0011): el trabajo periódico debe ejecutar `Database.run_anomaly_detection` del backend, no el processor.
- **Tres cautelas:** (1) la ingesta tampoco es periódica (`run_azure_cost_ingestion` es manual), así que detectar a menudo solo vigila lo que ya haya entrado; hay que escribirlo en la spec. (2) El guion de demo empieza con el panel sin detectar (D1), así que el planificador debe venir **apagado por defecto**. (3) Un fallo periódico no puede ser silencioso: hay que guardar la última ejecución automática y su resultado (migración nueva) y enseñarlo en el panel.
- **Dónde correría:** servicio Compose propio con la imagen del backend y bucle con intervalo configurable (recomendado), hilo dentro del backend (como el publisher de RabbitMQ) o timer del sistema.
- **Qué sería «avisar»:** nivel 1, dentro de la app (insignia «N nuevas, M P1» con el estado `new`, que ya significa «nadie lo ha mirado», y aviso en el panel); nivel 2, nivel 1 más una regla de Grafana sobre una métrica de P1 abiertas, como JUP-045; nivel 3, salida externa (webhook, correo, Discord), que choca con JUP-081 y exige secretos y reintentos. Recomendación: nivel 1 como primer incremento.
- **«Antes de cierre»:** se interpretó como detectar a diario para que aparezca días antes del cierre mensual, sin cuenta atrás; una cuenta atrás exigiría modelar un calendario de cierre que no existe.
