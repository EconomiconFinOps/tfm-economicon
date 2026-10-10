JUP: JUP-071
Trello: https://trello.com/c/H0woDubz

## Context

La batería JUP-069 conserva 28 casos con `answer`, `clarify` y `abstain`. Ya cubre coste sin alcance, denominador cero, coste shared sin reparto aprobado, monedas distintas e ingesta incompleta. JUP-071 amplía esa base con variaciones controladas y preguntas sobre tags, sin atribuir a esos escenarios sintéticos datos de un tenant real.

Inspección local del 2026-10-10: `apps/backend/app/main.py` instancia `AssistantService`; su método `answer(user_prompt, retrieved_chunks)` concatena la consulta y hasta tres fragmentos, o devuelve ausencia de contexto. No llama a un modelo generativo. `POST /assistant/conversations/{id}/messages` devuelve el mensaje, metadatos de citas y contexto recuperado, pero no evidencia verificable del modelo o de una llamada de generación. Esta constatación describe la copia inspeccionada; una rama o despliegue posteriores requieren otra comprobación.

La metodología de JUP-070 distingue juicios humanos de reglas numéricas, exige dos personas en los casos críticos, permite una medición provisional con una, conserva fallos de infraestructura y prescribe tres repeticiones finales. Sus prohibiciones por patrones son una cota inferior conocida (RF-070-004, RF-070-006 y RF-070-008). Aquí las prohibiciones semánticas se juzgan explícitamente para no convertir la ausencia de una coincidencia en prueba de robustez.

## Goals / Non-Goals

**Objetivos:** un instrumento reproducible, escenarios contrastables, informes honestos sobre la cobertura de revisión y una línea base ejecutable sin red. La tarjeta busca conocer limitaciones; una respuesta que falla es evidencia útil y no debe corregirse en el registro.

**No objetivos:** integrar el LLM, definir nuevas políticas de reparto o tagging, reemplazar JUP-070, arreglar todos sus hallazgos pendientes, emitir dictámenes por personas ausentes ni declarar robustez generativa sin una ejecución demostrada.

## Decisions

### 1. Batería ampliada sin modificar JUP-069

El fichero propio identifica versión, origen sintético, referencia y hash del banco JUP-069 y fuentes utilizadas. Cada variante tiene identificador estable JUP-071, referencia a un caso base, grupo de perturbación, contexto, pregunta, comportamiento y rúbrica. Al expandirla se incluyen los baselines originales una sola vez, aunque varias variantes compartan base. Se valida que todas las referencias existan, que no haya IDs repetidos y que los hashes sigan coincidiendo. No se reutilizan IDs para preguntas distintas.

Los grupos cubren ausencia o conflicto de tags, costes compartidos sin una base válida, datos parciales y ambigüedades de alcance/unidad/periodo. La rúbrica diferencia aclarar lo que falta, responder una parte sustentada y abstenerse de afirmar lo inaccesible. Debe penalizar tanto inventar una respuesta como abstenerse ante un control que sí tiene datos suficientes.

### 2. Adaptador propio sobre funciones existentes

`tools/assistant-robustness.py` carga el evaluador JUP-070 por su ruta y reutiliza `prompt_text(case)`, `check_number(...)` y `collect_cases(...)`. No altera sus comandos ni su banco por defecto. Son funciones internas, por lo que las pruebas del adaptador deben detectar cambios de firma o de semántica.

Los prompts se generan exclusivamente desde contexto y pregunta; ninguna rúbrica, comportamiento esperado o clave de respuestas forma parte del mensaje enviado. Al reutilizar `prompt_text`, el texto puede tener un envoltorio distinto del preparado por el CLI de JUP-069, pero la variante y su baseline se evalúan con la misma preparación documentada. El hash de la batería permite identificar esa ejecución, y la recogida debe conservar los prompts exactos preparados.

### 3. Dos caminos de ejecución con nivel explícito

La ejecución offline invoca `AssistantService.answer` de la aplicación. La recuperación es un doble fijo declarado, sin embeddings ni acceso a base de datos o red. Prueba cómo se comporta esa plantilla bajo el contexto suministrado y que el instrumento funciona; no mide relevancia del retrieval ni el chat HTTP completo.

La recogida HTTP delega en JUP-070: inicio de sesión, una conversación nueva por caso, envío exacto de su prompt y registro de respuesta, citas, fragmentos, HTTP y tiempo total. No hay reintentos. Credenciales sólo desde entorno y sin persistirlas. Los errores de infraestructura se registran `blocked` con categoría.

La ficha y el informe declaran si la ejecución es plantilla offline con doble, plantilla vía HTTP o un runtime de procedencia pendiente. El endpoint actual no acredita generación real. Un alias configurado manualmente o embeddings LiteLLM no elevan esa evidencia a modelo verificado. La evidencia de JUP-035 debe identificar commit desplegado, configuración real y prueba de que la respuesta recorrió el modelo; hasta tenerla, la conclusión generativa permanece pendiente.

### 4. Juicio humano de semántica, regla para cifras

La hoja de revisión reúne respuesta y contexto recuperado junto a comportamiento, puntos requeridos, prohibiciones y cifras esperadas. Los juicios humanos cubren `behavior`, cada `required` y cada `forbidden`; no se generan automáticamente desde la rúbrica o el resultado esperado. Las comprobaciones numéricas reutilizan etiqueta, alias, unidad y tolerancia de JUP-070 y no aceptan el mero eco del prompt.

Los casos críticos declarados por la batería necesitan dos personas distintas para cada juicio semántico; los baselines se tratan también como críticos. Esta exigencia incluye los casos con cifras y también riesgos semánticos sin cifras, como asignaciones inventadas o uso de datos de demo como datos reales. La identificación normalizada impide contar dos grafías de la misma persona. El modo provisional admite una y lo declara. Si faltan juicios y aún no se conoce ningún incumplimiento, el caso queda `not_run` aun si su respuesta se recogió. Si una comprobación numérica o un juicio recibido ya falla, se conserva `fail`, junto a todos los juicios pendientes y `assessment_complete=false`: la falta de revisión no oculta un fallo comprobado ni convierte el dictamen semántico en completo. Un desacuerdo o criterio incumplido impide el `pass`. Los juicios de dobles unitarios usan identidades de prueba y nunca se presentan como revisión humana del producto.

### 5. Informes con poblaciones y procedencia

Cada caso conserva uno de los cuatro estados del protocolo JUP-069. Las tasas distinguen `pass / total previsto` de `pass / (pass + fail)` e informan también `blocked`, `not_run` y juicios pendientes, evitando que un denominador reducido parezca cobertura completa. El denominador `pass + fail` incluye fallos ya conocidos con semántica todavía pendiente; no debe interpretarse como número de revisiones humanas completas. Se desglosan baselines/variantes, grupos y comportamientos. No se inventa un umbral de aceptación aprobado.

JUP-067/JUP-070 reservan ACC-1 y ACC-2 a casos `answer` y usan ACC-3 para `clarify`/`abstain`. El informe propio mantiene esas poblaciones conceptuales, pero no afirma compatibilidad del JSON con el calculador JUP-067 si usa un esquema propio con juicios adicionales. No se agregan métricas de retrieval ni latencias de etapas que no se han medido. La latencia HTTP observada es la petición total.

Los resultados versionables excluyen texto de preguntas, respuestas, fragmentos y notas privadas. Esos materiales se escriben fuera del repositorio. La ficha conserva versiones, hashes, fecha, commit, modo de ejecución y limitaciones, sin credenciales. La evidencia por criterio enlaza resultados y comandos y separa comprobaciones técnicas de revisión y validación humanas.

### 6. Repetición y dependencia de JUP-035

Una medición final con modelo requiere tres recogidas independientes con la misma batería y configuración, todas publicadas, con los juicios requeridos. No se elige la mejor. La línea base offline es ejecutable ahora y la herramienta HTTP deja preparado el siguiente paso; ningún resultado de la primera completa el pendiente generativo.

## Risks / Trade-offs

- La batería es pequeña, sintética y diseñada; no demuestra robustez universal ni del tenant real. Se publican tamaños y casos concretos.
- La revisión humana falta hasta que las personas emitan sus juicios. Se informa `not_run` mientras no haya un incumplimiento comprobado; un fallo conocido conserva `fail` con la revisión incompleta visible. Nunca se simula un aprobado.
- Los límites del lector de cifras de JUP-070 siguen vigentes (palabras, espacios de millares, asociación temporal o etiquetas). Se documentan y se comprueban con control numérico; la revisión semántica sigue siendo necesaria.
- Las funciones reutilizadas son internas y requieren pruebas de regresión del adaptador.
- Cambiar la aplicación o el corpus tras la medición exige repetir las comprobaciones afectadas; una fecha anterior no se presenta como validación actual.

## Validation Strategy

Pruebas sin red externa: estructura y referencias rotas de la batería, hashes alterados, baselines únicos, ausencia de rúbrica en prompts, llamada al servicio real en modo offline, fidelidad de la recogida y fallos HTTP mediante dobles, separación de modos, cada estado y denominador, ausencia de juicios y doble revisión, desacuerdo, cifras con unidad/etiqueta/tolerancia, y ausencia de texto privado en la salida versionable.

La evidencia registra los comandos realmente ejecutados y lo pendiente. OpenSpec y trazabilidad JUP se validan antes de la contribución; la revisión y validación de PR pertenecen a las personas registradas en Trello y no se sustituyen por estas pruebas.
