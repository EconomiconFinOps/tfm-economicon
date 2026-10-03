## Context

Hoy hay tres fuentes de numeros sobre el asistente que no se han definido juntas: la calibracion de recuperacion de JUP-022 (acierto por documento y por seccion, resultados vacios), el benchmark de modelos de JUP-078 (puntuacion por terminos, latencia p95 con un percentil propio) y la bateria de JUP-069 (rubrica con `required`, `forbidden` y `numbers`, y un protocolo con `pass`, `fail`, `blocked` y `not_run`). ADR-0002 (Proposed) tiene umbrales con pesos, pero no dice como se calcula cada cifra. El chat actual aun no genera la respuesta con un modelo (pega fragmentos), asi que las metricas de respuesta no tienen todavia un productor; las de recuperacion y de latencia de recuperacion si.

Restricciones heredadas: la bateria y sus etiquetas no se modifican (son de JUP-069 y JUP-022); los resultados no contienen texto de preguntas ni respuestas ni secretos; el repositorio evita dependencias nuevas en las herramientas de `tools/`.

## Goals / Non-Goals

**Goals:**
- Una definicion unica, versionada y comprobable de cada metrica.
- Un calculador de referencia reproducible que cualquiera pueda ejecutar sin red.
- Que JUP-070 y JUP-071 puedan producir un fichero de resultados y obtener cifras comparables.

**Non-Goals:**
- Ejecutar el asistente contra la bateria ni juzgar respuestas (JUP-070), ni robustez ante datos incompletos (JUP-071), ni metricas de negocio (JUP-068).
- Cambiar el backend, el processor o el frontend, ni ratificar los umbrales de ADR-0002.
- Usar un modelo como juez: queda como decision de JUP-070.

## Decisions

### 1. Catalogo en un fichero de datos y un documento corto

El catalogo vive en `docs/validation/JUP-067-metrics-catalogue.json` (version, y por metrica: id, familia, nombre, numerador, denominador, poblacion, fuente, unidad, objetivo provisional con su origen). El calculador lo lee y el informe imprime las definiciones desde el, de modo que no hay dos copias. Un documento `docs/validation/JUP-067-metrics.md` explica el por que de cada familia y enlaza el JSON. Una prueba falla si una metrica calculada no esta en el catalogo o al reves.

### 2. Metricas

| Id | Familia | Que mide | Poblacion |
| --- | --- | --- | --- |
| ACC-1 | Exactitud | casos `pass` entre `pass` mas `fail` | casos `answer` |
| ACC-2 | Exactitud | comprobaciones objetivas cumplidas (`numbers` y `forbidden`) entre las evaluadas | casos `answer` |
| ACC-3 | Exactitud | casos `pass` entre `pass` mas `fail` | casos `clarify`, y aparte `abstain` |
| REL-1 | Relevancia | casos con acierto de documento entre los evaluados | casos `answer` |
| REL-2 | Relevancia | casos con acierto de seccion entre los etiquetados con cobertura directa o parcial | casos `answer` |
| REL-3 | Relevancia | casos con resultado vacio entre los evaluados | por grupo de comportamiento |
| GRD-1 | Fundamento | citas que apuntan a un fragmento recuperado para esa pregunta y tenant entre las citas emitidas | casos con citas |
| GRD-2 | Fundamento | cifras de la respuesta que no se pueden rastrear al contexto, a la evidencia o a la pregunta | recuento por caso y total |
| GRD-3 | Fundamento | metricas y recomendaciones cuyas referencias de evidencia existen entre las emitidas | respuestas estructuradas |
| LAT-1 a LAT-3 | Latencia | mediana, percentil 95 y maximo por etapa (embedding, consulta, generacion, total) | llamadas correctas |
| LAT-4 | Latencia | llamadas fallidas o agotadas entre las totales | todas las llamadas de la etapa |
| STR-1 | Robustez | respuestas que cumplen el esquema entre las recibidas | respuestas estructuradas |
| STR-2 | Robustez | fallos por categoria (las nueve del proveedor y el fallo de esquema) | todos los fallos |

Un caso es critico si su rubrica tiene al menos un `numbers`: es un caso donde el sistema debe acertar una cifra. No se anade ningun campo a la bateria.

### 3. Estados y poblaciones

Se mantienen los cuatro estados del protocolo de JUP-069. `blocked` es un fallo de infraestructura y `not_run` es un caso sin ejecutar: ninguno de los dos entra en un denominador, y ambos se muestran como recuento junto a cada tasa, para que un error del entorno no baje la exactitud ni se oculte. Los casos `clarify` y `abstain` se miden aparte, igual que en la calibracion de JUP-022.

### 4. Tasas con intervalo

Con 28 casos, un caso son 3,6 puntos y un `answer` son 5. Toda tasa se publica como `k de n` y con el intervalo de Wilson al 95 %, calculado con la biblioteca estandar. Asi nadie compara 75 % con 70 % como si fueran distintos.

### 5. Comprobaciones objetivas y juzgadas

`numbers` y `forbidden` se deciden por regla (valor dentro de la tolerancia absoluta, con unidad y etiqueta; ausencia de la conducta prohibida). `required` lo decide una persona, y cada comprobacion juzgada guarda `decided_by` con `person` o `rule`. No se admite un modelo como juez en esta tarjeta.

### 6. Percentiles

Percentil por rango mas cercano (`ceil(p * n)`-esimo valor ordenado), igual que el benchmark de JUP-078 en la practica pero definido. Minimo de observaciones: 20 para el percentil 95 y 5 para la mediana y el maximo; por debajo se informa "no disponible". Los fallos no se mezclan con los percentiles: se cuentan en LAT-4 y las latencias se etiquetan como "solo llamadas correctas".

### 7. Formato de resultados

Un JSON versionado (`results_version: 1`) con la cabecera de la ejecucion (commit, version y hash de la bateria, hashes del corpus, proveedor, alias, parametros de generacion y de recuperacion, fecha) y una lista de casos con: `case`, `outcome`, `checks` (id, clase `objective` o `judged`, resultado, `decided_by`), `retrieved` (identificadores de fragmento, documento y seccion, y distancias), `citations`, `figures` (cifras de la respuesta con su origen o `untraceable`), `latency_ms` por etapa, `failure_category`, `structured_ok` y `evidence_refs`. No admite campos `question`, `prompt`, `response`, `content` ni nada con aspecto de clave; los rechaza por nombre y no se imprime su valor.

### 8. Calculador de referencia

`tools/assistant-metrics.py`, biblioteca estandar, sin red ni base de datos, con `--results`, `--output`, `--report` y `--generated-at`. Comprueba antes de calcular: formato, catalogo, que los casos existan en la bateria y que el hash de la bateria coincida. El informe lista los valores con `k de n`, intervalo, el objetivo provisional y si se cumple. La marca de tiempo es un argumento, por lo que dos ejecuciones iguales dan el mismo fichero.

### 9. Objetivos provisionales

Se citan los de ADR-0002 (Proposed): exactitud objetiva 90 %, sin cifras inventadas en casos criticos, 95 % de respuestas parseables y percentil 95 de latencia total de 10 s o menos en desarrollo. Para la relevancia no hay objetivo: se muestra el valor de la calibracion de JUP-022 como referencia, no como objetivo. El informe dice "provisional" y nunca "aprobado" o "rechazado".

### 10. Origen de los datos hoy

| Dato | Existe hoy | De donde sale |
| --- | --- | --- |
| Recuperacion, distancias, duracion de consulta | con PR #67 | evento `retrieval` y script de calibracion |
| Duracion de la llamada de embedding o de chat | si | evento `litellm_response` del cliente del processor (JUP-023) |
| Respuesta estructurada y evidencias | si, en el processor | `FinOpsResponse` y sus guardas |
| Citas del chat | con PR #55 | JUP-025 |
| Respuesta del chat generada por un modelo | no | pendiente; el adaptador de JUP-070 producira el fichero de resultados |

## Risks / Trade-offs

- [La muestra es pequena y las cifras se interpretan como exactas] → intervalo y `k de n` obligatorios en cada tasa.
- [Se optimiza hacia el objetivo y no hacia la calidad] → los objetivos son provisionales, se muestran como comparacion y no como puerta.
- [El formato de resultados nace antes de la primera ejecucion real y puede quedarse corto] → va versionado y JUP-070 puede subirlo de version; hay ejemplo y controles negativos.
- [Dos definiciones de "caso critico"] → una unica regla documentada (cifra esperada) y sin campo nuevo en la bateria.
- [Dependencia de PR sin integrar] → el calculador no importa codigo de ellos; solo lee ficheros. El ejemplo con datos reales espera a #67.

## Migration Plan

Aditivo: no cambia ningun servicio. Se integra el catalogo, el calculador y las pruebas; JUP-070 consume el formato. Si un consumidor necesita otra cosa se sube `results_version` y el catalogo.

## Open Questions

- Si el equipo adopta los objetivos de ADR-0002 como provisionales para estas metricas aunque el ADR siga Proposed.
- Quien decide los puntos `required` en JUP-070 (una persona o dos) y si hace falta un segundo revisor en los casos criticos.
- Si el informe debe publicarse tambien como pagina de `docs/` o basta el JSON y el Markdown generados por ejecucion.

## ADR

No aplica: son definiciones y una herramienta, no una decision de arquitectura duradera. Se enlaza ADR-0002 como fuente de objetivos provisionales sin sustituirlo ni ratificarlo.
