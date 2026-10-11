# JUP-035 — delta borrador sujeto a aprobación

**APROBACIÓN HUMANA DEL DELTA JSONB — Paris vía Project Manager 10/10/2026 09:15:41 (Atlantic/Canary): «si hazlo».** Aprobado `jsonb-history-design.md` entregado03:20:56: esquema por conversación, final conjunto pregunta/respuesta, alternativas sin duplicar pregunta, migración003/backfill conservador y tabla histórica sin rutas activas. Autoriza adaptación Red→Green→mutación y pruebas afectadas; ventana SIN escritores y migración únicamente LOCAL AISLADA. Sustituye el estado pendiente de ejecución de esta misma propuesta; no acredita implementación ni aceptación. Conservar IDs/citas/metadata/precisión, operaciones separadas y fuente JSONB única; retirada activa exigida a Revisor, Validador y cierre PM. Presupuesto compartido0,20EUR desde02:54:46 permanece, readiness/cota/reserva antes de gasto. No producción/remoto/Git/publicación/archivo/destrucción. Versión aprobada exacta y hashes conservados externamente por TL.


**CAMBIO VIGENTE DE HISTORIAL — Paris vía PM 10/10/2026 03:01:32, con control independiente añadido03:03:01 (Atlantic/Canary).** Historial canónico: un JSONB por conversación; pregunta y respuesta completa se añaden juntas al finalizar, sin cambios al enviar ni por deltas. [Contrato concreto y migración propuesta](../../jsonb-history-design.md). Sustituye el mecanismo de filas `messages`, su desempate temporal y la ausencia de backfill del diseño anterior; originales/decisiones históricas conservados. Preferencia JSONB aprobada; esquema003/backfill y reescritura material pendientes de validación/despacho, SIN implementación de este delta. Los demás contratos funcionales permanecen. Nueva autorización PM02:54:46 permite pruebas reales necesarias por ruta aprobada hasta0,20EUR acumulados compartidos, con coste acotado/contador antes de llamar; sustituye únicamente la prohibición de gasto anterior. No amplía Git/publicación/remoto/archivo.


**APROBACIÓN HUMANA PRE-CODE — Paris, vía Project Manager09/10/2026 23:23:27 (Atlantic/Canary): «pues aprobado».** Aprobado el diseño consolidado entregado23:17:59 y sus contratos/spec/tareas, incluidas esperas acumuladas, persistencia, seguridad, compresión LLM, concurrencia y UI. Autoriza desarrollo local y dependencias/migración definidas SOLO en entorno aislado de pruebas. Las menciones anteriores de propuestas/pre-code pendiente quedan como antecedentes fechados sustituidos por esta aprobación; no convierten hechos externos no confirmados en integrados ni resultados NOT_RUN en PASS. Sigue propuesta configurable/no medida la capacidad8, ahora autorizada para implementación/prueba en ese alcance. No autoriza nuevas inferencias con coste, publicación, gestión Git, archivo o merge; conservar guards y Red→Green→mutación separados. Versión exacta aprobada y SHA256 conservados fuera del repositorio por TL.


No es aprobación pre-code completa ni conducta implementada. Las elecciones humanas aprobadas están fechadas; escenarios futuros NOT_RUN.

## ADDED Requirements

### Requirement: Panel conversacional integrado

La interfaz SHALL ofrecer un panel derecho fijo v1 con control abierto–cerrado,
estilo del shell, acceso por teclado y adaptación responsive, preservando sesión,
tenant y conversación. El preview de escritorio SHALL reservar aproximadamente la mitad derecha (~50%
del ancho de ventana) al chat y mantener la app visible en la otra mitad, con
estilo existente y datos sintéticos, conforme a Paris vía PM15:25:33/TL15:25:57
del 09/10/2026. Atajo, animación y móvil requieren diseño aprobado.

#### Scenario: Panel

- **WHEN** un usuario autenticado abre o cierra el panel
- **THEN** el control comunica su estado, gestiona foco y conserva el scope autorizado sin cambiar la ruta funcional

### Requirement: Lectura y seguimiento del historial

El panel SHALL preservar la lectura cuando el usuario se desplaza hacia mensajes
anteriores y ofrecer volver al final para reanudar seguimiento. La política de
envío propio/carga y adaptación de altura se concretará en el spike aprobado;
streaming real es obligatorio por Paris vía PM15:47:28/TL15:48:23 del
09/10/2026; comportamiento UI concreto queda en spike posterior.

#### Scenario: Lectura y seguimiento

- **WHEN** llegan mensajes o cambia la altura de citas mientras el usuario lee arriba
- **THEN** el panel no lo arrastra al final y permite volver abajo de forma explícita, conservando scope al cambiar conversación

### Requirement: Respuesta natural real y evidenciada

El sistema SHALL responder preguntas con la vertical 020–026, gateway023,
guardrails024 y retrieval022, conservando citas025 y contrato de respuesta
aprobado; SHALL entregar texto generado incrementalmente desde gateway a UI
mediante processor y backend, antes de terminar la generación; SHALL reconocer
evidencia insuficiente sin inventar cifras.

#### Scenario: Respuesta real

- **WHEN** una pregunta autorizada dispone de evidencia relevante
- **THEN** un modelo real mediante gateway responde dentro del contrato validado y la plantilla o mock no cuentan como aceptación

#### Scenario: Sin evidencia

- **WHEN** no existe evidencia suficiente
- **THEN** se declara no_data o insufficient_data sin hechos financieros inventados

#### Scenario: Evidencia

- **WHEN** una respuesta afirma hechos basados en fuentes
- **THEN** las citas conservan origen y contenido persistido del tenant autorizado

#### Scenario: Fuentes ajenas

- **WHEN** una salida refiere evidencia desconocida o de otro tenant
- **THEN** el backend rechaza esas referencias al validar el final, antes de guardar la respuesta como confirmada o presentar sus citas como verificadas; la evidencia de entrada se autoriza antes de generar y los fragmentos de texto visibles siguen siendo provisionales

### Requirement: Streaming real y cierre verificable

Por instrucción humana de Paris vía PM09/10/2026 15:47:28, el sistema SHALL
transmitir incrementos de generación reales gateway→generador processor→backend→UI
con autorización tenant Y usuario. SHALL distinguir texto provisional, resultado
final validado/persistido, cancelación y fallo/interrupción. No se atribuye esta
instrucción a una mención de Trello no verificada.

#### Scenario: Streaming real

- **WHEN** el gateway está generando una respuesta autorizada
- **THEN** la UI recibe al menos un incremento de texto generado antes del fin del productor, sin esperar el cuerpo completo ni temporizar una respuesta ya terminada

#### Scenario: Cancelación streaming

- **WHEN** el propietario pulsa Detener durante una generación
- **THEN** el servidor intenta el cierre terminal único, confirma solo tras commit y propaga cierre upstream best effort sin garantizar cese de facturación

#### Scenario: Ocultación y cambio de identidad

- **WHEN** se oculta el panel, se pierde el lector o cambia sesión/tenant/usuario
- **THEN** ocultar o desconectar no envía Stop ni cancela implícitamente el productor; el cambio de identidad limpia estado/listeners y descarta callbacks antiguos sin mostrar datos del scope anterior

#### Scenario: Error tras headers

- **WHEN** un stream HTTP 200 emite error o termina sin evento final válido
- **THEN** se presenta error/interrupción saneado y el borrador no se considera respuesta final aceptada

#### Scenario: Final inválido

- **WHEN** al terminar la generación el objeto o sus referencias/citas no pasan validación completa y pertenencia
- **THEN** se reconcilia el borrador con error visible y no se persiste como respuesta confirmada; mostrar provisional antes del final no equivale a validarlo por token

### Requirement: Operación durable y pareja completa final

Por instrucciones Paris PM21:33:08 y aprobación PM21:46:22, el sistema SHALL separar reserva/idempotencia operacional del historial completo. SHALL conservar pregunta recuperable y contador/fences por operación; pregunta y respuesta completa SHALL persistirse juntas atómicamente al finalizar antes de confirmar completed. Reintentos SHALL reutilizar pregunta lógica y nunca concatenar fragmentos. El registro operacional separado permanece válido. La elección posterior PM10/10/2026 03:01:32 establece un documento JSONB por conversación como historial canónico; esquema003/backfill concretos están propuestos y pendientes de ejecución autorizada. RabbitMQ SHALL permanecer solo ingesta.

#### Scenario: Rollback de pareja

- **WHEN** falla la inserción de respuesta o el cierre de operación en la transacción final
- **THEN** no se publica pareja incompleta; la solicitud recuperable permanece y el error SQL no dispara otra inferencia

#### Scenario: Recuperación operacional

- **WHEN** cae el proceso con un intento reservado o con commit final ambiguo
- **THEN** se resuelve estado/contador mediante lectura y fencing, sin redispatch del mismo intento ni regeneración de completed; parcial RAM puede perderse, pregunta operacional se conserva

#### Scenario: Retry de solicitud antigua

- **WHEN** se reintenta una operación fallida cuya pregunta ya fue guardada por otra operación
- **THEN** la transacción final verifica pertenencia y contenido, reutiliza la pregunta y guarda otra respuesta completa sin duplicar user

#### Scenario: Stop frente al final

- **WHEN** Stop autorizado compite con commit final o programación de siguiente intento
- **THEN** un CAS/commit válido gana; Stop confirmado impide siguiente intento y final tardío, completed previo permanece

#### Scenario: Idempotencia y exclusión

- **WHEN** se repite clave/payload o se envía otra intención en una conversación abierta
- **THEN** la repetida observa misma operación sin productor adicional, distinto payload409conflict y otra intención409busy, sin segunda pregunta

### Requirement: Tres reintentos funcionales adicionales

Por Paris PM21:33:08/21:46:22, el backend SHALL permitir inicial más tres retries automáticos, máximo cuatro intentos por operación,120s por intento y480s activos. Transporte/gateway SHALL mantener retries0 para no multiplicarlos. Interrupciones transitorias SHALL programar otro intento si queda; errores permanentes, Stop voluntario y desconexión de lector SHALL quedar diferenciados. Por decisión humana PM23:05:12, cada solicitud SHALL disponer de dos presupuestos independientes acumulados:120s de espera automática local y120s de espera automática del proveedor. Retry/resume/recuperación de la misma operación SHALL conservar sus consumidos y contador, sin reinicio. El máximo240s de esperas automáticas SHALL distinguirse del tiempo total hasta respuesta y del presupuesto120s de ejecución por intento. Retry-After SHALL respetarse: si excede saldo proveedor restante, pausa visible conservando solicitud/contador/retry_at y reanudación explícita solo desde fecha mínima, sin renovar presupuestos ni anticipar envío.

#### Scenario: Cuatro interrupciones

- **WHEN** cuatro intentos de una operación fallan transitoriamente
- **THEN** no se ejecuta un quinto, cada intento usa ID/buffer propios, pregunta única y error final saneado

#### Scenario: Espera y cancelación

- **WHEN** el proveedor indica Retry-After o el usuario pulsa Stop durante espera
- **THEN** la espera automática solo se programa si cabe en el saldo proveedor acumulado restante; en otro caso hay pausa visible y resume explícito solo≥retry_at, sin reset de saldos/contador; Stop confirmado cancela programación y nunca se envía antes de fecha permitida

### Requirement: Estados de operación comprensibles

La interfaz SHALL distinguir vacío, carga, error, datos insuficientes y fallo
de proveedor y ofrecer información accesible sin revelar detalles sensibles.

#### Scenario: Estados

- **WHEN** cambia el estado de una conversación
- **THEN** se representa y anuncia de forma accesible sin atribuir datos reales a fixtures

#### Scenario: Error proveedor

- **WHEN** hay error permanente o se agotan los cuatro intentos por fallo transitorio
- **THEN** se muestra error final saneado y acción comprensible sin respuesta inventada; desconexión del lector no agota intentos

### Requirement: Historial persistente y privado

El sistema SHALL preservar mensajes y metadata JSONB tras recarga y restringir
lectura/escritura a tenant y usuario propietarios, conservando controles de sesión.

#### Scenario: Historial

- **WHEN** el propietario crea una conversación, envía un mensaje y recarga con Cockroach real
- **THEN** contenido y metadata/citas se recuperan sin doble decodificación JSONB

#### Scenario: Historial ajeno

- **WHEN** otro tenant o un usuario distinto del mismo tenant solicita una conversación ajena
- **THEN** la operación devuelve 404 sin revelar sus mensajes o metadata

#### Scenario: Identidad

- **WHEN** cambia tenant, identidad o sesión mientras una respuesta está en curso
- **THEN** ningún mensaje ni estado tardío del contexto anterior se muestra en el nuevo

### Requirement: Contexto de pantalla limitado y validado

Conforme Paris vía PM09/10/2026 19:42:02, UI Context Awareness SHALL capturar
una instantánea JSON YA preparada al recibir/cambiar datos de pantalla activa, filtros,
periodo, moneda, totales/desglose, fechas/completitud; SHALL excluir credenciales
y datos internos innecesarios. El servidor SHALL verificar identidad/tenant/ownership
y schema, tratar la captura como datos no confiables, conservarla por intento
y separar citas de pantalla declarada de evidencia financiera verificada.
SHALL permanecer separado del compresor QA mínimo de JUP-035 y de memoria avanzada JUP-041; el modelo no autoriza ámbitos.

#### Scenario: Contexto UI

- **WHEN** el cliente envía pantalla y filtros manipulados, caducados o de ámbito ajeno
- **THEN** el servidor valida su schema y permisos y rechaza o solicita aclaración conforme al contrato sin consultar datos ajenos

#### Scenario: Captura y discrepancia

- **WHEN** un envío copia la versión preparada de pantalla y su contraste servidor difiere o no está disponible
- **THEN** la captura completa se conserva bajo su propietario y la respuesta distingue declaración de pantalla, demo y evidencia propia verificada sin inventar cifras o certeza temporal

#### Scenario: Captura e idempotencia

- **WHEN** se repite la misma clave con captura idéntica o cambiada
- **THEN** idéntica recupera el intento sin regenerar; cambiada produce conflict; retry humano usa captura y clave nuevas sobre la pregunta existente

### Requirement: Prompts versionados exclusivamente en servidor

Por aprobación Paris vía PM19:42:02, el sistema SHALL cargar instrucciones estables
desde recursos versionados Git en servidor, reutilizar reglas JUP-024 y registrar
la versión por respuesta. Historial/evidencias/captura SHALL permanecer como datos
no confiables separados de instrucciones. La caché SHALL ser opcional y no sustituir
el contexto necesario de cada petición ni la base de datos.

#### Scenario: Versión y datos hostiles

- **WHEN** datos variables intentan cambiar instrucciones o el recurso requerido no coincide con la versión validada
- **THEN** datos cliente no seleccionan roles/prompts ni se convierten en autoridad; el runtime no infiere con recursos inválidos y no confirma salida que incumpla los guards

#### Scenario: Caché no disponible

- **WHEN** no hay hit o no se dispone de usage.cached_tokens
- **THEN** la corrección conserva el contexto completo necesario y no genera reintentos para calentar caché; campo ausente no se presenta como cero

### Requirement: Capacidad de costes explícita

La respuesta SHALL consultar costes084/036/037 únicamente mediante contratos
disponibles y autorizados, conservando periodo UTC, ámbito, moneda y procedencia.

#### Scenario: Costes disponibles

- **WHEN** una pregunta solicita una dimensión de coste que aún no está integrada
- **THEN** se declara la limitación sin fingir disponibilidad ni calcular con datos sintéticos como reales

### Requirement: Compresión mínima del diálogo con originales preservados

Por ampliación Paris vía PM09/10/2026 21:07:33, la propuesta JUP-035 SHALL preparar diálogo QA resumido y turnos recientes dentro del presupuesto compatible. El compresor SHALL generar resumen mediante llamada LLM por actualización necesaria solo de preguntas/respuestas completas, preservar originales/referencias, persistir fuentes/revisión y congelar contexto por intento. Controles locales no sustituyen la llamada LLM. Pantalla, metadata, evidencia y anexos SHALL permanecer fuera de su entrada. Defaults y nueva columna son propuestas pendientes de aprobación pre-code, no ejecución autorizada.

#### Scenario: Preparación y omisiones

- **WHEN** el diálogo supera el umbral propuesto o el espacio residual de la petición
- **THEN** se prepara un resumen best effort mediante LLM, fuentes trazables y recientes completos que caben y cobertura/omisiones explícitas, conservando todos los originales y el snapshot fuera del compresor

#### Scenario: Resumen fallido o anticuado

- **WHEN** falla la preparación, compiten dos candidatos o un retry completed cambia una fuente cubierta
- **THEN** CAS y hashes impiden instalar/usar un resumen obsoleto; el chat usa el previo válido o recientes que caben con limitación explícita, sin bloquear respuesta principal ni sustituirlo por resumen local; nuevas llamadas solo por actualización necesaria

### Requirement: Conversaciones privadas concurrentes

Por corrección Paris PM21:12:15, listado, lectura, envío, retry, estado, Stop, stream, reenganche, evidencias, contexto y resumen SHALL exigir tenant + propietario + conversación. Exclusión de generación SHALL ser por conversación. Capacidad global configurable SHALL permitir el objetivo de cinco chats privados concurrentes; límite8 es propuesta operativa, no capacidad upstream comprobada.

#### Scenario: Cinco usuarios del mismo tenant

- **WHEN** cinco usuarios envían simultáneamente en sus cinco conversaciones privadas
- **THEN** cinco productores pueden estar activos antes de finalizar ninguno; Stop/reenganche de uno no afecta los otros; un segundo envío del mismo chat continúa sujeto a exclusión

#### Scenario: Cruce de identidad en recursos

- **WHEN** un usuario solicita cualquier recurso o stream de otro usuario del mismo tenant o de otro tenant
- **THEN** no accede a mensajes, estados, buffers, snapshots, evidencia ni resúmenes ajenos y ninguna invocación amplía su ámbito

### Requirement: Snapshot por pestaña y presupuesto explícito

Por aprobación Paris PM21:15:55, el sistema SHALL mantener JSON específico con datos cargados de la pestaña, actualizado ante cambio de filtros/periodo/datos y Send SHALL copiar/congelar versión preparada sin construir/refetch ni diagnóstico. SHALL conservar captura íntegra hasta1MiB, aplicar el techo8192 tokens variables con conteo/capacidad compatibles, separar proyección y original y declarar excesos/omisiones sin truncado silencioso. El reparto es propuesta revisable; caché no sustituye transmisión de contexto.

#### Scenario: Cambio de pantalla y exceso

- **WHEN** cambian datos/filtros antes de enviar o la captura/presupuesto excede el límite
- **THEN** el intento toma la versión actual; captura sobre1MiB se rechaza explícitamente antes de reserva, proyección limitada declara omisiones y no descarta silenciosamente información indispensable

### Requirement: Canal privado autenticado en un DockerServer

Por elección Paris PM21:17:13, backend→processor SHALL usar red privada dedicada y autenticación/integridad/replay con secret exclusivo, processor sin host port y listener chat solo en interfaz privada. HTTP interno queda permitido únicamente en un DockerServer con esa topología; HTTPS externo permanece y entre hosts requiere reevaluación. Red privada y HMAC no proporcionan confidencialidad.

#### Scenario: Acceso por interfaz equivocada

- **WHEN** se intenta acceder al chat por host, otra red/interfaz o sin autenticación válida
- **THEN** el endpoint no queda expuesto en dichas interfaces y la llamada no autorizada no ejecuta generación, conservando conectividad legítima de ingesta, DB y gateway

### Requirement: Prefijo estable de resumen como datos

Por Paris PM21:33:08, resumen vigente SHALL permanecer como user no confiable después de system estable y antes de pantalla/pregunta/variables; SHA/revisión/versiones fijan bytes usados. Contexto necesario SHALL reenviarse en cada intento, sin promesa de hit/memoria remota ni promoción de resumen a instrucciones.

#### Scenario: Cambio de resumen y cache miss

- **WHEN** cambia revisión del resumen o no hay hit de caché
- **THEN** nuevo prefijo refleja versión autorizada para nueva operación; intentos ya congelados no cambian, contexto requerido se transmite y no se llama para calentar caché

### Requirement: Conteo offline fijado

Por aprobación Paris PM21:54:52, diseño SHALL usar tokenizers0.22.1 y artefacto ZAI de revisión/hash fijados en contrato de prompts, sin pesos/código remoto/fallback tokenizador ajeno como equivalente. Conteo contractual del límite8192 SHALL distinguirse de uso/facturación reportados; instalación/build/carga y prueba focal futuros tras pre-code.

#### Scenario: Artefacto o recuento inválido

- **WHEN** falta/cambia hash del tokenizer o el contexto contractual supera presupuesto
- **THEN** se cierra admisión o declara insuficiencia antes de upstream, sin equivalencia inventada bytes/tokens ni truncado silencioso de información esencial

### Requirement: Admisión visible con presupuestos acumulados

Por decisión humana PM23:05:12, una solicitud válida sin capacidad local inmediata SHALL conservarse waiting, con espera visible/cancelable, y SHALL arrancar automáticamente cuando haya plaza dentro de su saldo local acumulado120s. Esperar capacidad SHALL no consumir intento del proveedor ni crear active sin claim. Al agotar saldo local SHALL pasar a paused visible, conservar pregunta/operación y no reencolarse automáticamente. Resume explícito SHALL no renovar ningún presupuesto o contador; con saldo local agotado SHALL requerir plaza inmediata, permaneciendo paused si falta. No se promete plazo total de cuatro minutos ni capacidad medida8.

#### Scenario: Primera admisión sin plaza

- **WHEN** no hay capacidad inmediata para una solicitud válida
- **THEN** se reserva waiting sin intento consumido, visible/cancelable, y al obtener plaza dentro del saldo local se registra el claim y empieza automáticamente

#### Scenario: Agotamiento local acumulado

- **WHEN** la misma operación acumula120s de espera local entre admisión y reintentos
- **THEN** queda paused con pregunta conservada, sin bucle automático; resume explícito conserva saldos/contador y solo arranca si hay plaza inmediata

#### Scenario: Retry-After supera saldo proveedor

- **WHEN** quedan30s de espera proveedor automática y Retry-After exige60s
- **THEN** no hay envío anticipado ni nueva bolsa120s: pausa visible con retry_at, reanudación explícita solo desde esa fecha y saldo/counter intactos

#### Scenario: Reanudación o caída entre esperas

- **WHEN** una operación con consumidos locales90s y proveedor80s se recupera o reanuda
- **THEN** conserva saldos locales30s y proveedor40s, sin reset por nuevo intento, sin contar dos veces tiempo solapado y sin usar pausas humanas como renovación de espera automática

### Requirement: Documento canónico JSONB único por conversación

Por decisión Paris PM10/10/2026 03:01:32 el sistema SHALL mantener un documento JSONB por conversación como única fuente activa de historial completo, identificado por tenant/usuario/conversación, versionado y con revisión/ordinal explícitos. SHALL conservar el contrato público de mensajes, IDs, textos, metadata y citas. SHALL validar identidad y estructura bajo autorización de propietario; un documento inválido o no migrado SHALL fallar cerrado sin fallback por filas. Operaciones durables SHALL permanecer separadas del historial.

#### Scenario: Envío y deltas no modifican historial

- **WHEN** se envía una pregunta, espera o recibe contenido incremental sin final completo validado
- **THEN** el documento canónico permanece idéntico y la solicitud recuperable reside sólo en el registro operacional

#### Scenario: Turno final atómico exactamente una vez

- **WHEN** una operación vigente finaliza con respuesta completa validada
- **THEN** una sola transacción agrega pregunta y respuesta completas con ordinals consecutivos y confirma completed; rollback o Stop ganador no deja contenido parcial, y observar completed otra vez no agrega mensajes ni incrementa revisión

#### Scenario: Respuesta alternativa de una pregunta lógica

- **WHEN** se completa A, se completa B y después un retry humano de A
- **THEN** existen dos preguntas y tres respuestas completas con orden explícito, la pregunta A no se duplica y su latest answer se elige por ordinal; lectura, recuperación y contexto usan sólo el documento

#### Scenario: Migración legacy sin pérdida ni doble autoridad

- **WHEN** se ejecuta la transición aislada sin escritores y se reinicia tras un corte de backfill
- **THEN** IDs, textos, metadata, citas, autores nullable y timestamps/precisión legítimos se preservan y contrastan sin duplicación; datos inconsistentes bloquean sin destrucción; la versión sólo se registra tras completitud y los datos originales retenidos no tienen ruta productiva paralela

#### Scenario: Resumen derivado desde el documento

- **WHEN** lectura, retry, recuperación o compresión resuelven el historial y las QA completas
- **THEN** consultan el documento único; un retry invalida el derivado afectado en el mismo commit y reconstruye desde originales, conservando legacy no vinculado visible y excluido de QA/resumen sin adivinar parejas

### Requirement: Verificación independiente de retirada activa

Por instrucción Paris PM10/10/2026 03:03:01 la revisión y validación SHALL aportar evidencia específica de retirada del mecanismo activo sustituido: persistencia, lectores/escritores alternativos, helpers/config/contratos/tests/docs obsoletos y ausencia de doble fuente. SHALL distinguir soporte de migración/compatibilidad estrictamente necesario y evidencia histórica, sin borrar datos para cumplir limpieza. Revisor/Validador SHALL permanecer independientes y sin escrituras bajo guard PM.

#### Scenario: Inspección y ejecución de fuente única

- **WHEN** Revisor inspecciona las rutas activas y Validador ejecuta flujos documentados y contrasta DB
- **THEN** sus informes muestran fuente JSONB, ausencia de modificación al enviar/deltas, cierre atómico una vez, lectura/retry/recuperación/compresión y transición legacy sin escritura paralela; cada resto necesario tiene motivo y carece de ruta alternativa activa


### Requirement: Proyección compatible del esquema de resumen con autoridad local íntegra

Corrección propuesta el 11/10/2026, pendiente de decisión humana previa al código. El sistema SHALL enviar al proveedor una copia de `SummaryResponse` que omita exclusivamente `uniqueItems` en las listas `question_refs` y `answer_refs` de `SummaryTopic`, conservando todos los demás campos y restricciones, json_schema y strict true. SHALL mantener el esquema canónico v2 completo y rechazar referencias duplicadas tanto mediante Pydantic en el processor como mediante la validación local del backend. SHALL distinguir el hash del esquema local del hash de la proyección; no alterar payload, manifest, autorización o artefactos persistidos por esta adaptación.

#### Scenario: Petición proyectada sin alterar el contrato local

- **WHEN** se construye la petición de un lote de resumen autorizado
- **THEN** el esquema enviado carece exactamente de los dos flags uniqueItems y conserva strict true y el resto íntegro; el esquema local mantiene ambos flags y su hash `72404e66533f03268bf53727e7ed01cad00a71c31ad483f823ee4c3c8e06783e`, distinto del hash de proyección `ec92ca50508a0fe0b94ef08ef81c3b1f330973d5b9266d22a53c9b1ca4b8e5ac`

#### Scenario: Referencias repetidas devueltas por el proveedor

- **WHEN** un candidato contiene una referencia repetida en question_refs o answer_refs
- **THEN** processor y backend lo rechazan localmente sin deduplicarlo ni instalarlo, conservan las QA originales y el anterior válido y no hacen otra inferencia automática

#### Scenario: Cambio de transporte sin renovación de memoria ni presupuesto

- **WHEN** cambia únicamente la proyección enviada al proveedor y se prueba la corrección en un entorno aislado reiniciado
- **THEN** los artefactos compatibles continúan sujetos al esquema completo y a las mismas fuentes y epoch; el startup no despacha, un nuevo evento autorizado precede la evaluación y se preservan contadores, reservas, límites y rechazos previos sin afirmar cachehit ni aceptación semántica a partir de simulación

### Requirement: Periodo de respuesta gestionado por el servidor

El sistema SHALL excluir scope.period del esquema solicitado al modelo y conservarlo en FinOpsResponse 1.0. El backend SHALL fijar el periodo desde los registros de costes contrastados por el servidor: un unico intervalo UTC valido, o null si no existe un intervalo inequivoco. El processor SHALL ensamblarlo desde el contexto autenticado antes de validar el contrato completo; el backend SHALL comprobar la correspondencia antes de persistir.

#### Scenario: Pregunta sin periodo financiero verificado

- **WHEN** el contexto no contiene un periodo contrastado o contiene varios periodos distintos
- **THEN** la respuesta final contiene scope.period null y el modelo no puede generar ese campo

#### Scenario: Intervalo verificado unico

- **WHEN** los registros contrastados contienen un unico intervalo UTC con inicio anterior al fin
- **THEN** el servidor conserva exactamente ese intervalo en el contexto congelado y en la respuesta final

#### Scenario: Intento de sustituir el periodo del servidor

- **WHEN** el proveedor devuelve scope.period o el resultado recibido por el backend difiere del periodo congelado
- **THEN** se rechaza la respuesta sin corregir fechas ni persistir el resultado; las fechas del navegador no sustituyen la verificacion del servidor

### Requirement: Instruccion explicita para respuestas no accionables

El prompt de chat SHALL indicar que los estados no_data, insufficient_data, unsupported, refused y error requieren metrics y recommendations vacios. Las sugerencias no financieras para conseguir informacion SHALL expresarse en next_actions. Los validadores existentes SHALL permanecer activos sin reparacion silenciosa del candidato.

#### Scenario: Pantalla sin costes disponibles

- **WHEN** el proveedor responde no_data ante una pantalla vacia
- **THEN** devuelve metrics y recommendations como listas vacias y puede explicar como obtener informacion en next_actions; una respuesta que incumpla esta regla sigue siendo rechazada sin persistir una respuesta parcial

### Requirement: Contexto ampliado con limites conjuntos

El sistema SHALL usar presupuestos configurables de entrada, hasta el contexto
1048576 del modelo, con reservas de instrucciones, esquema, margen y salida800.
Backend y processor SHALL verificar el mismo descriptor de presupuesto. SHALL
conservar limites privados de 2097152 bytes para chat y 1048576 para resumen,
medidos sobre el sobre completo, sin convertir bytes a tokens por aproximacion.
El chat SHALL conservar el mayor sufijo de pares completos que cabe, sin limite
fijo de cuatro y sin duplicar los pares cubiertos por memoria valida.

#### Scenario: Historial mayor que los techos anteriores

- **WHEN** chat supera8192 tokens o un lote de resumen supera4096 y cabe en ambos presupuestos completos
- **THEN** se admite sin truncar mensajes ni evidencia esencial; los originales y validadores de citas, negaciones y periodos permanecen intactos

#### Scenario: Un limite conjunto no permite el siguiente par

- **WHEN** agregar un par completo supera tokens o bytes del sobre con las reservas
- **THEN** se conserva el mayor conjunto que cabe o se devuelve limite explicito si no cabe un par; no se afirma que un millon de tokens quepa en1MiB

### Requirement: Compresion durable excluyente y recuperable

El sistema SHALL persistir dialogue_compaction JSONB nullable mediante migracion
aditiva nueva. Final y pending SHALL confirmarse atomicamente. La admision SHALL
rechazar nuevos envios ocupados por tenant, usuario y conversacion con409
conversation_compacting, antes de trabajo caro y dentro de reserve, contrastando
revision de historial y hash de resumen del contexto. SHALL mantener disponibles
repeticiones idempotentes y lecturas. Un CAS de control SHALL excluir propietarios
obsoletos; la instalacion valida y la transicion del control SHALL ser atomicas.

#### Scenario: Carrera de envios e instalacion

- **WHEN** dos clientes envian durante compresion o usan contexto anterior a una instalacion
- **THEN** no se crea otra operacion ni se gasta inferencia con memoria obsoleta, y otra conversacion sigue disponible

#### Scenario: Reinicio con ejecucion remota incierta

- **WHEN** se recupera un trabajo running o reconciling tras reinicio o lease vencido
- **THEN** se consulta o cancela el mismo job, sin duplicar dispatch ni liberar por timeout; se muestra recuperacion pendiente hasta confirmar settlement

#### Scenario: Error y recuperacion explicita

- **WHEN** falla la compresion de forma confirmada
- **THEN** se conserva historial y ultimo resumen valido, se expone causa saneada y reintento explicito; un propietario antiguo no puede instalar ni liberar otro control

#### Scenario: Borrador durante compresion

- **WHEN** se abre, recarga o finaliza un chat con memoria ocupada
- **THEN** el frontend recupera el estado del servidor, conserva borrador editable y bloquea Enter y boton hasta instalar la memoria; error y recuperacion son visibles
