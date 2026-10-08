# Evaluación de las respuestas del chat — JUP-070

[Tarjeta](https://trello.com/c/tpSyzXOS) · [Herramienta](../../tools/assistant-eval.py) · [Reglas](JUP-070-evaluation-rules.json) · [Batería de preguntas](JUP-069-questions.json) · [Métricas](JUP-067-metrics.md)

Este documento explica cómo se mide si el chat responde bien y si inventa. Se apoya en la batería de JUP-069 (28 casos con rúbrica) y en el calculador de JUP-067, y completa lo que esas dos tarjetas dejaron a JUP-070: la evaluación de cada respuesta frente a la referencia, el adaptador que produce el fichero de resultados y los umbrales de aceptación.

**Qué no es.** No es un juez basado en un modelo: sería circular (un modelo juzgando a otro), tendría coste y variaría entre ejecuciones. Tampoco certifica un chat con modelo por sí solo: mide el chat que esté en marcha, sea la plantilla de hoy o el que genere JUP-035, y los resultados valen para ese commit, ese corpus y esa configuración.

## Quién decide qué

| Comprobación | Quién la decide | Cómo |
| --- | --- | --- |
| `numbers-N` (cifras esperadas) | La regla | El valor está dentro de la tolerancia, con la unidad y junto a la etiqueta o un alias en la misma frase |
| `forbidden-N` (conductas prohibidas) | La regla | Una de las 37 reglas del fichero de reglas, cada una con sus ejemplos |
| `required-N` (puntos requeridos) | Personas | Una o dos, según el caso; dos distintas en los críticos |
| Resultado del caso | La herramienta | `pass` solo si todo lo anterior pasa y no hay una cifra sin rastro en un caso crítico |
| Veredicto de aceptación | La herramienta | Los umbrales de abajo sobre el informe del calculador |

Los casos **críticos** son los 14 con cifras esperadas. Las reglas son una **cota inferior**: no ven toda violación semántica. Si una persona ve una conducta prohibida que la regla no detectó, falla el punto `required` correspondiente y anota por qué; el informe lo cuenta.

## Cómo ejecutarlo

Todos los ficheros con texto (respuestas, hoja de revisión, juicios) van **fuera del repositorio**; la herramienta se niega a escribirlos dentro. Solo se versiona el fichero de resultados, que no lleva texto, y el informe.

1. Preparar y comprobar la batería (ver [README](README.md)) y guardar los prompts fuera de Git:

   ```sh
   node tools/validation-questions.mjs validate
   node tools/validation-questions.mjs prepare > ../evaluacion/inputs.json
   ```

2. Tener el stack levantado con el corpus cargado por el flujo de ingesta existente, y recoger las respuestas. La contraseña de demostración se lee de una variable de entorno y no se imprime:

   ```sh
   python tools/assistant-eval.py collect --tenant tenant-core --inputs ../evaluacion/inputs.json --output ../evaluacion/crudo.json
   ```

   Cada caso usa una conversación nueva y el prompt exacto. No hay reintentos: un fallo de infraestructura deja el caso `blocked` con su categoría y no cuenta como respuesta incorrecta.

3. Generar la hoja de revisión y repartirla:

   ```sh
   python tools/assistant-eval.py review-sheet --raw ../evaluacion/crudo.json --output ../evaluacion/hoja.md
   ```

4. Cada revisor juzga cada punto `required-N` (`pass` o `fail`). Los juicios se juntan en un JSON fuera de Git:

   ```json
   {"judgments_version": 1, "cases": {"JUP-069-001": {"required-1": [
     {"reviewer": "lucia", "result": "pass", "note": ""},
     {"reviewer": "paris", "result": "pass", "note": ""}]}}}
   ```

5. Escribir la ficha de la ejecución (commit, fecha, corpus, proveedor y alias de embeddings, parámetros de recuperación y de generación) con el formato de `run` de [JUP-067](JUP-067-metrics.md); el cliente del chat no puede conocerlos.

6. Puntuar:

   ```sh
   python tools/assistant-eval.py score --raw ../evaluacion/crudo.json --judgments ../evaluacion/juicios.json --run-info ../evaluacion/ficha.json --output resultados.json --report informe.md --report-json informe.json
   ```

   Sale el veredicto («Aceptado» o «No aceptado») y los motivos. Con `--provisional` se admite un solo revisor en los casos críticos; la medición queda marcada como provisional y esos casos se listan. Sin ese indicador, un caso crítico con un solo revisor, o con el mismo dos veces, queda `not_run`.

7. Para una medición final se hacen **tres ejecuciones** con las mismas entradas y la misma configuración, cada una recogida y puntuada por separado, y se ve la variación:

   ```sh
   python tools/assistant-eval.py compare informe-1.json informe-2.json informe-3.json
   ```

   Se publican todas. No se sustituye una ejecución mala por otra mejor.

## Cómo se decide una cifra

Se leen las cifras de cada frase con ambos convenios decimales (`1.000,50` y `1,000.50`), el signo de porcentaje y las formas de la unidad (`EUR`, `euros`, `€`; `%`, `por ciento`; y los periodos `/día`, `al mes`, `por pedido`). Una cifra cuenta solo si el valor está dentro de la tolerancia absoluta, la unidad coincide y la etiqueta (o uno de sus alias) está en la misma frase. Un número dentro de otro mayor (`190` por `90`), pegado a una palabra o con signo negativo no vale. Una cifra escrita con palabras («seiscientos») no se reconoce y la comprobación falla: se prefiere un falso fallo visible a un falso acierto.

Si un falso fallo molesta, **se corrige la regla** (un alias o una forma nueva en el fichero de reglas) y se repite la puntuación; no se cambia a mano un resultado. Una cifra con unidad que afirma la respuesta se clasifica como proveniente de la pregunta, del contexto, de un fragmento recuperado o sin rastro; las que coinciden con un valor esperado de la batería (los totales o porcentajes que el caso pide calcular) cuentan como derivadas del contexto. Una cifra sin rastro en un caso crítico impide el `pass`.

## Umbrales de aceptación

Salen de los objetivos provisionales de ADR-0002 que ya calcula el calculador, más uno propio de JUP-070:

| Métrica | Umbral | Origen |
| --- | --- | --- |
| ACC-2, comprobaciones objetivas cumplidas | ≥ 90 % | ADR-0002, provisional |
| GRD-2, cifras sin rastro en casos críticos | 0 | ADR-0002, provisional |
| STR-1, respuestas que cumplen el esquema | ≥ 95 % | ADR-0002, provisional |
| LAT-2, latencia total, percentil 95 | ≤ 10 s en desarrollo | ADR-0002, provisional |
| ACC-1, casos `answer` con `pass` | ≥ 80 % | Propuesta de JUP-070, a validar por el equipo |

Un umbral obligatorio que no se puede calcular se informa como no disponible y el veredicto no puede ser «Aceptado». El informe publica cada tasa como `k de n` con el intervalo de Wilson al 95 %: con 28 casos, un caso son 3,6 puntos, y los casos `clarify` (6) y `abstain` (2) se leen solos.

## Límites

- **Una muestra pequeña:** 28 casos. No se compara 80 % con 75 % como una diferencia.
- **Solo se mide el tiempo total** de la petición, porque es lo único que ve el cliente. El formato de resultados exige la latencia de cuatro etapas: la herramienta atribuye la petición completa a la etapa `generation` y deja `embedding` y `retrieval` a cero. Solo el total es una medida; las otras filas del informe no se interpretan.
- **`structured_ok`** significa que la respuesta cumple el contrato de respuesta del chat. No es la salida estructurada `FinOpsResponse` de JUP-024; cuando el chat la devuelva, esa comprobación tendrá que añadirse.
- **Los embeddings `mock`** no tienen significado semántico: las métricas de recuperación (REL) de una ejecución con `mock` no miden relevancia real.
- **Las reglas de las prohibiciones son una cota inferior** y las cifras con palabras fallan por diseño.
- **Un modelo puede variar** entre ejecuciones aunque la temperatura sea cero; por eso las tres repeticiones.
- **La batería y sus respuestas esperadas no se cargan en el índice** ni se envían al chat; los datos numéricos van dentro del prompt.
- No sustituye la validación funcional del chat en la interfaz ni la evaluación de robustez (JUP-071).
