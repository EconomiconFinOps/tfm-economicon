# Metricas tecnicas del asistente — JUP-067

[Tarjeta](https://trello.com/c/bwvfLpUG) · [Catalogo](JUP-067-metrics-catalogue.json) · [Calculador](../../tools/assistant-metrics.py) · [Bateria de preguntas](JUP-069-questions.json) · [Etiquetas de recuperacion](JUP-022-retrieval-labels.json)

Este documento define como se mide el asistente. El catalogo JSON es la fuente unica de cada definicion (identificador, formula, poblacion, fuente y unidad); aqui se explica el por que de cada familia y como se usa. Si una definicion cambia, cambia la version del catalogo y un fichero de resultados que declare una version anterior se rechaza.

## Familias y por que existen

| Familia | Metricas | Pregunta que responde |
| --- | --- | --- |
| Exactitud | ACC-1 a ACC-3 | ¿La respuesta es correcta segun la rubrica de la bateria? |
| Relevancia y confianza de la recuperacion | REL-1 a REL-4 | ¿Lo recuperado es del documento y la seccion que toca, y cuanto se parece a la pregunta? |
| Fundamento | GRD-1 a GRD-3 | ¿Las citas y las cifras de la respuesta se apoyan en lo recuperado? |
| Latencia | LAT-1 a LAT-4 | ¿Cuanto tarda cada etapa y cuantas llamadas fallan? |
| Robustez de la salida | STR-1 y STR-2 | ¿La respuesta estructurada cumple el esquema y por que fallan las que no? |
| Disponibilidad | AVL-1 | ¿Que parte de las peticiones al chat no acaba en error del servidor? |

La confianza de la recuperacion (REL-4) es la similitud del mejor fragmento, 1 menos la distancia coseno que devuelve pgvector. Se publica tal cual, sin recortar, y con el proveedor `mock` no tiene significado semantico. La disponibilidad (AVL-1) es la unica metrica que no sale de un caso de la bateria: se toma de los contadores de peticiones de la ejecucion.

## Reglas que hay que conocer

- Cada caso tiene un resultado `pass`, `fail`, `blocked` o `not_run`. Una tasa se calcula solo sobre los `pass` y `fail` de su poblacion. `blocked` (fallo de infraestructura) y `not_run` no entran en ningun denominador y se cuentan aparte, para que un fallo del entorno ni baje la exactitud ni se oculte.
- Los casos `clarify` y `abstain` se miden aparte de los `answer`, igual que en la calibracion de JUP-022.
- Con 28 casos, un caso son 3,6 puntos. Toda tasa se publica como `k de n` con el intervalo de Wilson al 95 %, y no se debe leer 75 % frente a 70 % como una diferencia.
- Las comprobaciones `numbers` y `forbidden` se deciden por regla; las de `required` las decide una persona. En los casos criticos (los que tienen alguna cifra esperada: 14 de 28) las deciden dos personas de forma independiente, y el informe lista los criticos con un solo decisor.
- Los percentiles usan el rango mas cercano. Hacen falta 20 observaciones para el percentil 95 y 5 para la mediana, el maximo y los cuartiles; por debajo se informa "no disponible". Los fallos no se mezclan con los percentiles: se cuentan en LAT-4.
- La latencia se imprime junto al tamano del corpus (documentos y fragmentos): una prueba pequena no anticipa la carga de uno realista, asi que no se comparan ejecuciones de tamanos distintos como si fueran iguales.

## Objetivos provisionales

Los informes comparan algunos valores con los objetivos de ADR-0002: comprobaciones objetivas al 90 %, ninguna cifra sin rastro en los casos criticos, 95 % de respuestas que cumplen el esquema y percentil 95 de la latencia total de 10 s o menos en desarrollo. Son provisionales: se muestran junto al valor y a su origen, y el informe dice "cumple" o "no cumple", nunca "aprobado" o "rechazado". La relevancia no tiene objetivo.

## Formato de resultados (version 1)

Un fichero JSON con la cabecera de la ejecucion (`commit`, `date`, version y hash de la bateria, hash y tamano del corpus, `provider`, `alias`, parametros de recuperacion y de generacion y las peticiones y errores del servidor del chat) y una entrada por cada caso de la bateria, con su resultado, las comprobaciones, los fragmentos recuperados (identificador, fuente, encabezado y distancia), las citas, el origen de cada cifra, las latencias por etapa, el fallo (categoria y etapa), si cumplio el esquema y las referencias de evidencia. No puede contener el texto de preguntas, respuestas ni fragmentos, ni credenciales: el calculador rechaza por nombre cualquier campo `question`, `prompt`, `response`, `content`, `answer`, `text`, `excerpt` o con aspecto de clave, y no imprime su valor. Las categorias de fallo son las nueve del proveedor de embeddings mas `schema_validation`.

## Calcular un informe

```sh
python tools/assistant-metrics.py --results <resultados.json> --output <informe.json> --report <informe.md> --generated-at 2026-10-05T10:00:00Z
```

El calculador usa solo la biblioteca estandar, no abre red ni base de datos y, con la misma entrada y la misma marca de tiempo, produce los mismos bytes. Antes de calcular valida el formato, el catalogo, que cada caso exista en la bateria y que el hash de la bateria coincida. Las pruebas son `pnpm assistant-metrics:test`.

## Ejemplo trabajado

`tools/fixtures/assistant-metrics/synthetic-results.json` es un fichero **sintetico**, marcado como tal (`"synthetic": true`), pensado para ver el formato y el informe; no es una medicion del asistente. Con el, `python tools/assistant-metrics.py --results tools/fixtures/assistant-metrics/synthetic-results.json --report informe.md` produce, por ejemplo, ACC-1 como `14 de 18` con su intervalo, REL-3 por grupo de comportamiento y un caso critico con una cifra sin rastro. Los resultados reales con el modelo los produce JUP-070 y quedan como foto fechada en la evidencia de esa tarjeta, no como una pagina viva aqui.

## De donde salen los datos hoy

| Dato | Existe hoy | De donde sale |
| --- | --- | --- |
| Recuperacion, distancias y duracion de la consulta | Si | Evento `retrieval` del backend (JUP-022, integrado) y el script de calibracion |
| Duracion de las llamadas de embedding o de chat | Si | Evento `litellm_response` del cliente del processor (JUP-023) |
| Respuesta estructurada y evidencias | Si, en el processor | `FinOpsResponse` y sus guardas |
| Peticiones y errores del chat | Si | Contador `backend_http_requests_total` (JUP-043) |
| Citas del chat | Pendiente | JUP-025 (PR #55) |
| Respuesta del chat generada por un modelo | No | JUP-070 producira el fichero de resultados con un adaptador |

## Limitaciones

- La muestra es pequena: 28 casos (20 `answer`, 6 `clarify`, 2 `abstain`) y las tasas de `abstain` tienen intervalos muy anchos.
- La bateria tiene rubrica, no respuestas de referencia completas, asi que no se calculan ROUGE, BLEU ni similitud de embeddings de la respuesta; un juez basado en un modelo queda como decision de JUP-070.
- No hay trayectoria del agente porque el chat no es agentico, ni una definicion de incidente: STR-2 y LAT-4 ya cuentan los fallos por categoria y etapa.
- Las metricas de negocio son de JUP-068.
