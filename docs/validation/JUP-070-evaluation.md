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

5. Si se quieren las métricas de recuperación (REL-1 y REL-2), el cliente del chat no ve la fuente ni la sección de cada fragmento. Se guarda un mapa fuera de Git con el identificador de cada documento y su ruta en el corpus y se pasa a `score` con `--document-map`; la herramienta etiqueta cada fragmento con la fuente de la batería y la sección del documento con el mismo troceado y las mismas secciones que la calibración de JUP-022. Con la base vectorial en marcha, el mapa sale de la tabla `knowledge_documents` (`id` y `artifact_uri`).

6. Escribir la ficha de la ejecución (commit, fecha, corpus, proveedor y alias de embeddings, parámetros de recuperación y de generación) con el formato de `run` de [JUP-067](JUP-067-metrics.md); el cliente del chat no puede conocerlos.

7. Puntuar:

   ```sh
   python tools/assistant-eval.py score --raw ../evaluacion/crudo.json --judgments ../evaluacion/juicios.json --run-info ../evaluacion/ficha.json --document-map ../evaluacion/mapa.json --output resultados.json --report informe.md --report-json informe.json
   ```

   Sale el veredicto («Aceptado» o «No aceptado») y los motivos. Con `--provisional` se admite un solo revisor en los casos críticos; la medición queda marcada como provisional y esos casos se listan. Sin ese indicador, un caso crítico con un solo revisor, o con el mismo dos veces, queda `not_run`.

8. Para una medición final se hacen **tres ejecuciones** con las mismas entradas y la misma configuración, cada una recogida y puntuada por separado, y se ve la variación:

   ```sh
   python tools/assistant-eval.py compare informe-1.json informe-2.json informe-3.json
   ```

   Se publican todas. No se sustituye una ejecución mala por otra mejor.

## Medir con embeddings reales a través del gateway local

La ejecución con `mock` no mide relevancia. Para REL-1 y REL-2 con embeddings reales se levanta el gateway de `infra/litellm` solo en local y se le pide una clave virtual por servicio, restringida a los alias de embeddings y con presupuesto:

1. Las claves del proveedor y las claves virtuales van en ficheros fuera de Git; no se imprimen ni se pegan en el chat.
2. El stack de la medición recibe la clave virtual y la URL del gateway (`host.docker.internal` desde un contenedor, puerto de loopback) por variables de entorno del shell, que tienen prioridad sobre el `.env`.
3. Se carga el corpus con el flujo de ingesta y se comprueba que el proveedor registrado es `litellm` antes de recoger.
4. La ficha de la ejecución lleva el proveedor y el alias reales. Se consulta el gasto de la clave en el gateway al terminar.
5. Hay que parar el stack con `docker compose -p <proyecto> down -v` y el gateway al terminar.

Solo se pagan llamadas de embeddings (céntimos de dólar con 28 preguntas y 52 fragmentos). Mientras el chat no genere con modelo, la evaluación no llama a ningún modelo de lenguaje.

## Cómo se decide una cifra

Se leen las cifras de cada frase con ambos convenios decimales (`1.000,50` y `1,000.50`), el signo de porcentaje y las formas de la unidad (`EUR`, `euros`, `€`; `%`, `por ciento`; y los periodos `/día`, `al mes`, `por pedido`). Una cifra cuenta solo si el valor está dentro de la tolerancia absoluta, la unidad coincide y la etiqueta (o uno de sus alias) está en la misma frase. Un número dentro de otro mayor (`190` por `90`), pegado a una palabra o con signo negativo no vale. Una cifra escrita con palabras («seiscientos») no se reconoce y la comprobación falla: se prefiere un falso fallo visible a un falso acierto.

Si un falso fallo molesta, **se corrige la regla** (un alias o una forma nueva en el fichero de reglas) y se repite la puntuación; no se cambia a mano un resultado. La etiqueta tiene que estar junto a la cifra (antes, o después si lo de antes nombra otra cifra del caso): la cifra correcta bajo la etiqueta de otra no cuenta. Una cifra con unidad, con signo o de tres o más dígitos sin unidad (salvo años e identificadores como JUP-107) que afirma la respuesta se clasifica como proveniente de la pregunta, del contexto, de un fragmento recuperado o sin rastro; las que coinciden con un valor esperado de la batería (los totales o porcentajes que el caso pide calcular) cuentan como derivadas del contexto. Una cifra sin rastro en un caso crítico impide el `pass`.

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
- **Cuando el chat genere con modelo** (JUP-035), la ficha lleva el alias y la temperatura reales de la generación, y la latencia de `generation` pasa a tener sentido junto a la del total; hasta entonces las filas de etapa no se interpretan.
- **Los embeddings `mock`** no tienen significado semántico: las métricas de recuperación (REL) de una ejecución con `mock` no miden relevancia real.
- **Formas que el lector de cifras no reconoce:** el espacio como separador de miles y las cifras con palabras. Una cifra previa en «pasó de 80 % a 90 %» puede cumplir un 90 % esperado. Los puntos juzgados por personas cubren esos huecos y están registrados en `openspec/findings/backlog.md` (RF-070-001 a RF-070-004).
- **Un revisor se identifica por su nombre sin tildes ni mayúsculas:** «Ana» y «ana» son la misma persona. Más de dos revisores en un punto es un error.
- **Las reglas de las prohibiciones son una cota inferior** y las cifras con palabras fallan por diseño.
- **Un modelo puede variar** entre ejecuciones aunque la temperatura sea cero; por eso las tres repeticiones.
- **La batería y sus respuestas esperadas no se cargan en el índice** ni se envían al chat; los datos numéricos van dentro del prompt.
- No sustituye la validación funcional del chat en la interfaz ni la evaluación de robustez (JUP-071).
