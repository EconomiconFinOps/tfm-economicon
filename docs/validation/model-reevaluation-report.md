# Informe antes y después del cambio de modelo (JUP-133)

Tarjeta: [JUP-133](https://trello.com/c/Yv1ETc2G). Cambio de modelo: [JUP-132](https://trello.com/c/ERLZlPsT). Plan y presupuesto: [model-reevaluation-plan.md](model-reevaluation-plan.md). Qué medidas dependen del modelo: [inventario](model-dependence-inventory.md). Cifras de la memoria afectadas: [model-change-memory-figures.md](model-change-memory-figures.md). Procedimiento y evidencia: [JUP-133-validation.md](../evidence/JUP-133-validation.md).

**Lectura corta.** El chat con DeepSeek V4.1 Flash se midió una vez, con una repetición y una revisora, y los resultados son provisionales. En robustez, el número de aciertos coincide (7 de 29) con un conjunto distinto de casos; el coste por llamada al modelo y por operación baja de forma clara; y el resto de las comparaciones no permiten decir si mejora o empeora, porque cambiaron a la vez el modelo, los recursos del chat (prompts y tokenizer v4 frente a v3), el método de recogida y la muestra evaluada. Además se midió por primera vez el banco de 28 preguntas de JUP-069 con el chat real (apartado 3): no tiene medición anterior con la que compararse.

## 1. Qué se compara

| | Antes | Después |
| --- | --- | --- |
| Alias | `economicon-chat` | `economicon-chat` |
| Modelo servido (`generation_model_id`) | `openrouter/z-ai/glm-5.2` | `openrouter/deepseek/deepseek-v4.1-flash` |
| Proveedor (`generation_provider`) | No registrado | `deepinfra` |
| Cuantización (`generation_quantization`) | No registrada | `fp8` |
| Configuración del gateway (`gateway_config_sha256`) | No registrada | `9f74f807…05f2` |
| Recursos del chat (prompts y tokenizer) | v3 | v4 |
| Commit del producto | `88a6ce4c8a6c` | `ee84f791ca0a` |
| Fecha de la ejecución (UTC) | 20/10/2026 | 21/10/2026 |
| Revisora de los juicios | Lucía (sola, provisional) | Lucía (sola, provisional), a partir de una propuesta preparada con apoyo de un agente de programación y aprobada por ella el 22/10/2026 |
| Identidad atestiguada por el instrumento | No | No |

El modelo «antes» consta por el registro de gasto del gateway (`docs/evidence/JUP-130/JUP-130-ai-cost.md` recoge 100 consultas con `openrouter/z-ai/glm-5.2`); el proveedor y la cuantización de esa ejecución no constan en ninguna evidencia del repositorio y se dejan sin registrar. Los valores «después» son los que declara la configuración del gateway; el instrumento no verifica qué modelo respondió.

## 2. Medida a medida

Una repetición de 29 casos en ambas campañas, sin intervalos de confianza. Las tasas son de la campaña de robustez de JUP-071.

| Medida | Antes | Después | Condiciones iguales | Lectura |
| --- | --- | --- | --- | --- |
| Aciertos de 29 casos | 7 (7/24 evaluadas: 29,2 %) | 7 (7/28 evaluadas: 25,0 %) | No | límite de la comparación |
| Casos fallidos / bloqueados | 17 / 5 | 21 / 1 | No | límite de la comparación |
| Prohibiciones incumplidas | 0 de 55 | 0 de 64 | No | límite de la comparación |
| Puntos requeridos cubiertos | 65,2 % (30/46) | 64,8 % (35/54) | No | límite de la comparación |
| Comportamiento esperado | 91,7 % (22/24) | 82,1 % (23/28) | No | límite de la comparación |
| Pide el dato que falta | 20,0 % (3/15) | 31,6 % (6/19) | No | límite de la comparación |
| Degradación entre referencia y perturbación | 50,0 % (3/6) | 60,0 % (3/5) | No | límite de la comparación |
| Operaciones completadas | 93,1 % (27/29) | 96,6 % (28/29) | No | límite de la comparación |
| Coste por operación (informado por el servidor) | 0,0065 USD (27 operaciones) | 0,0011 USD (28 operaciones) | No | límite de la comparación |
| Tokens de entrada por operación | 17.411 | 18.489 | No | límite de la comparación |
| Tokens de salida por operación | 1.354 | 1.036 | No | límite de la comparación |
| Coste de IA facturado por consulta al modelo | 0,002601 USD (100 consultas con GLM-5.2, 9 a 20/10/2026) | 0,000596 USD (73 consultas con DeepSeek V4.1 Flash, 21/10/2026) | No | límite de la comparación |
| Comprobaciones numéricas automáticas | 4 pass, 9 fail | 0 pass, 13 fail | No | límite de la comparación |
| Latencia p95 de la campaña | No medido | No medido | — | sin comparación |
| Batería N3/N5: conformidad por requisito | Medida en octubre con otra versión | No medido | — | sin comparación |
| Señales en vivo (Prometheus) | No medido | Ver el apartado 5 | — | sin comparación |
| Detector de anomalías, frescura y reconciliación de datos | Valores de JUP-130 | No se repite | — | independiente del modelo |

**Notas del autor** (no son lecturas de la tabla):

- El coste del chat baja con un orden de magnitud que no cabe en las diferencias de muestra o de recursos: por consulta al modelo pasa de 0,0026 a 0,0006 USD facturados, y por operación de 0,0065 a 0,0011 USD según el servidor. Los tokens de entrada por operación son un 6 % más con los recursos v4. La regla de lectura impide escribir «mejora» porque las condiciones no son iguales, y las dos cifras son de ventanas distintas con distinto número de consultas.
- Las comprobaciones numéricas automáticas pasan de 4 a 0 aciertos. Es la limitación conocida del lector numérico de JUP-070, que exige una etiqueta concreta antes de la cifra; con las respuestas nuevas el formato cambió. Cinco casos fallan solo por esa comprobación (`JUP-069-002`, `-011`, `-027`, `JUP-071-002` y `-003`): tienen todos los puntos humanos en pass y los cálculos correctos a mano, así que no debe leerse como una caída de calidad.
- La muestra evaluada pasa de 24 a 28 casos porque hay menos casos bloqueados (de 5 a 1). Cambia el denominador de todas las tasas.

## 3. Banco de JUP-069 con el chat real (sin medición anterior)

Las 28 preguntas del banco de JUP-069 (20 de responder, 6 de pedir el dato que falta y 2 de abstenerse) se ejecutaron una vez con el chat real y DeepSeek V4.1 Flash, y se puntuaron con la herramienta de JUP-070. Los juicios de los puntos requeridos los preparó un agente de programación y los aprobó Lucía el 22/10/2026 sin cambios; es una sola revisora, así que el informe es provisional. El banco no se había medido antes con el chat real (las dos campañas de JUP-070 de octubre se hicieron con la plantilla sin modelo), por lo que **no hay comparación antes/después**: son las primeras cifras de referencia del modelo nuevo.

| Medida | Valor |
| --- | --- |
| Casos aprobados | 10 de 28 (6 de 20 en los de responder) |
| Comprobaciones objetivas | 31 de 51 (60,8 %); la regla de aceptación pide 0,9 |
| Puntos juzgados cumplidos | 25 de 30 (83,3 %); en total 38 de 46 puntos requeridos |
| Citas válidas | 22 de 22 |
| Respuestas que cumplen el esquema | 28 de 28 |
| Pedir el dato que falta (6 casos) | 2 de 6 aprobados |
| Abstenerse (2 casos) | 2 de 2 aprobados |
| Acierto de documento / de sección | 8 de 20 / 5 de 20 |
| Resultado de recuperación vacío (responder / pedir / abstenerse) | 12 de 20 / 3 de 6 / 0 de 2 |
| Latencia mediana / p95 / máxima por conversación | 20,8 s / 41,3 s / 66,7 s |
| Veredicto de la herramienta | No aceptado (ACC-1 0,3 frente a 0,8; ACC-2 y LAT-2 sin cumplir) |

**Cómo leerlo.**

- **Más de la mitad de los fallos son del lector numérico.** 9 de los 18 casos fallan solo por la comprobación numérica automática (`001`, `002`, `006`, `007`, `011`, `013`, `018`, `021`, `027`); a mano tienen las cuentas correctas. Es la limitación conocida del lector de JUP-070, que exige una etiqueta concreta antes de la cifra.
- **Dos fallos por reglas automáticas que a mano no se incumplen.** `JUP-069-008` (la regla ve «verde» aunque la respuesta lo niega) y `JUP-069-014` (la regla ve 1200 EUR en una línea de cálculo).
- **Ocho puntos juzgados fallan.** Cinco son «no pide lo que falta» (`009`, `016`, `019`, `020`, `026`), uno es que no dice que las claves van en minúsculas (`010`) y dos son de `005`, donde el chat se niega a clasificar aunque el enunciado da la regla.
- **Fundamento.** Las citas son válidas en las 22 emitidas. Hay una cifra sin rastro (en `JUP-069-008`), en un caso no crítico.

**Límites propios del banco.**

- Se recogen como máximo 12 fragmentos por pregunta: los 4 aciertos más los vecinos que añade el producto. Las métricas de relevancia son por eso más laxas que con `top_k 4`.
- En 13 de las 28 hubo que reconstruir el contenido recuperado desde la base por identificador; los 13 coincidieron por hash con el que registró el servidor.
- La latencia es la del ordenador local de Lucía, medida por el generador, y la de embedding y recuperación vale 0 porque la herramienta no las separa. En `JUP-069-010` incluye dos intentos del producto.
- La disponibilidad (28 de 28) es lo que observó el generador, sin errores 5xx; no es una medida independiente.

## 4. Reglas de lectura

Se aplican las de la [plantilla](model-reevaluation-report-template.md): «sin comparación» si falta una medición, «límite de la comparación» si las condiciones difieren (batería, corpus, recuperación, revisora o recursos del chat), «diferencia no distinguible» si los intervalos se solapan, y «mejora» o «empeora» solo con condiciones iguales e intervalos separados. Aquí no se cumple ninguna de las condiciones para escribir «mejora» ni «empeora».

## 5. Límites de las cifras

- **Muestra y repeticiones.** Una repetición de 29 casos y una revisora. Sin intervalos de confianza.
- **Informe provisional.** Los juicios son de un solo revisor (modo `--provisional`). La propuesta la preparó un agente de programación y la aprobó Lucía el 22/10/2026 sin cambios; en el 20/10 los juicios fueron de Lucía con ayuda de un agente de programación.
- **Recogida distinta.** El 20/10 se reconstruyeron 10 de las 13 recuperaciones desde la base vectorial y se bloquearon 3; el 21/10 se reconstruyeron las 12 que hacían falta y coincidieron todas por hash, y la única bloqueada es la operación que falló (`JUP-069-010`, rechazada dos veces por el validador de salida del producto). El generador de las conversaciones no es el mismo script.
- **Recursos del chat.** JUP-132 cambia el modelo y los recursos (prompts y tokenizer) a la vez; esta medición no puede separarlos.
- **Latencia.** La campaña de robustez no mide latencia. Como dato informal del generador, cada conversación tardó entre 15 y 27 s, y la primera 73,6 s por arranque en frío; la llamada remota al modelo tardó de 4 a 16 s. Es una medida del ordenador local de Lucía, no del producto desplegado.
- **Señales en vivo (ventana de dos horas, 21/10/2026).** p95 de todas las rutas del backend: 0,95 s; unas 800 peticiones, dos con error 5xx y tres fallos de recuperación (los tres timeouts de la primera recogida). No hay medida anterior con la que comparar.
- **Ventana de coste mixta.** La ventana del 21/10 incluye 2 consultas de GLM-5.2 anteriores a la campaña (0,0063 USD). Se informan por modelo.
- **Infraestructura local.** Las métricas sensibles a la máquina y las que habría que repetir en la infraestructura definitiva están en el [plan](model-reevaluation-plan.md#sensibilidad-a-la-infraestructura-local).

## 6. Gasto

| Concepto | Valor |
| --- | --- |
| Presupuesto autorizado | 1,5 USD |
| Gasto real del gateway (ventana del 21/10/2026) | 0,049456 USD estimados en 75 consultas |
| Gasto real contrastado con OpenRouter | **0,049765 USD** facturados, cobertura del 100 % (75/75) |
| De ese gasto, GLM-5.2 anterior a la campaña | 0,006278 USD (2 consultas) |
| Gasto atribuible a JUP-133 (DeepSeek V4.1 Flash) | **≈ 0,0435 USD** en 73 consultas (campaña de 29, muestra de coste y reintentos), más 0,000068 USD de embeddings estimados |
| Banco de 28 preguntas de JUP-069 | **≈ 0,033 USD** estimados por el gateway (sin contrastar con OpenRouter) |
| Total atribuible a JUP-133 | **≈ 0,077 USD** |
| Muestras sin medir por llegar al tope | Ninguna |

El gasto total es el 5 % del presupuesto autorizado (los 0,0435 USD contrastados con OpenRouter más los 0,033 USD estimados del banco). Incluye la muestra de coste de tres conversaciones, la campaña ligera, los reintentos del producto y el banco de 28 preguntas.

## 7. No se reevaluó

| Medida | Motivo | Cifra de la memoria afectada |
| --- | --- | --- |
| Batería N3/N5 (84 ejecuciones) | Solo se repitió una vez el banco de 28 preguntas (apartado 3), no las 84 ejecuciones. No es cuestión de presupuesto (≈ 0,1 USD con el coste medido). Requiere el ejecutor de la campaña B (con el libro de contabilidad de JUP-123) y la revisión por requisito de unas 78 respuestas | Conformidad de N3/N5: obsoleta; la repetición ligera da una referencia nueva pero no la sustituye |
| Latencia p95 de la campaña | El instrumento de JUP-071 no la mide | Latencia frente al objetivo de 10 s: sin medir |
| Segunda revisora y dos repeticiones más de JUP-071 | Fuera del alcance ligero acordado | Robustez: queda provisional |
| Detector de anomalías, datos y calibración de la recuperación | Independientes del modelo (ver inventario) | Se mantienen |
| Campañas RAG A-D del 17/10 y comparativa del 19/10 | No constan en el repositorio con esas cifras; ver la lista de cifras de la memoria | Sin origen verificable |

## 8. Dónde se ve

El dashboard de evaluación de Grafana (uid `economicon-assistant-evaluation`) cargó las 12 ejecuciones y 647 resultados. Los 18 paneles con consulta SQL respondieron sin error contra el Grafana real; el banco del apartado 3 aparece en el detalle de exactitud, relevancia y latencia con su modelo servido, y las dos ejecuciones de JUP-071 figuran como ejecuciones distintas con su modelo, no comparten serie (0 series comparables) y la vista de cambios las anota con «Cambia: identificador de modelo, proveedor del modelo, cuantizacion, configuracion del gateway». Detalle en la [evidencia](../evidence/JUP-133-validation.md). Las capturas de pantalla de los paneles están pendientes.
