JUP: JUP-022
Trello: https://trello.com/c/DPZpQ09b

## Why

Hasta ahora el asistente funciona con un prototipo: la consulta del chat se apoya en un embedding simulado (mock) y devuelve siempre los 4 fragmentos mas cercanos, sean relevantes o no. Sirve para probar el recorrido, pero no busca de verdad lo que el usuario pregunta.

Esta HU sustituye ese prototipo por una recuperacion semantica real: dada una pregunta, el sistema debe encontrar los fragmentos del corpus que realmente la responden, saber decir cuando no hay nada relevante, y hacerlo de forma medible y trazable. Es el eslabon que une la pregunta con los documentos, y sin el no hay respuesta con fuentes que se pueda evaluar.

Corre prisa porque la ingesta (JUP-023) pasara a guardar vectores reales de 1536 dimensiones: si la consulta siguiera con el embedding simulado, compararia vectores reales con ruido y quedaria peor que hoy.

## What Changes

- El backend calcula el embedding de la pregunta con el mismo modelo y la misma dimension que usa la ingesta (alias `economicon-embedding`, 1536 dimensiones), llamando al gateway con una clave virtual propia del backend, distinta de la del processor y restringida a ese alias.
- Contrato de recuperacion explicito y configurable: `top_k`, umbral de distancia, orden determinista (desempate estable) y resultado vacio cuando ningun fragmento supera el umbral.
- Comprobacion de compatibilidad en consulta: si el modelo o la dimension del embedding de la pregunta no coinciden con los vectores almacenados, la consulta falla con un error claro y no devuelve resultados sin sentido.
- Fallos del proveedor de embeddings y del almacen vectorial tratados como errores saneados, sin filtrar texto ni credenciales y sin devolver un 500 generico.
- Trazabilidad de cada recuperacion: identificador del fragmento, documento, distancia y parametros usados, sin guardar el texto de la pregunta en los registros.
- Medicion de la recuperacion con las 28 preguntas de JUP-069: acierto a nivel de documento con las fuentes ya declaradas en el banco, y un fichero de etiquetas aparte, a nivel de seccion, sin modificar el banco. Los valores por defecto de `top_k` y del umbral salen de esa medicion con embeddings reales, no se fijan a ojo.
- Se mantienen los mocks como modo de arranque habitual y para los tests, con un proveedor determinista que conserva algo de significado para poder probar el contrato sin red ni coste.

## Capabilities

### New Capabilities

- `semantic-retrieval`: contrato de recuperacion en consulta: embedding de la pregunta, parametros, orden, resultado vacio, compatibilidad de modelo y dimension, errores saneados y trazabilidad.
- `retrieval-calibration`: medicion reproducible de la recuperacion con el banco de preguntas y etiquetas de seccion, con informe versionado del que salen los valores por defecto.

### Modified Capabilities

Ninguna. El contrato de ingesta (`document-ingestion-handoff`), el corpus (`assistant-document-corpus`) y las guardas de respuesta (`finops-response-guardrails`) no cambian de requisitos.

## Impact

- Backend: el servicio de consulta vectorial, la ruta del asistente, la configuracion (proveedor, alias, URL del gateway, clave virtual como `SecretStr`, tiempos y reintentos acotados) y el proveedor de embeddings de la consulta. Sin dependencias nuevas: el cliente usa solo la biblioteca estandar, como el del processor.
- Compose, `.env.example`, README y los tests de topologia: variables nuevas del backend, sin valores por defecto para la clave.
- Una prueba de paridad entre backend y processor sobre alias y dimension, para que no diverjan.
- Datos: una base existente con `vector(8)` no es compatible con el modelo real; la migracion a `vector(1536)` exige una coleccion nueva y reindexar, y queda fuera de este change salvo el error claro de incompatibilidad.
- Documentacion: informe de calibracion y etiquetas de seccion en `docs/validation/` y `docs/spikes/`.
- Fuera de alcance: el gateway y el cliente del processor (JUP-023), el despliegue de pgvector (JUP-021), las citas por respuesta (JUP-025), la respuesta con un LLM (JUP-024 y JUP-036) y los presupuestos de gasto del gateway.
- Dependencias: JUP-023 define el modelo, el alias y la dimension; JUP-021 vigila la dimension almacenada al arrancar; JUP-025 reescribe las mismas funciones de consulta, por lo que este change se aplica despues de que esa tarjeta se integre o se coordina con ella. ADR-0002 sigue en estado propuesto y este change se apoya en sus decisiones sin darlas por cerradas.
