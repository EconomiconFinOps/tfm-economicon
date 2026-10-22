# Evidencia de JUP-133: reevaluación de métricas tras el cambio de modelo

Tarjeta: [JUP-133](https://trello.com/c/Yv1ETc2G). Informe: [model-reevaluation-report.md](../validation/model-reevaluation-report.md). Plan y gasto: [model-reevaluation-plan.md](../validation/model-reevaluation-plan.md).

Esta evidencia describe cómo se obtuvieron las cifras y qué se comprobó. No valida nada que no esté aquí.

## Entorno

- Rama sobre develop con JUP-132 integrado (ee84f791). Pila `economicon-ai` en el ordenador local de Lucía (Docker Desktop, 7,7 GB para los contenedores): gateway LiteLLM, backend, processor, PostgreSQL con pgvector, Prometheus y Grafana.
- Modelo servido por el alias `economicon-chat`: `openrouter/deepseek/deepseek-v4.1-flash`, proveedor DeepInfra, cuantización fp8. La huella de la entrada del gateway se calcula con `corepack pnpm gateway-config-hash` (`9f74f807…05f2`). El instrumento no verifica qué modelo respondió: son los valores que declara la configuración.

## Mediciones

| Medición | Cómo se hizo | Resultado | Fichero |
| --- | --- | --- | --- |
| Campaña ligera de JUP-071 | 29 conversaciones con `POST /assistant/conversations/{id}/generations`, una repetición, recogida con el colector de JUP-123. En 12 recuperaciones se reconstruyó el contenido recuperado desde la base por identificador y coincidieron las 12 con el hash del servidor | 7 de 29 casos aprobados; 21 fallidos y 1 bloqueado | `docs/evidence/JUP-071-live-flash-r1-report.json`, `.md` y `-rows.json` |
| Coste de IA | `tools/memory-indicators.py ai-cost` sobre el registro del gateway del 21 al 22/10/2026, contrastado con OpenRouter | 75 de 75 consultas contrastadas; 0,049765 USD facturados | `docs/evidence/JUP-133/JUP-133-ai-cost.md` y `.rows.json` |
| Banco de JUP-069 con el chat real | 28 conversaciones, una repetición; 13 recuperaciones reconstruidas desde la base con coincidencia de hash; puntuado con `tools/assistant-eval.py score --provisional` | 10 de 28 casos aprobados; 38 de 46 puntos requeridos; 22 de 22 citas válidas | `docs/evidence/JUP-133/JUP-133-bank28-report.json` y `.md` |

Los juicios de los puntos requeridos de ambas campañas los preparó un agente de programación con un criterio fijo («pedir» cumple solo si la respuesta pide el dato; las prohibiciones cumplen si no se incurre en la conducta) y los aprobó Lucía el 22/10/2026 sin cambios; constan como revisora única (`lucia`), por lo que los informes son provisionales. Los ficheros crudos con texto de respuestas y los juicios están fuera del repositorio.

La ejecución del banco consta con fecha `2026-10-22T00:00:00Z`: el informe de JUP-070 solo trae la fecha, sin hora, y es lo que muestra el dashboard («2026-10-22 00:00»).

## Gasto

0,0435 USD (contrastados con OpenRouter: campaña, muestra de coste y reintentos) más 0,033 USD estimados por el gateway del banco: ≈ 0,077 USD de los 1,5 USD autorizados. Cada gasto se lanzó con la confirmación expresa de Lucía en ese momento.

## Grafana

Se cargaron con `evaluation-dashboard:load` 12 ejecuciones y 647 resultados en la base real `embeddings` (esquema `evaluation`). Contra el Grafana real, las 18 consultas SQL de los paneles respondieron sin error. Las dos ejecuciones de JUP-071 figuran como ejecuciones distintas con su modelo, no comparten serie (0 series comparables) y la vista de cambios las anota con «Cambia: identificador de modelo, proveedor del modelo, cuantizacion, configuracion del gateway». El banco aparece en el detalle de exactitud, relevancia y latencia. Los paneles de evolución dicen «Sin datos», que es lo correcto porque no hay una ejecución anterior comparable. Verificado por la API de Grafana; las capturas de pantalla están pendientes.

Un fallo real encontrado durante la verificación: la carga sobre una base existente fallaba con «column generation_model_id does not exist» porque el esquema usa `CREATE TABLE IF NOT EXISTS`. Se añadió `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` y una prueba contra PostgreSQL real que parte de la tabla anterior (`scripts/tests/test_evaluation_identity_upgrade.py`).

## Pruebas

- Nuevas: `test_evaluation_model_inventory.py`, `test_evaluation_model_identity.py`, `test_evaluation_model_change_docs.py`, `test_evaluation_identity_upgrade.py` y `tools/gateway-config-hash.test.mjs`.
- Actualizadas por el crecimiento del conjunto versionado a 12 ejecuciones y 647 resultados: SQL, filas, manifiesto, carga, atomicidad, conciliación, consultas de paneles y anotaciones.
- Resultado de la batería completa y de la revisión adversarial: ver `review.md` del change.

## No validado

- Latencia, disponibilidad y fallos técnicos en la infraestructura definitiva: las cifras son de la máquina local.
- Batería N3/N5 de 84 ejecuciones con revisión por requisito: no se repitió.
- Segunda revisora y repeticiones adicionales de JUP-071.
- Capturas de pantalla de Grafana.
- Qué modelo respondió realmente: el instrumento no lo atestigua.
