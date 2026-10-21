# Plan de reejecución de las medidas que dependen del modelo (JUP-133)

Tarjeta: [JUP-133](https://trello.com/c/Yv1ETc2G). Cambio de modelo: [JUP-132](https://trello.com/c/ERLZlPsT). Qué medidas dependen del modelo: [inventario](model-dependence-inventory.md). Qué se informa al terminar: [plantilla del informe](model-reevaluation-report-template.md).

## Presupuesto y autorización

| Concepto | Valor |
| --- | --- |
| Presupuesto máximo total | **1,5 USD** en OpenRouter, por todas las campañas de este plan |
| Quién lo fijó | Lucia Mateo, 21/10/2026 |
| Clave | La única clave de OpenRouter de Lucia; no se guarda ni se escribe en el repositorio |
| Proveedor y modelo | Los que deje JUP-132 en `economicon-chat`. No se fija otro proveedor para medir |
| Estado de la autorización | **El tope está fijado; el lanzamiento está sin autorizar** hasta la confirmación de abajo |

El tope no equivale a una orden de gastar. Antes de lanzar cada campaña con gasto hace falta una confirmación expresa de Lucia en ese momento, con estos tres datos delante:

1. La entrada del gateway que se va a usar: la salida de `corepack pnpm gateway-config-hash` (alias, modelo, proveedor, cuantización y huella).
2. La estimación de coste de esa campaña, calculada con una muestra pequeña medida y no supuesta.
3. El gasto acumulado hasta ese momento frente al tope.

**Parar:** la ejecución para en cuanto el gasto acumulado alcanza el tope, o antes si la estimación de la campaña siguiente no cabe en lo que queda. Lo que no llega a ejecutarse se registra como «No medido» y nunca como fallo ni acierto. No se repiten fallos para llegar a un resultado favorable.

## Antes de gastar

- JUP-132 integrado, o un gateway aislado con `economicon-chat` apuntando a DeepSeek V4.1 Flash.
- La identidad del modelo anotada en la entrada del manifiesto (`model_identity`) con los valores de `gateway-config-hash`. Son valores declarados por la configuración: el instrumento no atestigua qué modelo respondió.
- Nombre de la ejecución, commit del producto y configuración del gateway apuntados en el registro de gasto de abajo.
- La versión de los recursos del chat (prompts y tokenizer) que usa la ejecución nueva. JUP-132 cambia modelo y recursos a la vez, así que el informe no puede atribuir al modelo una diferencia que también puede ser del prompt.
- Una pila de Grafana real disponible para verificar la carga (tarea 4.4b).

## Medidas dependientes y decisión de reejecución

| Medida (id del inventario) | Campaña | Llamadas al modelo | Coste estimado | Decisión | Autorización |
| --- | --- | --- | --- | --- | --- |
| `live-robustness-jup071` | Campaña ligera: 29 conversaciones, una repetición, una revisora, informe provisional | 29 de generación más los reintentos que pida el validador de salida | Referencia: 0,176 USD con GLM-5.2 (27 operaciones con uso). La del modelo nuevo se mide con una muestra antes de lanzar | Se reejecuta | Sin autorizar hasta la confirmación |
| `ai-cost-jup130` | Comando `ai-cost` sobre el registro del gateway durante la campaña anterior | Ninguna: lee el registro y contrasta con OpenRouter | Sin gasto de modelo: lee el registro del gateway y consulta a OpenRouter los datos de facturación de cada generación | Se recalcula | No necesita |
| `live-signals-prometheus` | Lectura de contadores con tráfico real tras el cambio | Ninguna | Sin gasto | No se reejecuta; se lee con tráfico y se rotula el instante del cambio. Sin tráfico, «No medido» | No necesita |
| `chat-battery-n3-n5` | Batería de 28 casos con tres repeticiones (84 ejecuciones) | 84 de generación | Sin estimar; con la referencia de 0,176 USD cada 27 operaciones sería de varias veces esa cifra | **Sin decidir.** No cabe en el tope junto con la campaña ligera si su coste por ejecución es el de la referencia. Si no se reejecuta, consta aquí el motivo y la cifra de la memoria queda «obsoleta sin sustituto» | Sin autorizar |

Las medidas `independiente` e `historica` no se reejecutan; su motivo está en el inventario.

## Orden

1. Medir una muestra pequeña (tres conversaciones) y calcular la estimación de la campaña ligera.
2. Confirmación de Lucia con los tres datos de arriba.
3. Campaña ligera de JUP-071; registro del gasto tras cada bloque.
4. `ai-cost` sobre el registro del gateway del mismo periodo.
5. Añadir las ejecuciones al manifiesto versionado, cargar con `evaluation-dashboard:load` y verificar en Grafana (series separadas, modelo visible, paneles sin error).
6. Rellenar el informe antes/después y la lista de cifras de la memoria.

## Registro de gasto

Se rellena durante la ejecución. Cada fila lleva una campaña, la fecha, el gasto informado por el gateway, el contrastado con OpenRouter y el acumulado.

| Campaña | Fecha (UTC) | Gasto del gateway | Gasto de OpenRouter | Acumulado | Tope |
| --- | --- | --- | --- | --- | --- |
| Muestra de coste: 3 conversaciones (`JUP-069-002`, `JUP-071-001`, `JUP-071-002`), 4 llamadas al modelo de chat | 21/10/2026 | 0,003833 USD (incluye 17 peticiones del gateway, 5 de embeddings de una recogida anterior sin respuesta) | Sin contrastar | 0,003833 USD | 1,5 USD |

## Qué queda fuera

Repetir la comparativa de modelos, elegir otro modelo, cambiar baterías o instrumentos, y el despliegue en DockerServer.
