# Evidencia técnica — JUP-070

Fecha: 2026-10-08. Rama: `feat/JUP-070-assistant-response-evaluation`. [Trello](https://trello.com/c/tpSyzXOS).

## Entregable

- [Herramienta](../../tools/assistant-eval.py) con `collect`, `review-sheet`, `score` y `compare`, y sus [reglas](../validation/JUP-070-evaluation-rules.json).
- [Metodología](../validation/JUP-070-evaluation.md): quién decide cada comprobación, cómo ejecutarla, umbrales y límites.
- Dos mediciones de referencia del chat actual, sin texto de respuestas:

| Ejecución | Resultados | Informe | Embeddings |
| --- | --- | --- | --- |
| 1 | [resultados](JUP-070-run-1-results.json) | [informe](JUP-070-run-1-report.md) | `mock` (sin significado semántico) |
| 2 | [resultados](JUP-070-run-2-results.json) | [informe](JUP-070-run-2-report.md) | `litellm`, alias `economicon-embedding`, vector de 1536 |

## Qué se midió

Las dos ejecuciones usan el mismo corpus (4 documentos, 52 fragmentos), la misma batería de JUP-069 (28 casos), `top_k` 4 y fragmentos de 500 con solape 50. La distancia máxima fue 0,6 en la ejecución 2 y no hubo umbral en la ejecución 1 (`max_distance` nulo). El código de `apps/` es el mismo en ambas.

**Ningún modelo generó las respuestas.** El chat actual devuelve una plantilla que repite la pregunta y lista fragmentos recuperados (la generación con modelo es JUP-035). Por eso esta medición es la línea base del chat de hoy, no una tasa de acierto del producto final.

| Métrica | Ejecución 1 (mock) | Ejecución 2 (litellm) |
| --- | --- | --- |
| Casos | 0 pass, 28 fail | 0 pass, 28 fail |
| ACC-1 (casos `answer` con pass) | 0 de 20 | 0 de 20 |
| ACC-2 (comprobaciones objetivas) | 26 de 51 | 25 de 51 |
| REL-1 (acierto de documento) | 16 de 20 | 20 de 20 |
| REL-2 (acierto de sección) | 6 de 20 | 16 de 20 |
| GRD-2 (cifras sin rastro, críticos) | 0 | 0 |
| AVL-1, GRD-1, GRD-3 | 100 % | 100 % |
| STR-1 | 100 % del contrato de respuesta del chat; umbral «no aplica» | igual |
| LAT-2 total, percentil 95 | 1835 ms | 4562 ms |
| Veredicto | No aceptado | No aceptado |

El veredicto es «No aceptado» por ACC-1 (umbral propuesto, 0,8) y ACC-2 (umbral ADR-0002, 0,9): la plantilla no calcula las cifras que piden los casos críticos. Con embeddings reales la recuperación mejora de forma clara (REL-1 de 0,8 a 1,0 y REL-2 de 0,3 a 0,8). Con 20 casos, un caso son 5 puntos: no se interpretan diferencias pequeñas.

**ACC-2 baja de 26 a 25 aunque la recuperación mejora, y no es una regresión.** En la ejecución 2, `forbidden-1` del caso JUP-069-006 («Clasificar 5 % exacto como amarillo») sale `fail` porque el segundo fragmento recuperado es la sección «KPIs Mínimos» de `economicon-mvp-rules.md`, que contiene la línea «amarillo: mayor que 5 % y menor o igual a 10 %», y el patrón de la regla coincide con «amarillo: mayor que 5 %». La plantilla copia el fragmento y no clasifica nada. Es el falso positivo registrado como RF-070-008, que además es más amplio que los casos 006 y 007 (ver su fila en el backlog). El veredicto de la medición no cambia, pero esta métrica sí.

## Límites de esta medición

- **STR-1 no mide salida estructurada.** `structured_ok` solo dice que la respuesta cumple el contrato de respuesta del chat, que la recogida ya exige, así que el calculador da 100 %. El veredicto lo trata como «no aplica» (`acceptance.structured_output` en las reglas) hasta que el chat devuelva la salida estructurada de JUP-024.
- **Provisional.** Los 46 puntos `required-N` los juzgó una sola persona (Lucía) como `fail`, porque la respuesta es la plantilla y no hace lo que pide ningún punto. Los 14 casos críticos deberían tener dos revisores: se puntuó con `--provisional` y el informe los lista.
- **Una sola repetición por proveedor.** El método pide tres ejecuciones con la misma configuración; aquí hay una de cada. La variación entre las dos mide el cambio de embeddings, no la variabilidad de una misma configuración.
- **Solo se mide la latencia total.** Las filas de embedding y recuperación valen 0 por construcción y no se interpretan. La latencia de la ejecución 2 incluye la llamada de embeddings a través del gateway local.
- **Las ejecuciones se hicieron sobre `b12b3c8` (1) y `8a116df` (2).** Desde la ejecución 2 (`8a116df`) hasta la cabeza de la rama, los ficheros que intervienen en el chat y la recuperación (`apps/backend/app/api/routes/assistant.py`, `apps/backend/app/services/assistant.py`, `vector_store.py`, `citations.py`, `embedding_provider.py`), `apps/processor`, `tools/assistant-metrics.py` y la batería no cambian. El merge de `develop` trajo JUP-047 (23 ficheros en `apps/`, la salud del sistema y su configuración), que no interviene en la medición. Esta comprobación cubre la cabeza frente a la ejecución 2; para la ejecución 1 (`b12b3c8`) no se repitió.
- **Los textos de las respuestas, las hojas y los juicios no se versionan** y se guardaron fuera del repositorio.
- **Coste.** La ejecución 2 pasó por un gateway local con claves virtuales restringidas a modelos de embeddings y con presupuesto; el gasto total registrado fue de unos 0,00016 USD.

## Comprobaciones locales

Entorno: Windows, Python 3.14 y Node.js 24. La CI usa Python 3.12 y Node.js 22.

| Comando | Resultado |
| --- | --- |
| `corepack pnpm assistant-eval:test` | 109 pruebas correctas |
| `corepack pnpm assistant-metrics:test` | 103 pruebas correctas, sin cambios en el calculador |
| `node --test tools/*.test.mjs` | 246 pruebas correctas, 0 fallidas |
| `node tools/validation-questions.mjs validate` | 28 consultas, 7 categorías |
| `corepack pnpm openspec:validate` | 54 elementos correctos, 0 fallidos |
| `corepack pnpm jup:check:all` | Todos los cambios correctos (el change está archivado, por lo que `jup:check -- --change` ya no lo encuentra) |
| `node tools/jup-cleanup-check.mjs` | Correcto |
| `git diff --check` | Sin errores de espacios |
| `git diff 2f9a5f5 HEAD -- apps tools/assistant-metrics.py docs/validation/JUP-069-questions.json` | Vacío: ni el producto, ni el calculador, ni la batería han cambiado |

Se hicieron cuatro pasadas del revisor adversarial independiente (ver `review.md`). Los resultados guardados se puntuaron con la herramienta tras la pasada 2. Los cambios posteriores de la herramienta (cifras derivadas redondeadas, texto no codificable) solo pueden reclasificar una cifra de «sin rastro» a «contexto», y los dos resultados no tienen ninguna cifra sin rastro, así que una nueva puntuación daría los mismos ficheros. Los textos de las respuestas no se conservan (estaban fuera del repositorio y la carpeta ya no existe), así que repetir la puntuación exige volver a recoger las respuestas con `collect`.

## Nota de release

| Fecha | JUP | Nota de release | Review | ADRs |
| --- | --- | --- | --- | --- |
| 2026-10-09 | JUP-070 | Herramienta de evaluación de las respuestas del chat con reglas, revisión humana y veredicto, y medición de referencia de la plantilla actual. | [review](../../openspec/changes/archive/2026-10-09-jup-070-assistant-response-evaluation/review.md) | No aplica |
