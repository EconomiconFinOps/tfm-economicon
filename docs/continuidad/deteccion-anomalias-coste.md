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
- JUP-038 (explicar anomalias en el chat) estaba en espera del PR de JUP-114: el PR #122 se mergeo el 12/10, asi que Lucia puede liberarlo (la etapa 2 ya no forma parte de JUP-114).
- **Change 1 archivado el 12/10** (`openspec/changes/archive/2026-10-12-jup-114-persisted-anomalies/`) con dos pasadas de revision adversarial (la segunda `accept`), validacion con stack real (18/18) y aprobacion de Lucia; specs `cost-anomaly-episodes` (nueva), `cost-anomaly-detection` y `finops-agent-tool-contract` sincronizadas; evidencia en [JUP-114-validation.md](../evidence/JUP-114-validation.md); hallazgos `RF-114-001` a `RF-114-010`. Sin PR todavia: el PR unico se abre al terminar el change 3.
- **Change 2 archivado el 12/10** (`openspec/changes/archive/2026-10-12-jup-114-anomalies-panel-live/`, misma rama, sin PR): revision adversarial en dos pasadas (la segunda `accept`), validacion con stack real y aprobacion de Lucia; evidencia en [JUP-114-validation.md](../evidence/JUP-114-validation.md), hallazgos `RF-114-011` a `015` abiertos y `RF-114-012` aceptado como riesgo conocido del PR; specs `anomalies-panel`, `cost-anomaly-episodes`, `synthetic-anomaly-data` y `synthetic-cost-demo` sincronizadas. Contenido: deteccion sin limite de 7 dias (`RF-114-006` resuelto), lista con «Revisado hasta», indicador sintetico y total abierto exacto por moneda; panel `/anomalies` conectado (resumen, tabla, filtros, «Detectar ahora», detalle con cambio de estado y exportacion CSV con escape de formulas (el PDF se retiro del panel en la validacion del PR #122)); conjunto de demo diario (134 registros) con P1, P2 y P3 y `remove` que limpia episodios (`RF-114-007`); demo de 3 minutos con el paso D12. Decisiones de UX de Lucia del 12/10 recogidas en el diseño y las specs del change.

## PR #122 mergeado — 2026-10-12

Los dos changes se integraron en `develop` con un solo PR (`2175c60`). Revisión de Víctor Mendez (cambios pedidos y atendidos: recarga fallida sin cifras anteriores, pruebas del resumen y del cambio de cliente, documentación, ADR renumerado a ADR-0020) y validación de Paris Arcos, que encontró que el cambio de estado fallaba en el navegador porque CORS no permitía `PATCH`; se arregló y el panel exporta ya solo CSV (el PDF no era verificable). La validación final la publicó Víctor bajo la excepción de misma persona porque la de Paris quedó descartada, así que no es independiente de la revisión. Notas no bloqueantes de esa revisión, llevadas a un PR aparte de documentación: `README` y ADR-0007 del backend con los métodos de CORS, `RF-104-004`, los días hasta P1 de un servicio nuevo (12, no 16) y el hallazgo `RF-114-018` (id de usuario y hora ISO en el detalle).

## Etapa 2 (ejecución periódica y avisos) fuera del MVP — 2026-10-12

Decisión de Lucia, con los hitos delante: el change 3 (la tarjeta [JUP-115](https://trello.com/c/0wQKN1yz), planeada antes como el change `jup-114-anomaly-alerts-schedule`,) **no se hace antes de la entrega**: el 12/10 la etapa 2 se separó de JUP-114 y pasó a «80 — Después del MVP». La congelación interna del código fue el 9/10, la de la memoria es el 16/10, el ensayo de la demo el 20/10 y la entrega el 23/10. El PR único de JUP-114 lleva los changes 1 y 2 (etapas 1 y 3 de la tarjeta, sin la etapa 2). El criterio «(Etapa 2) se avisa de las anomalías antes del cierre» queda **sin cumplir** en el MVP y la memoria debe contarlo como trabajo futuro, no como hecho. La división de la tarjeta en Trello la decide Lucia.

Exploración hecha el 12/10, para retomarla sin repetir la investigación:

- **Qué hay:** no existe ningún planificador en las apps (solo el timer de despliegue de `infra/cd`). El único precedente de avisos es JUP-045: regla de Grafana provisionada como código y **sin receptor externo**, por decisión del equipo para no reabrir la política de Discord solo lectura de JUP-081. No hay SMTP ni webhooks.
- **Qué ayuda:** la detección ya es idempotente, usa una marca de agua por tenant y lee los días de los datos, no del reloj, así que repetirla es barato y se pone al día sola. Las tablas de anomalías son del backend (ADR-0011): el trabajo periódico debe ejecutar `Database.run_anomaly_detection` del backend, no el processor.
- **Tres cautelas:** (1) la ingesta tampoco es periódica (`run_azure_cost_ingestion` es manual), así que detectar a menudo solo vigila lo que ya haya entrado; hay que escribirlo en la spec. (2) El guion de demo empieza con el panel sin detectar (D1), así que el planificador debe venir **apagado por defecto**. (3) Un fallo periódico no puede ser silencioso: hay que guardar la última ejecución automática y su resultado (migración nueva) y enseñarlo en el panel.
- **Dónde correría:** servicio Compose propio con la imagen del backend y bucle con intervalo configurable (recomendado), hilo dentro del backend (como el publisher de RabbitMQ) o timer del sistema.
- **Qué sería «avisar»:** nivel 1, dentro de la app (insignia «N nuevas, M P1» con el estado `new`, que ya significa «nadie lo ha mirado», y aviso en el panel); nivel 2, nivel 1 más una regla de Grafana sobre una métrica de P1 abiertas, como JUP-045; nivel 3, salida externa (webhook, correo, Discord), que choca con JUP-081 y exige secretos y reintentos. Recomendación: nivel 1 como primer incremento.
- **«Antes de cierre»:** se interpretó como detectar a diario para que aparezca días antes del cierre mensual, sin cuenta atrás; una cuenta atrás exigiría modelar un calendario de cierre que no existe.

## Incorporación en la base de B — 2026-10-15

Al reconciliar JUP-123 se comprobó que la base develop de A/8ea5a0c4 es
`0543c5ee671cb1b400254561f5bdc6e419664510`, cuyo commit incorpora la explicación
de anomalías de #128. El estado «sin PR» del corte13/10 inferior es histórico.
No se han vuelto a comprobar las reviews o la CI de #128 en este corte.

B/7be57c05 incluye ese código y las resoluciones de A en assistant.py y
AnswerEvidence.tsx, conservando el caller atómico y la evidencia. Pruebas propias
del conjunto:550 backend PASS/141 omisiones que necesitan SQL nativo y1354 frontend
PASS; regresión Linux/SQL aún en curso. No trasladar las validaciones históricas
de JUP-038 al conjunto B. Origen: chat `01a1270c-e332-7462-9c90-706d49ade92c`;
alcance, hashes y siguiente paso en [evaluación local](chat-evaluacion-local.md)
y [división A/B](chat-entregas-a-b.md).

## Corte histórico: explicar anomalías — JUP-038 (2026-10-13)

[Tarjeta JUP-038](https://trello.com/c/QzkjVY7P), liderada por Víctor Mendez (pairing Paris Arcos Martin, revisión Lucía Mateo, validación, pruebas y documentación Alejandro Aguado). El PR #94 se cerró sin integrar el 10/10 y **no se reutiliza ni su rama ni su código**: se reinició desde `develop` (`2175c60`, con el PR #122 de JUP-114) en la rama `feat/JUP-038-explain-anomaly-episodes`, change `jup-038-explain-anomaly-episodes`. Estado: implementado y validado en la rama, change archivado el 13/10 (`openspec/changes/archive/2026-10-13-jup-038-explain-anomaly-episodes/`), **sin PR abierta todavía**; la revisión de Lucía y la validación independiente de Alejandro siguen pendientes.

- **Qué hace:** el usuario elige un episodio guardado y el asistente responde con una explicación **determinista, sin modelo generativo** (patrón de JUP-037): por qué se abrió (referencia, observado, diferencia absoluta y porcentual frente a los umbrales de `jup019-daily-v1`), cuánto lleva (impacto acumulado, días y severidad P1/P2/P3), en qué estado está y sus limitaciones. Siempre como candidata, sin causa raíz, ahorro ni conversión de moneda. Contrato en [anomaly-explanations.md](../api/anomaly-explanations.md), con un ejemplo real.
- **Cómo se pide:** enlace «Explicar en el asistente» en el detalle del panel `/anomalies` (abre `/assistant?episode=<id>`) o casilla «Explicar una anomalía» en el redactor. El cuerpo lleva `anomaly_query` (`episode_id`), nunca tenant ni usuario; un id ajeno o inexistente da el mismo 404 `anomaly_episode_not_found`.
- **Fotografía fijada:** la respuesta se guarda en la conversación con su evidencia (`anomaly_evidence`, id por sha256 y `explained_at`), porque el episodio cambia con el tiempo. Las diferencias y porcentajes salen de los operandos exactos de la tabla (12 decimales), con un único redondeo, no de las cadenas redondeadas de la API.
- **Piezas:** el explicador es una función pura (`explain_episode` en `services/anomaly_explanations.py`) que JUP-035 podrá envolver como la herramienta `detect_cost_anomaly_candidates`; **este change no registra ninguna herramienta del agente** (`RF-038-006`). La lectura es `fetch_anomaly_episode_snapshot` (una sola consulta con el tenant de la sesión). Sin migración nueva y sin ADR nuevo: nota fechada en [ADR-0020](../adr/ADR-0020-cost-anomaly-episodes.md).
- **Aplazado:** las aclaraciones del corpus del asistente (`RF-114-001`, punto 11 del ADR-0020) siguen `Open`: el documento está fijado por sha256 en JUP-069, JUP-022 y JUP-070 y cambiarlo obliga a regenerar huellas y repetir la calibración. Hallazgos nuevos `RF-038-001` a `009` en el backlog; las pruebas intermitentes de JUP-098 en esta máquina ya estaban en `RF-098-004` y `RF-103-005`.
- **Validación hecha:** pruebas por grupo con mutación, regresión con CockroachDB real y con configuración de CI, y recorrido en un navegador real con el stack aislado (capturas e informes en `docs/evidence/JUP-038/`), con la explicación de Compute recalculada de forma independiente. Detalle, conteos y lo no validado en [JUP-038-validation.md](../evidence/JUP-038-validation.md).
- **Conflictos previstos con JUP-035 (PR #120 y #121):** este change añade cambios en `routes/assistant.py` y `AnswerEvidence.tsx`, además del conflicto que `AnomaliesPanel.tsx` ya tenía; quien integre debe usar `append_pair` también en la rama `anomaly_query` (`RF-038-005`).
