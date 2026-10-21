# Dashboard de resultados de evaluación del asistente — JUP-121

Última actualización documental: 2026-10-16. Esta nota no repite el alcance de la tarjeta, que vive en [Trello](https://trello.com/c/aIdxwsXR).

## Comparativa GLM/DeepSeek: soporte preparado — 18/10/2026

Autorización humana excepcional en HAL 9000
`01a1270c-e332-7462-9c90-706d49ade92c`: publicar cifras históricas,
incorporarlas a Grafana y regularizar el ADR, sin tocar PR63.
Integración aislada en `docs/JUP-063-model-comparison-publication`, base
`6d9e6710`; no cambia roles ni presume dictámenes de los implementadores.

Se añade `jup-063-paired-v1` y un manifiesto suplementario: un run del informe,
dos modelos y18 filas agregadas. Panel25 separado del resto de campañas;
los tres contadores de rúbrica local provisional usan `judgment=null`, sólo en
`paired_local_provisional`. Sus medidas técnicas conservan `automatic`.
No se inventa adjudicación humana/automática ni aceptación de calidad actual.
[Datos y procedencia](../evidence/JUP-063/glm-deepseek-20261016/README.md) y
[guía de carga limitada](../validation/evaluation-glm-deepseek.md).

`sql --preserve-existing` prepara una transacción limitada a la identidad/huella
de este run, sin DDL, roles, permisos oTRUNCATE; conserva otras ejecuciones.
No aplicar `load` histórico a un destino compartido: regenera toda la proyección.
El destino conocido de configuración es `postgres-pgvector:5432`, base
`embeddings`, esquema `evaluation`, datasource `evaluation-postgres`, dashboard
`economicon-assistant-evaluation`; esto no identifica un stack remoto vigente.

La prueba PG opt-in preparada comprueba sentinel/rollback/idempotencia yconsulta
del panel. **No ejecutada en PostgreSQL real ni Grafana live**: la aprobación
automática rechazó transferir seis archivos públicos de prueba a DockerServer
por falta de autorización humana específica para ese destino/payload. No se
transfirió ni arrancó nada, y no se busca una vía alternativa.

La guardia integrada completa ejecutó1862 tests y encontró6 fallos de contratos
nuevos del panel más4 fallos promtool/DockerWindows `invalid mode:/t`. Se corrigió
el rótulo/mapping de clasificación y se amplió el orden esperado expresamente,
sin eliminar controles:118 pruebas afectadas PASS en el candidato integrado.
Los cuatro promtool siguen sin acreditar ejecución: archivo de pruebas y
expresiones Prometheus idénticos a develop6d9e6710, fallo de mount previo al
arranque. No se declara toda la suite local verde ni se atribuye un resultadoPG.
OpenSpec81/81 y trazabilidad10 cambios PASS. Publicación normal autorizada tras
la guardia ROOT; el estado remoto/CI se consulta en la PR de esta rama. Sin merge
autorizado. Los siguientes apartados conservan su corte histórico del16/10.

## Estado

- Rama `feat/JUP-121-assistant-evaluation-dashboard`, creada desde `develop`; `origin/develop` integrado dos veces (JUP-120 y JUP-122). PR [#132](https://github.com/EconomiconFinOps/tfm-economicon/pull/132) abierta. Paris pidió cambios (`local:doctor` con la variable nueva) y Lucia dejó un comentario de pairing con mejoras de lectura; ambos se atienden en el change `jup-121-lectura-dashboard` ([archivado](../../openspec/changes/archive/2026-10-16-jup-121-lectura-dashboard/)), pendiente de revalidación. Las segundas revisiones (anotaciones de la latencia, estado de casos solo de JUP-070, contrato de clasificación para JUP-071, orden de la sección A, títulos de C y fecha de la matriz) se resuelven en el change `jup-121-anotaciones-y-fuente` ([archivado](../../openspec/changes/archive/2026-10-16-jup-121-anotaciones-y-fuente/)).
- OpenSpec: `openspec/changes/archive/2026-10-15-jup-121-assistant-evaluation-dashboard/` (propuesta, diseño, spec, tareas y `review.md` con la evidencia por tarea). ADR: [ADR-0022](../adr/ADR-0022-assistant-evaluation-results-in-grafana.md), en estado Proposed.
- Guía y contrato de datos: [evaluation-dashboard.md](../validation/evaluation-dashboard.md). Manifiesto versionado: [evaluation-runs.json](../validation/evaluation-runs.json). Evidencia: [JUP-121-validation.md](../evidence/JUP-121-validation.md) y capturas en `docs/evidence/JUP-121/`.
- Producto: `tools/evaluation-dashboard.py` (adaptadores, SQL, carga, rol), `apps/monitoring/grafana/dashboards/assistant-evaluation.json` (24 paneles, secciones A, B y C, con resumen de la última campaña, matriz por métrica y ejecución y evolución de la latencia), datasource `evaluation-postgres.yml`, variable `GRAFANA_EVALUATION_DB_PASSWORD` en `docker-compose.yml` y `.env.example`, scripts `evaluation-dashboard:*` y un paso de CI. Cambio mínimo en el backend: `assistant.py` crea a 0 las series de `backend_retrieval_failures_total`.

## Decisiones que no se deducen del código

- **PostgreSQL nativo como fuente** (esquema `evaluation` en el `postgres-pgvector` existente, rol `grafana_evaluation_reader` de solo lectura) y no Pushgateway, JSON directo ni un endpoint propio: Prometheus fecha lo que ingiere con la hora de ingesta, no la de la ejecución, y el datasource JSON necesita un plugin que no está instalado. Los informes siguen siendo la fuente de verdad; la base es una proyección que se tira y se recarga.
- **Contrato `rows-v1`:** JUP-071 (robustez) no existe aún; entra emitiendo ese formato o con su propio adaptador. Mientras tanto la sección de robustez muestra «Sin datos».
- **Lo no medido nunca es 0 %.** Las ejecuciones de plantilla, dobles o sintéticas se rotulan «no real» y sus series van discontinuas. Una serie con menos de dos puntos medidos no se dibuja.
- **Latencia y disponibilidad de campaña (tipo A) y de tráfico real (tipo C) no se mezclan** en un panel.
- **El `load` necesita la pila de Compose levantada y el `.env` completo**; la contraseña de Grafana y la de `load` son la misma variable.

- **La matriz «Resultados por métrica y ejecución» pivota con `groupingToMatrix`** (una columna por ejecución, funciona con texto en Grafana 11.3.0), pero la transformación no ordena las filas: la consulta cruza las ejecuciones con el catálogo de métricas y ordena en SQL. Los nombres legibles salen de un `CASE` con las 17 métricas de JUP-067 (una prueba exige que cubra el catálogo entero). Las tablas por fila se conservan como «detalle» porque la conciliación con los informes originales las usa. Todo el dashboard va en UTC.

## Qué tocar si cambia algo

- Un informe nuevo: añadir su adaptador a `tools/evaluation-dashboard.py` o emitir `rows-v1`, y una entrada en el manifiesto; el dashboard no cambia. Comprobar con `corepack pnpm evaluation-dashboard:rows`.
- Un panel: editar `assistant-evaluation.json` (las pruebas estructurales exigen tipo A/B/C, «Mide:» y «No demuestra:», un solo datasource por panel y los textos de «Sin datos»).
- Una categoría nueva de fallo de recuperación: se añade a `FAILURE_CATEGORIES` y la serie a 0 sale sola.
- Regenerar los datos: `corepack pnpm evaluation-dashboard:load`; pruebas: `corepack pnpm evaluation-dashboard:test` (las que usan PostgreSQL real necesitan Docker).

## Pendiente

- Revalidación de Paris y revisión técnica de Alejandro sobre el candidato corregido; respuesta a los comentarios de la PR #132.
- Añadir `GRAFANA_EVALUATION_DB_PASSWORD` al `.env` local y al de DockerServer antes de levantar la pila: `docker compose` se niega a arrancar sin ella.
- Tarjeta de pulido del dashboard (por crear en Trello, la crea el líder): columnas repetidas, referencias JUP en el texto visible, descripciones de los ⓘ, calibración y benchmark en español, sección C sin duplicar el dashboard técnico y gráficas para la sección B y la calibración (propuestas de Lucia). Las tablas «(detalle)» se movieron al final de la sección A pero no se pliegan, porque una fila plegada anida sus paneles y la conciliación recorre los de primer nivel.
- Hallazgos diferidos con su detalle en `openspec/findings/backlog.md` (cargas simultáneas, contraseña en claro en el `ALTER ROLE` si el servidor registra sentencias, y otros de severidad baja).
- La robustez espera a JUP-071; la validación en DockerServer y la primera ejecución de la CI en GitHub no se han hecho.


## Reconciliación documental de PR141 — 19/10/2026

Por orden humana de HAL9000, PR141 incorpora develop `f444ba11e38203b6cfd645a098fd9946d55955e3` sobre el incremento `3274abcf78439b7fd260085df4ccfeaf51d98cb4`. Único conflicto manual: índice de continuidad; se conserva la documentación aportada por ambas ramas. Los cambios de la base se incorporan sin reimplementar ni modificar otra PR. Adaptador, panel, fuentes, contratos y ADR de la comparativa se preservan; sus identidades y pruebas afectadas se comprobarán antes de publicar el candidato.

El usuario autorizó expresamente sustituir revisión y validación humanas por dos agentes independientes de implementación para este incremento de PR141/JUP063. Sus informes separados sobre3274 no se convierten en aprobaciones humanas ni se trasladan sin comprobar el delta. No se alteran checks/protecciones ni se autoriza merge. El hallazgo P2 del resumen de cleanup del runner se conserva como precisión pendiente, fuera de esta reconciliación documental; el retiro histórico fue comprobado independientemente.

La nota histórica de transferencia/PG NOT_RUN del18/10 queda superada por el recibo posterior [6254995818](https://github.com/EconomiconFinOps/tfm-economicon/pull/141#issuecomment-6254995818): PostgreSQL17.11,16controlesPASS y retiro confirmado, con las seis huellas originales como ámbito. Se reutiliza esa evidencia sólo si el candidato conserva sus entradas; no implica nueva ejecución ni Grafana live. No se ha cargado ni verificado dashboard desplegado, ni hay nueva inferencia, gasto o aceptación semántica de campañas. No se repiten recursos ni se opera sobre servicios compartidos. CI y confirmación incremental del candidato reconciliado se registrarán por su identidad exacta en PR141; no se atribuyen antes de comprobarlas.
