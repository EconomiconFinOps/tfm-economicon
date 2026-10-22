# ADR-0022 — Resultados de evaluación del asistente en Grafana desde PostgreSQL

- Status: Proposed
- Date: 2026-10-14
- Related JUP/OpenSpec: JUP-121, [jup-121-assistant-evaluation-dashboard](../../openspec/changes/archive/2026-10-15-jup-121-assistant-evaluation-dashboard/design.md)
- Trello: https://trello.com/c/aIdxwsXR
- Supersedes: none
- Superseded by: none

## Context

Los resultados de las evaluaciones del asistente están repartidos en informes sueltos con formatos distintos: las ejecuciones de JUP-070 (`docs/evidence/JUP-070-run-{1,2}-report.json`), el benchmark de modelos de JUP-078, la calibración de la recuperación de JUP-022 y los registros de negocio de JUP-068. JUP-121 los reúne en un dashboard de Grafana y necesita tres cosas que condicionan cómo llegan los datos:

1. **Series con la fecha real de cada ejecución.** Las ejecuciones se hacen cuando el equipo las lanza, no cuando se carga el informe. La evolución en el tiempo y las anotaciones de cambio de batería, modelo, prompt o corpus dependen de esa fecha.
2. **Lo no medido tiene que seguir siendo no medido.** Un `null`, una métrica con `available=false` o un caso `blocked` o `not_run` no puede llegar al panel como 0 %.
3. **Solo ejecuciones de hito en Git.** Los informes con texto de preguntas o de respuestas viven fuera del repositorio y las ejecuciones que no son de hito no se versionan; el dashboard debe poder mostrar ambas, y regenerarse con un único comando.

El estado actual de Grafana es ADR-0005: Prometheus como único datasource y un dashboard provisionado desde ficheros. Prometheus fecha cada muestra al ingerirla y aplica una retención corta, así que no sirve para estas series.

## Decision

1. **Los resultados se guardan en PostgreSQL.** Un esquema `evaluation` en la base de `postgres-pgvector` que ya existe en Compose, con una tabla de ejecuciones (`runs`), una de resultados (`results`) y una vista de cambios de configuración (`config_changes`). Grafana lo lee con su datasource PostgreSQL integrado (uid `evaluation-postgres`), provisionado desde un fichero versionado.
2. **Acceso de solo lectura.** Grafana entra con el rol `grafana_evaluation_reader`, que tiene `USAGE` y `SELECT` únicamente sobre el esquema `evaluation`. Su contraseña llega por `GRAFANA_EVALUATION_DB_PASSWORD`, obligatoria en Compose y sin valor en `.env.example`.
3. **Los informes siguen siendo la fuente de verdad.** La base es una proyección que se regenera y se puede tirar: `corepack pnpm evaluation-dashboard:load` lee un manifiesto versionado (`docs/validation/evaluation-runs.json`) con los informes de hito, admite manifiestos locales fuera de Git para las demás ejecuciones y reemplaza los datos de forma atómica e idempotente.
4. **Un adaptador por tipo de informe.** Cada adaptador convierte su informe a filas planas (ejecución, fuente, grupo, conducta, estado, recuento, valor y denominador) sin recalcular métricas. El formato de filas planas `rows-v1` es el contrato de entrada para informes futuros, en particular el de robustez de JUP-071.
5. **Lo no medido se guarda como `NULL`** con el estado `not_measured`, y los paneles lo muestran como «No medido»; nunca como 0 %. Una serie sin otra ejecución comparable muestra «Sin datos: no hay con qué comparar».
6. **La herramienta usa solo la biblioteca estándar de Python y el `psql` del contenedor.** Genera un script SQL transaccional y lo envía por la entrada estándar a `docker compose exec`; no añade librerías ni plugins.

## Consequences

- Las series usan la fecha de cada ejecución, los `NULL` se conservan y las anotaciones salen de una consulta SQL.
- Perder el volumen de la base no pierde datos de hito: basta con volver a ejecutar la carga.
- Grafana tiene ahora un segundo datasource y una variable de entorno obligatoria más. Si falta, Compose no arranca, también en DockerServer, y habrá que avisar a quien lo mantiene antes del merge.
- Antes de la primera carga, los paneles de las secciones A y B muestran error de relación inexistente; la guía pone la carga justo después de `docker compose up`.
- El esquema de evaluación comparte instancia con los embeddings. El aislamiento es por esquema y por rol; borrar `evaluation` no toca las tablas de embeddings.
- Las ejecuciones que no son de hito solo existen en la base local de quien las carga; no se comparten por Git.
- Hoy casi todas las ejecuciones son de plantilla, con dobles o sintéticas; el dashboard las rotula y no las presenta como calidad del asistente.

## Alternatives Considered

- **Pushgateway hacia Prometheus:** descartada; Pushgateway no acepta marcas de tiempo, así que cada ejecución quedaría fechada al subirla, y la retención de Prometheus borraría el histórico.
- **Volcado con `promtool tsdb create-blocks-from`:** descartada; arrastra el mismo problema de retención y es una operación delicada.
- **Datasource TestData con los datos dentro del JSON del dashboard:** descartada; es un datasource de pruebas, tiene pocas anotaciones y obliga a commitear el dashboard en cada ejecución, lo que choca con «en Git solo las de hito».
- **Plugin Infinity leyendo un endpoint del backend:** descartada; hay que fijar un plugin externo que se descarga al arrancar y añadir al backend una API que no necesita.
- **Un PostgreSQL aparte para evaluación:** descartada; es un servicio más que mantener y el esquema con su rol ya dan el aislamiento necesario.
- **Cargar desde el backend:** descartada; mezcla la evaluación con la API del producto.

## Evidence And Follow-up

- Diseño y decisiones de detalle: [design.md](../../openspec/changes/archive/2026-10-15-jup-121-assistant-evaluation-dashboard/design.md). Requisitos: [spec.md](../../openspec/changes/archive/2026-10-15-jup-121-assistant-evaluation-dashboard/specs/assistant-evaluation-dashboard/spec.md).
- Seguimiento: JUP-071 cargará la robustez por `rows-v1`. JUP-046 (alertas sobre degradación) y la carga automática tras cada despliegue quedan fuera de este ADR.
- Pendiente: que la CD de DockerServer (JUP-052) ejecute la carga tras desplegar, si el equipo lo decide.
- Estado `Proposed` hasta la revisión del pull request; la evidencia de validación se enlazará desde `docs/evidence/JUP-121-validation.md`.

## Amendment — JUP-133 (2026-10-21)

La clave de comparabilidad identificaba el modelo de generación solo por el alias del gateway. Al cambiar el modelo por defecto del chat (JUP-132) sin cambiar el alias, ejecuciones con modelos distintos habrían compartido serie. Se amplía el contrato `rows-v1` y el esquema `evaluation.runs` con `generation_model_id`, `generation_provider`, `generation_quantization` y `gateway_config_sha256`; la clave de comparabilidad los incorpora solo cuando alguno está registrado, de modo que las claves anteriores no cambian, y el manifiesto admite `model_identity` para rotular el historial sin editar los informes. No cambia la decisión de este ADR. Detalle: [design.md](../../openspec/changes/archive/2026-10-22-jup-133-reevaluacion-metricas-modelo/design.md) y [guía](../validation/evaluation-dashboard.md#identidad-del-modelo-de-generación-jup-133).
