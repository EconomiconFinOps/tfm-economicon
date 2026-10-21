# Dashboard de resultados de evaluación del asistente (JUP-121)

Contrato de datos y guía de uso del dashboard de Grafana que reúne los resultados de evaluación del asistente. Tarjeta: [JUP-121](https://trello.com/c/aIdxwsXR). Decisión: [ADR-0022](../adr/ADR-0022-assistant-evaluation-results-in-grafana.md). Requisitos: [spec](../../openspec/changes/archive/2026-10-15-jup-121-assistant-evaluation-dashboard/specs/assistant-evaluation-dashboard/spec.md).

> **Estado:** implementado. Este documento fija el contrato de datos y describe el dashboard (`apps/monitoring/grafana/dashboards/assistant-evaluation.json`, uid `economicon-assistant-evaluation`). La herramienta `tools/evaluation-dashboard.py` y los comandos de abajo funcionan; la sección de robustez espera el informe de JUP-071.

## Qué muestra y qué no demuestra

El dashboard junta tres tipos de medida que responden a preguntas distintas. Cada panel declara su tipo en su descripción, con tres líneas: `Tipo: A|B|C`, `Mide: …` y `No demuestra: …`.

| Tipo | Responde a | Datos | No demuestra |
| --- | --- | --- | --- |
| **A. Calidad con rúbrica** | ¿Responde bien el asistente a casos que conocemos? | Campañas de JUP-070 sobre la batería de JUP-069 con las métricas de JUP-067, calibración de JUP-022 y benchmark de JUP-078 | El comportamiento con usuarios reales ni con preguntas fuera de la batería |
| **B. Negocio** | ¿Qué valor aportaría el asistente? | Registros reproducibles de JUP-068 | Un beneficio observado mientras no haya un piloto real |
| **C. Señales en vivo** | ¿Está sano el sistema ahora? | Métricas de Prometheus emitidas por el backend con tráfico real | Que las respuestas sean correctas: solo detecta síntomas |

La latencia y la disponibilidad existen en A (sobre las peticiones de una campaña) y en C (sobre tráfico real) con significados distintos. Nunca comparten panel.

Las definiciones y fórmulas de las métricas de A están en el [catálogo de JUP-067](JUP-067-metrics-catalogue.json) y no se repiten aquí.

## Dashboard

Cada sección empieza con un panel de texto («Cómo leer la sección…») y sus paneles llevan en la descripción lo que miden y lo que no demuestran.

- **A. Calidad con rúbrica.** De arriba abajo: el **resumen de la última campaña** de JUP-070 (fecha, tipo de ejecución, casos aprobados sobre el total y si todavía no hay una evaluación con modelo real); las ejecuciones cargadas y el estado de sus casos; la tabla **«Resultados por métrica y ejecución»** (una fila por métrica y variante, con su nombre del catálogo, y una columna por ejecución); justo debajo, tres gráficas de evolución (proporciones automáticas, **latencia de la campaña** y juicio humano, solo hitos); la calibración de la recuperación, el benchmark de modelos y la robustez; y, al final, las dos tablas por fila de exactitud, relevancia y fundamento y de latencia, formato y disponibilidad de la campaña, que se conservan como **«(detalle)»** para auditar y conciliar con los informes. Las tablas por fila muestran con cada fila la fecha, la versión de la batería, el commit (abreviado a 8 caracteres; entero en la tabla de ejecuciones) y el modelo de su ejecución; la matriz no los repite, porque su cabecera ya identifica cada ejecución por fecha (`AAAA-MM-DD hh:mm`, en UTC como todo el dashboard) y tipo.
- **B. Métricas de negocio.** Una tabla con las 23 filas de JUP-068: tiempo, asignación de gasto y ahorro, con los mismos metadatos. El numerador y el denominador salen con la unidad del valor: minutos para el tiempo y euros para los importes (el informe los emite en milisegundos y céntimos y la consulta los convierte); un denominador de parejas es un recuento y se queda como número.
- **C. Señales en vivo.** Cinco gráficas de Prometheus (consultas por minuto, latencia p95, tasa de error y las dos proporciones de búsquedas sin contexto y de fallos de recuperación) que miran siempre la última hora.

Cómo leerlo (el panel «Cómo leer la sección A» del dashboard resume solo tres ideas: ejecuciones «no real», «No medido» y evolución; el resto está aquí):

- **Lo no medido** se muestra como «No medido» y nunca como 0 %: un 0 % que se ve es un cero medido. Un metadato que el informe no registra se muestra como «no registrado» (la fecha, «No registrada»); nada se rellena con el de otra ejecución. En la matriz, «—» significa que esa ejecución no trae esa métrica (no es 0 % ni «No medido»).
- **Las ejecuciones «no real»** (plantilla, dobles de prueba, sintéticas o sin modelo verificado) llevan «no real» y su motivo en la columna **Tipo de ejecución**, en morado, y sus series de evolución se dibujan discontinuas. Son pruebas del flujo, no calidad del asistente. «Estado» solo designa el estado de los casos (aprobados, fallidos, bloqueados, no ejecutados): la clasificación real o no real nunca se llama así.
- **Variante.** La columna «Variante» (antes «Conducta») traduce el desglose de cada métrica: `todas`, `con juicio humano`, `aclarar`, `abstenerse`, `responder`, `mediana`, `primer cuartil`, `tercer cuartil`, las etapas `embedding`, `recuperación`, `generación` y `total`, y las diez categorías de fallo de STR-2 (tiempo agotado, conexión, transporte, autenticación, petición rechazada, redirección, límite de peticiones, fallo del servicio externo, respuesta no válida y validación del esquema). Las tablas de detalle conservan el valor original en una columna oculta (`behavior`) porque la conciliación con los informes lo usa. La columna de resultado (`status`) está oculta en ellas: todo lo que muestran está medido y lo no medido se lee «No medido» por el valor vacío.
- **Matriz.** Cada celda lleva el valor con su unidad, el numerador y el denominador (`25/51`) cuando existen y el intervalo de confianza del 95 % (`IC95 lo–hi %`) solo cuando el informe trae los dos límites. Las columnas se ordenan por fecha y se nombran con la fecha UTC y el tipo de ejecución; una ejecución sin fecha va al final con el identificador.
- **La evolución** solo dibuja una serie (métrica, variante y clave de comparabilidad; la leyenda la nombra con la métrica, la fuente y «serie» seguido de los 8 primeros caracteres de la clave) con al menos dos puntos medidos; una con un solo punto no se dibuja. Hay tres gráficas: las proporciones automáticas (en %), la latencia de la campaña (mediana LAT-1 y percentil 95 LAT-2 de la etapa `total`, en milisegundos; mismas reglas) y el juicio humano.
- **La línea une puntos medidos.** En las gráficas de evolución la línea une los puntos medidos de una serie. Una ejecución en la que esa métrica no se midió no genera punto: la línea salta de la ejecución anterior medida a la siguiente medida y no se inventa ningún valor.
- **Rango de tiempo.** El selector de tiempo del dashboard (por defecto, el último año) solo acota las gráficas de evolución, que consideran todas las ejecuciones cargadas con fecha dentro de ese rango: para ver ejecuciones más antiguas, amplíalo. Las tablas no se filtran por él y muestran siempre todas las ejecuciones cargadas. Las marcas verticales de las evoluciones indican un cambio de batería, modelo, prompt o corpus entre ejecuciones consecutivas de la misma fuente.
- **Sin semáforos.** Los umbrales de JUP-067 son provisionales y no se aplican: ningún valor se colorea como bueno o malo.
- **Campaña no es tráfico real.** La latencia y la disponibilidad de la sección A son las de las peticiones de una campaña; las del tráfico real están en la sección C.

## Puesta en marcha

1. Añadir `GRAFANA_EVALUATION_DB_PASSWORD` al `.env` (el ejemplo está en `.env.example`, sin valor). **Es obligatoria**: `docker compose up` se niega a arrancar sin ella. En un despliegue existente (DockerServer incluido) hay que añadirla al `.env` del servidor **antes** de actualizar la pila, con el valor que se usará al cargar; no se cambia ninguna otra variable.
2. Levantar la pila: `docker compose up -d`. Grafana provisiona los dos dashboards («Economicon — Métricas técnicas» y «Economicon — Evaluación del asistente») y el datasource `Evaluacion`.
3. Cargar los resultados: `corepack pnpm evaluation-dashboard:load` con la misma variable en el entorno de la terminal. Es el paso que crea el rol y los datos; hasta entonces las secciones A y B muestran el error de autenticación descrito abajo.
4. Abrir Grafana (puerto 3000) y el dashboard de uid `economicon-assistant-evaluation`.

La contraseña de Grafana y la de `load` son la misma variable: si se rota, hay que repetir la carga (fija la contraseña del rol) y reiniciar Grafana.

## Regenerar los datos

Un único comando carga los informes en la base. Con el entorno levantado (`docker compose up -d`):

```sh
corepack pnpm evaluation-dashboard:load
```

- Lee el manifiesto versionado [evaluation-runs.json](evaluation-runs.json) y reemplaza los datos anteriores de forma atómica e idempotente: dos cargas seguidas dejan lo mismo, y una carga que falla conserva la anterior.
- Necesita `GRAFANA_EVALUATION_DB_PASSWORD` en el entorno (la contraseña del rol de lectura de Grafana, la misma variable que recibe Grafana). Si falta, o es inválida (vacía, de más de 200 caracteres o con caracteres de control), termina con un error que nombra la variable o el campo `password` —nunca el valor— y no lee ni ejecuta nada.
- Carga con un único `psql` y un único flujo de entrada: primero el script de datos y después el script del rol. Por defecto ejecuta `docker compose exec -T -e PGCLIENTENCODING=UTF8 postgres-pgvector psql -U postgres -d embeddings -v ON_ERROR_STOP=1 -X -q` desde la raíz del repositorio, así que necesita la pila de Compose levantada y el `.env` completo (Compose interpola todo `docker-compose.yml`). Para otra base, para un contenedor concreto (`docker exec -i <contenedor> psql -U postgres -d embeddings`) o para un `psql` local se pasa `--psql-command "<comando>"` (se parte con `shlex`: en Windows, rutas con `/`); un comando vacío es un error de uso. `load` no admite `--output`.
- Grafana lee los resultados con un datasource PostgreSQL provisionado desde `apps/monitoring/grafana/provisioning/datasources/evaluation-postgres.yml` (nombre `Evaluacion`, uid `evaluation-postgres`, tipo `grafana-postgresql-datasource`, usuario `grafana_evaluation_reader`, base `embeddings`). Su contraseña llega por la variable de entorno `GRAFANA_EVALUATION_DB_PASSWORD`, que el servicio `grafana` de Compose declara como obligatoria (`${GRAFANA_EVALUATION_DB_PASSWORD:?required}`): sin ella `docker compose up` se niega a arrancar e indica la variable. El datasource predeterminado sigue siendo Prometheus, y Grafana no depende de PostgreSQL para arrancar (el datasource se conecta al primer uso: antes de la primera carga, que crea el rol y el esquema, el rol aún no existe y los paneles de las secciones A y B muestran el error `password authentication failed for user "grafana_evaluation_reader"`; tras cargar, un recargado de Grafana basta).
- El script del rol (aparte del de datos, que no lleva credenciales) crea `grafana_evaluation_reader` si no existe, fija siempre su contraseña (así se rota con otra carga) y le da solo `CONNECT`, `USAGE` del esquema `evaluation` y `SELECT` de sus tablas y vistas (y de las que se creen después). No puede escribir ni leer otros esquemas ni catálogos sensibles, y no es superusuario. La contraseña solo viaja por la entrada estándar de `psql`; si `psql` falla y repite la sentencia, el mensaje sale con la contraseña sustituida por `***`.
- Limitación conocida: la sentencia `ALTER ROLE … PASSWORD` lleva la contraseña en claro, como cualquier `ALTER ROLE` sin hash previo. Si el servidor registra sentencias (`log_statement` en `ddl` o `all`, o un error de la propia sentencia con `log_min_error_statement`), quedará en su registro; con la configuración por defecto de PostgreSQL no se registra. Mejora posible: enviar el hash SCRAM calculado en Python.
- Para añadir ejecuciones que no son de hito, sin tocar Git, se pasa un manifiesto local: `corepack pnpm evaluation-dashboard:load -- --manifest ../evaluacion/manifiesto.json`. Se pueden pasar varios `--manifest`.
- Scripts de `package.json`: `corepack pnpm evaluation-dashboard:load` (carga), `evaluation-dashboard:rows` (JSON normalizado, sin base de datos), `evaluation-dashboard:sql` (el script SQL, sin ejecutarlo) y `evaluation-dashboard:test` (las pruebas; las que usan PostgreSQL real necesitan Docker y se saltan solas sin él, y la CI las ejecuta en el paso «Validate governance tooling»). Los argumentos propios se pasan tras el nombre del script, con o sin `--` (pnpm 9 reenvía el `--` literal y la herramienta lo ignora).
- `corepack pnpm evaluation-dashboard:rows` escribe el conjunto de datos normalizado en JSON sin tocar la base, para revisarlo o para probar un informe nuevo (se puede lanzar ya como `python tools/evaluation-dashboard.py rows`). Opciones: `--manifest RUTA` (repetible, se añade al versionado), `--no-versioned` (no lee el manifiesto versionado), `--output FICHERO` (escribe el JSON en un fichero de forma atómica; si hay un error no crea ni modifica nada) y `--root DIR` (raíz contra la que se resuelven las rutas relativas, por defecto la del repositorio). La salida es JSON UTF-8 con `
`, byte a byte igual por la salida estándar y por `--output`, y dos ejecuciones seguidas dan el mismo resultado. Un error sale como `error: <fichero>: <campo>: <problema>` en la salida de error con código 1; un uso incorrecto, con código 2.
- Cada ejecución del conjunto de datos lleva, además de los campos del contrato, `is_real`, `non_real_reasons` y `comparability_key` (clasificación), `format`, `milestone`, `report_path` y `report_sha256`. El `run_id` de un informe de JUP-070, JUP-078 o JUP-022 que no lo declara se deriva como `<fuente en minúsculas>-<AAAAMMDDThhmmssZ en UTC o undated>-<8 primeros caracteres de la huella>`; el de JUP-068 es el del propio informe. `report_sha256` es el sha256 del JSON canónico del documento ya parseado (no de los bytes del fichero: en Windows el fin de línea cambia con `autocrlf` y los identificadores derivados deben ser iguales en todas las máquinas); en JUP-068 es la huella de la entrada, no la del informe que genera Node. `report_path` solo se registra si el informe está dentro del repositorio y su ruta usa el alfabeto cerrado; una ruta local absoluta puede llevar nombres de usuario y solo deja la huella. Un informe que no produce ninguna fila es un error.

Los informes siguen siendo la fuente de verdad. La base es una proyección que se puede tirar y volver a cargar.

## Manifiesto

```json
{
  "manifest_version": 1,
  "runs": [
    { "path": "docs/evidence/JUP-070-run-2-report.json", "format": "jup-070-report-v1", "milestone": true }
  ]
}
```

| Campo | Obligatorio | Significado |
| --- | --- | --- |
| `path` | sí | Ruta del informe. Relativa, se resuelve desde la raíz del repositorio; también se admite una ruta absoluta, pensada para manifiestos locales |
| `format` | sí | Formato del informe, de la tabla siguiente |
| `milestone` | sí | `true` para una ejecución de hito. El manifiesto versionado solo lista hitos; los locales suelen usar `false` |
| `run_id` | no | Identificador de la ejecución. Si falta se toma el del informe (JUP-068 lo trae) o se deriva como `<fuente>-<fecha UTC compacta o undated>-<8 primeros caracteres del sha256 del informe>` |

| `format` | Informe |
| --- | --- |
| `jup-070-report-v1` | Informe JSON de JUP-070 (`report_version` 1) |
| `jup-078-benchmark-v1` | Resultados del benchmark de modelos de JUP-078 (`schema_version` 1) |
| `jup-022-calibration-v1` | Calibración de la recuperación de JUP-022 (`schema_version` 1) |
| `jup-068-input-v1` | Entrada de JUP-068; la herramienta ejecuta `tools/business-metrics.mjs report` y normaliza su salida |
| `rows-v1` | Filas ya normalizadas, según el contrato de más abajo |

Una ruta que no existe, un formato desconocido, una versión de esquema desconocida, un campo obligatorio ausente o un `run_id` repetido entre manifiestos terminan la carga con un error que nombra el fichero y el campo. No se carga ninguna fila de esa regeneración.

## Contrato de filas planas `rows-v1`

Es el formato al que se normalizan todos los informes y el que debe emitir cualquier informe futuro, en particular el de robustez de JUP-071. Un fichero `rows-v1` pasa la misma validación que la salida de los adaptadores.

```json
{
  "contract_version": 1,
  "run": { "run_id": "…", "source": "JUP-071", "…": "…" },
  "results": [
    { "measure_type": "A", "grp": "…", "metric_id": "…", "behavior": "…", "status": "pass", "count": 12, "denominator": 14 }
  ]
}
```

### Ejecución (`run`)

Todo campo que el informe no trae se guarda como `null` y el dashboard lo muestra como «no registrado». Nada se rellena con un valor deducido.

| Campo | Obligatorio | Contenido |
| --- | --- | --- |
| `run_id` | sí | Identificador único de la ejecución |
| `source` | sí | Fuente: `JUP-070`, `JUP-078`, `JUP-022`, `JUP-068` o la de un informe nuevo (`JUP-071`) |
| `run_at` | no | Fecha y hora UTC de la ejecución (ISO 8601). Sin ella la ejecución se lista como «fecha no registrada» y no entra en ninguna serie temporal |
| `commit` | no | Commit sobre el que se ejecutó |
| `suite`, `suite_version`, `suite_sha256` | no | Batería: identificador, versión y huella |
| `corpus_sha256` | no | Huella del corpus. Para JUP-022, que lista varios documentos, es el sha256 de las líneas `<clave>=<sha256>` ordenadas y unidas con saltos de línea |
| `embedding_provider`, `embedding_alias` | no | Proveedor y alias de embeddings |
| `retrieval` | no | Objeto con algunas de las claves `top_k`, `max_distance`, `chunk_size` y `chunk_overlap` (no se exigen las cuatro: la calibración de JUP-022 solo lleva el troceado porque `top_k` y `max_distance` van por fila); valores numéricos o `null` |
| `generation_model` | no | Alias del modelo de generación |
| `prompt_sha256` | no | Huella del prompt. Ningún informe actual la registra |
| `synthetic` | no | `true` si el informe declara ser sintético |
| `milestone` | no | Lo fija el manifiesto, no el informe; en un `rows-v1` es una clave desconocida y se rechaza |

### Resultado (`results`)

En un fichero `rows-v1` son obligatorias `measure_type`, `grp`, `metric_id`, `behavior` y `status`; el resto puede omitirse (queda `null`, y `selected` queda `false`), pero la validación común exige además `unit` en todas las filas y `judgment` en las de tipo A, así que en la práctica también hay que escribirlas.

| Campo | Contenido |
| --- | --- |
| `measure_type` | `A` (calidad con rúbrica) o `B` (negocio) |
| `grp` | Familia o bloque, como `accuracy`, `latency` o `calibration` |
| `metric_id` | Identificador de la métrica del catálogo (`ACC-1`, `LAT-2`…) o de la medida (`cases`, `time_saved`…) |
| `behavior` | Conducta, etapa, modelo o punto del barrido, como `answer`, `generation`, `economicon-chat` o `top_k=4,max_distance=0.6` |
| `status` | `pass`, `fail`, `blocked` o `not_run` en los recuentos de casos; `measured` o `not_measured` en los valores |
| `count` | Recuento de casos en ese estado |
| `value`, `unit` | Valor y unidad (`tasa`, `ms`, `recuento`, `similitud`, `eur`…) |
| `numerator`, `denominator` | Numerador y denominador cuando la métrica es una proporción |
| `ci_low`, `ci_high` | Intervalo de confianza cuando el informe lo trae |
| `judgment` | `automatic` o `human` en el tipo A; `null` en el tipo B |
| `selected` | `true` en el candidato que eligió la calibración; `false` en los demás |

### Reglas

1. **Lo no medido es `null`, nunca cero.** Un valor que el informe no midió (`null`, métrica con `available` igual a `false`, `realized_minor` nulo, metadato ausente) se guarda con `status: not_measured` y `value`, `numerator` y `count` a `null`. Los paneles lo muestran como «No medido».
2. **Estados con denominador.** Un resultado de casos lleva sus cuatro recuentos y el total como denominador. `blocked` y `not_run` no se suman a `fail`.
3. **Sin texto libre.** Los campos de texto solo admiten identificadores y unidades: empiezan por letra o dígito, contienen `A-Z a-z 0-9 . _ : = , / + @ -`, no llevan espacios y tienen como máximo 80 caracteres. Los identificadores de caso (`JUP-069-024`) caben. Un enunciado, una respuesta, un fragmento recuperado o la nota de un revisor no.
4. **Los adaptadores copian, no recalculan.** El valor de cada fila es el del informe original; la conciliación de JUP-121 comprueba que los recuentos coinciden.
5. **Una métrica no medida conserva su denominador.** Si el informe trae `n` (aunque sea 0), la fila `not_measured` lo guarda en `denominator`; `value`, `numerator`, `ci_low`, `ci_high` y `count` quedan a `null`.
6. **`available` manda sobre el valor.** Una métrica con `available: false` es `not_measured` aunque el informe traiga un `rate`. En GRD-2, si no está disponible, solo sale la fila `all` como no medida y el desglose por caso del informe no se publica. Un cero medido (`rate` 0.0, `k` 0, una latencia de 0 ms) sigue siendo `measured`.
7. **Validación común.** Se aplica a la salida de todos los adaptadores y a la entrada `rows-v1`, y para en el primer error con la ruta del campo como prefijo (`run.<campo>`, `results[i].<campo>`). Reglas: `run` lleva exactamente las claves del contrato y `results` es una lista de filas con exactamente las suyas; `run_id`, `source`, `grp`, `metric_id`, `behavior`, `unit` y las cadenas de la ejecución son identificadores (regla 3); `run_at` es `null` o una fecha y hora UTC con formato exacto `AAAA-MM-DDThh:mm:ss[.f{1,6}](Z|±hh:mm)` (separador `T`, segundos y zona obligatorios, fecha real), porque el texto acaba en un script SQL y `fromisoformat` de Python acepta cualquier separador; `count` y `denominator` son enteros no negativos y `value`, `numerator` e intervalo son números finitos (el numerador puede ser negativo: un tiempo ahorrado negativo es un dato); un entero no puede superar `ROW_MAX_INTEGER = 2^53 - 1` en valor absoluto (la misma cota de enteros seguros de `business-metrics.mjs`), de modo que `count` y `denominator` caben en `bigint` y el resto en `double precision` sin pérdida; los números en coma flotante finitos no tienen cota nueva; `judgment` es `automatic` o `human` en el tipo A y `null` en el tipo B.
8. **Coherencia por estado.** Un estado de caso (`pass`, `fail`, `blocked`, `not_run`) exige `count` y no lleva `value` ni `numerator`; `measured` exige `value` y no lleva `count`; `not_measured` no lleva `count`, `value`, `numerator` ni intervalo, y puede conservar el `denominator`. El intervalo lleva siempre sus dos límites. Con unidad `tasa`, `0 <= numerator <= denominator`. No puede haber dos filas con la misma `(grp, metric_id, behavior, status)` en una ejecución.

## Tablas del esquema `evaluation`

`python tools/evaluation-dashboard.py sql` (y `corepack pnpm evaluation-dashboard:load`, que lo ejecuta contra la base) genera un script transaccional que crea el esquema `evaluation` si no existe, vacía las dos tablas y las vuelve a llenar a partir del conjunto de datos de `rows`. Es idempotente (dos cargas seguidas dejan lo mismo) y atómico (si algo falla, la transacción deshace el vaciado y quedan los datos de la carga anterior). Usa `TRUNCATE` y no `DROP`, así que los permisos que se concedan después sobreviven. El script nunca lleva credenciales; el rol de solo lectura de Grafana lo crea la carga con otro script.

**`evaluation.runs`**, una fila por ejecución (clave primaria `run_id`): `source`, `run_at` (`timestamptz`, nulo si el informe no trae fecha), `commit_sha`, `suite`, `suite_version`, `suite_sha256`, `corpus_sha256`, `embedding_provider`, `embedding_alias`, `retrieval` (`jsonb`), `generation_model`, `prompt_sha256`, `synthetic`, `is_real`, `non_real_reasons` (`text[]`), `comparability_key`, `format`, `milestone`, `report_path` y `report_sha256`.

**`evaluation.results`**, una fila por resultado (clave primaria `run_id, grp, metric_id, behavior, status`, y `run_id` referencia a `runs` con `ON DELETE CASCADE`): `measure_type` (`A`/`B`), `grp`, `metric_id`, `behavior`, `status`, `case_count` (`bigint`; es el `count` del contrato), `value` (`double precision`), `unit`, `numerator`, `denominator` (`bigint`), `ci_low`, `ci_high`, `judgment` y `selected`.

Dos `CHECK` impiden en la propia base lo que el contrato prohíbe: una fila `not_measured` no puede llevar `value`, `numerator`, `case_count` ni intervalo, y una fila `measured` tiene que llevar `value`. Así lo no medido no puede ser un 0 aunque alguien cargue datos a mano.

Para escribir el script, los valores se convierten a literales SQL con una función única que duplica las comillas simples, fija `standard_conforming_strings` en la transacción, rechaza el carácter NUL y los números no finitos, y escribe `retrieval` como JSON canónico con cast a `jsonb`; nunca se interpola una cadena sin escapar. Los textos no admitidos por la regla 3 ya los rechaza la validación común, pero el escapado no depende de ella. Como las tablas se crean con `IF NOT EXISTS`, un cambio futuro del esquema no migra una base ya cargada: en desarrollo basta con borrar el esquema `evaluation` y volver a cargar.

### Vistas

El mismo script crea dos vistas (`CREATE OR REPLACE VIEW`) de las que beben los paneles:

- **`evaluation.config_changes`**: una fila por cada par de ejecuciones consecutivas de la misma fuente (ordenadas por `run_at`, solo las que tienen fecha) en el que cambió algo. Columnas: `run_id` (la posterior), `previous_run_id`, `source`, `run_at`, `changes` (`text[]` con `bateria`, `modelo`, `prompt` o `corpus`, en ese orden) y `annotation` (`Cambia: bateria, modelo`). Cambia la batería si lo hacen `suite_version` o `suite_sha256`, el modelo si cambia `generation_model`, el corpus si cambia `corpus_sha256`; el prompt solo si las dos huellas están registradas y son distintas (un prompt no registrado no genera anotación). Un par sin cambios no genera fila. Con los datos versionados hoy está vacía: las dos ejecuciones de JUP-070 solo difieren en el proveedor de embeddings y en los parámetros de recuperación.
- **`evaluation.comparable_runs`**: las ejecuciones con fecha cuya clave de comparabilidad tiene al menos dos ejecuciones con fecha. Columnas: `comparability_key`, `run_id`, `source`, `run_at`, `is_real`, `milestone` y `series_runs`. Una clave con una sola ejecución no aparece: de ahí sale el «Sin datos: no hay con qué comparar» de los paneles de evolución (cada panel declara además su `noValue`).

Para usarlas en Grafana: `run_at AS time` directamente (es `timestamptz`), `array_to_string(changes, ',') AS tags` para las anotaciones (una `text[]` llegaría como `{a,b}`) y `'modelo' = ANY(changes)` para filtrar por tipo de cambio.

## Qué toma cada adaptador

| Informe | Ejecución | Filas |
| --- | --- | --- |
| **JUP-070** | Bloque `run` (commit, fecha, versión y huella de la batería, huella del corpus, proveedor y alias de embeddings, parámetros de recuperación, alias del modelo, `synthetic`) | Una fila por estado de `counts` con `cases` como denominador; una fila por métrica del catálogo con `k`, `n`, `rate` e `ci95`; una fila por etapa de latencia |
| **JUP-078** | Sin commit, fecha, batería, corpus, embeddings, prompt ni modelo de generación (el informe trae varios modelos): quedan `null`. `synthetic` es siempre `false`: el benchmark llama de verdad al gateway y sus «casos sintéticos» son preguntas públicas, no una ejecución sintética | Por modelo (en `behavior`, el alias), `grp` `benchmark`: `cases` con `pass` = `successful` y `fail` = `cases - successful` (denominador `cases`); `keyword_score` (unidad `puntuacion`), `latency_p95` (`ms`) y `cost` (`usd`). Si `successful` es 0 las tres son no medidas aunque el informe traiga un número: el generador escribe `mean_keyword_score: 0` sin llamadas correctas y ese 0 significa «sin datos». El juicio es siempre `automatic` |
| **JUP-022** | `generated_at` como fecha; proveedor y alias de embeddings; troceado como parámetros de recuperación | Por punto del barrido (`top_k`, `max_distance`): acierto de documento, acierto de sección y resultado vacío, con el número de casos como denominador, y los candidatos de `selection` (uno por `top_k` en el informe real) con `selected: true`, es decir, todas las filas de los puntos que coinciden con alguno. El numerador es `round(rate × casos)` solo si reproduce la tasa del informe (tolerancia 5e-5, porque el informe redondea a 4 decimales); si no, `null`. Una tasa sobre cero casos es no medida. `grp` `calibration`; `metric_id` `document_hit_answer`, `section_hit_answer`, `empty_answer`, `document_hit_non_answer` y `empty_non_answer`; `behavior` `top_k=K,max_distance=D` (`none` si no hay umbral). `by_category` no se publica porque trae tasas sin denominador. El `retrieval` del `run` solo lleva `chunk_size` y `chunk_overlap`: `top_k` y `max_distance` van por fila |
| **JUP-068** | `commit`, `dataset_version` (como `suite_version`) e `input_sha256` (como `suite_sha256`) del informe; `suite` `JUP-068`; `synthetic` es `true` si `provenance` es `synthetic` y `false` si es `measured`. `run_at` queda `null`: el informe no trae marca de ejecución y su periodo no se deduce como fecha. No se publican `scope`, `configuration`, `reviewer`, `evidence`, `period`, `pairs` ni `estimates` (texto libre o identificadores arbitrarios). El informe se obtiene ejecutando `node tools/business-metrics.mjs report <entrada>` (sin shell y con tope de 60 s; una ruta relativa se resuelve desde la raíz del repositorio) | 23 filas de tipo B, `judgment` `null`, `behavior` `all`: **tiempo** (`grp` `time`): `time_trials` con los cuatro estados y su total como denominador (unidad `parejas`), `manual_time`, `assisted_time` y `time_saved` (`ms`, denominador `eligible_pairs`) y `time_saved_percent` (`porcentaje`); **asignación** (`allocation`): `allocated`, `shared`, `unallocated`, `excluded`, `total` y `eligible` (unidad `<moneda>_minor_<dígitos>`, p. ej. `eur_minor_2`) y los porcentajes `assigned_percent`, `governed_percent` (numerador `allocated + shared`) y `unallocated_percent`, con `eligible_minor` de denominador; **ahorro** (`savings`): `opportunities` (`behavior` `estimated`, `candidate` o `not_evaluable`, unidad `recuento`), `potential_savings`, `potential_savings_percent` y `realized_savings`. El ahorro realizado, que el informe deja en `null` por diseño, queda como no medido: es la fila que dice «beneficio realizado no medido». `manual_time` y `assisted_time` son no medidos si no hay parejas elegibles (son sumas de nada); en cambio un importe de asignación sin líneas de coste es un `0` medido, copia fiel del informe, y sus porcentajes sí son no medidos |

## Ejecuciones no reales

Cada ejecución se clasifica como real o no real. Una ejecución no real lleva uno o más motivos y los paneles la distinguen por rótulo y estilo.

| Motivo | Cuándo se asigna |
| --- | --- |
| `plantilla` | El modelo de generación es `plantilla-sin-modelo` |
| `doble` | El proveedor o el alias de embeddings es `mock` |
| `sintetica` | El informe declara `synthetic: true` o `provenance: synthetic` |
| `sin_modelo_verificado` | La fuente es una campaña sobre el chat (`JUP-070` o `JUP-071`) y no hay modelo de generación registrado |

Con los informes actuales, las dos ejecuciones de JUP-070 son de plantilla y la primera además usa embeddings `mock`; el ejemplo de JUP-068 es sintético. Son pruebas del flujo, no calidad del asistente.

## Evolución y comparabilidad

Dos ejecuciones son comparables si comparten la **clave de comparabilidad**: fuente, `suite_version`, `suite_sha256`, `corpus_sha256`, `embedding_provider`, `embedding_alias`, `retrieval`, `generation_model`, `prompt_sha256` y motivos de ejecución no real. Un campo `null` solo es igual a otro `null`.

- Una serie con una sola ejecución, o sin otra comparable, muestra «Sin datos: no hay con qué comparar». No se dibuja ninguna línea ni un 0 %.
- Con los datos actuales, las ejecuciones 1 y 2 de JUP-070 tienen claves distintas (cambian el proveedor de embeddings y `max_distance`), así que las dos muestran ese mensaje.
- Una anotación marca cada cambio de batería, modelo, prompt o corpus entre ejecuciones consecutivas de la misma fuente, con la fecha de la segunda. Si el informe no registra el prompt, se muestra «prompt no registrado» y no hay anotación de cambio de prompt.
- Las series automáticas y las de juicio humano van separadas. Las de juicio humano solo incluyen ejecuciones de hito.
- La latencia de la campaña tiene su propia gráfica porque su unidad (milisegundos) no se puede mezclar con las proporciones (%). Dibuja solo LAT-1 (mediana) y LAT-2 (percentil 95) de la etapa `total`, con las mismas reglas: una serie por clave de comparabilidad, al menos dos puntos medidos y «Sin datos: no hay con qué comparar» si ninguna llega a dos. LAT-3, las demás etapas, GRD-2 y REL-4 quedan fuera de esta gráfica (motivos en «Calculado y no mostrado»). LAT-4, que es una tasa, sí se dibuja en la gráfica de proporciones de las métricas automáticas.

### Juicio humano o automático

El resultado de cada caso (`outcome`) combina comprobaciones objetivas por regla y puntos juzgados por personas, así que todo lo que se cuenta a partir de él depende de juicio humano.

| Métrica | Juicio |
| --- | --- |
| Recuentos `pass` y `fail` de los casos, `ACC-1`, `ACC-3` | `human` |
| Recuentos `blocked` y `not_run`, `ACC-2` (comprobaciones objetivas), `REL-1` a `REL-4`, `GRD-1` a `GRD-3`, `LAT-1` a `LAT-4`, `STR-1`, `STR-2`, `AVL-1` | `automatic` |
| Calibración de JUP-022 y benchmark de JUP-078 | `automatic` |
| Tipo B | `null` (no aplica) |

La herramienta lleva esta tabla fija y una prueba falla si el catálogo de JUP-067 incorpora un identificador sin clasificar.

## Señales en vivo (sección C)

Son los síntomas de salud que ya emite el backend, leídos de Prometheus y no de esta base: consultas por minuto, latencia p95, tasa de error y las proporciones de búsquedas vacías y de fallos de recuperación sobre las consultas que terminaron. La sección enlaza al [dashboard de métricas técnicas](../../apps/monitoring/grafana/dashboards/technical-metrics.json) y no mezcla sus consultas con las de las campañas.

Los contadores de fallos de recuperación nacen a 0 al arrancar el backend (una serie por categoría conocida), de modo que las proporciones valen 0 mientras haya consultas y no haya fallos, y solo muestran «Sin datos» si no ha terminado ninguna consulta en la ventana. La gráfica de consultas por minuto muestra 0 sin tráfico (es un cero medido). La tasa de error del backend vale 0 mientras haya peticiones y ninguna termine en 5xx (el numerador lleva `or vector(0)`, de modo que un cero medido no se confunde con la ausencia de datos) y solo muestra «Sin datos: no hubo peticiones» cuando no hubo peticiones en la ventana; por eso su expresión ya no es idéntica a la del dashboard técnico (JUP-043), que no se toca. La latencia p95 del backend agrega **todas las rutas** del backend (el título, «Latencia p95, todas las rutas», lo dice; los títulos de la sección C miden como máximo 40 caracteres para no cortarse y «tráfico real» va en la descripción): no es la latencia de las consultas al asistente, que en una campaña está en la sección A.

La proporción de búsquedas vacías es un límite inferior: el denominador incluye consultas respondidas sin pasar por la recuperación. Sin consultas en la ventana el panel muestra «Sin datos».

## Robustez (JUP-071)

No existe todavía un informe de robustez. La sección está en el dashboard y muestra «Sin datos» hasta que haya filas. Cuando JUP-071 tenga su informe, puede emitir un fichero `rows-v1` con `source: JUP-071` (por categoría y tipo de perturbación, comparada con su caso base en `behavior`) o aportar su propio adaptador, y añadirlo al manifiesto; el dashboard no cambia.

La lectura del panel «Robustez (JUP-071)» (nombres, traducciones y categorías) no está cerrada: se hará con el informe real de JUP-071, cuando exista.

### Contrato de clasificación para nuevas fuentes

Quien emita filas `rows-v1` para una fuente nueva (por ejemplo, JUP-071) debe clasificarlas bien, porque las gráficas de evolución son genéricas a propósito: no filtran por fuente y cualquier serie comparable entra. En concreto, la gráfica de métricas automáticas no filtra por fuente, así que lo único que impide que una proporción que depende de personas aparezca en ella es la marca de juicio (`human` o `automatic`) que ponga quien emite las filas. Reglas:

- Las proporciones que salen del resultado de un caso (`pass_over_total`, `pass_over_evaluated` y los `pass`/`fail` de casos) se marcan `human`: el resultado de un caso mezcla reglas y puntos juzgados por personas, y marcarlas `automatic` las llevaría a «Evolución de las métricas automáticas».
- Los marcados de revisión (`reduced_coverage`) también se marcan `human`, porque los decide una persona.
- Las comprobaciones que decide una regla (`numeric_checks`) se marcan `automatic`.
- No se reutilizan los grupos de las campañas de JUP-070 (`accuracy`, `relevance`, `grounding`, `latency`, `robustness`, `availability`): varios paneles toman esos grupos sin filtrar por fuente y mezclarían las series de la nueva fuente con las de las campañas. Una fuente nueva usa grupos propios y distintos de esos.
- «Estado de los casos por ejecución» solo muestra ejecuciones de JUP-070: una ejecución de otra fuente con el grupo y la métrica `cases` no aparece en ese panel.

## Indicadores de la memoria (JUP-130)

Tarjeta: [JUP-130](https://trello.com/c/mkwnaPz2). Tres informes `rows-v1` que genera `tools/memory-indicators.py` (un subcomando por indicador) y que se versionan en `docs/evidence/JUP-130/` junto a una tabla Markdown para la memoria. Están en el manifiesto, así que los carga el comando de siempre (`evaluation-dashboard:load`) sin pasos nuevos: la carga solo lee ficheros versionados y no consulta ni al gateway ni a la pila.

| Indicador | Subcomando | Fuente | Grupo | Tipo | Panel |
| --- | --- | --- | --- | --- | --- |
| Calidad de la detección de anomalías | `anomalies` | `JUP-130-anomalies` | `anomaly_detection` | A (automático) | «Calidad de la detección de anomalías», sección A |
| Coste de IA facturado frente a estimado | `ai-cost` | `JUP-130-ai-cost` | `ai_cost` | B | «Coste de IA: facturado frente a estimado», sección B |
| Frescura y reconciliación de los datos | `data` | `JUP-130-data` | `data_quality` | B | «Frescura y reconciliación de los datos», sección B |

```
python tools/memory-indicators.py anomalies --reference 2026-10-30
python tools/memory-indicators.py data --reference 2026-10-30 --base-url http://localhost:8000
python tools/memory-indicators.py ai-cost --from 2026-10-09 --to 2026-10-21
```

`data` lee la contraseña de la cuenta demo de la variable `DEMO_PASSWORD`; `ai-cost` lee la clave de administración del gateway de `LITELLM_MASTER_KEY` y la del proveedor de `OPENROUTER_API_KEY` (o de ficheros con `--gateway-key-file` y `--openrouter-key-file`). Ninguna clave se imprime ni se escribe en un informe. Con `--run-at` y `--commit` se fijan la fecha y el commit del informe, y con los mismos argumentos el informe y la tabla salen idénticos byte a byte.

- **Una fuente por indicador.** La vista `config_changes` anota las diferencias entre ejecuciones consecutivas de una misma fuente y `comparable_runs` agrupa como serie las de igual configuración. Con una fuente común, las tres medidas se anotaban entre sí («Cambia: batería») y se agrupaban. La batería de cada una la identifican `suite_version` y, en anomalías, la huella `suite_sha256` de la lista de eventos inyectados (`docs/validation/JUP-130-injected-events.json`): si esa lista cambia, el dashboard lo anota.
- **El panel de negocio de JUP-068 filtra por su fuente.** Antes solo filtraba por `measure_type = 'B'` y habría mostrado las filas de coste de IA y de datos, que también son de tipo B.
- **Coste de IA: el gateway dice qué consultas hubo y OpenRouter lo que se facturó.** El gateway aporta consultas, modelo y errores (`/spend/logs`); OpenRouter aporta el coste facturado de cada generación de chat (`GET /api/v1/generation`). El coste por consulta es el facturado. Se informan además la cobertura de lo confirmado y la diferencia entre estimado y facturado. Los embeddings no llevan identificador de generación de OpenRouter y se informan aparte como estimados. Leer `/spend/logs` desde la herramienta de medición, y no desde Grafana, amplía [ADR-0022](../adr/ADR-0022-assistant-evaluation-results-in-grafana.md) sin cambiar su sentido: Grafana no accede a la base del gateway.
- **Los 429 son del gateway, no del proveedor.** Son el límite por clave del propio gateway (`ProxyRateLimitError`); los fallos del proveedor son errores 5xx (`APIError`). Se informan como dos tasas separadas.
- **Reconciliación con un único redondeo.** La fuente (el CSV de la demo) se suma por inquilino y divisa con aritmética decimal exacta y se redondea una sola vez con `ROUND_HALF_UP` a dos decimales, igual que el contrato de costes; las divisas nunca se compensan entre sí. La diferencia se informa en unidades menores.
- **Lo no medido.** Sin gateway, sin clave de OpenRouter o sin pila, las filas correspondientes son `not_measured` (el panel muestra «No medido» o «Sin datos»), nunca 0. El informe de coste de IA añade una fila `measurement_cause` por cada causa (`gateway:clave_ausente`, `gateway:conexion`, `gateway:http_401`, `openrouter:clave_ausente`, `openrouter:conexion`…) para distinguir «sin clave» de «servicio caído». La cobertura de lo facturado solo es una cifra medida si se llegó a consultar a OpenRouter. Una generación que OpenRouter no devuelve cuenta como no confirmada y baja la cobertura.

El retraso hasta la detección vale 0 por construcción: el episodio se abre el mismo día evaluado en que se dispara la regla, así que no mide la latencia real (en producción el mínimo es de un día, porque solo se evalúan días completos).

Primera medición (2026-10-21): con la referencia 2026-10-30 el detector abre 5 episodios de 7 eventos inyectados (precisión 5/5, recall 5/7, y 5/5 sobre los detectables por diseño; los dos que faltan, un pico desde cero y la aparición de un servicio, no se detectan por diseño). El coste de IA sobre 100 consultas de chat, todas confirmadas por OpenRouter, es de 0,002601 USD por consulta; el gateway estimó 0,250394 USD y OpenRouter facturó 0,260096 USD, y esa diferencia la explican cuatro consultas del 2026-10-20 que el gateway registró con gasto 0. Los datos reconcilian a cero en los tres pares inquilino-divisa y la frescura es de 0 días. Cada tabla de `docs/evidence/JUP-130/` declara qué no demuestra: datos sintéticos, pocos eventos, etiquetas escritas por quien diseñó los datos y un gasto local a la máquina que ejecutó las consultas.

## Calculado y no mostrado

Cifras que el informe de origen calcula, o que existen en el sistema, y que el dashboard no enseña (salvo el intervalo de confianza, que ahora sí se muestra). Cada una lleva su motivo para que echarla en falta no parezca un olvido; ninguna se ha descartado por incómoda y todas se pueden reconsiderar en otro change.

- **Intervalo de confianza del 95 %.** Se carga desde el informe de JUP-070 (`ci_low` y `ci_high`) y ahora sí se muestra: aparece en la tabla «Resultados por métrica y ejecución» junto al valor como `IC95 lo–hi %`, solo cuando existen los dos límites. No se dibuja en las gráficas de evolución porque una banda por serie las haría ilegibles y porque el intervalo ya se lee en la matriz.
- **GRD-2 (cifras sin rastro).** Es un recuento de cifras de la respuesta que no aparecen en la evidencia, no una tasa: la evolución solo dibuja tasas (y la latencia en milisegundos), así que mezclarlo en una gráfica forzaría un eje con otra unidad. Se ve en la matriz.
- **REL-4 (confianza de la recuperación).** Es una similitud (mediana y cuartiles), no una tasa, por la misma razón que GRD-2 no entra en la evolución de proporciones; se ve en la matriz.
- **LAT-3 (latencia máxima).** Está en la matriz, pero no en la evolución porque el máximo lo fija un solo caso lento y es demasiado ruidoso para dibujarlo como una línea entre ejecuciones; la evolución usa la mediana y el percentil 95.
- **Tamaño del corpus (documentos y trozos).** No se carga ni se muestra porque el contrato `rows-v1` y los adaptadores solo transportan la huella del corpus (`corpus_sha256`), no su tamaño; ampliarlo sería otro change que tocaría el contrato y la herramienta de carga.
- **Casos críticos.** El informe de JUP-070 los calcula, pero no se muestran porque no entran en el contrato `rows-v1` y, por tanto, no llegan a la base ni al dashboard; mostrarlos exigiría ampliar el contrato y los adaptadores.
- **Casos juzgados por una sola persona.** El informe de JUP-070 también los calcula, pero no se muestran porque tampoco entran en el contrato `rows-v1`; la matriz solo enseña las métricas con juicio humano (variante `con juicio humano`) y no cuántos casos tuvieron un único juez.
- **Calibración por categoría.** Solo se carga el barrido global de JUP-022 (por `top_k` y distancia máxima); `by_category` no se publica porque trae tasas sin denominador y el contrato exige que cada proporción lleve el suyo.
- **Fallos de recuperación por categoría.** No se muestran por categoría porque la sección C suma todas las categorías en una sola proporción para mantener el panel legible; el detalle por categoría está en Prometheus, con `backend_retrieval_failures_total{category=…}`, y no en este dashboard.
