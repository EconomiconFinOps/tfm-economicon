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
| `bank28-live-jup133` | Banco de 28 preguntas de JUP-069 con el chat real, una repetición | 28 de generación más un reintento | Medido: ≈ 0,033 USD estimados | Se reejecutó una vez (22/10/2026, provisional). Repetir con la infraestructura definitiva antes de usar su latencia | Hecho; sin nueva autorización |
| `chat-battery-n3-n5` | Batería de 28 casos con tres repeticiones (84 ejecuciones) | 84 de generación | Sin estimar; con la referencia de 0,176 USD cada 27 operaciones sería de varias veces esa cifra | **Parcial.** Las 84 ejecuciones no se repiten (hace falta el ejecutor de la campaña B y la revisión por requisito; con el coste medido serían del orden de 0,1 USD). Sí se repitió una vez el banco de 28 preguntas con el chat real (~0,033 USD). La cifra de la memoria queda «obsoleta sin sustituto» | Sin autorizar |

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
| Campaña ligera de JUP-071: 29 conversaciones con el chat real, una repetición, y los reintentos del producto | 21/10/2026 | Dentro de la ventana de 75 consultas (0,049456 USD estimados, de los que 0,006278 USD son de GLM-5.2 anteriores) | 0,049765 USD facturados en la ventana (cobertura 100 %); atribuible a JUP-133: 0,0435 USD | 0,0435 USD | 1,5 USD |
| Banco de 28 preguntas de JUP-069: 28 conversaciones con el chat real, una repetición, un reintento del producto (`JUP-069-010`) | 22/10/2026 | 0,033045 USD estimados | Sin contrastar | ≈ 0,077 USD | 1,5 USD |

## Sensibilidad a la infraestructura local

Las mediciones de esta reejecución se hacen en el ordenador local de Lucia con Docker Desktop (7,7 GB de memoria para los contenedores), no en la infraestructura definitiva. Algunas métricas dependen más de esa máquina que del modelo y conviene repetirlas donde vaya a funcionar el producto. La lista se completa con lo que aparezca durante la campaña.

| Métrica (catálogo de JUP-067) | Por qué es sensible | Qué hacer |
| --- | --- | --- |
| LAT-1, LAT-2, LAT-3: latencia mediana, p95 y máxima de la campaña | Es de extremo a extremo e incluye backend, processor, cola, base de datos, validador y arranque en frío, además de la llamada al modelo | Repetir en la infraestructura definitiva. No atribuir al modelo la latencia de esta máquina |
| LAT-4 y AVL-1: llamadas fallidas o agotadas y disponibilidad del chat | Los timeouts y los 503 de la recogida dependen de la capacidad del equipo | Repetir allí; separar lo técnico de lo semántico |
| STR-2: fallos por categoría | Las categorías `timeout` y `service` salen de la capacidad local | Repetir allí |
| Muestras `blocked` de la campaña de robustez por fallo técnico | Se bloquean por cortes de infraestructura, no por el comportamiento del asistente | Repetir las bloqueadas allí |
| Señales en vivo de Prometheus (latencia p95 y tasa de error del chat) | Se leen sobre el despliegue en el que corre el tráfico | Leerlas en la infraestructura definitiva |

No dependen de la máquina (salvo errores de ejecución): el contenido de las respuestas, los puntos de rúbrica, el coste por token y por consulta, el detector de anomalías y la reconciliación de datos.

Hechos observados en esta máquina (21/10/2026), para tenerlos presentes al leer las cifras:

- La recuperación del backend dio tres timeouts de 20 s en la llamada de embeddings (`retrieval_failed`, categoría `timeout`), mientras que la misma llamada directa al gateway respondía en 0,6–1,1 s.
- La primera conversación tardó 73,6 s en total; la llamada remota al modelo, 15,8 s. Las dos siguientes, 25,5 s y 15,6 s.
- Tras parar el stack con un cierre forzado, PostgreSQL tardó unos 2 minutos en recuperarse.
- El build del backend falló una vez por descargar el tokenizer histórico (20 MB) con otros builds en paralelo y se resolvió reconstruyéndolo solo.
- La lectura del registro de gasto del gateway tardó unos 16 s con 927 filas: las herramientas de medición se ralentizan con el volumen.

## Qué queda fuera

Repetir la comparativa de modelos, elegir otro modelo, cambiar baterías o instrumentos, y el despliegue en DockerServer.
