JUP: JUP-071
Trello: https://trello.com/c/H0woDubz

## Context

La batería JUP-069 conserva 28 casos con `answer`, `clarify` y `abstain`. Ya cubre coste sin alcance, denominador cero, coste shared sin reparto aprobado, monedas distintas e ingesta incompleta. JUP-071 amplía esa base con variaciones controladas y preguntas sobre tags, sin atribuir a esos escenarios sintéticos datos de un tenant real.

Inspección del 2026-10-10 (contribución original): `AssistantService.answer(user_prompt, retrieved_chunks)` concatena la consulta y hasta tres fragmentos, o devuelve ausencia de contexto. No llama a un modelo. `POST /assistant/conversations/{id}/messages` devuelve el mensaje, metadatos de citas y contexto recuperado, pero no evidencia verificable del modelo.

Situación del 2026-10-16: `develop` integró JUP-035 entrega A (#130, `cf821570`). El chat generativo se sirve por `POST /assistant/conversations/{id}/generations` (streaming) y entra desactivado (`CHAT_ENABLED=false`, la ruta nueva responde `503 chat_unavailable`), mientras `/messages` sigue contestando con la plantilla. La entrega B (JUP-123) se integró el 2026-10-18 (#140, `0e686f91`) y el equipo publicó antes un colector de solo lectura de operaciones terminadas del chat (PR #131). Todo esto condiciona qué puede medir este change (decisión 8).

La metodología de JUP-070 distingue juicios humanos de reglas numéricas, exige dos personas en los casos críticos, permite una medición provisional con una, conserva fallos de infraestructura y prescribe tres repeticiones finales. Sus prohibiciones por patrones son una cota inferior conocida (RF-070-004, RF-070-006 y RF-070-008) y su lector numérico solo mira la etiqueta anterior a la cifra (registrado en `openspec/findings/backlog.md`). Aquí las prohibiciones semánticas se juzgan explícitamente para no convertir la ausencia de una coincidencia en prueba de robustez.

## Goals / Non-Goals

**Objetivos:** un instrumento reproducible, escenarios contrastables, informes honestos sobre la cobertura de revisión y una línea base ejecutable sin red. La tarjeta busca conocer limitaciones; una respuesta que falla es evidencia útil y no debe corregirse en el registro.

**No objetivos:** integrar el LLM, definir nuevas políticas de reparto o tagging, reemplazar o modificar JUP-070, arreglar todos sus hallazgos pendientes, escribir el colector de `/generations` o un ejecutor de campañas de pago (JUP-123), construir el dashboard (JUP-121), emitir dictámenes por personas ausentes ni declarar robustez generativa sin una ejecución demostrada.

## Decisions

### 1. Batería ampliada sin modificar JUP-069

El fichero propio identifica versión, origen sintético, referencia y hash del banco JUP-069, de la metodología de JUP-070 y de las fuentes utilizadas. Cada variante tiene identificador estable JUP-071, referencia a un caso base, categoría, grupo de perturbación, contexto, pregunta, comportamiento, riesgo y rúbrica. Al expandirla se incluyen los baselines originales una sola vez, aunque varias variantes compartan base. Se valida que todas las referencias existan, que no haya IDs repetidos y que los hashes sigan coincidiendo. No se reutilizan IDs para preguntas distintas.

Los grupos cubren ausencia o conflicto de tags, costes compartidos sin una base válida, datos parciales y ambigüedades de alcance/unidad/periodo. La rúbrica diferencia aclarar lo que falta, responder una parte sustentada y abstenerse de afirmar lo inaccesible. Debe penalizar tanto inventar una respuesta como abstenerse ante un control que sí tiene datos suficientes.

Cuando `develop` cambia el banco, la metodología o el corpus (ocurrió con JUP-120, que subió JUP-069 a `1.0.1`), un hash que ya no coincide detiene la evaluación. Las referencias se actualizan solo tras comprobar que las preguntas y las reglas de las que dependen las variantes siguen vigentes (por ejemplo, que la regla de anomalía diaria de la variante JUP-071-014 no cambió). La batería conserva su propia versión.

### 2. Adaptador propio sobre funciones existentes

`tools/assistant-robustness.py` carga el evaluador JUP-070 por su ruta y reutiliza `prompt_text(case)`, `check_number(...)` y `collect_cases(...)`. No altera sus comandos ni su banco por defecto. Son funciones internas, por lo que las pruebas del adaptador deben detectar cambios de firma o de semántica.

Los prompts se generan exclusivamente desde contexto y pregunta; ninguna rúbrica, comportamiento esperado o clave de respuestas forma parte del mensaje enviado. Al reutilizar `prompt_text`, el texto puede tener un envoltorio distinto del preparado por el CLI de JUP-069, pero la variante y su baseline se evalúan con la misma preparación documentada. El hash de la batería permite identificar esa ejecución, y la recogida debe conservar los prompts exactos preparados.

### 3. Dos caminos de ejecución con nivel explícito

La ejecución offline invoca `AssistantService.answer` de la aplicación, tras comprobar que el fichero del servicio coincide con la versión revisada. La recuperación es un doble fijo declarado, sin embeddings ni acceso a base de datos o red. Prueba cómo se comporta esa plantilla bajo el contexto suministrado y que el instrumento funciona; no mide relevancia del retrieval ni el chat HTTP completo.

La recogida HTTP delega en JUP-070: inicio de sesión, una conversación nueva por caso, envío exacto de su prompt y registro de respuesta, citas, fragmentos, HTTP y tiempo total. No hay reintentos. Credenciales sólo desde entorno y sin persistirlas. Los errores de infraestructura se registran `blocked` con categoría. La descripción de la ejecución se valida antes de la primera petición, de modo que una configuración errónea no gasta recursos.

El informe distingue dos tipos de ejecución: `template_mock` (plantilla offline con doble) y `live_unverified` (recogida contra un servidor, sin verificar qué hay detrás). Qué responde al otro lado lo declara el operador en el proveedor, el alias y la generación; el informe no puede distinguir una plantilla servida por HTTP de un runtime desconocido más que por esa declaración. El endpoint de mensajes no acredita generación real. Un alias configurado manualmente o embeddings LiteLLM no elevan esa evidencia a modelo verificado. La evidencia de JUP-035 debe identificar commit desplegado, configuración real y prueba de que la respuesta recorrió el modelo; hasta tenerla, la conclusión generativa permanece pendiente.

### 4. Juicio humano de semántica, regla para cifras

La hoja de revisión reúne el prompt, la respuesta, las citas y el contexto recuperado junto a los puntos de juicio (comportamiento, puntos requeridos y prohibiciones). La hoja no incluye el campo de cifras esperadas, que comprueba la regla numérica, aunque el texto de un punto requerido pueda mencionar un valor. Los juicios humanos cubren `behavior`, cada `required` y cada `forbidden`; no se generan automáticamente desde la rúbrica o el resultado esperado.

Los casos críticos declarados por la batería necesitan dos personas distintas para cada juicio semántico; los baselines se tratan también como críticos, y la validación de la batería exige que todo caso con cifras esperadas sea crítico para que una sola persona no baste. La exigencia incluye también riesgos semánticos sin cifras, como asignaciones inventadas o uso de datos de demo como datos reales. La identificación normalizada impide contar dos grafías de la misma persona (no autentica identidades). El modo provisional admite una persona y lo declara: cada caso crítico con menos de dos revisores lleva `reduced_coverage` y la evaluación no se da por completa mientras exista alguno.

Si faltan juicios y aún no se conoce ningún incumplimiento, el caso queda `not_run` aun si su respuesta se recogió. Si una comprobación numérica o un juicio recibido ya falla, se conserva `fail`, junto a todos los juicios pendientes y `assessment_complete=false`: la falta de revisión no oculta un fallo comprobado ni convierte el dictamen semántico en completo. Un desacuerdo o criterio incumplido impide el `pass`. Los juicios de dobles unitarios usan identidades de prueba y nunca se presentan como revisión humana del producto.

### 5. Cifras: alias declarados y rivales por alias

Las cifras reutilizan etiqueta, unidad y tolerancia de JUP-070 y no aceptan el mero eco del prompt. Para decidir qué etiqueta nombra una cifra, la batería puede declarar `aliases` por cifra; si no los declara se usan los de las reglas de JUP-070 y, en su defecto, la etiqueta. Los rivales de una cifra son los alias de las demás cifras del mismo caso, como en JUP-070, de modo que una respuesta que pone el valor de una cifra bajo la etiqueta de otra falla. Sin alias propios, una respuesta correcta parafraseada («el cumplimiento es del 10 %») fallaba en las variantes de cumplimiento de tagging aunque pasaba en su baseline. Además esas dos variantes pedían una segunda cifra (el coste etiquetable, 1.000 EUR) que su pregunta no solicita, de modo que una respuesta correcta que daba solo el 10 % también fallaba, sin posibilidad de que un juicio humano lo revirtiera. Con los alias declarados y una única cifra, como en su baseline, pasan igual en ambas.

Los alias deben seguir siendo no vacíos y únicos tras normalizar: un alias vacío casaría con cualquier frase. Persiste una limitación heredada de JUP-070 (solo se mira la etiqueta anterior a la cifra, registrada en el backlog): un `fail` numérico en un caso con varias cifras se revisa a mano antes de atribuirlo al asistente.

### 6. Informes con poblaciones y procedencia

Cada caso conserva uno de los cuatro estados del protocolo JUP-069. Las tasas distinguen `pass / total previsto` de `pass / (pass + fail)` e informan también `blocked`, `not_run`, juicios pendientes y casos con cobertura reducida, evitando que un denominador reducido parezca cobertura completa. El denominador `pass + fail` incluye fallos ya conocidos con semántica todavía pendiente; no debe interpretarse como número de revisiones humanas completas. Se desglosan baselines/variantes, comportamientos, tipos de perturbación y categorías: los tipos tienen un caso cada uno, por lo que las categorías agregan variantes (la categoría `anomalies` sigue teniendo un solo caso y el informe muestra siempre el tamaño de cada grupo). Un denominador sin casos evaluados se muestra como «no disponible» y nunca como cero ni como éxito. No se inventa un umbral de aceptación aprobado.

JUP-067/JUP-070 reservan ACC-1 y ACC-2 a casos `answer` y usan ACC-3 para `clarify`/`abstain`. El informe propio mantiene esas poblaciones conceptuales, pero no afirma compatibilidad del JSON con el calculador JUP-067 porque usa un esquema propio con juicios adicionales. No se agregan métricas de retrieval ni latencias de etapas que no se han medido. La latencia HTTP observada es la petición total.

Los resultados versionables excluyen texto de preguntas, respuestas, fragmentos, nombres de revisores y notas privadas. Esos materiales se escriben fuera del repositorio. La ficha conserva versiones, hashes, fecha, commit, modo de ejecución y limitaciones, sin credenciales. La evidencia por criterio enlaza resultados y comandos y separa comprobaciones técnicas de revisión y validación humanas.

### 7. Repetición y dependencia de JUP-035

Una medición final con modelo requiere tres recogidas independientes con la misma batería y configuración, todas publicadas, con los juicios requeridos. No se elige la mejor, y reexportar la misma recogida no cuenta como ejecución independiente. La línea base offline es ejecutable ahora y la herramienta HTTP deja preparado el siguiente paso; ningún resultado de la primera completa el pendiente generativo.

### 8. El chat generativo de JUP-035 no usa el contrato de mensajes

Inspección del 2026-10-14 sobre #130 (integrada el 2026-10-15): el chat generativo se sirve por `/generations`, con respuesta en streaming y un cuerpo propio (contenido y contexto de pantalla con la identidad del usuario y el tenant), mientras `/messages`, que reutiliza `collect_cases` de JUP-070, sigue llamando a la plantilla. Por tanto `collect` solo mide la plantilla, aunque el chat generativo esté activo; una campaña con modelo real necesita un colector de `/generations`.

JUP-123 (PR #131) publica un colector de solo lectura que lee operaciones terminadas del chat y las exporta al evaluador de esta herramienta, y no genera respuestas ni entrega un ejecutor de campañas. Este change no lo duplica: lo consume. Se probó contra un backend real con chat activado y modelo simulado (ver la evidencia), sin coste y sin demostrar calidad alguna. El presupuesto de inferencia es compartido con B (techo acumulado de 2 USD según la tarjeta de JUP-123), de modo que ninguna campaña con modelo se lanza sin comprobar su contabilidad ni sin acordarlo con quien lidera B.

Reparto: JUP-071 entrega el instrumento, la batería, las líneas base y las limitaciones conocidas; la medición con modelo real se ejecuta cuando el chat esté activado con un modelo, exista quien genere las respuestas y se haya acordado el presupuesto, y no se declara robustez generativa antes.

### 9. Informe preparado para un consumidor posterior y para el colector

Los resultados de las tarjetas de evaluación se mostrarán más adelante en un dashboard común (tarjeta JUP-121). Para no reescribir informes ya publicados, el informe propio incorpora un bloque `run` con los mismos nombres que la cabecera de JUP-070 (`commit`, `date`, `provider`, `alias`, `suite_version`, `suite_sha256`, `generation`) y un identificador único de ejecución derivado de la recogida. Una ejecución con plantilla declara que no hay modelo en lugar de omitir `provider` y `alias`. Los campos actuales se conservan y no cambia ningún resultado ni denominador.

El colector de JUP-123 describe la ejecución con seis cadenas. Para que su exportación sea válida aquí, el bloque `run` acepta un commit declarado de 7 a 40 caracteres hexadecimales en minúscula y `generation` como una sola cadena, que se registra como alias del modelo sin temperatura (la forma de objeto con temperatura sigue siendo válida). Se probó que sin esta adaptación ninguna combinación de valores servía a ambas herramientas. Los marcadores descriptivos de la guía de ese colector no valen: hay que escribir un identificador real.

Para no obligar al dashboard a conocer los grupos anidados de este informe, el comando `rows` lo convierte al contrato `rows-v1` que define JUP-121 (decisión 14). Quedan fuera, y pasan a JUP-121: decidir dónde se muestran las filas y unificar los formatos de JUP-067, JUP-070 y JUP-078.

### 10. Validación estricta de la batería con errores controlados

Antes de usar la batería se validan sus tipos y sus bloques de referencia: la versión de esquema es el entero uno (no un booleano), la versión de la batería tiene forma mayor.menor.parche, cada caso es un objeto con campos de texto y listas del tipo esperado, y los bloques de banco, metodología y fuentes existen. Cualquier incumplimiento detiene la ejecución con un error que nombra el caso o el bloque, y no con una excepción sin contexto. Estas comprobaciones se añadieron tras una revisión adversarial que encontró accesos sin guarda que producían trazas. La misma garantía cubre la entrada hostil: un entero demasiado grande para un número de coma flotante (que `math.isfinite` no soporta y lanza `OverflowError`) o un documento anidado miles de niveles (que lanza `RecursionError`) terminan en el mismo error controlado. Las cifras esperadas, la temperatura declarada, las distancias recuperadas y las duraciones usan una única comprobación de número finito.

### 11. Límites de las rutas de salida

El material crudo, las hojas de revisión y las plantillas de juicios se escriben fuera del repositorio. Dentro solo se admiten los informes generados `JUP-071-*-report` de `docs/evidence`; ninguna salida puede sobrescribir entradas, referencias, la batería, el servicio, el evaluador u otra salida, y el directorio de destino debe existir. Las rutas se comparan normalizadas: se quitan prefijos extendidos de Windows, los puntos y espacios finales de cada componente y las diferencias de mayúsculas, y en Windows se rechazan las rutas de red, incluidos los recursos administrativos, porque pueden apuntar de vuelta al propio repositorio. La misma debilidad existe en el CLI de JUP-070 y no se corrige aquí (backlog).

### 12. Metadatos declarados por el operador

Proveedor, alias e identificador de generación son declaraciones del operador, no mediciones. Se aceptan solo identificadores en minúsculas de hasta 64 caracteres (letras, dígitos, punto, barra y guion) sin partes con forma de clave (`sk`, `pk`, `xox`, `gh*`, `akia`, `eyj`, `key`, `token`, `secret`, `bearer`) ni tramos alfanuméricos de 24 caracteres o más. Es una heurística contra la divulgación accidental y no una garantía, y comprueba la forma y no el significado: palabras como `tbd` o `unknown` cumplen el patrón y se aceptan (la plantilla offline usa `none` como alias). Declarar valores reales es responsabilidad del operador. Solo los campos validados llegan al informe versionable; el resto de la configuración (claves, hashes del colector) no se copia. En la recogida, la descripción de la ejecución admite exactamente los seis campos declarados (commit, corpus, proveedor, alias, recuperación y generación), porque se guarda entera junto al crudo: un campo adicional se rechaza por su nombre, sin repetir su valor. La restricción alcanza a los valores anidados: `generation` solo lleva `model_alias` y `temperature`, y `corpus` y `retrieval` son un texto corto o un objeto plano de hasta 16 valores escalares cortos con claves en minúscula que no parezcan credenciales. `prepare`, como los demás ficheros privados, solo escribe fuera del repositorio. `configuration_sha256` es el hash de toda la configuración declarada, no solo de los campos validados: una configuración de forma conocida con un secreto corto podría revelarse por fuerza bruta (registrado en el backlog). Ningún campo declarado ni un conjunto de juicios todo-pass establece la verificación de modelo ni la aceptación de robustez generativa.

### 13. Evidencia del chat real sin distancia

El formato de recogida de JUP-070 exige, para cada fragmento recuperado, una distancia numérica medida. La evidencia de corpus que ofrece el chat generativo de JUP-035 entrega A no la incluye. El colector de JUP-123 no la inventa: su cabeza `af8388d0` bloqueaba todas las filas con corpus (las exportaba como `invalid_response` y el scorer las puntuaba `blocked`, no como fallo semántico) y asignaba a este change adaptar el evaluador. Este change resuelve su mitad: la validación del crudo acepta un fragmento con `distance: null` (la clave debe existir; un texto, un booleano o un valor no finito siguen rechazados) y una lista opcional `public_evidence` por caso (objetos con `id` y `kind` de texto no vacíos, `id` únicos dentro del caso, `source` y `content` de texto cuando existen, y distancia nula o finita). La hoja de revisión muestra ambas en el bloque de citas y fragmentos, de modo que quien juzga ve la evidencia real y que no hay distancia, y nada puntúa por distancia. La herramienta expone `ACCEPTS_UNMEASURED_DISTANCE = True`, y la cabeza actual del colector (`e0a0c41e`) la detecta y exporta la evidencia con distancia nula en lugar de bloquear la fila; con una herramienta anterior (sin la constante) mantiene el bloqueo, de modo que el orden de integración de ambos PR no importa. Queda como tarea 6.6 validar esa cabeza con un backend real que devuelva evidencia de corpus (solo se probó una fila construida con su forma) y que su CI esté en verde; hasta entonces una campaña real con citas no está demostrada.

### 14. Emisión del contrato del dashboard

El comando `rows --input <informe> --output <fichero>` convierte el informe de puntuación al contrato `rows-v1` de `tools/evaluation-dashboard.py` (JUP-121, PR #132): una `run` con la identidad del informe (`run_id`, fecha, commit, suite y su hash, alias del modelo, `synthetic` verdadero para la plantilla) y filas con los grupos `cases` (total, por grupo de baseline o variante y conducta, y por categoría), `perturbation_type` (los estados de cada tipo de perturbación), `rates`, `review` y `numeric`. Los recuentos de casos llevan `count` y `denominator` y nunca `value`; una tasa sin casos evaluados es `not_measured` con `value` nulo, no cero. Siguiendo la guía del dashboard (cabeza `b6695100` del PR #132), `pass` y `fail` de casos, las dos tasas y `reduced_coverage` (lo decide una persona) son juicio `human`, y el resto, incluidas las comprobaciones numéricas por regla, `automatic`; así ninguna proporción que depende de personas entra en la gráfica de métricas automáticas. No hay texto de respuestas, nombres ni notas, porque el informe de puntuación no los contiene. Antes de emitir se valida la coherencia del informe (recuentos enteros no negativos que suman el total, `evaluated` igual a `pass + fail`, tasas iguales a su cociente, tipos anidados, tipo de ejecución conocido); cualquier fallo es un error controlado y no se escribe nada. Las dos tasas son `not_measured` cuando no hay casos evaluados, porque «0 de 29» sin ningún caso evaluado no es un éxito del 0 %. `provider` y `alias` del informe viajan como identidad de embedding. Una ejecución real no verificada deja `generation_model` nulo, ya que esta herramienta nunca verifica qué modelo corrió y el dashboard la marca así como `sin_modelo_verificado` en lugar de presentarla como real; el alias declarado se conserva en el informe y se pierde en las filas hasta que exista verificación. Si la recogida trae la procedencia que reporta el servidor (`execution.collection.server_reported`, que copia el colector de JUP-123), la validación del crudo exige una lista de objetos no atestiguados con hash de 64 hexadecimales o ausente, y el informe añade `server_reported` con el hash único, o con el estado `mixed` o `absent` si las muestras no coinciden o no lo traen. Solo un hash único llega a `prompt_sha256` de `rows`; así la anotación de cambio de prompt del dashboard puede funcionar sin que esta herramienta atestigüe nada (el servidor lo declara, no se verifica). Las ejecuciones sin ese bloque, como las de plantilla, no cambian. Los campos de corpus y recuperación van nulos: ningún informe los registra todavía;

Los nombres de grupo y métrica son una propuesta: la guía de ese PR dice que la lectura del panel «Robustez» se cerrará con el informe real y no fija nombres. Se comprobó con el validador de las cabezas `e4b403d4` y `b6695100` del PR #132 (acepta el conjunto de filas y lo clasifica como no real por `plantilla` y `sintetica`) y no depende de que ese PR esté integrado. Los ficheros generados de `docs/evidence` se llaman `JUP-071-*-rows.json` y se regeneran junto a los informes.

### 15. Indicadores de la campaña como insumo para el dashboard

La tarjeta JUP-129 rediseña la presentación de la evaluación en Grafana por las cuatro familias de un RAG y deja fuera crear métricas nuevas. JUP-071 es quien tiene datos reales de un chat generativo, así que calcula aquí un conjunto acotado de indicadores y los emite como filas `rows-v1`; la presentación, los umbrales y la señal de empeoramiento son de JUP-129. Se decidió no crear un comando nuevo: el comando `rows` acepta opcionalmente el crudo y los recibos y añade los indicadores a la misma ejecución, porque dos ficheros de filas con el mismo `run_id` no se pueden cargar a la vez.

Los datos salen de tres fuentes: el informe de puntuación (puntos juzgados, pares, estados), el crudo (respuestas, citas, uso y coste informados por el servidor) y los recibos públicos (manifiesto de contexto con los fragmentos listados y su forma de admisión, y el estado de cada operación). Se descartó ampliar la exportación del colector con los recuentos de recuperación porque ese formato lo mantiene el equipo de JUP-123, y ampliar `score` porque no recibe los recibos. El enlace entre fuentes es el hash del crudo que nombra el informe y la igualdad de la respuesta de cada recibo con la del crudo.

| Familia | Indicador | Fórmula | Marca |
| --- | --- | --- | --- |
| `rob_core` | `invention_rate` | prohibiciones fallidas / prohibiciones juzgadas | humano |
| | `required_coverage` | requeridos en pass / requeridos juzgados | humano |
| | `behavior_match_rate` | puntos `behavior` en pass / juzgados | humano |
| | `valid_citations` | ids citados dentro de la evidencia de su operación / ids citados | automático |
| | `literal_quotes` | citas «» localizadas literalmente en el fragmento citado / citas con fuente | automático |
| `rob_retrieval` | `empty_retrieval_rate` | muestras sin evidencia en el manifiesto / muestras verificadas | automático |
| | `fragments_per_query` | fragmentos listados / muestras con recuperación | automático |
| | `neighbor_share` | fragmentos admitidos como vecinos / fragmentos listados | automático |
| | `context_utilization` | fragmentos citados / fragmentos listados | automático |
| | `unused_retrieval_rate` | muestras con recuperación y sin citas / muestras con recuperación | automático |
| `rob_system` | `completion_rate` | operaciones completadas / muestras previstas | automático |
| | `unmeasured_by_cause` | muestras sin recogida verificada por causa (`operation_failed`, `evidence_unverified`) | automático |
| | `cost_per_query`, `prompt_size_per_query`, `completion_size_per_query` | coste o tokens informados / operaciones que los informan (en las filas, los tamaños llevan la unidad `unidades`: el escáner de secretos del dashboard rechaza la palabra «token») | automático, no atestiguado |
| `rob_conversation` | `request_rate` | casos clarify y abstain evaluados con todos sus puntos de petición en pass / los que tienen alguno | humano |
| | `over_abstention_rate` | casos `answer` evaluados con `behavior` fallido / casos `answer` evaluados | humano |
| | `pair_degradation` | pares con referencia en pass y perturbación en fail / pares con referencia en pass | humano |

Valores de referencia de la campaña `r1` (20/10/2026) para la conciliación, ya calculados a mano y recogidos en la evidencia: `invention_rate` 0 de 55, `required_coverage` 30 de 46, `behavior_match_rate` 22 de 24, `literal_quotes` 27 de 27, `empty_retrieval_rate` 0 de 24, 253 fragmentos listados (96 primarios y 157 vecinos), `context_utilization` 22 de 253, `unused_retrieval_rate` 14 de 24, `completion_rate` 27 de 29, 2 `operation_failed` y 3 `evidence_unverified`, `over_abstention_rate` 1 de 9 y `pair_degradation` 3 de 6. Conciliado el 2026-10-21 con la implementación, que reproduce todas las cifras anteriores y fija `valid_citations` en 22 de 22, `request_rate` en 3 de 15, `fragments_per_query` en 253 fragmentos entre 24 consultas (10,54), el coste medio en 0,0065 USD por consulta y 17.411 y 1.354 tokens de entrada y salida por consulta, sobre las 27 operaciones que informan uso.

Límites: `request_rate` depende de una heurística (los puntos requeridos cuyo texto contiene «pedir», «solicitar» o «proponer aportar») y su clasificación en la batería actual queda fijada por una prueba; las citas «completas» no se incluyen porque detectar el corte de un fragmento es una heurística frágil y ya está registrada como hallazgo; las citas solo se reconocen con el formato del backend `Fuente: <título> — «<texto>»` (con la raya larga), de modo que una campaña que usara otro separador dejaría `literal_quotes` sin medir; la latencia no se calcula porque `total_ms` es nulo; no hay indicador de distancia porque es nula en todos los fragmentos; y la relevancia por fragmento y la fidelidad por afirmación exigen etiquetado. Los indicadores heredan el carácter provisional del informe y no mejoran la evidencia.

## Risks / Trade-offs

- La batería es pequeña, sintética y diseñada; no demuestra robustez universal ni del tenant real. Se publican tamaños y casos concretos.
- La revisión humana falta hasta que las personas emitan sus juicios. Se informa `not_run` mientras no haya un incumplimiento comprobado; un fallo conocido conserva `fail` con la revisión incompleta visible. Nunca se simula un aprobado.
- Los límites del lector de cifras de JUP-070 siguen vigentes (palabras, espacios de millares, asociación temporal o etiquetas, y solo la etiqueta anterior). Se documentan y se comprueban con control numérico; la revisión semántica sigue siendo necesaria y un `fail` numérico se revisa a mano.
- Las funciones reutilizadas son internas y requieren pruebas de regresión del adaptador.
- Las validaciones de metadatos y de rutas son heurísticas y no sustituyen a un control de secretos ni a la configuración de seguridad del entorno.
- El adaptador del colector de JUP-123 fija el commit y los hashes de la suite en su plan: cualquier cambio posterior en la copia de JUP-071 obliga a preparar otro plan y a volver a leer los recibos.
- Cambiar la aplicación, el banco o el corpus tras la medición exige repetir las comprobaciones afectadas; una fecha anterior no se presenta como validación actual.

## Validation Strategy

Pruebas sin red externa: estructura y referencias rotas de la batería, tipos mal formados, hashes alterados, baselines únicos, ausencia de rúbrica en prompts, llamada al servicio real en modo offline, fidelidad de la recogida y fallos HTTP mediante dobles, separación de modos, cada estado y denominador, ausencia de juicios y doble revisión, cobertura reducida, desacuerdo, cifras con unidad/etiqueta/alias/tolerancia y rivales, rutas de salida disfrazadas, metadatos declarados con forma de clave, y ausencia de texto privado en la salida versionable.

La evidencia registra los comandos realmente ejecutados y lo pendiente. OpenSpec y trazabilidad JUP se validan antes de la contribución, la revisión adversarial independiente se repite sobre el estado final, y la revisión y validación de PR pertenecen a las personas registradas en Trello y no se sustituyen por estas pruebas.
