JUP: JUP-067
Trello: https://trello.com/c/bwvfLpUG

## Why

El asistente ya recupera contexto, tiene un contrato de respuesta con evidencia y una bateria de 28 preguntas con rubrica (JUP-069), pero no hay una definicion acordada de que significa "preciso", "relevante", "fundamentado" o "rapido", ni de como se calcula cada cifra. Sin ella, JUP-070 y JUP-071 compararian numeros distintos segun quien los calcule, y los umbrales sueltos de ADR-0002 (Proposed) y de la calibracion de JUP-022 no se pueden contrastar entre si.

## What Changes

- Un catalogo de metricas tecnicas con identificador estable, formula, numerador, denominador, poblacion, fuente del dato y unidad, para seis familias: exactitud, relevancia y confianza del contexto recuperado (similitud coseno del mejor resultado), fundamento (citas y cifras), latencia, robustez de la salida estructurada y disponibilidad del chat. Los resultados incluyen el tamano del corpus para poder comparar latencias entre tamanos.
- Reglas de poblacion: estados `pass`, `fail`, `blocked` y `not_run` de la bateria, que los casos `clarify` y `abstain` se midan aparte y que cada tasa se publique con sus conteos y un intervalo de confianza, porque la muestra es pequena.
- Un formato de resultados por caso, versionado y sin texto de preguntas, respuestas ni secretos, y un informe agregado derivado de el.
- Un calculador de referencia, determinista, sin red y con la biblioteca estandar, que valida el fichero de resultados y calcula las metricas, con pruebas que incluyen controles negativos.
- Objetivos provisionales tomados de ADR-0002 junto a cada valor medido, sin convertirlos en puertas de aceptacion.
- Documento de definiciones para el equipo en `docs/` y ejemplo trabajado con datos que ya existen (la calibracion de recuperacion de JUP-022).

Fuera de alcance: ejecutar el asistente con un modelo real contra la bateria y juzgar las respuestas (JUP-070), la robustez ante datos incompletos (JUP-071), las metricas de negocio (JUP-068), las citas visibles en la interfaz (JUP-025) y cambiar el backend o el processor para emitir nuevos datos.

## Capabilities

### New Capabilities

- `assistant-technical-metrics`: definicion, formato de datos y calculo reproducible de las metricas tecnicas del asistente.

### Modified Capabilities

## Impact

- Nuevo `tools/assistant-metrics.py` con sus pruebas y un fichero de ejemplo; nuevo documento en `docs/` y spec principal al archivar.
- Sin cambios en el backend, el processor ni el frontend. Se apoya en la bateria `docs/validation/JUP-069-questions.json`, en las etiquetas y el informe de JUP-022 (PR #67) y en el contrato `FinOpsResponse` del processor.
- Cableado en la CI como una prueba mas de herramientas.
