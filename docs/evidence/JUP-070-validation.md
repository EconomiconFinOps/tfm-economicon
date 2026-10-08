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

Las dos ejecuciones usan el mismo corpus (4 documentos, 52 fragmentos), la misma batería de JUP-069 (28 casos), `top_k` 4, distancia máxima 0,6 y fragmentos de 500 con solape 50. El código de `apps/` es el mismo en ambas.

**Ningún modelo generó las respuestas.** El chat actual devuelve una plantilla que repite la pregunta y lista fragmentos recuperados (la generación con modelo es JUP-035). Por eso esta medición es la línea base del chat de hoy, no una tasa de acierto del producto final.

| Métrica | Ejecución 1 (mock) | Ejecución 2 (litellm) |
| --- | --- | --- |
| Casos | 0 pass, 28 fail | 0 pass, 28 fail |
| ACC-1 (casos `answer` con pass) | 0 de 20 | 0 de 20 |
| ACC-2 (comprobaciones objetivas) | 26 de 51 | 25 de 51 |
| REL-1 (acierto de documento) | 16 de 20 | 20 de 20 |
| REL-2 (acierto de sección) | 6 de 20 | 16 de 20 |
| GRD-2 (cifras sin rastro, críticos) | 0 | 0 |
| STR-1, AVL-1, GRD-1, GRD-3 | 100 % | 100 % |
| LAT-2 total, percentil 95 | 1835 ms | 4562 ms |
| Veredicto | No aceptado | No aceptado |

El veredicto es «No aceptado» por ACC-1 (umbral propuesto, 0,8) y ACC-2 (umbral ADR-0002, 0,9): la plantilla no calcula las cifras que piden los casos críticos. Con embeddings reales la recuperación mejora de forma clara (REL-1 de 0,8 a 1,0 y REL-2 de 0,3 a 0,8). Con 20 casos, un caso son 5 puntos: no se interpretan diferencias pequeñas.

## Límites de esta medición

- **Provisional.** Los 46 puntos `required-N` los juzgó una sola persona (Lucía) como `fail`, porque la respuesta es la plantilla y no hace lo que pide ningún punto. Los 14 casos críticos deberían tener dos revisores: se puntuó con `--provisional` y el informe los lista.
- **Una sola repetición por proveedor.** El método pide tres ejecuciones con la misma configuración; aquí hay una de cada. La variación entre las dos mide el cambio de embeddings, no la variabilidad de una misma configuración.
- **Solo se mide la latencia total.** Las filas de embedding y recuperación valen 0 por construcción y no se interpretan. La latencia de la ejecución 2 incluye la llamada de embeddings a través del gateway local.
- **Las ejecuciones se hicieron sobre `b12b3c8` (1) y `8a116df` (2).** Entre ellos y la cabeza de la rama solo cambió la herramienta de evaluación y su documentación: `git diff` de `apps/`, `tools/assistant-metrics.py` y la batería es vacío.
- **Los textos de las respuestas, las hojas y los juicios no se versionan** y se guardaron fuera del repositorio.
- **Coste.** La ejecución 2 pasó por un gateway local con claves virtuales restringidas a modelos de embeddings y con presupuesto; el gasto total registrado fue de unos 0,00016 USD.

## Comprobaciones locales

Se rellenan al cerrar el change (ver `tasks.md`, grupo 4).
