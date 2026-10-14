JUP: JUP-121
Trello: https://trello.com/c/aIdxwsXR

## Why

Los resultados de las evaluaciones del asistente están repartidos en informes sueltos: dos ejecuciones de JUP-070, el benchmark de modelos de JUP-078, la calibración de la recuperación de JUP-022 y los registros de negocio de JUP-068. Cada uno tiene su propio formato y ninguno se puede comparar con otra ejecución sin abrirlo a mano. El único dashboard de Grafana (JUP-043) muestra señales en vivo y no sirve para saber si el asistente responde bien ni si ha empeorado entre dos ejecuciones. Con las entregas del 23/10 y el 29/10 cerca, el equipo necesita una vista única que separe calidad medida, valor de negocio y salud del sistema, y que diga en cada caso qué no demuestra.

## What Changes

- Nuevo dashboard de Grafana dedicado a los resultados de evaluación del asistente, versionado y provisionado junto al de métricas técnicas. Tiene tres secciones que no se mezclan:
  - **A. Calidad con preguntas con rúbrica**: JUP-070 (ACC, REL, GRD, LAT, STR, AVL), calibración de JUP-022 y benchmark de JUP-078.
  - **B. Métricas de negocio**: informe de JUP-068.
  - **C. Señales en vivo**: síntomas a partir de las métricas que ya emite el backend.
- Cada panel indica su tipo (A, B o C), qué mide y qué no demuestra.
- Un adaptador por tipo de informe convierte cada informe en filas planas: ejecución, fuente, grupo, conducta, estado, recuento y valor, junto con los metadatos de la ejecución (batería, versión, commit, modelo, fecha y tipo de ejecución).
- Los valores no medidos (null, `available=false`, `blocked`, `not_run`) se guardan y se muestran como no medidos, nunca como 0 %.
- Las ejecuciones de plantilla, con dobles, sintéticas o sin modelo verificado se distinguen visiblemente de las ejecuciones con modelo real.
- Evolución en el tiempo para la sección A: una serie por batería y configuración comparable, con anotaciones cuando cambia la batería, el modelo, el prompt o el corpus. Si no hay otra ejecución comparable, el panel muestra «Sin datos: no hay con qué comparar». Las series automáticas se separan de las que dependen de juicio humano.
- Un único comando documentado regenera los datos del dashboard a partir de un manifiesto versionado de informes de hito. Se le pueden añadir manifiestos locales fuera de Git.
- Los resultados se guardan en un esquema propio de la base PostgreSQL existente y Grafana los lee con su datasource PostgreSQL integrado y un rol de solo lectura (ADR-0022).
- El formato de filas planas queda documentado como contrato de entrada para la robustez de JUP-071, que todavía no existe. La sección de robustez aparece en el dashboard y muestra «Sin datos» mientras no haya filas.
- Pruebas que concilian los recuentos del dashboard con los de cada informe original, y que comprueban que en la base no hay texto de preguntas ni de respuestas.

Este change no cambia baterías, métricas, fórmulas ni umbrales. Tampoco ejecuta campañas nuevas, dispara evaluaciones tras un despliegue, añade alertas (JUP-046) ni evalúa respuestas reales de usuarios. El adaptador y los datos de robustez son de JUP-071.

## Capabilities

### New Capabilities

- `assistant-evaluation-dashboard`: normalización de los informes de evaluación a filas planas, carga reproducible con un único comando y dashboard de Grafana con las secciones A, B y C, su evolución en el tiempo y el tratamiento explícito de lo no medido y de las ejecuciones no reales.

### Modified Capabilities

Ninguna. El dashboard de métricas técnicas de JUP-043 (`technical-metrics`) no cambia. La sección C del nuevo dashboard lo enlaza y añade sus propios paneles de síntomas sobre métricas ya emitidas.

## Impact

- **Monitorización**: nuevo dashboard en `apps/monitoring/grafana/dashboards/` y nuevo datasource PostgreSQL en `apps/monitoring/grafana/provisioning/datasources/`.
- **Compose**: Grafana recibe la contraseña del rol de solo lectura por una variable de entorno nueva y obligatoria, que se añade a `.env.example`. Hay que actualizar `tools/docker-topology.test.mjs`.
- **Base de datos**: esquema `evaluation` en `postgres-pgvector`, con tablas de ejecuciones y resultados y un rol `SELECT` solo sobre ese esquema. El esquema de embeddings no cambia.
- **Herramientas**: nueva herramienta en `tools/` con sus pruebas en `scripts/tests/`, scripts `corepack pnpm` y su inclusión en el paso «Validate governance tooling» de la CI.
- **Documentación**: ADR-0022, guía del dashboard y del comando de regeneración, contrato de filas planas para JUP-071 y fila en `docs/continuidad/`.
- **Dependencias**: ninguna librería ni plugin nuevo. Se usan la biblioteca estándar de Python, `psql` del contenedor existente y el datasource PostgreSQL que ya trae Grafana 11.3.
- **Relacionadas**: JUP-071 (consumirá el contrato), JUP-046 (alertas, fuera de alcance), JUP-035, JUP-109 y JUP-065 (figura para la memoria y la demo).
