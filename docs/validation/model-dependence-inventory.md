# Inventario de medidas por dependencia del modelo (JUP-133)

Tarjeta: [JUP-133](https://trello.com/c/Yv1ETc2G). El cambio de modelo por defecto del chat lo hace [JUP-132](https://trello.com/c/ERLZlPsT) (DeepSeek V4.1 Flash detrás del alias `economicon-chat`). Este inventario dice qué medidas hay que repetir. La fuente de verdad es [model-dependence-inventory.json](model-dependence-inventory.json); lo valida `scripts/tests/test_evaluation_model_inventory.py`, que además falla si el manifiesto del dashboard lista una fuente que el inventario no clasifica.

## Las tres clases

| Clase | Qué significa | Qué se hace |
| --- | --- | --- |
| `dependiente` | Su valor cambia si cambia el modelo de generación | Se repite, o consta por escrito por qué no |
| `independiente` | No pasa por el modelo de generación, y hay una comprobación hecha que lo acredita | Se mantiene |
| `historica` | Antecedente fechado o comparativa que no describe el defecto nuevo | Se conserva con su modelo y no se repite |

Una medida solo es `independiente` si la comprobación está hecha y es localizable (código o informe). «Parece que no usa el modelo» no basta.

## Clasificación

| Medida | Clase | Por qué | Reejecución |
| --- | --- | --- | --- |
| Robustez con el chat real (JUP-071) | dependiente | Puntúa respuestas generadas | Campaña ligera, tope 1,5 USD |
| Batería del chat N3/N5 (JUP-035/123) | dependiente | Revisa por requisito respuestas generadas | Parcial: se repitió una vez el banco de 28 preguntas; las 84 ejecuciones no |
| Coste de IA (JUP-130) | dependiente | Tokens por tarifa del modelo servido | Se recalcula sobre la campaña ligera, sin gasto extra |
| Señales en vivo (Prometheus) | dependiente | La latencia y los errores incluyen la generación | Se leen con tráfico tras el cambio |
| Detector de anomalías (JUP-130) | independiente | Reglas deterministas sobre las series de coste | No |
| Reconciliación y frescura de datos (JUP-130) | independiente | Compara con el API de facturación | No |
| Métricas de negocio (JUP-068) | independiente | Registros de tiempo y gasto, ejemplo sintético | No |
| Calibración de la recuperación (JUP-022) | independiente | Solo embeddings, que JUP-132 no cambia | No, salvo que JUP-132 toque el alias de embeddings |
| Catálogo de métricas (JUP-067) | independiente | Definiciones, sin valores | No |
| Línea base de plantilla (JUP-070, 08/10/2026) | histórica | Plantilla sin modelo de generación | No |
| Banco de 28 preguntas con el chat real (JUP-069/070, 22/10/2026) | dependiente | Puntúa respuestas generadas por el modelo servido | Hecho una vez en JUP-133 |
| Benchmark de modelos (JUP-078) | histórica | Compara candidatos, no el defecto nuevo | No |
| Comparativa GLM/DeepSeek (JUP-063) | histórica | Antecedente de la elección | No |

## Lo que este inventario no resuelve

La fuente **JUP-133** añadida el 25/10 corresponde a las proyecciones de evolución
del viernes y domingo, clasificadas como **dependientes** del modelo/proveedor y
del entorno. [Método y límites](../evidence/JUP-133/evolution-20261025/README.md).
Reutiliza mediciones existentes; no autoriza una repetición ni convierte protocolos
distintos en una comparación causal o una aceptación de RC.

- **El modelo de la medición «antes» no está atestiguado.** La ejecución viva de JUP-071 del 2026-10-20 se publica como `live_unverified`: el instrumento no verifica qué modelo respondió, por eso guarda `generation_model` nulo y el dashboard la marca «no real: sin modelo verificado». Según la configuración de ejemplo del gateway y la tarjeta de JUP-132, el alias apuntaba a GLM-5.2, pero eso es una declaración, no una atestación. La ejecución nueva tendrá el mismo límite si no cambia el contrato de JUP-035. El informe antes/después lo debe decir, y los campos de identidad del modelo de este cambio se registran como declarados.
- **Campos de proveedor en el informe vivo.** El informe de JUP-071 guarda el proveedor y el alias del chat (`litellm-openrouter`, `economicon-chat`) en las columnas `embedding_provider` y `embedding_alias` de la ejecución normalizada. Es una correspondencia del adaptador existente; este cambio no la modifica porque cambiar instrumentos está fuera de alcance, pero hay que tenerlo en cuenta al leer esas columnas.
- **N3/N5 se repitió solo en parte.** Las 84 ejecuciones y la revisión por requisito no se repiten (necesitan el ejecutor de la campaña B y unas 78 revisiones). Sí se midió una vez el banco de 28 preguntas con la herramienta de JUP-070; esa referencia no sustituye la conformidad por requisito, que queda obsoleta.
