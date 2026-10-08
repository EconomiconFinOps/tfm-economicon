# Revisión — JUP-070

## Resumen

Herramienta de evaluación de las respuestas del chat (`tools/assistant-eval.py`) con reglas versionadas, juicio humano para los puntos requeridos, veredicto con umbrales y una medición de referencia del chat actual (plantilla sin modelo) con embeddings `mock` y `litellm`. La metodología está en `docs/validation/JUP-070-evaluation.md` y la evidencia en `docs/evidence/JUP-070-validation.md`.

## Decisiones

- La regla decide cifras y prohibiciones; las personas deciden los puntos `required-N`; la herramienta no usa un modelo como juez.
- La medición es provisional: una sola revisora y 46 juicios `fail` porque la respuesta es la plantilla.
- STR-1 se informa como «no aplica» mientras el chat no devuelva salida estructurada (`acceptance.structured_output` en las reglas).

## Adversarial Review (pass 1)

Revisor independiente, base `2f9a5f5`. Veredicto: changes-requested. Hallazgos reproducidos con el código real:

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | BLOCKING | Corregido: una respuesta malformada o una excepción de `http.client` bloquea solo su caso (`schema_validation` o `connection`) y la recogida sigue; la sesión también las captura. Pruebas `MalformedReplyTests`. |
| ADV-2 | HIGH | Corregido: el revisor se normaliza (sin tildes ni mayúsculas) y «Ana» y «ana» son una persona; un revisor que no es texto es un error claro. |
| ADV-3 | HIGH | Corregido: STR-1 es «no aplica» en el veredicto mientras `structured_output` sea falso; la evidencia lo explica. |
| ADV-4 | HIGH | Corregido: los importes que no están en el prompt no se anulan por una negación cercana; ejemplos nuevos en las reglas. |
| ADV-5 | HIGH | Corregido en dos partes: la etiqueta debe estar junto a la cifra (no cuenta bajo la etiqueta de otra) y las cifras con signo o de tres o más dígitos sin unidad cuentan como cifras sin rastro. «De X a Y» queda registrado como RF-070-001. |
| ADV-6 | MEDIUM | Corregido: el informe dice que `embedding` y `retrieval` valen 0 por construcción y no son una medición. |
| ADV-7 | MEDIUM | Corregido: los errores del calculador muestran el campo. |
| ADV-8 | MEDIUM | `reviewer: null` o no textual es un error claro. Más de dos revisores sigue siendo un error por diseño (documentado). |
| ADV-9 | MEDIUM | Corregido en parte: patrones nuevos y ejemplos para «corresponden a la factura» y «se ha conectado a tu tenant real»; la negación cercana queda como RF-070-004. |
| ADV-10 | MEDIUM | Corregido: moneda como palabra antes de la cifra y énfasis de markdown. El espacio como separador de miles queda como RF-070-002. |
| ADV-11 | MEDIUM | Corregido en la evidencia: la ejecución 1 no tuvo umbral de distancia. |
| ADV-12 | LOW | Registrado como RF-070-003. |
| ADV-13 | LOW | Cierre pendiente de la tarea 4. |

Además, al revisar se vio que los ficheros generados llevaban saltos de línea CRLF en Windows: ahora se escriben siempre con LF (los bytes no dependen del sistema) y `compare` ya no falla con tildes en una consola que no es UTF-8.

Ataques que resistieron: números dentro de otros, ambos convenios decimales, unidad y tolerancia, determinismo byte a byte, ausencia de texto y de credenciales en la evidencia, escritura fuera del repositorio, reglas completas, casos sin juicio, discrepancia entre revisores, bloqueos por infraestructura y reducción de muestra.

Barrido del patrón: la normalización de identificadores solo estaba en `reviewers_of`; la excepción fuera del `except` se repetía en el inicio de sesión (corregido); la negación por defecto afectaba a las dos reglas de importe (corregido); las cifras sin unidad o con signo afectaban a `classify_figures` y a `amount_not_in_prompt` (la primera corregida; la segunda no cambia el criterio «importe con unidad»).

## Adversarial Review (pass 2)

Revisor independiente, sobre los cambios de la pasada 1. Veredicto: changes-requested (1 BLOCKING, 3 HIGH).

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | BLOCKING | Una respuesta malformada se recogía como `schema_validation`, que `score_case` trataba como bloqueo y el calculador rechazaba, de modo que un solo caso abortaba toda la puntuación. Corregido: se recoge como `invalid_response` (fallo de proveedor del calculador, caso `blocked`) y una prueba puntúa una batería completa con ese caso. |
| ADV-2 | HIGH | La proximidad de etiqueta daba falsos fallos con «200 EUR (20 %)» y similares. Corregido: solo bloquea que justo antes de la cifra aparezca la etiqueta de otra cifra; si no hay ninguna etiqueta, vale la del resto de la frase. Diez redacciones naturales en las pruebas. «Julio … (agosto)» queda como RF-070-005. |
| ADV-3 | HIGH | Alias que faltaban (`superamos`, `pasamos`, `aumenta`, `sube`…). Añadidos en los casos que usan `supera` y `aumento`. |
| ADV-4 | HIGH | Cifras derivadas correctas se marcaban sin rastro. Corregido: sumas, diferencias y cocientes (en %) de los números del caso y de los valores esperados cuentan como derivadas del contexto. Una cifra inventada que coincida con una derivada pasaría; las pruebas fijan que 9.999, 777 y 4.321 siguen sin rastro. |
| ADV-5 | MEDIUM | Identificadores sin guion («fragmento 120», «ISO 8601», `chunk:105`) dejan de contar como importes. Los años de 1900 a 2100 sin unidad siguen exentos (decisión documentada). |
| ADV-6 | MEDIUM | La recogida valida el tipo de los campos del fragmento y captura `RecursionError`: el caso queda `blocked` y la recogida sigue. |
| ADV-7 | MEDIUM | Con `structured_output: true` y STR-1 no calculable, el veredicto da `not_available`. |
| ADV-8 | LOW | Los caracteres de formato Unicode se quitan del nombre del revisor. «Ana G.» y «Ana» siguen siendo dos personas. |
| ADV-9 | LOW | Decisión deliberada, registrada como RF-070-006. |
| ADV-10 | LOW | Registrado como RF-070-005. |
