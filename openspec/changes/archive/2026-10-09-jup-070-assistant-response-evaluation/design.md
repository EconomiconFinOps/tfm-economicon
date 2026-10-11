JUP: JUP-070
Trello: https://trello.com/c/tpSyzXOS

## Context

Ver `proposal.md` (por qué y qué cambia) y `specs/assistant-response-evaluation/spec.md` (requisitos).

Estado de partida, comprobado en `develop` (`2f9a5f5`):

- La batería `docs/validation/JUP-069-questions.json` tiene 28 casos: 20 `answer`, 6 `clarify` y 2 `abstain`; 14 llevan cifras esperadas (los «críticos») y hay 37 conductas prohibidas. Cada caso tiene `question`, `context`, `sources` y `expected` con `required`, `forbidden` y `numbers` (etiqueta, valor, unidad y tolerancia absoluta). `node tools/validation-questions.mjs prepare` emite solo el identificador y el prompt de cada caso.
- `tools/assistant-metrics.py` (JUP-067) valida un fichero de resultados versión 1 contra la batería y el catálogo y calcula las métricas. Exige un `check` por cada punto de la rúbrica con ids `numbers-N`, `forbidden-N` y `required-N`; las `numbers` y las `forbidden` son objetivas y solo las decide la regla (`decided_by: ["rule"]`); las `required` son juzgadas por una o dos personas. El formato no puede llevar textos ni credenciales. Lista aparte los casos críticos con un solo decisor.
- El chat expone `POST /conversations` y `POST /conversations/{id}/messages`, que devuelve el mensaje del asistente (texto y metadatos con citas) y `retrieved_context` con cada fragmento y su distancia. Hoy `AssistantService.answer` devuelve una plantilla y no llama a ningún modelo.
- JUP-069 y JUP-067 dejan a JUP-070 la metodología, los umbrales de aceptación y el adaptador que produce el fichero de resultados. Los objetivos de ADR-0002 son provisionales.

## Goals / Non-Goals

**Goals:**

- Un procedimiento repetible que recoja las respuestas del chat, decida por regla lo objetivo, deje a las personas lo que requiere juicio y produzca resultados que el calculador ya acepta.
- Que el procedimiento sirva igual para el chat de hoy (plantilla) y para el de JUP-035, sin cambiar la herramienta.
- Que un fallo de la regla se corrija en la regla, y no con una decisión manual escondida.

**Non-Goals:**

- Evaluar con un modelo como juez, medir latencia por etapa, tocar el chat o el calculador, ni cambiar la batería.

## Decisions

### 1. Una herramienta con tres pasos, solo biblioteca estándar

`tools/assistant-eval.py` con `collect`, `review-sheet` y `score` (más `compare` para ver la variación entre repeticiones). Sigue el estilo de `assistant-metrics.py`: sin dependencias, deterministas, sin escribir en el repositorio nada que lleve texto. La prueba está en `scripts/tests/test_assistant_eval.py`, como la del calculador.

### 2. Los textos se guardan fuera de Git

El fichero de la ejecución cruda (respuestas, citas, fragmentos), la hoja de revisión y los juicios llevan texto de respuestas y nombres de revisores, así que viven fuera del repositorio. La herramienta rechaza escribir esos ficheros dentro del árbol del repositorio. En Git solo entran el fichero de resultados (sin texto), el informe y la evidencia.

### 3. Recogida por la API real del chat, sin reintentos

`collect` inicia sesión con la cuenta de demostración (la contraseña se lee de una variable de entorno y no se imprime), crea una conversación por caso, envía el prompt preparado tal cual y guarda respuesta, citas, fragmentos con distancias, estado HTTP y duración total medida alrededor de la petición. Un 5xx, un tiempo agotado o un fallo de conexión se guarda con su categoría y el caso queda `blocked`. No reintenta: un reintento ocultaría el fallo y falsearía la disponibilidad. Las cabeceras del tenant y el destino (`--base-url`, por defecto el local) son parámetros; la herramienta no abre otras conexiones.

La cabecera de la ejecución (commit, hash y tamaño del corpus, proveedor y alias de embeddings, ajustes de generación) la aporta quien ejecuta con una pequeña ficha, porque el cliente del chat no puede conocerlos; el commit se lee de Git si no se da. Como el cliente solo ve el tiempo total de la petición, la latencia por etapa que exige el formato se informa así: `total` es el medido y la petición completa se atribuye a la etapa `generation`, con `embedding` y `retrieval` a cero; solo el total es una medida, y los informes lo indican para que no se lean las demás etapas.

### 4. Cifras decididas por una regla conservadora

Se extraen las cifras de la respuesta (separadores de miles y decimales en ambos convenios, signo de porcentaje y formas de palabra de la unidad) y se exige que coincida el valor dentro de la tolerancia, la unidad y la etiqueta (o un alias del fichero de reglas) en la misma frase. Un número dentro de otro mayor no vale. La etiqueta debe estar junto a la cifra: antes de ella, o después si lo que hay antes nombra otra cifra del caso; así «Virtual Machines cuesta 50 EUR y el total es 600 EUR» no cumple los 600 EUR de Virtual Machines. Se aceptan la moneda como palabra antes de la cifra («EUR 1.000») y el énfasis de markdown. Una cifra escrita con palabras («seiscientos») no se reconoce y la comprobación falla: se prefiere un falso fallo visible a un falso acierto. Los falsos fallos se corrigen añadiendo un alias o una forma al fichero de reglas y repitiendo la puntuación; el informe lista las comprobaciones de cifras fallidas para poder auditarlas.

### 5. Conductas prohibidas con regla explícita para las 37

El calculador exige que `forbidden` sea objetivo, así que las 37 llevan regla en `docs/validation/JUP-070-evaluation-rules.json`, de tres tipos: un patrón sobre el texto normalizado (minúsculas, sin tildes, espacios colapsados), una cifra prohibida (el valor que delata el error, por ejemplo el total que sale de sumar actual y amortizado), o «importe que no está en el prompt». La herramienta se niega a puntuar si falta alguna. Las reglas son una cota inferior: no ven toda violación semántica. Por eso la hoja de revisión también muestra las prohibiciones, y si una persona ve una violación que la regla no detectó, la anota fallando el punto `required` correspondiente, con nota, y el informe la cuenta como «violación no detectada por la regla».

### 6. Juicio humano con hoja y fichero de juicios, doble revisión en los críticos

`review-sheet` genera un Markdown fuera de Git con, por caso, el comportamiento esperado, los puntos `required`, las prohibiciones, la respuesta original, las citas y los fragmentos. Los juicios se devuelven en un JSON (`pass` o `fail` por punto, revisor y nota). Por defecto, un caso crítico exige dos revisores distintos; con `--provisional` se admite uno y la medición queda marcada como provisional y con la lista de esos casos, igual que el calculador. Dos revisores en desacuerdo en un punto cuentan como fallo y el caso se lista como discrepancia. Un caso sin juicios no se puntúa (`not_run`).

### 7. Resultado del caso y trazabilidad de cifras

`pass` exige todas las comprobaciones objetivas y todos los puntos `required` en `pass`. Cada cifra con unidad que afirma la respuesta se clasifica como `question`, `context` (según dónde aparezca en el caso de la batería), `evidence` (si está en un fragmento recuperado cuyo texto guardó la recogida) o `untraceable` (también las cifras con signo y las de tres o más dígitos sin unidad, que no sean un año ni parte de un identificador como JUP-107); en un caso crítico una cifra `untraceable` impide el `pass`. Una cifra que coincide con un valor esperado de la batería (el total o el porcentaje que el caso pide calcular) cuenta como derivada del contexto y se clasifica como `context`, porque casi todos los casos críticos exigen cifras que no están literalmente en el prompt. El calculador exige que un caso completado informe `structured_ok`: para el chat, `true` significa que la respuesta cumple el contrato de respuesta del chat (mensaje del asistente y contexto recuperado); no es la salida estructurada `FinOpsResponse` de JUP-024. Una respuesta que no cumple ese contrato se recoge como fallo `invalid_response` y bloquea el caso.

### 8. Umbrales en el fichero de reglas y veredicto

`score` lee los objetivos que el calculador ya incluye en el informe (ACC-2 ≥ 90 %, GRD-2 igual a cero en críticos, STR-1 ≥ 95 % y latencia total p95 ≤ 10 s en desarrollo, todos de ADR-0002 y provisionales) y añade los umbrales propios del fichero de reglas: ACC-1 ≥ 80 % de los casos `answer`, que es una propuesta de JUP-070 a validar por el equipo. El fichero de reglas también lista las métricas no aplicables cuando no hay salida estructurada (STR-1) y declara con `structured_output` si el chat la devuelve; mientras sea `false`, STR-1 se informa como no aplicable aunque el calculador dé 100 %, porque `structured_ok` solo comprueba el contrato de respuesta. Un umbral obligatorio que no se puede calcular se informa como no disponible y el veredicto no puede ser «aceptado». El veredicto se publica junto al intervalo de Wilson y al tamaño de la muestra; con 28 casos, un caso son 3,6 puntos.

### 9. Repeticiones

Cada ejecución se recoge y puntúa por separado, con una etiqueta. `compare` muestra, para varias ejecuciones, el valor de cada métrica y su variación. La metodología exige tres repeticiones para una medición final y prohíbe sustituir una ejecución mala por otra mejor. Con un chat que no llama a ningún modelo las repeticiones deberían coincidir; con un modelo no tienen por qué.

### 10. Medición de referencia del chat actual

Se mide el chat tal cual está, con el corpus del proyecto cargado y embeddings `mock`. Se espera que casi todo falle porque el chat repite la pregunta y pega fragmentos. Es el «antes», no una evaluación de un sistema generativo: la evidencia lo dice y los umbrales y las métricas de recuperación (que con `mock` no tienen significado semántico) se leen con esa salvedad. La medición se marca provisional si los juicios los da una sola persona.

### 11. ADR no aplicable

No hay decisión arquitectónica duradera: es una herramienta de evaluación, un fichero de reglas y documentación.

## Risks / Trade-offs

- [La regla de cifras da falsos fallos con formatos que no prevé] → Se corrige la regla y se repite; las pruebas incluyen buenas y malas respuestas sintéticas de cada caso crítico y el informe lista los fallos de cifras.
- [Una regla de prohibición no ve una violación] → Es una cota inferior, y las personas pueden anotar la violación no detectada; el informe la cuenta aparte.
- [Pocos revisores y poco tiempo antes del 16/10] → El modo `--provisional` permite medir con uno; la medición final espera a dos.
- [Los casos `abstain` son 2 y los `clarify` 6] → Se publican con su intervalo y sin umbral propio; no se lee un caso como una tendencia.
- [Con `mock` la recuperación no es semántica] → Las métricas de recuperación se publican con esa nota, como ya hace el calculador.
- [El modelo varía entre ejecuciones] → Repeticiones registradas y variación visible.
- [La medición final depende de JUP-035 y de la clave de JUP-078] → La herramienta no cambia; solo se repite la medición.

## Migration Plan

No hay migración. Para revertir, basta retirar la herramienta, el fichero de reglas, el documento, la prueba, la evidencia y las líneas de `package.json`, `ci.yml` y `ci-workflow.test.mjs`.

## Open Questions

- Quién hace la segunda revisión de los casos críticos en la medición final. Es un acuerdo del equipo y no cambia el diseño.
