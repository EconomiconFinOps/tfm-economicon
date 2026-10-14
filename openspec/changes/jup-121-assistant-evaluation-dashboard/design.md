JUP: JUP-121 · ADR: [ADR-0022](../../../docs/adr/ADR-0022-assistant-evaluation-results-in-grafana.md)

## Context

La motivación está en `proposal.md` (Why) y el comportamiento exigido, en `specs/assistant-evaluation-dashboard/spec.md`. Este diseño solo recoge el estado actual que condiciona la solución.

- **Grafana 11.3.0** en `docker-compose.yml`, con provisioning por fichero. Tiene un único datasource, Prometheus (uid `prometheus`), y un único dashboard, `technical-metrics.json` (uid `economicon-technical-metrics`), de JUP-043 y ADR-0005. Ninguno de sus paneles tiene descripción. `tools/docker-topology.test.mjs` fija los volúmenes, el `depends_on` y las variables de entorno de Grafana.
- **Prometheus** guarda cada muestra con la hora a la que la ingiere y tiene la retención por defecto. No sirve para series fechadas con la fecha de cada ejecución ni para un histórico de semanas.
- **`postgres-pgvector`** (PostgreSQL 17, base `embeddings`) ya está en compose, con su volumen y la credencial obligatoria `POSTGRES_PASSWORD`. Grafana 11.3 trae el datasource PostgreSQL de serie.
- **Informes de entrada.** No hay ninguno de robustez porque JUP-071 no está hecha.

  | Informe | Ruta | Formato | Notas |
  | --- | --- | --- | --- |
  | JUP-070, ejecuciones 1 y 2 | `docs/evidence/JUP-070-run-{1,2}-report.json` | `report_version` 1, catálogo 1.0.0 | Las dos son de plantilla; la 1 usa embeddings `mock` |
  | JUP-078, benchmark | `docs/evidence/JUP-078-benchmark-results.json` | `schema_version` 1 | Sin commit ni fecha |
  | JUP-022, calibración | `docs/spikes/JUP-022-retrieval-calibration.json` | `schema_version` 1 | |
  | JUP-068, entrada | `docs/validation/JUP-068-example.json` | | Hay que pasarlo por `tools/business-metrics.mjs report` para obtener el informe |

- **Señales en vivo** (`apps/backend/app/core/metrics.py`): `backend_assistant_queries_total` cuenta las consultas respondidas, también las que se responden sin recuperación (`assistant.py:120`). `backend_retrieval_empty_total` cuenta las búsquedas vacías, que sí se responden. `backend_retrieval_failures_total{category}` cuenta los fallos, que devuelven 503 y no suman a las consultas respondidas.
- **Herramientas de evaluación**: son scripts de `tools/` con solo la biblioteca estándar de Python. Sus pruebas `unittest` están en `scripts/tests/` y la CI las lanza con `corepack pnpm <x>:test` en «Validate governance tooling».

## Goals / Non-Goals

**Goals:**
- Una sola fuente de verdad por resultado: el informe original. La base del dashboard es una proyección que se regenera y se puede tirar.
- Que lo no medido llegue a Grafana como `NULL` y que la normalización nunca lo convierta en 0.
- Que los adaptadores, la clasificación de ejecuciones y el SQL generado se puedan probar sin Docker. Las pruebas con base real son pocas y comprueban la conciliación y los permisos.
- No añadir librerías, plugins ni servicios.

**Non-Goals:**
- Recalcular métricas o cambiar las fórmulas del catálogo de JUP-067.
- Guardar o versionar ejecuciones que no son de hito; eso queda en manifiestos locales.
- Ejecutar la regeneración en el despliegue continuo de DockerServer (ver Open Questions).
- Cambiar el dashboard de métricas técnicas de JUP-043.

## Decisions

### D1. Los resultados se guardan en PostgreSQL y Grafana los lee con su datasource integrado (ADR-0022)

Se crea un esquema `evaluation` en la base de `postgres-pgvector` y un datasource PostgreSQL provisionado (uid `evaluation-postgres`) que entra con el rol `grafana_evaluation_reader`. Ese rol solo tiene `USAGE` y `SELECT` sobre ese esquema.

- Las series usan la fecha real de cada ejecución (`run_at`), los `NULL` siguen siendo `NULL` y las anotaciones salen de una consulta SQL.
- Los informes siguen en Git, así que perder el volumen no pierde datos: basta con volver a regenerar.

Alternativas descartadas:
- **Pushgateway → Prometheus.** Pushgateway rechaza las marcas de tiempo y la retención borraría el histórico.
- **Volcado con `promtool tsdb create-blocks-from`.** Arrastra el mismo problema de retención y es una operación delicada.
- **Datasource TestData con CSV dentro del dashboard.** Es un datasource de pruebas, tiene pocas anotaciones y obliga a commitear el dashboard en cada ejecución, lo que choca con «en Git solo las de hito».
- **Plugin Infinity con un endpoint del backend.** Hay que fijar un plugin externo que se descarga al arrancar y añadir una API al backend que no la necesita.
- **Un PostgreSQL aparte.** Es un servicio más que mantener; el esquema y el rol propios ya dan el aislamiento.

### D2. Una herramienta con solo la biblioteca estándar genera SQL y lo carga con el `psql` del contenedor

`tools/evaluation-dashboard.py` tiene estos subcomandos:

| Subcomando | Qué hace | Necesita la base |
| --- | --- | --- |
| `rows --manifest …` | Normaliza y escribe ejecuciones y filas en JSON | No |
| `sql --manifest …` | Escribe un script SQL transaccional con el esquema y los datos, sin credenciales | No |
| `load --manifest …` | Genera ese script y se lo pasa por la entrada estándar a `docker compose exec -T postgres-pgvector psql -U postgres -d embeddings -v ON_ERROR_STOP=1` | Sí |

`load` también crea o actualiza el rol de lectura con la contraseña que lee de `GRAFANA_EVALUATION_DB_PASSWORD`. Esa contraseña solo viaja por la entrada estándar: nunca aparece en los argumentos ni en la salida.

El comando documentado es `corepack pnpm evaluation-dashboard:load`, que carga el manifiesto versionado y admite `-- --manifest <local>` para añadir otros.

Alternativas descartadas:
- **`psycopg` en el host.** Añade una dependencia al Python del host, que hoy no tiene ninguna.
- **Que cargue el backend.** Mezcla la evaluación con la API del producto.

### D3. Manifiesto versionado con los informes de hito y manifiestos locales opcionales

`docs/validation/evaluation-runs.json` (`manifest_version` 1) lista cada informe con su ruta, su formato y `milestone: true`. Los formatos son `jup-070-report-v1`, `jup-078-benchmark-v1`, `jup-022-calibration-v1`, `jup-068-input-v1` y `rows-v1`.

- La entrada de JUP-068 apunta al fichero de entrada. La herramienta ejecuta `node tools/business-metrics.mjs report` y normaliza la salida, sin repetir sus fórmulas.
- Los manifiestos locales, fuera de Git, añaden ejecuciones con `milestone: false`.
- Una ruta repetida o un `run_id` duplicado entre manifiestos es un error.

### D4. Modelo de datos y contrato de filas planas `rows-v1`

**`evaluation.runs`**, una fila por ejecución:
- Identidad: `run_id`, `source` (`JUP-070`, `JUP-078`, `JUP-022`, `JUP-068` o la fuente que declare un fichero `rows-v1`), `report_path`, `report_sha256`.
- Batería: `suite`, `suite_version`, `suite_sha256`, `corpus_sha256`.
- Configuración: `embedding_provider`, `embedding_alias`, `retrieval` (jsonb), `generation_model`, `prompt_sha256`.
- Contexto: `commit`, `run_at`, `milestone`.
- Clasificación: `is_real`, `non_real_reasons text[]`, `comparability_key`.

Todo campo que el informe no trae queda `NULL`.

**`evaluation.results`**, una fila por resultado:
- Origen: `run_id`, `measure_type` (`A` o `B`), `grp` (familia o bloque), `metric_id`, `behavior` (conducta, etapa o modelo).
- Resultado: `status`, que vale `pass`, `fail`, `blocked` o `not_run` en los recuentos y `measured` o `not_measured` en los valores; `count`, `value`, `numerator`, `denominator`, `unit`, `ci_low`, `ci_high`.
- Juicio: `judgment` (`automatic` o `human`).

Ninguna columna admite texto libre más allá de identificadores y unidades.

**`evaluation.config_changes`** es una vista que alimenta las anotaciones: compara cada ejecución con la anterior de la misma fuente y nombra lo que cambió.

El contrato `rows-v1` es un JSON con `contract_version: 1`, una ejecución y sus filas, con estos mismos campos. Se documenta en `docs/validation/evaluation-dashboard.md` y es la vía de entrada de JUP-071. Un fichero `rows-v1` pasa la misma validación que la salida de los adaptadores.

### D5. Clasificación de ejecuciones y comparabilidad

**Motivos de ejecución no real:**
- `plantilla`: el modelo de generación es `plantilla-sin-modelo`.
- `doble`: el proveedor o el alias de embeddings es `mock`.
- `sintetica`: el informe declara `synthetic: true` o `provenance: synthetic`.
- `sin_modelo_verificado`: no hay modelo de generación registrado en una fuente que lo exige.

**Clave de comparabilidad:** es la huella de fuente, `suite_sha256`, `corpus_sha256`, `embedding_provider`, `embedding_alias`, `retrieval`, `generation_model`, `prompt_sha256` y `non_real_reasons`. Con los datos actuales, las ejecuciones 1 y 2 de JUP-070 tienen claves distintas, porque cambian el proveedor de embeddings y `max_distance`. Por eso las dos muestran «Sin datos: no hay con qué comparar», que es el comportamiento que pide la tarjeta.

**Juicio humano:** ACC-1 y ACC-3 dependen del juicio humano (el `outcome` de cada caso sale de los juicios de los puntos `required-N`). Las demás métricas de JUP-070 son automáticas.

- La herramienta tiene una tabla fija que asigna cada métrica a un tipo de juicio.
- Una prueba falla si el catálogo de JUP-067 tiene un identificador que la tabla no clasifica.
- Las series de juicio humano solo usan ejecuciones con `milestone = true`.

### D6. Cómo muestra el dashboard lo no medido y la falta de comparación

- **Paneles de evolución.** La consulta solo devuelve series cuya clave tenga al menos dos ejecuciones. Sin filas, el panel enseña su `noValue`, «Sin datos: no hay con qué comparar». Se configuran con `spanNulls: false` y sin rellenar con ceros.
- **Paneles de valor y tablas.** Un `NULL` se muestra como «No medido» (con `noValue` o con un mapeo de valor), nunca como 0.
- **Estados.** Se pintan como recuentos por estado junto al total de casos.
- **Ejecuciones no reales.** Llevan un rótulo con sus motivos en la tabla de ejecuciones y en la leyenda, y un estilo de serie distinto (línea discontinua mediante overrides por rótulo).

### D7. Estructura del dashboard

El fichero es `apps/monitoring/grafana/dashboards/assistant-evaluation.json`, con uid `economicon-assistant-evaluation`. Está escrito a mano y versionado, como el de JUP-043, y tiene filas plegables por sección.

1. **A. Calidad con rúbrica.**
   - Ejecuciones y sus metadatos.
   - Estados por ejecución.
   - ACC, REL y GRD por ejecución.
   - Evolución automática y evolución de juicio humano.
   - LAT, STR y AVL de la campaña.
   - Calibración de JUP-022.
   - Benchmark de JUP-078.
   - Robustez (JUP-071), vacía por ahora.
2. **B. Métricas de negocio.** Tiempo ahorrado con sus estados, cobertura de gasto asignado y ahorro potencial.
3. **C. Señales en vivo, solo síntomas.**
   - Consultas por minuto, latencia p95 y tasa de error, con las mismas expresiones que JUP-043.
   - Proporción de búsquedas vacías: `sum(rate(backend_retrieval_empty_total[5m])) / (sum(rate(backend_assistant_queries_total[5m])) + sum(rate(backend_retrieval_failures_total[5m])) > 0)`.
   - Proporción de fallos de recuperación, con el mismo denominador.
   - Enlace al dashboard técnico.

   El `> 0` del denominador hace que, sin tráfico, no haya resultado y el panel diga «Sin datos» en vez de dar `NaN` o 0. Las consultas respondidas sin pasar por la recuperación entran en el denominador, así que la proporción es un límite inferior; la descripción del panel lo dice.

Cada panel lleva una descripción con tres líneas fijas: `Tipo: A|B|C`, `Mide: …` y `No demuestra: …`.

Una prueba estructural del JSON comprueba que:
- todos los paneles llevan esas tres líneas;
- ningún panel mezcla los datasources `prometheus` y `evaluation-postgres`;
- todo panel de evolución define el `noValue` acordado.

### D8. Credenciales y compose

- **Datasource.** `apps/monitoring/grafana/provisioning/datasources/evaluation-postgres.yml` interpola `$GRAFANA_EVALUATION_DB_PASSWORD`.
- **Compose.** Grafana recibe `GRAFANA_EVALUATION_DB_PASSWORD: ${GRAFANA_EVALUATION_DB_PASSWORD:?required}`. Se añade a `.env.example` sin valor y se actualiza `tools/docker-topology.test.mjs`.
- **Arranque.** No se añade `depends_on` de Grafana a `postgres-pgvector`, porque el datasource se conecta al primer uso. Así el arranque de Grafana no depende de una base que no es suya.

## Risks / Trade-offs

- **[El esquema de evaluación vive en la base de embeddings]** → Esquema y rol separados. Borrar `evaluation` no toca las tablas de embeddings, y la herramienta solo escribe dentro de `evaluation`.
- **[Antes de la primera carga los paneles de la sección A y B dan error de relación inexistente]** → La guía pone `evaluation-dashboard:load` justo después de `docker compose up`. `load` crea el esquema aunque el manifiesto esté vacío.
- **[DockerServer y la CD necesitan la variable nueva o Compose no arranca]** → Se añade a `.env.example` y a la guía de despliegue. La evidencia de validación lo deja como requisito de despliegue para que se avise a quien mantiene DockerServer antes del merge.
- **[Hoy casi todo son ejecuciones de plantilla o sintéticas]** → Es lo honesto. El dashboard lo rotula y la evidencia lo dice; no se presenta como calidad del asistente.
- **[El juicio humano de ACC-1 y ACC-3 se deduce por diseño, no viene marcado en el informe]** → Tabla fija probada contra el catálogo y documentada. Si JUP-067 cambia el catálogo, la prueba avisa.
- **[La proporción de búsquedas vacías es un límite inferior]** → Lo explica la descripción del panel. No se cambian las métricas del backend en este change.
- **[El dashboard JSON escrito a mano puede desviarse de la spec]** → La prueba estructural y la conciliación ejecutan las mismas consultas SQL que los paneles.

## Migration Plan

1. Añadir `GRAFANA_EVALUATION_DB_PASSWORD` al `.env` local (y al de DockerServer cuando se despliegue).
2. `docker compose up -d` y después `corepack pnpm evaluation-dashboard:load`.
3. **Rollback:** quitar el dashboard y el datasource provisionados, y ejecutar `DROP SCHEMA evaluation CASCADE; DROP ROLE grafana_evaluation_reader;`. No afecta a ningún otro dato.

## Open Questions

- Si la CD de DockerServer debe ejecutar la carga tras desplegar. Es un ajuste del pipeline de JUP-052 que no cambia este diseño; se plantea a quien lo mantiene.
- Cuando JUP-071 u otras campañas registren la huella del prompt (`prompt_sha256` en `run`), las anotaciones de cambio de prompt empezarán a aparecer sin tocar el dashboard.
