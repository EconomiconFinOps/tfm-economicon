# Dashboard de resultados de evaluación del asistente (JUP-121)

Contrato de datos y guía de uso del dashboard de Grafana que reúne los resultados de evaluación del asistente. Tarjeta: [JUP-121](https://trello.com/c/aIdxwsXR). Decisión: [ADR-0022](../adr/ADR-0022-assistant-evaluation-results-in-grafana.md). Requisitos: [spec](../../openspec/changes/jup-121-assistant-evaluation-dashboard/specs/assistant-evaluation-dashboard/spec.md).

> **Estado:** este documento fija el contrato. La herramienta `tools/evaluation-dashboard.py` y el dashboard se implementan en las tareas 2 a 4 de JUP-121; hasta entonces los comandos de abajo todavía no existen.

## Qué muestra y qué no demuestra

El dashboard junta tres tipos de medida que responden a preguntas distintas. Cada panel declara su tipo en su descripción, con tres líneas: `Tipo: A|B|C`, `Mide: …` y `No demuestra: …`.

| Tipo | Responde a | Datos | No demuestra |
| --- | --- | --- | --- |
| **A. Calidad con rúbrica** | ¿Responde bien el asistente a casos que conocemos? | Campañas de JUP-070 sobre la batería de JUP-069 con las métricas de JUP-067, calibración de JUP-022 y benchmark de JUP-078 | El comportamiento con usuarios reales ni con preguntas fuera de la batería |
| **B. Negocio** | ¿Qué valor aportaría el asistente? | Registros reproducibles de JUP-068 | Un beneficio observado mientras no haya un piloto real |
| **C. Señales en vivo** | ¿Está sano el sistema ahora? | Métricas de Prometheus emitidas por el backend con tráfico real | Que las respuestas sean correctas: solo detecta síntomas |

La latencia y la disponibilidad existen en A (sobre las peticiones de una campaña) y en C (sobre tráfico real) con significados distintos. Nunca comparten panel.

Las definiciones y fórmulas de las métricas de A están en el [catálogo de JUP-067](JUP-067-metrics-catalogue.json) y no se repiten aquí.

## Regenerar los datos

Un único comando carga los informes en la base. Con el entorno levantado (`docker compose up -d`):

```sh
corepack pnpm evaluation-dashboard:load
```

- Lee el manifiesto versionado [evaluation-runs.json](evaluation-runs.json) y reemplaza los datos anteriores de forma atómica e idempotente: dos cargas seguidas dejan lo mismo, y una carga que falla conserva la anterior.
- Necesita `GRAFANA_EVALUATION_DB_PASSWORD` en el entorno (la contraseña del rol de lectura de Grafana). Si falta, termina con un error que nombra la variable.
- Para añadir ejecuciones que no son de hito, sin tocar Git, se pasa un manifiesto local: `corepack pnpm evaluation-dashboard:load -- --manifest ../evaluacion/manifiesto.json`. Se pueden pasar varios `--manifest`.
- `corepack pnpm evaluation-dashboard:rows` escribe las filas normalizadas en JSON sin tocar la base, para revisarlas o para probar un informe nuevo.

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
| `retrieval` | no | Objeto con `top_k`, `max_distance`, `chunk_size` y `chunk_overlap` |
| `generation_model` | no | Alias del modelo de generación |
| `prompt_sha256` | no | Huella del prompt. Ningún informe actual la registra |
| `synthetic` | no | `true` si el informe declara ser sintético |
| `milestone` | no | Lo fija el manifiesto, no el informe |

### Resultado (`results`)

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

## Qué toma cada adaptador

| Informe | Ejecución | Filas |
| --- | --- | --- |
| **JUP-070** | Bloque `run` (commit, fecha, versión y huella de la batería, huella del corpus, proveedor y alias de embeddings, parámetros de recuperación, alias del modelo, `synthetic`) | Una fila por estado de `counts` con `cases` como denominador; una fila por métrica del catálogo con `k`, `n`, `rate` e `ci95`; una fila por etapa de latencia |
| **JUP-078** | Sin commit, fecha, batería, corpus, embeddings, prompt ni modelo de generación (el informe trae varios modelos): quedan `null`. `synthetic` es siempre `false`: el benchmark llama de verdad al gateway y sus «casos sintéticos» son preguntas públicas, no una ejecución sintética | Por modelo (en `behavior`, el alias), `grp` `benchmark`: `cases` con `pass` = `successful` y `fail` = `cases - successful` (denominador `cases`); `keyword_score` (unidad `puntuacion`), `latency_p95` (`ms`) y `cost` (`usd`). Si `successful` es 0 las tres son no medidas aunque el informe traiga un número: el generador escribe `mean_keyword_score: 0` sin llamadas correctas y ese 0 significa «sin datos». El juicio es siempre `automatic` |
| **JUP-022** | `generated_at` como fecha; proveedor y alias de embeddings; troceado como parámetros de recuperación | Por punto del barrido (`top_k`, `max_distance`): acierto de documento, acierto de sección y resultado vacío, con el número de casos como denominador, y el candidato de `selection` con `selected: true`. El numerador es `round(rate × casos)` solo si reproduce la tasa del informe; si no, `null` |
| **JUP-068** | `run_id`, `commit` y periodo del informe; `provenance` conservada | Tipo B: estados de tiempo ahorrado, tiempo ahorrado, cobertura de gasto asignado y ahorro potencial con sus denominadores; el ahorro realizado, que el informe deja en `null`, queda como no medido |

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

Dos ejecuciones son comparables si comparten la **clave de comparabilidad**: fuente, `suite_sha256`, `corpus_sha256`, `embedding_provider`, `embedding_alias`, `retrieval`, `generation_model`, `prompt_sha256` y motivos de ejecución no real. Un campo `null` solo es igual a otro `null`.

- Una serie con una sola ejecución, o sin otra comparable, muestra «Sin datos: no hay con qué comparar». No se dibuja ninguna línea ni un 0 %.
- Con los datos actuales, las ejecuciones 1 y 2 de JUP-070 tienen claves distintas (cambian el proveedor de embeddings y `max_distance`), así que las dos muestran ese mensaje.
- Una anotación marca cada cambio de batería, modelo, prompt o corpus entre ejecuciones consecutivas de la misma fuente, con la fecha de la segunda. Si el informe no registra el prompt, se muestra «prompt no registrado» y no hay anotación de cambio de prompt.
- Las series automáticas y las de juicio humano van separadas. Las de juicio humano solo incluyen ejecuciones de hito.

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

La proporción de búsquedas vacías es un límite inferior: el denominador incluye consultas respondidas sin pasar por la recuperación. Sin consultas en la ventana el panel muestra «Sin datos».

## Robustez (JUP-071)

No existe todavía un informe de robustez. La sección está en el dashboard y muestra «Sin datos» hasta que haya filas. Cuando JUP-071 tenga su informe, puede emitir un fichero `rows-v1` con `source: JUP-071` (por categoría y tipo de perturbación, comparada con su caso base en `behavior`) o aportar su propio adaptador, y añadirlo al manifiesto; el dashboard no cambia.
