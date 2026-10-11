# Asistente conversacional

Actualizado: 2026-10-11. JUP-035. Trello conserva el alcance, las responsabilidades y el estado oficial; este documento resume decisiones técnicas y evidencia local.

## Alcance y decisiones

Rama `feat/JUP-035-conversational-web-interface`, base `ceb6520`. Paris Arcos lidera la JUP; Víctor tiene asignado el pairing, Alejandro la revisión y Lucía la validación. Esta asignación no acredita que dichas intervenciones ya se hayan realizado.

La interfaz conversacional, el historial canónico de preguntas y respuestas en un JSONB por conversación y los controles de aislamiento, recursos, cancelación y contratos están implementados localmente. La pregunta y respuesta completas se incorporan conjuntamente al finalizar. La memoria mediante resumen está en integración y todavía no tiene aceptación funcional completa. El resumen conserva referencias a las fuentes originales y no sustituye su historial ni habilita cálculos o citas financieras sin evidencia.

Diseño y criterios: [OpenSpec](../../openspec/changes/jup-035-conversational-web-interface/design.md), [extensión de memoria](../../openspec/changes/jup-035-conversational-web-interface/context-compression-extension.md) y [tareas](../../openspec/changes/jup-035-conversational-web-interface/tasks.md).

## Evidencia y límites

El frontal tiene 693 pruebas satisfactorias, comprobación de tipos y compilación. Las suites completas originales del backend y procesador conservaron fallos y omisiones ambientales. Después de las correcciones anteriores al diagnóstico descrito abajo se ejecutaron las suites completas: backend 1283 PASS/52 SKIP y procesador 694 PASS/63 SKIP; Azure 59 PASS y frontal 693 PASS se reutilizaron por identidad. El build raíz pasó sus cuatro tareas. El wrapper de test raíz no se repitió; existe correspondencia documentada con las ejecuciones por componente, sin declarar un PASS del wrapper. El nuevo diagnóstico tiene comprobaciones afectadas separadas; no se afirma haber repetido estas suites completas tras ese cambio.

Las pruebas con simulador acreditan el recorrido local, incluida persistencia de memoria al reiniciar, sin demostrar fidelidad del proveedor real. La prueba nativa del ajuste JSONB ejecutó 13 casos satisfactorios; el caso AMQP omitido y su ampliación retirada no acreditan ni implican un fallo de RabbitMQ. El transporte del chat y su aceptación no dependen de esa ampliación.

La respuesta principal real completó previamente su recorrido y conservó los mensajes originales. Tres solicitudes de resumen posteriores recibieron un error genérico de la pasarela. Una única prueba diagnóstica autorizada, separada del medidor de claves virtuales, obtuvo HTTP 200 que el cliente convirtió en error lógico 400; el detalle técnico menciona DeepInfra y `uniqueItems`. El código instalado confirma esa conversión. No se conserva el cuerpo original ni se afirma haber capturado todos sus metadatos.

Paris aprobó la proyección del esquema el 11/10 a las 02:17 Atlantic/Canary. Está implementada la omisión exclusiva de `uniqueItems` en las dos listas de referencias del esquema enviado al proveedor. El esquema local completo y el rechazo de duplicados por Pydantic y el backend permanecen vigentes. Red, Green y mutación separados acreditaron el cambio: 112 pruebas del procesador y 171 del backend satisfactorias, con omisiones declaradas, y cuatro mutaciones funcionales detectadas. Esta proyección todavía no se ha ejercitado mediante un resumen real corregido.

Los dos intentos principales siguientes recibieron HTTP 200 y cierre SSE del proveedor, pero la aplicación terminó ambos como `failed/provider_error`, sin final completo ni nuevos mensajes visibles. Los 26 mensajes existentes se conservaron. No hubo resumen nuevo ni consumidor; no se presenta HTTP 200 como aceptación. El detalle descartado impide clasificar retrospectivamente esos dos fallos.

Paris aprobó el diagnóstico local el 11/10 a las 11:19 Atlantic/Canary. Se implementó en dos archivos del procesador un evento estructural de hasta 2 KiB con UUID de operación/intento, etapa, clase normalizada, campo/tipo y seis códigos estáticos de reglas conocidas. No registra contenidos, credenciales, valores del candidato ni texto libre de excepciones; no cambia validación, respuesta pública o retries. El cierre determinista mantiene el contexto dentro de la tarea que consume el stream.

Red inicial acreditó la ausencia del diagnóstico; un Red separado reprodujo tres fallos de cierre en la propia tarea consumidora. La corrección pasó 53 pruebas de gateway/ruta privada; los controles afectados de capacidad pasaron 62 casos y otros dos tras corregir exclusivamente su montaje de pruebas. Se conservan los fallos originales de preparación. Tres mutaciones externas de fuga, correlación y clasificación fueron detectadas; el control original pasó 25 casos. Los checkpoints y guards de cada fase permanecen separados; un checkpoint anterior sin mutantes se conserva como NOT_RUN. Estos resultados locales no sustituyen revisión, validación independiente o aceptación real de E5.

## Pendientes

Quedan instalar un resumen válido mediante el proveedor real, demostrar su uso por una respuesta posterior y entregar el panel para pruebas personales. Paris retiró el techo financiero humano el 11/10 para las pruebas reales necesarias y proporcionadas hasta entregar JUP-035. Se conserva el registro de llamadas, consumo, incertidumbre y reservas históricas; la contabilidad no impide ejecutar pruebas autorizadas. Los límites efectivos del proveedor o de recursos compartidos siguen vigentes y cualquier modificación requiere su autorización específica. Los agentes no inician las interacciones reservadas para Paris. El panel personal permanece deshabilitado hasta completar su preparación.

La incidencia de carga de la vista de E4 permanece abierta: un reintento manual recuperó el recorrido, sin causa determinada ni corrección acreditada. Paris autorizó registrar la incidencia y avanzar a E5; no convirtió el fallo en PASS. También se conserva el fallo del control estricto original de actualización de la clave de resumen y la ausencia de su referencia completa en memoria; los controles materiales adicionales permitieron la operación diagnóstica, sin sustituir el control original ni el guard independiente de publicación.

Después son necesarias la revisión y validación independientes, incluida la retirada del uso activo del historial antiguo, doble escritura o fallback; la aprobación humana final y el archivado específicamente autorizado en la misma rama antes de solicitar las revisiones humanas de GitHub. Conservar migración y evidencia histórica legítimas. No hay aprobación de aceptación, publicación o merge por este documento.

## Correccion local del periodo de respuesta - 2026-10-11

El periodo deja de solicitarse al modelo de chat: se deriva de los intervalos UTC
contrastados por el backend y se ensambla antes de validar FinOpsResponse 1.0.
Sin intervalo verificado unico se conserva null. El contrato publico no cambia.

Correccion implementada solamente en checkout aislado; pendiente de integrar y
revisar. Regresion: 82 processor y 55 backend; dos mutaciones detectadas y E5 real
con periodo null aceptado por processor y validacion backend en memoria. No es
validacion de persistencia real ni cierre de JUP-035. Vease
[la evidencia de la correccion](../evidence/jup-035-server-period-correction.md).

## Correccion local del prompt no accionable - 2026-10-11

El recorrido completo aislado detecto una respuesta no_data incompatible con la
prohibicion existente de metricas/recomendaciones. Paris aprobo explicitar esa
regla y ubicar las sugerencias de obtencion de datos en next_actions, sin relajar
validadores. Se actualizo el fingerprint del prompt; no hay cambios de esquema.

83 pruebas processor y 55 backend pasan, con un solo caso nuevo y mutacion del
bundle anterior detectada. La repeticion real desde navegador completo la
operacion en un intento y guardo pregunta y respuesta en CockroachDB. Persistencia
tras reinicio y compresion siguen como comprobaciones separadas pendientes.
No implica revision humana, integracion ni cierre de JUP-035. Vease
[la evidencia del prompt](../evidence/jup-035-non-actionable-prompt-correction.md).

Comprobacion secuencial posterior: reinicio del CockroachDB aislado y de ambos
servicios superado. Historial y operaciones se conservan identicos; navegador
recupera pregunta y respuesta sin nuevas inferencias. No prueba recreacion de
contenedores ni restauracion de copias. La compresion sigue pendiente.

Comprobacion posterior de compresion y reutilizacion (2026-10-11): dos lotes
reales generan un resumen persistido que utiliza la siguiente pregunta enviada
desde navegador. Los 24 mensajes sinteticos originales conservan sus hashes;
28 mensajes al finalizar, sin metricas ni recomendaciones financieras inventadas.
Cobertura parcial: 2 pares resumidos, 8 pendientes y 4 recientes reservados.
Se conserva un intento 429 y una limitacion de calidad: dos frases del resumen
terminan cortadas. No se atribuye una causa aun ni se declara calidad general
superada. Vease [la evidencia de memoria](../evidence/jup-035-conversation-memory-validation.md).
Esta comprobacion local no sustituye revision/validacion independientes.
