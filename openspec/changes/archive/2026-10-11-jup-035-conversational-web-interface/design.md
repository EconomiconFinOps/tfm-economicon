# JUP-035 — Diseño consolidado para revisión de Paris

**APROBACIÓN HUMANA DEL DELTA JSONB — Paris vía Project Manager 10/10/2026 09:15:41 (Atlantic/Canary): «si hazlo».** Aprobado `jsonb-history-design.md` entregado03:20:56: esquema por conversación, final conjunto pregunta/respuesta, alternativas sin duplicar pregunta, migración003/backfill conservador y tabla histórica sin rutas activas. Autoriza adaptación Red→Green→mutación y pruebas afectadas; ventana SIN escritores y migración únicamente LOCAL AISLADA. Sustituye el estado pendiente de ejecución de esta misma propuesta; no acredita implementación ni aceptación. Conservar IDs/citas/metadata/precisión, operaciones separadas y fuente JSONB única; retirada activa exigida a Revisor, Validador y cierre PM. Presupuesto compartido0,20EUR desde02:54:46 permanece, readiness/cota/reserva antes de gasto. No producción/remoto/Git/publicación/archivo/destrucción. Versión aprobada exacta y hashes conservados externamente por TL.


**CAMBIO VIGENTE DE HISTORIAL — Paris vía PM 10/10/2026 03:01:32, con control independiente añadido03:03:01 (Atlantic/Canary).** Historial canónico: un JSONB por conversación; pregunta y respuesta completa se añaden juntas al finalizar, sin cambios al enviar ni por deltas. [Contrato concreto y migración propuesta](jsonb-history-design.md). Sustituye el mecanismo de filas `messages`, su desempate temporal y la ausencia de backfill del diseño anterior; originales/decisiones históricas conservados. Preferencia JSONB aprobada; esquema003/backfill y reescritura material pendientes de validación/despacho, SIN implementación de este delta. Los demás contratos funcionales permanecen. Nueva autorización PM02:54:46 permite pruebas reales necesarias por ruta aprobada hasta0,20EUR acumulados compartidos, con coste acotado/contador antes de llamar; sustituye únicamente la prohibición de gasto anterior. No amplía Git/publicación/remoto/archivo.


**APROBACIÓN HUMANA PRE-CODE — Paris, vía Project Manager09/10/2026 23:23:27 (Atlantic/Canary): «pues aprobado».** Aprobado el diseño consolidado entregado23:17:59 y sus contratos/spec/tareas, incluidas esperas acumuladas, persistencia, seguridad, compresión LLM, concurrencia y UI. Autoriza desarrollo local y dependencias/migración definidas SOLO en entorno aislado de pruebas. Las menciones anteriores de propuestas/pre-code pendiente quedan como antecedentes fechados sustituidos por esta aprobación; no convierten hechos externos no confirmados en integrados ni resultados NOT_RUN en PASS. Sigue propuesta configurable/no medida la capacidad8, ahora autorizada para implementación/prueba en ese alcance. No autoriza nuevas inferencias con coste, publicación, gestión Git, archivo o merge; conservar guards y Red→Green→mutación separados. Versión exacta aprobada y SHA256 conservados fuera del repositorio por TL.


Estado: **DECISION_REQUIRED**, solo diseño. Entrega anterior corregida por instrucción humana PM09/10/2026 21:33:08; nuevas elecciones aprobadas PM21:46:22 y contador PM21:54:52. Sin código, migración ejecutada, infraestructura, Git gestionado, nuevas inferencias o gasto. No aprobación pre-code global.

Base/HEAD `ceb6520fd9b92c561c455cd8cbcd40aecf2c9f46`, rama `feat/JUP-035-conversational-web-interface`; CONTRIBUTING2026-09-30/JUP-100. Paris líder, Víctor pairing, Alejandro revisión, Lucía validación. Trello y fuentes/publicaciones oficiales exclusivamente PM. Esta consolidación no altera specs canónicos.

## Decisiones vigentes y trazabilidad

La [matriz decisión→sección→estado](design-decision-matrix.md) es la lectura completa de decisiones y detalles restantes. Cumplimiento documental no es aceptación de producto. Los siguientes contratos reemplazan las propuestas previas de compresor local, placeholder en messages, prohibición global de retries, deadline global120s y construcción de pantalla en Send.

- assistant-ui con API/Cockroach propios, sin AssistantCloud; visual/interacción del spike aprobados, streaming real y RabbitMQ solo ingesta conservados.
- Resumen por **llamada LLM** de QA exclusivamente. Originales, recientes y resumen persistido por conversación; pantalla/metadata/evidencia fuera del compresor (PM21:33:08/21:46:22).
- Operación durable separada del historial visible; guardar pregunta y respuesta **completa juntas en transacción final**. Diseño y adaptación/migración necesarios aprobados PM21:46:22, ejecución pendiente.
- Máximo cuatro intentos: inicial+**tres reintentos automáticos**,120s por intento/hasta480s activos aprobados. Stop voluntario no retry, desconexión del lector no fallo del productor. Esperas aprobadas PM23:05:12:120s locales acumulados+120s proveedor acumulados por solicitud; no reset retry/resume y no plazo total respuesta. La interpretación por intervalo PM22:37:04 queda sustituida; resume nunca anterior a retry_at. El HTTP principal recibe el plazo restante del claim menos margen final propuesto5s; se retiran los cortes ocultos total30s/idle20s, sin reiniciar el reloj.
- JSON por pestaña preparado **al recibir/cambiar datos**, antes de Send; Send solo copia/congela versión existente, sin construir/refetch/diagnóstico.
- Resumen estable después del system y antes de variables como **datos user no confiables**, candidato a prefijo cacheable; contexto reenviado en cada intento, sin memoria remota/hit garantizados.
- Tenant+usuario+conversación en todas las rutas/buffers/artefactos; una operación abierta por chat y cinco chats privados concurrentes. Capacidad8 configurable propuesta, no límite diagnóstico1 ni concurrencia ilimitada.
- Captura completa hasta1MiB y techo8192 tokens variables aprobados. Tokenizers0.22.1+artefacto ZAI fijo aprobados en diseño/futura implementación aprobada PM21:54:52; no instalación ni conteo idéntico a facturación acreditados.
- HTTP interno autenticado en red privada de un DockerServer, secret exclusivo/replay y listener privado; HTTPS externo permanece, entre hosts reevaluar.

## Persistencia, recuperación e intentos

[Historial y operaciones](history-persistence-design.md): una tabla `chat_operations` y columna `conversations.dialogue_summary JSONB` propuestas. La operación guarda pregunta/entrada/versiones y contador/fences durables; no es mensaje completo. Cuatro pasos DDL aditivos independientes, catálogo/verificación y registro DML posterior; sin backfill ni cambios de columnas messages. Runner/migrador y pruebas Cockroach futuros.

Al finalizar candidato válido, una transacción reautoriza, comprueba Stop/attempt/fence/deadline, inserta pareja user+assistant y confirma operación/conversación; solo después emite final. Si pregunta ya existe por retry humano, verifica owner/contenido y la reutiliza sin duplicar. Terminal incompleto vive en sección operacional, no como respuesta completa; originales visibles intactos. Caída puede perder parcial RAM, pero conserva solicitud y contador. Commit ambiguo se resuelve por lectura/CAS SQL, sin inferencia de comprobación.

Backend dirige los tres retries funcionales. Transporte/gateway retries0 evitan multiplicación. IDs/buffers por intento, evento de reset antes del siguiente, cero concatenación. Fallos transitorios permiten siguiente intento; permisos/schema/guard/refusal permanentes terminan con error. Stop cancela active/waiting/paused y programa cero intentos nuevos. Scheduler durable recupera el siguiente número tras fencing/deadline, nunca redispatch del anterior ni contador nuevo tras crash.

**Admisión y esperas aprobadas PM23:05:12:** Paris vía PM09/10/2026 23:05:12 aprueba dos presupuestos independientes ACUMULADOS POR SOLICITUD:120 s de espera automática por capacidad local y120 s de espera automática del proveedor. No se reinician por retry, resume ni recuperación de la misma operación. Máximo240 s de esperas automáticas, no plazo total hasta respuesta. Se mantienen120 s de ejecución por intento e inicial+3/max4, sin retries anidados. Sin plaza inmediata se reserva solicitud waiting, visible/cancelable y sin claim/intento consumido; arranque automático al obtener plaza dentro del saldo local. Agotado saldo local: paused con pregunta intacta, sin bucle automático. Resume explícito no renueva saldo y, con saldo local agotado, solo puede arrancar si hay plaza inmediata. Retry-After superior al saldo proveedor restante produce pausa visible; resume explícito solo desde retry_at, conservando presupuestos/contador. No enviar antes para encajar en120s. Detalles durables/recuperación en [historial](history-persistence-design.md).

## Resumen LLM, contexto y caché

[Compresor QA](context-compression-extension.md): llamada no streaming por actualización necesaria, prompt/schema SummaryResponse distintos de FinOps, refs exactas y fuentes scoped. Umbral6144 o presión residual, objetivo cuatro recientes, resumen512 de contenido/hasta768 de artefacto; input por lote4096/output800, cobertura/omisiones visibles, todos defaults propuestos. Recomendación actual: resumen anterior válido+QA nuevos en orden desde frontera, sin reemplazar memoria por ventana reciente. Hasta dos lotes por evento y backlog explícito; un par demasiado grande no se salta ni permite avanzar frontera, requiere alternativa/política humana. CAS/revisión/source hashes/epoch invalidan ante retry completed antiguo o cambio de política; rebuild recomendado desde originales por lotes con frontera y pérdidas de detalle visibles. Resumir sucesivamente puede perder matices, no garantiza memoria perfecta ni preservación íntegra de todos los hechos. Una llamada fallida no se convierte en resumen local ni dispara loop; previo válido o recientes con limitación explícita.

Resumen máximo1 upstream ocioso, compartiendo techo8 y dejando≥5 plazas principales; prioridad inferior a respuestas/retries. Clave/presupuesto de resumen separado aún propuesto. Reserva conservadora sin cache hasta0,004992USD POR LOTE en techo4096/800; una reconstrucción de m lotes necesita hasta m veces ese importe y dos lotes por evento propuestos hasta0,009984USD; precio de diseño, no factura ni autorización de llamadas. Principal debe contemplar hasta4 llamadas por solicitud en presupuesto productivo.

[Prompts/pantalla](prompt-context-design.md): processor carga recursos Git y reglas/schema024 canónicos con roles reales; descriptor firmado fija versiones. Registro de pantalla usa el resultado ya renderizado al recibir/cambiar selección/datos. Snapshot completo guardado separado de proyección; fuentes financieras server autorizadas distintas de pantalla/demo/resumen.

8192 es techo variable compartido incluyendo resumen/recientes/pregunta/pantalla/evidencia/envolturas. Reparto y omisiones propuestos, información esencial antes de upstream; captura íntegra hasta1MiB no se reduce silenciosamente. Tokenizer offline ZAI revision `a66456a59f21345d1e5e586345c448a9106d29d7`, SHA256 `19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d`, tokenizers0.22.1, sin pesos/código remoto/descarga runtime. Metadatos compatibles Python3.12, build/carga/conteo focal aún NOT_RUN; no fallback tiktoken presentado como equivalente.

## Integración y despliegue examinados

[Plan técnico/Compose](integration-readiness-plan.md) fija la inspección local y fuentes oficiales públicas durante el diseño: dos append backend no atómicos, cliente con retries anidados, roles aplanados, DNS bloqueante, rangos Python sin freeze y fallback de tokenizer. Propone adaptaciones concretas; pruebas futuras verifican implementación, no investigación pospuesta.

Fetch/SSEv2 con operación+attempt IDs y parser acotado; final pequeño≤64KiB tras pareja commit, GET result/context/evidence completos y privados. Snapshot answer≤4000codepoints; captura1MiB fuera de frame. Productor supervisado independiente del lector, scope uniforme y buffer nuevo por intento. Cinco productores activos antes del primer final en prueba futura, Stop/reenganche de uno no afecta otros.

Canal HMAC/nonce/boot/attempt fencing en red privada dedicada; processor sin host port, app chat8003 solo IP privada y apphealth8001 sin routerchat en otras interfaces. Mantener redes ingesta/DB/gateway, secretfile exclusivo solo servicios necesarios, HTTPS externo. Red privada/HMAC no cifran; elección humana de un DockerServer no se extiende entre hosts.

Un migrador efímero y backend verify-only; health backend no depende processor para evitar ciclo, chatreadiness separado sin inferencia. Entornos/volúmenes mock embedding8 y real1536 separados; sin reset/drop. Constraints/lock/asset hashes y recursos se comprueban en build futuro; pool8/control4 y límites memoria/CPU propuestos y por medir. Sin servicios/configuración creados.

## Evidencia reutilizada y límites

Visual assistant-ui aprobado PM19:13:37 («me gusta aprobado»):27 checks iniciales y31 del ajuste, types/build del spike, desktop/sintéticos. No auth/DB/producto ni mobile/a11y acreditados; override experimental no se hereda a producto. Bundle689,67kB warning500kB conservado.

Gateway: dos llamadas stream reales autorizadas; primera rechazada causa UNKNOWN, segunda84deltas/primer1,390s/cierre7,656s y guards existentes PASS. Viabilidad mínima, no fiabilidad general ni vertical producto. Cache: dos intentos iniciales(200cached0/429sinusage) y una llamada followup,3840/4053 cached_tokens reportados, coste gateway adicional0,0005266125USD. PM20:20:45 cierra condición cache; tres intentos total, no repetir.429 origen indeterminado. Reutilizar recibos/negativos sin nuevas inferencias.

## Dependencias y orden de ejecución futuros

Fuente oficial PM22:14:44: tarjeta035 «Relacionadas036037070», alcance «lo que integren036037». Contrato036 publicado PR69draft SHAaee2571… no integrado es referencia para DISEÑO SIN esperar merge; adaptación de escritores/atomicidad/busy requiere coordinación para implementación.037P1/relación no es gate automático: conectar capacidad efectivamente integrada y criterio confirmado. No se ha confirmado aquí un criterio035 que obligue037/070; si una capacidad falta, describir ese límite concreto y mapear criterio antes de atribuir bloqueo. No fixtures como aceptación ni alcance inventado. RF-035-001 sigue Open fuera de alcance.

Restante: detalles técnicos propuestos de cola/admisión, cobertura/proyección/schema del resumen, detalle keys/budgets/capacidad/secret/bind y recursos, acuerdos de adaptación036 y037 condicional según criterio/capacidad, sin bloqueo universal; aprobación pre-code completa. Separación operacional/migración EN DISEÑO,120×4,LLM,contador y elecciones funcionales ya aprobadas no se reconsultan.

Tras pre-code: Red→Green→mutación con checkpoints separados; smoke mock temprano auténtico, Cockroach/concurrencia/crash/DDL real, UI/seguridad/regresiones y prueba IA separadamente autorizada. Revisor/Validador independientes y evidencias por criterio; final Paris, archive específicamente autorizado en mismo branch antes de reviews humanas GitHub. CI/checks documentales no aceptación ni permiso de publicación.

## Registro original de decisiones 15:24–19:13

Texto histórico conservado literalmente. Persistencia inicial/terminal y reintentos se sustituyen en los puntos afectados por PM21:33:08/21:46:22; el contrato vigente es el anterior, sin reconsultar decisiones que permanecen.


- PM09/10/2026 15:24:08: assistant-ui + API y Cockroach propios, sin AssistantCloud.
- PM15:47:28: streaming real obligatorio; PM16:16:04: conexión directa preferida,
  RabbitMQ solo ingesta.
- PM16:48:09: Detener explícito con propagación best effort; ocultar no cancela.
  Parcial incompleto fuera del contexto posterior; reintento humano ligado a la
  pregunta existente. Persistir inicio y terminal, sin checkpoints periódicos;
  aceptada pérdida del parcial RAM ante caída completa, conservando pregunta y
  respuestas completadas persistidas. No volver a consultar estas decisiones.
- PM18:55:20: historial ocultable superpuesto al extremo derecho, sin estrechar
  chat ni desplazar app; selección de otro hilo cierra historial, chat abierto;
  Nueva conversación inicia hilo vacío.
- PM19:13:37 transmite Paris «me gusta aprobado» tras ver demo45135: aprobados
  spike y diseño visual/interacción observados — panel derecho50%, estilo mostrado,
  historial y selección/Nueva conversación. Spike cerrado satisfactoriamente en
  ese alcance. No integración backend, migración, dependencia productiva o
  aceptación final de JUP-035. Prototipo/evidencia reproducibles conservados.

## Revisión acotada PM22:14:44 — tres puntos

Timeout:30s actual es total HTTP, no idle. Nueva recomendación pasa restante del claim120s a cliente/gateway, sin clamp30/idle20 ni reset, reservando5s propuestos para validación/commit. Preparación/conexión consumen ese mismo plazo; ejemplo de unos110s efectivos de proveedor, no120s además de preparación. No configurado ni probado ahora.

Compresión: anterior válido+QA nuevos desde frontera, con lineage/ledger scoped y CAS; pantalla/recentes separados. Recomendación para revisión, no decisión humana de descartar lo antiguo. Rebuild al cambiar fuente antigua, lotes/coste/backlog/par grande y degradación de matices explícitos.

Dependencias:036 referencia disponible para diseño sin esperar merge;037 integración condicional a lo que llegue integrado. Relación/P1 no sustituye criterio de aceptación; fuente/acuerdo pendiente distinto de gate obligatorio demostrado.


## Corrección propuesta del esquema enviado al proveedor — 2026-10-11

**Pendiente de aprobación humana previa al código.** La revisión técnica del TL autoriza documentar este diseño, sin modificar producto ni tests. Las aprobaciones e hipótesis históricas anteriores se conservan; no autorizan por sí solas esta corrección.

Una única prueba diagnóstica real, autorizada y acotada, con el modelo y ruta existentes y la entrada sintética original, recibió HTTP 200 y produjo `BadRequestError` lógico 400 en LiteLLM 1.103.2. El mensaje técnico saneado señaló un error comunicado por DeepInfra y nombró `uniqueItems`. El código instalado convierte también un cuerpo con `error` significativo cuando HTTP es satisfactorio. No se conserva el cuerpo original ni se afirma conocer todos sus campos; el esquema original emitido por la pasarela no se capturó. La prueba acredita un indicio concreto de incompatibilidad del keyword en esta solicitud reconstruida, sin aceptación funcional ni una corrección ya comprobada.

La modificación mínima es una copia del esquema exclusivo de `SummaryResponse` para el proveedor. Eliminará exactamente `uniqueItems` en `/$defs/SummaryTopic/properties/question_refs` y `/$defs/SummaryTopic/properties/answer_refs`; conservará el resto íntegro, `response_format=json_schema`, `strict=true`, nombre, campos requeridos, tipos, patrones, referencias, límites y `additionalProperties=false`. El processor expondrá la proyección en `SummaryResources` y `SummaryGateway` la usará únicamente al construir la petición. No se aplica a FinOpsResponse ni se cambia proveedor, stream, prompt, dependencias o logging compartido.

El modelo Pydantic `SummaryTopic.unique_refs` ya rechaza duplicados en ambas listas. El backend también los rechaza mediante su validador del esquema completo. Esos controles y el esquema canónico v2 permanecerán idénticos: no se normalizan ni deduplican candidatos inválidos. Un duplicado conserva el comportamiento de fallo, los originales y el resumen anterior válido, sin inferencia adicional.

El hash local de autoridad seguirá siendo `72404e66533f03268bf53727e7ed01cad00a71c31ad483f823ee4c3c8e06783e`; el hash canónico propuesto del esquema enviado al proveedor es `ec92ca50508a0fe0b94ef08ef81c3b1f330973d5b9266d22a53c9b1ca4b8e5ac`. Son contratos distintos y se identificarán por separado en tests y evidencia. No se modifica manifest, payload v2, DTO interno, firma de autorización o contrato persistido. Artefactos compatibles conservan su validación completa de versión, owner, fuentes y epoch. Si se necesitara incorporar el nuevo hash al contrato firmado o persistido, requeriría un diseño adicional explícito.

Cambian los bytes de la petición y su posible identidad de caché; no se supone hit ni descuento. No se borra el `last_attempt` RAM ni se relanza un hash fallido en caliente. Un rebuild/reinicio normal de la pareja aislada pierde RAM conforme al contrato existente, no despacha al startup y requiere un nuevo evento completed autorizado para evaluar la corrección, conservando el registro financiero y todos los contadores previos. Se medirá la proyección/envoltura efectiva antes de la llamada; permanecen input 4096, output 800, plazo 30 s y retries 0.

Red verificará contra el producto actual que la petición omite sólo esos dos flags y que el esquema de autoridad no cambia. Los rechazos de referencias duplicadas del processor y backend serán regresiones explícitas, sin presentarlos como Red nuevo si ya funcionan. Green sólo modificará `apps/processor/app/core/summary_resources.py` y `apps/processor/app/clients/summary_gateway.py`; se ejecutarán los controles focales y afectados. Mutation reintroducirá un flag y desactivará el rechazo de duplicados para demostrar sensibilidad, con fases y guardas separadas. Después deberán instalarse y usarse resúmenes válidos en la integración real; un simulador, JSON válido o el diagnóstico no demuestra fidelidad semántica ni aceptación.

El gate siguiente es validación estricta de OpenSpec y trazabilidad, revisión técnica y decisión humana material por PM antes de Red. Revisión, validación independientes y aprobación final permanecen pendientes.


## Diagnóstico seguro de respuesta principal64 — propuesta pendiente de aprobación humana pre-code

Encargo Tech Lead 11/10/2026 03:02:54, formalización analysis-design de esta ruta exclusivamente. No autoriza producto/tests o nuevas llamadas. La aprobación del diseño63 se conserva y no cubre este nuevo cambio.

# JUP-035 · propuesta mínima de diagnóstico seguro de la respuesta principal

Estado: propuesta externa para decisión de Paris a través del PM. No implementada; no autoriza cambios de producto, pruebas ni otra inferencia. Proceso 2026-09-30/JUP-100. Paris lidera; Víctor pairing, Alejandro revisión y Lucía validación, sin acreditar intervenciones realizadas.

## Hechos y límite de captura

La proyección del esquema de resumen está aprobada e implementada: omite únicamente dos `uniqueItems` al enviar la petición; conserva autoridad local, rechazo de duplicados, strict, firmas, manifest y contrato persistido. RGM pasó con 283 pruebas afectadas y cuatro mutaciones funcionales detectadas. Aún no se ha enviado un resumen real corregido al proveedor.

El trigger y su único retry terminal autorizado recibieron HTTP 200 y SSE terminado del proveedor, pero la aplicación terminó ambos como `failed/provider_error` sin final ni evento completed. Todos los 26 mensajes previos se conservan. Contadores: 7 main, 3 summary y un SDK diagnóstico separado. Ninguna llamada de resumen nueva ni consumer. Pruebas reales detenidas por contrato TL/PM.

Los registros propios correlacionados y los artefactos conservan la respuesta pública parcial, hashes y uso/coste; no conservan el JSON completo del candidato, finish original ni excepción concreta. La fuente actual demuestra que `ChatGateway._records` descarta el detalle del fallo antes de devolver un error genérico; la ruta privada lo retransmite y el backend guarda `provider_error`. Una excepción en la validación del candidato del backend habría quedado como `invalid_response`. Esto delimita la ruta, sin identificar un campo Pydantic ni atribuir una causa específica.

La interfaz privada mantiene por intento únicamente deadline y task, que se libera al acabar el stream; no hay un GET que recupere el candidato descartado. El backend conserva eventos públicos de texto/terminal y resultado sólo para completed. No se propone acceder a volcados de memoria, tablas del proxy o rutas que devuelvan cuerpos/credenciales. No es posible reconstruir los campos ausentes a partir del texto de `answer`.

## Cambio estable mínimo propuesto

Dos archivos de producto: `apps/processor/app/clients/chat_gateway.py` y `apps/processor/app/chat.py`. La primera fase aprobada futura podrá escribir pruebas sólo en `apps/processor/tests/test_chat_gateway_jup035.py` y `apps/processor/tests/test_chat_private_jup035.py`.

En `ChatGateway._records`, emitir antes de perder el detalle un único evento estructural del fallo mediante logging de stdlib y la configuración local existente. La respuesta HTTP/NDJSON, categorías actuales, guardrails, validación y política de retries permanecen idénticas. No se cambia FinOpsResponse, el esquema del resumen, prompts, proveedor, claves, DTO, persistencia, logging compartido ni dependencias.

Para correlacionar sin ampliar el contrato privado o la firma del gateway, `app/chat.py` establecerá un contexto de diagnóstico de stdlib ContextVar alrededor de la ejecución ya autenticada y autorizada del gateway. Sólo contendrá operation_id y attempt_id con formato UUID validado. Cada extracción con `asyncio.to_thread` recibe su contexto; el scope se cierra en finally. Los mocks con la firma actual de dos argumentos continúan compatibles. Debe demostrarse aislamiento entre dos intentos concurrentes en la prueba offline. No registrar tenant, usuario o conversación.

El evento tendrá un nombre constante y un máximo de 2 KiB. Campos propuestos:

- UUID de operación e intento; hash SHA256 de los bytes de petición ya ensamblados, sin cabeceras. Este hash permite correlación adicional con el journal existente.
- Etapa de fallo de una lista fija: request, transport, envelope SSE, provisional_answer, finish, JSON candidato o validación del modelo. Sólo se registra la etapa realmente ejecutada, no una causa deducida.
- Clase de excepción de una lista cerrada: ValidationError, ValueError, JSONDecodeError, UnicodeDecodeError, TypeError; cualquier otra se normaliza a OtherException, sin su nombre arbitrario.
- Como máximo tres errores Pydantic obtenidos con `errors(include_input=False, include_context=False, include_url=False)`, con `type` de lista cerrada y `loc` de hasta seis segmentos. Nombres sólo de campos conocidos del esquema y posiciones enteras acotadas; segmentos desconocidos se sustituyen por un marcador constante. No extraer input, ctx, url o valores del candidato. El `msg` sólo podrá examinarse efímeramente en RAM para la igualdad exacta de las seis constantes verificadas abajo; nunca se registra, conserva ni hashea.
- `finish_reason` sólo si se observó: stop, length, content_filter, tool_calls o function_call; valores distintos se normalizan a other y la ausencia se identifica como ausencia. No inferir finish a partir del uso ni de `[DONE]`.

No usar `str(exception)`, repr, traceback, prompt, cuerpo de petición/respuesta, mensajes del proveedor, cabeceras, claves o nombres libres. El fallo del observador no cambia la respuesta ni dispara otro POST. No se propone cambiar los mensajes ni el comportamiento de los validadores.

### Clasificador cerrado de reglas actuales

La lectura de la fuente actual confirma seis raises ValueError con literales constantes, sin valores dinámicos. Para un error Pydantic de type value_error se propone igualdad total con cada cadena fija que Pydantic genera: `Value error, ` seguido del literal exacto de esta tabla. No regex, prefijos abiertos, coincidencia parcial, extracción de contexto ni clasificación de excepciones por texto libre. Sólo se publica rule_code. Un texto desconocido o una clase/tipo distinto se normaliza a `unclassified_model_rule`. La forma concreta del msg se verificará mediante los fixtures futuros, sin ejecutar ahora validadores ni pruebas; si no coincide exactamente, se conserva unclassified y no se amplía la lectura.

| Literal fijo en schemas.py | rule_code |
| --- | --- |
| period.from must be before period.to | period_order |
| estimated_savings and currency must either both be set or both be null | savings_currency_pair |
| evidence ids must be unique | evidence_id_duplicates |
| non-actionable responses cannot contain metrics or recommendations | non_actionable_with_metrics_or_recommendations |
| metrics and recommendations must reference known evidence | unknown_evidence_reference |
| ok and partial responses require evidence | actionable_requires_evidence |

Procedencia fija de la tabla: `apps/processor/app/agents/schemas.py`, SHA256 `4ba4051c0f9dbb861cd9a289f826c501874acf8b250972924c9738550682a98d`. No se propone editar esa fuente, validadores, schema, mensajes o comportamiento aceptado/rechazado. El mapeo identifica una regla efectivamente emitida incluso con loc vacío, sin identificar qué valores del candidato la incumplieron. Reglas nuevas, errores desconocidos o truncados después de los tres primeros siguen sin causa específica; se declaran esas limitaciones. Los dos fallos reales previos no se pueden clasificar retrospectivamente porque no conservaron esas excepciones.

### Cobertura de salidas y contexto

Fuente inspeccionada, sin ensayos nuevos: `chat_gateway.py` SHA256 `9e77a8db5d5e3fd12a2b999066e0e8f2861f895247d395a2297b88c8d2ceca06`, `chat.py` SHA256 `bdfedcad680c68bf0db45a5e976ef7acfe48e019766ed3630fdc5d8d983a6b41` y `chat_stream_parser.py` SHA256 `14705ccf6e030b3253d0d757594b03185a2122337d319a883329af81899d3144`.

- Antes de DONE: separar etapa de decoder/SSE/envelope de la extracción incremental de answer, que también puede lanzar ValueError. No mapear estos ValueError a reglas del modelo.
- En DONE: comprobar finish observado; separar parse de complete_json de model_validate. Emitir el diagnóstico antes de la rama actual finish length que devuelve incomplete, y antes de la rama que relanza a invalid_response. Una marca local evita duplicarlo al llegar al catch externo.
- HTTPError, URLError y TimeoutError/OSError: conservar exactamente las categorías, cierre y retry_after actuales; sólo evento transport con clase normalizada y estado HTTP entero si existe, sin reason, cabeceras o cuerpo. EOF/deadline previo no llevan excepción: clase null y categoría fija existente. Cancelación y candidato válido no generan diagnóstico de fallo. No sintetizar finish.
- La construcción de payload/request ocurre antes del try actual; si falla, el diagnóstico se limita a etapa request y clase normalizada y se relanza la misma excepción a la ruta actual, sin cambiar su categoría pública. El hash sólo existe después de ensamblar los bytes; no registrar un hash inexistente ni cuerpos.
- Establecer y resetear ContextVar dentro del ciclo real de la tarea que consume el stream, antes de crear tareas `__anext__`, no en la petición que sólo devuelve StreamingResponse. El contexto se copia a cada asyncio.to_thread y se resetea en finally después de cerrar iterator/cancelar pending. Una copia ya en el hilo conserva sólo los UUID de ese intento; no estado global mutable ni cruce con otro intento. Cierre/cancelación y excepción del gateway deben probar limpieza. Ninguna nueva respuesta, DTO o parámetro de gateway.

La alternativa temporal de instrumentar el proxy compartido, conservar JSON crudo o añadir otro SDK queda fuera de esta propuesta. El evento local acotado utiliza el punto exacto donde se pierde el detalle y conserva la utilidad de diagnóstico tras esta prueba.

## Tres fixtures offline para RGM después de aprobación

1. Candidato FinOps válido: mismo candidato, stream y resultado que antes; sin evento de fallo ni nuevas llamadas.
2. Error Pydantic: falta/tipo de campo conocido y parametrización real de las seis reglas de la tabla, incluyendo las cuatro reglas con loc raíz vacío; entradas/nombres desconocidos y error ValueError desconocido con secretos sintéticos. Registro acotado con rule_code, loc/type saneados y ningún input/ctx/msg/valor; los desconocidos no se clasifican por parecido. La respuesta fallida sigue igual. Esta familia debe demostrar diagnóstico accionable del evento original de cada regla, no sólo probar el diccionario del clasificador.
3. Error JSON/finish: excepción y finish no permitido con secretos sintéticos; sólo clase/etapa/enum normalizados. Dos contextos de intento distintos no se cruzan y se limpian al cerrar/cancelar. No hay red externa, claves reales o inferencia.

Red debe fallar por falta del diagnóstico/correlación segura en producto original. Green sólo esos dos productos; pruebas fijas. Mutation externa y guard separado debe detectar el escape de un valor sensible, una correlación equivocada y un rule_code incorrecto, con control original satisfactorio; ninguna edición persistente del producto. La revisión y validación independientes y las aprobaciones humanas siguen pendientes.

## Próxima ejecución, si se aprueba

No se ejecutará otra llamada antes del gate humano previo al código y el contrato TL correspondiente. Una vez aprobado e implementado el diagnóstico, la próxima operación necesaria será normal y correlacionada, no un SDK ni un sondeo de pago adicional. El journal actual y los dos fallos se conservarán. Existe un último slot main previamente financiado; hasta cuatro llamadas background de summary están reservadas y sin usar. Held EUR 0,191350, libre 0,008650 y reserva personal 0,056562, conforme al TL; las llamadas de coste desconocido continúan retenidas.

La admisión por POST mide y congela el cuerpo real, verifica clave/precios y escribe reserva antes de forward. Un consumer posterior requiere completed y artefacto válido y la reserva de su cuerpo real antes del POST; el TL resolverá esa admisión y el contador operativo dentro del presupuesto humano conjunto vigente de 0,20 EUR. Ocho main es planificación interna, no un límite humano ni razón para bloquear el consumer por sí sola. No asumir que un slot cubre dos POST ni añadir otra certificación financiera previa: se conserva la admisión efectiva por cada petición y el saldo realmente autorizado. No tocar desconocidos, reserva de Paris ni límites del servicio compartido. No se garantiza el recorrido ni el presupuesto de llamadas aún no admitidas. E5 y el panel personal siguen pendientes; una nueva respuesta fallida no se transforma en aceptación.

## Formalización documental despachada por TL03:02:54

Se formalizará este diseño completo únicamente como append en `openspec/changes/jup-035-conversational-web-interface/design.md`, mediante checkpoint analysis-design fresco y guard de esa ruta exacta. Se conservarán todos los bytes y bloques de aprobación previos. Strict OpenSpec, trazabilidad y diff focal serán los únicos controles nuevos. No modificar requisitos, producto/tests ni marcar E5/revisión/validación completos. El TL conserva la reconciliación de tasks/proposal y coherencia; continuidad/README no tienen encargo de escritura ahora. El borrador externo final-documentation-reconciliation64.md queda como propuesta no aplicada. No crear otro identificador o backlog; la incidencia oficial corresponde al PM.


## JUP-035 — período de respuesta gestionado por el servidor (propuesta 11/10/2026)

### Dirección humana, alcance y estado

Esta propuesta sustituye la mitigación consistente únicamente en pedir al modelo fechas ordenadas. PM verificó la dirección de Paris «el period lo gestionemos nosotros y no el modelo» y TL la transmitió a Desarrollador el 11/10/2026 a las 12:07:39 Atlantic/Canary; referencias de origen: chat `01a07c55-c454-7bb3-8053-cbf2ad70d2ec`, turno `01a12aa2-3c42-7a92-8a83-9b544855bd82`, mensajes `01a12aa2-3c80-7a01-bc54-cafb79dd6837` y `01a12aa2-8d8b-77f1-9a57-a0b86303c5bb`. Es dirección para diseñar, no aprobación previa al código. La autorización «autorizado» recibida posteriormente en el chat Desarrollador corresponde al recorrido real E5 previamente descrito, no aprueba por anticipado esta modificación material.

Solo se añade esta sección a design.md. Se mantienen íntegros los documentos y las aprobaciones anteriores. Rama `feat/JUP-035-conversational-web-interface`, revisión/base `ceb6520fd9b92c561c455cd8cbcd40aecf2c9f46`, proceso `2026-09-30 (JUP-100)`. Asignaciones humanas transmitidas: Paris líder, Víctor pairing, Alejandro revisión y Lucía validación; no se afirma participación ya realizada. TL reconcilia tasks/proposal/continuidad. No hay edición de producto/tests, inferencia, aceptación, archivo o publicación en esta fase.

Los importes y reservas de secciones anteriores son registros históricos. La dirección humana vigente transmitida por PM/TL elimina el techo financiero para pruebas necesarias y proporcionadas de JUP-035; la contabilidad y costes desconocidos se conservan, sin usarlos como gate ni presumir coste cero o devolución. Los límites efectivos de claves/servicios siguen siendo restricciones técnicas; no se modifican servicios compartidos ni habilitan interacciones personales por este diseño.

### Hechos comprobados y límites causales

- `apps/processor/app/agents/schemas.py`: ResponseScope.period es obligatorio y nullable (`Period | None`); Period rechaza `from >= to`. Null es válido, omitir la clave en la respuesta pública no lo es. Se conserva SHA256 `4ba4051c0f9dbb861cd9a289f826c501874acf8b250972924c9738550682a98d` del archivo y el esquema FinOpsResponse 1.0 completo.
- El gateway actual envía FinOpsResponse.model_json_schema() y valida el candidato directamente como FinOpsResponse. El backend vuelve a validar estructura, período y procedencia antes de persistir.
- ChatContextBuilder.billing contrasta selección con fetch_billing_summary del tenant y valida BillingSummary; exige igualdad exacta del período UTC solicitado y recibido. Solo después crea evidence de kind cost_query/source billing-summary-v2 con `record.period`. Un dato de navegador discrepante se distingue del registro contrastado; la autoridad es el registro, no el total declarado por la pantalla.
- Contexto privado existente: authorized_evidence, source_citations, verification_records, messages y manifest. Los QA/resúmenes y documentos recuperados no acreditan por sí mismos un intervalo financiero.
- Réplica externa 5, informada por PM/TL: 422 invalid_response, model_validation/ValidationError, loc scope.period, rule_code period_order, finish stop, una llamada sin retry, 73,855 s, content_stored false, UUID de operación/intento null. Acredita fechas iguales/invertidas de esa respuesta; no clasifica retrospectivamente los dos fallos principales de las 02:49 ni acredita E5. Réplica externa 3 es otro hallazgo: el backend copiado rechazó cuatro IDs frente a uno autorizado, sin backend activo ni persistencia. No se confunden ambas causas.

### Contrato propuesto: selección, contexto y ensamblado

El backend posee el período. Una función pura deriva un descriptor cerrado `response_period` exclusivamente de los períodos de evidence autorizada del contexto actual cuyo kind/source son cost_query/billing-summary-v2. Esos registros proceden del contraste anterior; no se inicia otra consulta ni se cambian filtros de costes. Se usa fecha ISO canónica, zona UTC y comparación real de fechas `from < to`.

Reglas deterministas de selección:

1. Ningún registro de costes contrastado: `{v:1,value:null,source:"not_applicable",evidence_ids:[]}`. Incluye E5 con pantalla sin datasets/selección y preguntas sobre límites históricos. No se infieren fechas de captured_at, reloj, pregunta, QA, resumen o corpus.
2. Uno o varios registros contrastados con el mismo intervalo exacto: source `verified_billing`, value `{from:<start_date>,to:<end_date>}` y evidence_ids de todos esos registros en el orden autorizado original. Se copian fechas; no se redondean, extienden, intercambian ni combinan.
3. Más de un intervalo contrastado distinto: source `ambiguous`, value null y lista de los IDs de costes implicados. No se elige el primero ni se fabrica la unión/intersección. El contexto actual declara la ambigüedad para que la explicación y limitaciones distingan los intervalos. Futuro soporte de un intervalo elegido requeriría otra decisión; no forma parte del cambio.

El descriptor usa únicamente esas cuatro claves, v=1 y los tres source enumerados. Un registro declarado autorizado de costes con fecha inválida, zona distinta de UTC, intervalo igual/invertido, metadatos incompatibles o ID duplicado invalida el contexto antes del proveedor: no se convierte silenciosamente en null. Un dataset no contrastado nunca se eleva a registro autorizado; se conserva la omisión existente y no suministra fechas. Null sigue siendo un valor definido, no una ausencia de la clave final.

ChatContextBuilder añade response_period al contexto privado canónico y una copia informativa al JSON UNTRUSTED_CURRENT_CONTEXT. El primero queda cubierto por el hash de entrada, claim HMAC y comparación con canonical_input almacenado. El processor verifica el descriptor recalculándolo desde authorized_evidence del mismo contexto firmado; no toma la copia textual ni datos del proveedor como autoridad. La comprobación autentica lo declarado por el backend; no se presenta como una segunda consulta independiente al origen. Ante discrepancia/missing/extra se rechaza antes de consumir gateway. Se conserva propiedad, tenant/usuario/conversación, versión, deadline y reserva del intento.

El schema enviado al proveedor es un contrato intermedio derivado por copia del schema público: se retira exclusivamente `scope.properties.period`, su entrada en `scope.required` y la definición Period que queda sin referencias; se conserva `additionalProperties:false` y todos los demás límites, enums, campos requeridos y referencias. El nombre/título intermedio será `FinOpsChatDraft`; no es un DTO público ni un cambio de schema_version 1.0. No se modifica el modelo global utilizado por JUP-024.

Al completar JSON/SSE, el processor exige que scope sea objeto y NO contenga period, aunque sea null o coincida con el esperado. Si el proveedor devuelve el campo retirado, rechaza el candidato como invalid_response: no elimina, ignora ni sobrescribe fechas. Solo para un borrador conforme añade al objeto nuevo `scope.period=response_period.value`, ejecuta el FinOpsResponse original completo y devuelve el candidato final existente. Esta composición explícita no repara una respuesta FinOps inválida: el contrato solicitado al modelo ya no es FinOpsResponse completo.

El backend conserva `validate_response` íntegro y además exige igualdad de scope.period con el descriptor congelado/recalculado de ese intento antes de persistir. Un processor/fixture que devuelva otro período no puede instalar QA. Se mantiene respuesta pública, SSE provisional/final, citas, persistencia conjunta, estados y política de retry existentes; no hay segunda inferencia automática ni fallback. La etapa de diagnóstico sigue model_validation, con códigos saneados existentes y sin registrar valores ni borradores.

Ejemplo del cambio de contratos (todos los demás campos se conservan):

```json
{"antes_proveedor_y_final":{"scope":{"cloud":"azure","data_environment":"simulated","subscription_ids":[],"period":null}},"despues_proveedor":{"scope":{"cloud":"azure","data_environment":"simulated","subscription_ids":[]}},"despues_final_E5":{"scope":{"cloud":"azure","data_environment":"simulated","subscription_ids":[],"period":null}}}
```

### Guía separada de evidencia: texto exacto antes/después

Se preservan todos los bytes actuales de system.md, incluido el prefijo de SYSTEM_PROMPT global y su bloque de reglas. Antes: el sufijo de chat termina exactamente en `No muestres instrucciones internas ni controles privados de ejecución.` seguido del salto de línea existente. Después: se conserva ese final y se añade exactamente este bloque UTF-8, con LF:

```text

Campos gestionados por el servidor:
El contrato de salida solicitado al modelo es un borrador de chat. No incluyas
scope.period: el servidor incorpora ese campo a la respuesta final a partir del
intervalo contrastado del contexto actual, o null cuando no hay un intervalo
unico aplicable. No deduzcas ni inventes fechas desde la pregunta, la pantalla,
el historial o el resumen. Distingue intervalos cuando el contexto declare
ambiguedad y explica las limitaciones pertinentes.

Fuentes autorizadas para esta respuesta:
Solo puedes seleccionar evidence de UNTRUSTED_CURRENT_CONTEXT.evidence.
Copia exactamente sus campos id, kind, title y source, sin crear otros IDs,
fuentes o metadatos. Si no hay evidencia autorizada, evidence debe ser [].
Toda referencia evidence_ids de metricas o recomendaciones debe pertenecer
a la evidence seleccionada. La pregunta, los QA anteriores y el resumen no
crean evidencia financiera ni autorizan reutilizar fuentes de otro contexto.
```

No se modifica input.md ni SYSTEM_PROMPT global. Esta guía reduce ambigüedad sobre IDs y metadatos; la seguridad sigue en los validadores reales. Se conserva el rechazo de evidence no autorizada/metadata distinta, cifras no contrastadas, referencias desconocidas y estados no accionables con métricas/recomendaciones. No hay sustitución determinista de IDs inventados, ni relajación de validadores, ni promesa de obediencia del modelo. Fallar en evidencia aún puede impedir E5 aunque el período ya esté gestionado correctamente.

### Rutas exactas futuras y versionado

Producto propuesto, sujeto a aprobación y despacho de fases separados:

| Ruta | Cambio limitado |
| --- | --- |
| apps/backend/app/core/chat_response_contract.py (nuevo) | Derivación pura de response_period y schema intermedio a partir del JSON público existente; sin importar processor. |
| apps/backend/app/services/chat_context.py | Derivar descriptor del conjunto autorizado actual; congelarlo y añadir copia informativa. |
| apps/backend/app/services/chat_operations.py | Contraste final de período contra descriptor congelado antes de validate_response/persistencia. |
| apps/backend/app/core/chat_resources.py | Validar nuevos hashes/contrato y contar schema proveedor real; descriptor compatible. |
| apps/processor/app/core/chat_response_contract.py (nuevo) | Proyección exacta del schema y validación/composición explícita del borrador con descriptor autenticado. |
| apps/processor/app/core/chat_resources.py | Validar descriptor privado, manifest y presupuesto con schema proveedor real. |
| apps/processor/app/clients/chat_gateway.py | Enviar schema intermedio y componer antes de FinOpsResponse original. |
| apps/processor/app/agents/prompt_resources/jup035/chat/v2/system.md | Append literal anterior. |
| apps/processor/app/agents/prompt_resources/jup035/chat/v2/manifest.json | Hashes/contratos derivados, sin edición del schema final. |

No se cambian `agents/schemas.py`, `agents/prompts.py`, `backend/app/schemas/chat.py`, `finops_response_v1.json`, filtros/servicios billing, summary, frontend, SQL, dependencias, CI ni proxy compartido. JSONB guarda el nuevo descriptor como parte del contexto canónico existente; no requiere migración. Si la implementación necesitase otra ruta material, devuelve diseño al TL antes de editarla.

El manifest conserva v=2/kind=jup-035.chat.v2 y response_schema_sha256 del contrato público (`baf067ac8fe35a693848012c5358cb1c6ab8883ebaa02a63166b00f7d8298018`). Añade provider_response_schema_sha256 y response_contract cerrado versión 1 que declara ownership de scope.period, proyección y política de intervalos anterior; response_contract_sha256 cubre su JSON canónico. Assembler_contract conserva su protocolo versión 2 y añade declaración de response_period privado e informativo, cambiando assembler_sha256. Input_contract público, input_sha256, system_base_sha256, tokenizer y límites conservan identidad. System_sha256 y manifest canónico cambian.

Ambos loaders deben comprobar exactamente los mismos campos/derivaciones, sin valores arbitrarios. Descriptor autenticado y metadata del contexto añaden provider_response_schema_sha256 y response_contract_sha256; el hash público conserva su significado. Prompt_version sigue `jup-035.chat.v2:<SHA256(manifest canónico)>` y cambia por contenido; no se etiqueta todo como una versión pública nueva. Los hashes nuevos serán resultado de bytes aprobados en implementación, no constantes inventadas en este diseño.

Definición exacta del nuevo response_contract canónico:

```json
{"v":1,"provider_name":"FinOpsChatDraft","server_owned_fields":["scope.period"],"server_period_policy":"verified-billing-single-interval-or-null","context_field":"response_period","provider_period":"forbidden"}
```

La declaración exacta añadida a assembler_contract es `server_owned_context_fields:["response_period"]` y `current_informational_fields:["response_period"]`; sus otros campos y orden significativo de arrays se preservan. SHA256 se calcula sobre JSON UTF-8 con claves ordenadas, separadores compactos y sin NaN. Estos valores son contrato propuesto, no un manifest instalado.

Backend schema_text para presupuesto y processor check_messages usarán el schema realmente enviado al proveedor; el hash/schema final se conserva aparte. Se medirán tokens del nuevo sistema/schema y cuerpo completo; no se reutilizan 6102/11014 ni SHA cfa951… como si cubrieran el nuevo payload. Ambos bundles/imágenes propios se desplegarán juntos. Una mezcla rechaza descriptor/contexto, sin fallback. Operaciones congeladas antiguas continúan bajo su versión original; no se reescribe su canonical_input ni se reanuda un retry contra el nuevo prompt_version. El recorrido siguiente necesita operación normal/contexto fresco y admisión adecuada del cuerpo nuevo en el relay propio, conservando registros/counters anteriores.

### Pruebas proporcionadas y entrega pendiente

Rutas Red propuestas: `apps/backend/tests/test_chat_context_assembly_jup035.py`, `apps/backend/tests/test_chat_operations_jup035.py`, `apps/processor/tests/test_chat_resources_jup035.py`, `apps/processor/tests/test_chat_context_budget_jup035.py`, `apps/processor/tests/test_chat_gateway_jup035.py` y `apps/processor/tests/test_chat_private_jup035.py`. Pruebas nuevas puras en `apps/backend/tests/test_chat_response_contract_jup035.py` y `apps/processor/tests/test_chat_response_contract_jup035.py` si permiten aislar las derivaciones sin ampliar suites. TL fija exactamente qué rutas requiere cada subfase antes de escribir.

Casos focales con modelos, assembler, recursos y transporte reales instalados, sin mera búsqueda de textos:

1. Billing contrastado con período válido: selección exacta, descriptor privado firmado/congelado, borrador sin period, FinOps final con período idéntico y backend acepta/persiste; varios registros con intervalo idéntico conservan IDs.
2. Sin intervalo/E5 sin datasets: descriptor null, borrador sin period y final con clave period:null pasa ambos validadores; QA/summary/pregunta con fechas no crean un período. Corpus por sí solo tampoco.
3. Igual/invertido/malformado/UTC incompatible u origen no autorizado: no entra como período contrastado. Descriptor privado falsificado, falta/extra, IDs incongruentes o manipulación de evidencia declarada invalida contexto antes del gateway; ningún POST/QA. Dos intervalos distintos generan null/ambiguous, no fechas derivadas.
4. Proveedor devuelve scope.period, incluso null/correcto: candidato rechazado sin quitarlo ni modificarlo. Otras faltas/tipos/extras y reglas raíz siguen fallando en FinOps original tras composición. Archivo/schema público original idénticos y aceptación/rechazo de sus casos anteriores preservados.
5. Evidence válida con metadata exacta se admite; ID no autorizado, fuente/título/kind alterados, referencias inexistentes o cifra no contrastada siguen rechazados por los validadores existentes, sin autocorrección.
6. Manifest/descriptor/bundle viejos o cruzados fallan; igualdad exacta de proyección backend/processor, diff semántico solo campo retirado/definición huérfana/título intermedio, hash público intacto, conteos reales y límites actuales. No se inventa un PASS de una suite completa no repetida.

Red/Green/mutación necesitarán checkpoints independientes después del gate humano. Mutantes pertinentes: aceptar el campo proveedor retirado, confiar en fechas de pantalla/historial, omitir igualdad final con descriptor, aceptar mezcla de hashes; controles originales satisfactorios y KILL observable, sin ampliar a decisiones no cambiadas. El diagnóstico RGM67 y evidencia no afectada se reutilizan por identidad; las pruebas de gateway/ruta privada afectadas se repiten proporcionalmente, sin repetir baterías completas por rutina.

Offline prueba contratos e integración local, no al proveedor remoto. Tras implementación y readiness autorizadas: operación real normal processor → backend → QA persistido; solo si completa, summary real con artefacto válido/lineage/persistencia; solo entonces consumer que demuestra uso de esa memoria con evidencia financiera del contexto actual. HTTP 200/finish stop no son aceptación. Se conservarán todos los fallos originales y el historial previo; no se rellenan mensajes con datos simulados para declarar E5.

Antes del POST, TL coordina quiescencia efectiva de la clave compartida (el ejecutor externo declaró cinco intentos y cese después de period_order; esa declaración no es observación continua), identidad de imágenes/bundles, autoridad humana y fase/slot. No se repite SDK ni se añaden sondas pagadas. El auto-review rechazó dos intentos previos antes de ejecución; no hubo tercera llamada ni creación de marcador paid-intent67. La autorización humana directa recibida ahora se comunica al TL; no sustituye el nuevo gate pre-code ni permite mezclar contratos.

### Fuentes primarias, alternativas y riesgos

Inspección local del 11/10/2026: schemas.py, chat_gateway.py, chat_resources.py de ambos componentes, backend chat_context.py/chat_operations.py y schemas/chat.py; proceso local CONTRIBUTING/AGENTS vigente. La documentación primaria de [Pydantic, validadores de modelo](https://pydantic.dev/docs/validation/latest/concepts/validators/) explica controles que se ejecutan sobre el modelo completo; se conserva ese punto final. [OpenRouter, structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs) describe response_format y soporte por endpoint. Inferencia de diseño: un schema enviado al proveedor no sustituye comprobaciones semánticas ni autoridad de servidor; se valida el resultado real incluso con strict=true. No se afirma compatibilidad remota demostrada para la nueva proyección antes de ejercitarla.

Solo insistir en fechas por prompt no elimina propiedad del LLM; sobrescribir/ordenar fechas recibidas ocultaría respuestas inválidas; permitir period opcional en FinOps alteraría el contrato público. Se elige un borrador explícito limitado y ensamblado trazable del campo del servidor. El coste es sincronizar dos loaders y un contrato privado nuevo, controlar intervalos ambiguos y volver a medir contexto. No se extiende autoridad a nuevos orígenes ni se añaden dependencias. La selección determinista de null ante ambigüedad debe recibir aprobación humana junto con el resto del diseño.

Estado: propuesta preparada para validación técnica TL y aprobación explícita de Paris antes de producto. Revisor/Validador independientes, aprobación final y archive específicamente autorizado siguen pendientes. Los controles de esta fase son únicamente strict OpenSpec, trazabilidad JUP, diff focal e integridad del checkpoint con prefijo original; sus resultados se adjuntan externamente al entregar, sin convertir el diseño en aceptación funcional.
