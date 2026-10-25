# Evidencia JUP-067 — metricas tecnicas del asistente

Change: [jup-067-assistant-technical-metrics](../../openspec/changes/archive/2026-10-04-jup-067-assistant-technical-metrics/) · [Tarjeta](https://trello.com/c/bwvfLpUG) · [Definiciones](../validation/JUP-067-metrics.md) · [Catalogo](../validation/JUP-067-metrics-catalogue.json) · [Calculador](../../tools/assistant-metrics.py)

Base: `develop` c3aa9d6 (con JUP-022 integrado). Rama `feat/JUP-067-assistant-technical-metrics`, ejecutado en Windows con el Python 3.12 del venv del backend.

## Que se entrega

El catalogo de 17 metricas (ACC-1 a 3, REL-1 a 4, GRD-1 a 3, LAT-1 a 4, STR-1 y 2, AVL-1), el formato de resultados version 1, el calculador de referencia y su documentacion. No hay cambios en el backend, el processor ni el frontend, asi que no se repiten las suites de producto.

## Comandos y resultados

| Comando | Resultado |
| --- | --- |
| `corepack pnpm assistant-metrics:test` | 98 pruebas correctas |
| `corepack pnpm retrieval-calibration:test` | 27 pruebas correctas, 1 omitida (prueba de otro change, no toca este) |
| `node --test tools/*.test.mjs` | 244 pruebas, 243 correctas. El fallo es `ports already published by this Compose project are not busy` de `local-doctor`, de JUP-050: falla en la maquina de la autora porque tiene su propio stack en los puertos 3000 y 9090, no por este change |
| `corepack pnpm openspec:validate` | 45 de 45 |
| `corepack pnpm jup:check -- --change jup-067-assistant-technical-metrics` | correcto |
| `corepack pnpm jup:check:all` | correcto |
| `corepack pnpm jup:cleanup:check` | 820 archivos sin agentes personales, binarios ni tareas paralelas |
| `git diff --check origin/develop...HEAD` | limpio |
| Dos ejecuciones de `python tools/assistant-metrics.py --results tools/fixtures/assistant-metrics/synthetic-results.json ... --generated-at 2026-10-05T10:00:00Z` | informes JSON y Markdown identicos byte a byte |

La prueba que compara el hash de la bateria de Python con el de `node tools/validation-questions.mjs prepare` pasa; la bateria tiene hash `e15349564edfa5ce6cef94ff90ee2bfd15ef17656a2c4b201ac37bcd6d44571c`.

## Pruebas, mutantes y controles negativos

Las pruebas se escribieron antes del codigo (RED) y cubren formulas calculadas a mano (intervalo de Wilson con 7 de 10, 0 de 5 y 5 de 5; percentil por rango mas cercano con 10, 19 y 20 observaciones; cuartiles con 5 datos), las poblaciones (`blocked` y `not_run` fuera de los denominadores y contados, `clarify` y `abstain` aparte), las reglas del formato, los objetivos provisionales exactamente en su limite y la CLI con entradas hostiles (enteros enormes, anidamiento, rutas de salida iguales a una entrada o a un enlace duro, BOM, `--generated-at`, caracteres no ASCII por tuberia). Se rechazan por nombre y sin imprimir su valor los campos que no estan en el formato.

Se aplicaron a mano 105 mutantes sobre el calculador, uno por vez en una copia restaurada despues, y cada uno hace fallar al menos una prueba: denominadores y estados, extremos y z del intervalo de Wilson, suelo en lugar de techo en el percentil, minimos de observaciones, similitud con el peor fragmento o con el signo cambiado, disponibilidad con un error de mas, definicion de caso critico, quien decide cada tipo de comprobacion y su grafia, hash de la bateria y del catalogo, campos y longitudes permitidos, una comprobacion por punto de rubrica, coherencia entre resultado, fallo, etapa, `structured_ok` y latencias, datos de respuesta en llamadas fallidas, parametros de recuperacion, proteccion de las entradas frente a `--output`, enlaces duros, BOM, fecha real y las poblaciones `answer`. Dos mutantes sobrevivieron al principio (el minimo de observaciones del percentil 95 y los valores exactamente en el objetivo) y se cerraron con pruebas de limite.

## Revision adversarial

Cinco pasadas independientes con el agente `adversarial-reviewer`; el detalle y la disposicion de cada hallazgo estan en [review.md](../../openspec/changes/archive/2026-10-04-jup-067-assistant-technical-metrics/review.md). Los hallazgos BLOCKING y HIGH se reprodujeron antes de corregirlos: un caso critico con cifra sin rastro que contaba como acierto, una llamada fallida contada en los percentiles y en la tasa de fallos, un entero enorme que lanzaba una traza, un `pass` sin comprobaciones, datos de respuesta en una llamada fallida, un caso real no representable (critico con la rubrica cumplida y una cifra inventada) y un fallo de esquema sin latencias. Los cuatro hallazgos LOW restantes los acepto Lucia y estan en `openspec/findings/backlog.md` (RF-067-001 a RF-067-004).

## Nota de release

| Fecha | JUP | Nota de release | Review | ADRs |
| --- | --- | --- | --- | --- |
| 2026-10-04 | JUP-067 | Hay un catalogo versionado de 17 metricas tecnicas del asistente, un formato de resultados por caso sin texto ni credenciales y un calculador offline determinista (`tools/assistant-metrics.py`, `pnpm assistant-metrics:test`). Los objetivos de ADR-0002 se muestran como referencia provisional, no como puerta de aceptacion. | [review.md](../../openspec/changes/archive/2026-10-04-jup-067-assistant-technical-metrics/review.md) | No aplica (ADR-0002 es la fuente de los objetivos, sin cambiarlo) |

## No validado

- No hay una ejecucion real contra el asistente: el productor de resultados lo crea JUP-070, asi que el fichero de ejemplo es sintetico y esta marcado como tal. El formato puede subir de version cuando JUP-070 lo use.
- No se evaluan respuestas generadas por un modelo, ni la relevancia con embeddings reales, ni la latencia real.
- La CI de GitHub sobre estos commits no se ha ejecutado; las comprobaciones son locales.
- La revision y la validacion de otros miembros del equipo se registran en el PR y en Trello, no aqui.
