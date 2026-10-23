# JUP-133 — CI de develop después del PR156

Comprobado el **23/10/2026 19:48 (Europe/Paris)** sobre `db8f69ab5e2d4a42931cd6dc7412b99e855f0148`. PR156 integrado mediante squash el 23/10 a las 19:38:28 París. Diagnóstico de solo lectura; sin correcciones, reejecuciones de CI, cargas ni inferencias.

## Estado observado

| Workflow / trabajo | Estado |
| --- | --- |
| [CI](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39996735445) | failure |
| Landing static checks | success |
| OpenSpec | failure |
| Frontend build | success |
| Frontend type check | success |
| AWS PostgreSQL application | success |
| Python tests (backend) | success |
| Python tests (azure-cost-api) | success |
| AWS demo offline | success |
| Python tests (processor) | success |
| JUP policy | skipped |
| [CD DockerServer](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39996735531) | failure |
| validate / OpenSpec | failure |
| validate / Frontend build | success |
| validate / Landing static checks | success |
| validate / Python tests (azure-cost-api) | success |
| validate / AWS PostgreSQL application | success |
| validate / Python tests (backend) | success |
| validate / Frontend type check | success |
| validate / Python tests (processor) | success |
| validate / AWS demo offline | success |
| validate / JUP policy | skipped |
| DockerServer deployment eligible | skipped |

## Bloqueo de integración y promoción

El job **OpenSpec** falla en `Validate governance tooling`, al ejecutar `evaluation-dashboard:test`: **1960 pruebas, 110 fallos, 30 errores y 2 omitidas**. La ejecución de `openspec:validate`, situada después, no llega a realizarse; el nombre del job no prueba un defecto de las especificaciones. El CD repite exactamente esos recuentos y no puede declarar esta revisión elegible para DockerServer.

Causas contrastadas en logs y fuentes:

- Expectativas y listas de fixtures antiguas: 12 ejecuciones / 647 filas frente a 18 / 1670; orden, fechas, identidad declarada del modelo y selección de la campaña más reciente también cambian. Los escenarios que insertaban una campaña de prueba de 14/10 ahora compiten con las del 23/10.
- 29 errores de permisos son en cadena por el montaje: los helpers exigen mensajes de 16 o 14 ejecuciones y reciben 22 o 20 tras sumar sus fixtures locales. No acreditan por sí solos una vulneración de permisos. El error restante es un IndexError al indexar la lista antigua de IDs.
- La prueba de altura detecta una matriz de 51 filas, altura 52, frente al mínimo 57 de su contrato. No basta con cambiar todos los contadores: hace falta revisar también presentación y aislamiento de las pruebas.

Las tres pruebas focales fallidas documentadas antes del merge eran un subconjunto. La CI completa confirma un alcance mayor; no son 140 incidencias independientes del modelo. Las comprobaciones AWS demo offline y PostgreSQL pasan en este SHA. El fallo de processor en la CI previa de develop `3d4e574` fue un timeout de 8 minutos instalando herramientas de extracción; se mantiene separado del resultado actual.

## Bloqueos para aceptación de la entrega

- La RC sigue como **demo con incidencias**, no aceptada integralmente. El último ensayo documentado conserva 003 (no propone investigación), 004 (afirmación sobre todo el corpus sin soporte) y 025 (completa tras truncado/EOF y reintentos; estabilidad no acreditada). Este diagnóstico no repite ese ensayo.
- Las campañas nuevas conservan 13 operaciones sin respuesta verificable. La revisión de 158 respuestas por un único juez IA es provisional: no acredita doble revisión humana ni aceptación formal.
- Siguen sin medirse distancias, tiempos por etapa, disponibilidad HTTP y otros campos que el contrato de captura no aporta; el agregador completo JUP-070 continúa bloqueado. El modelo generador está declarado, no atestiguado.

Siguiente trabajo acotado: reconciliar fixtures/selección de campañas y el contrato visual del dashboard con los datos nuevos, conservar las pruebas de permisos y atomicidad, ejecutar la suite afectada y comprobar CI/CD completos. La aceptación funcional debe resolverse aparte; una CI verde no la sustituye. Sin cambios a accesos, cuotas o al tope de 10 USD en esta comprobación.

Referencias: [demo congelada](../JUP-065-frozen-demo-20261023.md), [revisión del juez IA](JUP-133-agent-review-report.md), [estado JSON](JUP-133-develop-ci-report.json). Logs y snapshots privados: `materiales/07-evidencias/JUP-133-campanas-infra-20261023/agent-review/develop-*.{log,json}` del workspace.

Origen: «Levantar Jupiter en dockerDevelop», `01a16421-03a0-7460-b110-24738407ccb1`.
