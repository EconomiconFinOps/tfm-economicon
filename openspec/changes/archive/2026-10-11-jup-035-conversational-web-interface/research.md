# JUP-035 — evidencia y comparación local

**APROBACIÓN HUMANA DEL DELTA JSONB — Paris vía Project Manager 10/10/2026 09:15:41 (Atlantic/Canary): «si hazlo».** Aprobado `jsonb-history-design.md` entregado03:20:56: esquema por conversación, final conjunto pregunta/respuesta, alternativas sin duplicar pregunta, migración003/backfill conservador y tabla histórica sin rutas activas. Autoriza adaptación Red→Green→mutación y pruebas afectadas; ventana SIN escritores y migración únicamente LOCAL AISLADA. Sustituye el estado pendiente de ejecución de esta misma propuesta; no acredita implementación ni aceptación. Conservar IDs/citas/metadata/precisión, operaciones separadas y fuente JSONB única; retirada activa exigida a Revisor, Validador y cierre PM. Presupuesto compartido0,20EUR desde02:54:46 permanece, readiness/cota/reserva antes de gasto. No producción/remoto/Git/publicación/archivo/destrucción. Versión aprobada exacta y hashes conservados externamente por TL.


**CAMBIO VIGENTE DE HISTORIAL — Paris vía PM 10/10/2026 03:01:32, con control independiente añadido03:03:01 (Atlantic/Canary).** Historial canónico: un JSONB por conversación; pregunta y respuesta completa se añaden juntas al finalizar, sin cambios al enviar ni por deltas. [Contrato concreto y migración propuesta](jsonb-history-design.md). Sustituye el mecanismo de filas `messages`, su desempate temporal y la ausencia de backfill del diseño anterior; originales/decisiones históricas conservados. Preferencia JSONB aprobada; esquema003/backfill y reescritura material pendientes de validación/despacho, SIN implementación de este delta. Los demás contratos funcionales permanecen. Nueva autorización PM02:54:46 permite pruebas reales necesarias por ruta aprobada hasta0,20EUR acumulados compartidos, con coste acotado/contador antes de llamar; sustituye únicamente la prohibición de gasto anterior. No amplía Git/publicación/remoto/archivo.


**APROBACIÓN HUMANA PRE-CODE — Paris, vía Project Manager09/10/2026 23:23:27 (Atlantic/Canary): «pues aprobado».** Aprobado el diseño consolidado entregado23:17:59 y sus contratos/spec/tareas, incluidas esperas acumuladas, persistencia, seguridad, compresión LLM, concurrencia y UI. Autoriza desarrollo local y dependencias/migración definidas SOLO en entorno aislado de pruebas. Las menciones anteriores de propuestas/pre-code pendiente quedan como antecedentes fechados sustituidos por esta aprobación; no convierten hechos externos no confirmados en integrados ni resultados NOT_RUN en PASS. Sigue propuesta configurable/no medida la capacidad8, ahora autorizada para implementación/prueba en ese alcance. No autoriza nuevas inferencias con coste, publicación, gestión Git, archivo o merge; conservar guards y Red→Green→mutación separados. Versión exacta aprobada y SHA256 conservados fuera del repositorio por TL.


> Registro histórico fechado de investigación y ensayos, no contrato vigente de implementación. Las recomendaciones preliminares se conservan como tales; compresor local, noautorretries, messages iniciales, global120 y snapshot construido en Send quedan retirados por PM21:33:08/21:46:22. Contratos actuales: [diseño](design.md), [matriz](design-decision-matrix.md) y cinco documentos técnicos enlazados. El apartado final registra resultados nuevos de inspección, sin nuevas pruebas/inferencias.

Fecha: 09/10/2026, Atlantic/Canary. Base ceb6520fd9b92c561c455cd8cbcd40aecf2c9f46.
Estado RESEARCH_READY_WITH_PENDING_DECISIONS; spike/demo/modelo NOT_RUN.
Fuentes oficiales suministradas por PM vía TL, no consultadas externamente por
Desarrollador. Comprobado significa lectura del código, no ejecución ni auditoría.

Corrección humana de Paris del 09/10/2026, vía PM15:47:28 y TL15:48:23 Atlantic/Canary: «el streaming es obligatorio de hecho creo que está en los requisitos de la jup». Streaming real es obligatorio por esta instrucción; no se atribuye a Trello una mención que PM no ha verificado. No autoriza producto, ejecución, inferencias ni spike.

Fase actual: contratos backend/conexiones/historial. Material UI y auto-scroll
de puntos1/2 queda solo pendiente de spike posterior; no se reinvestiga aquí.

## 1. Panel derecho y referencia visual

Comprobado: frontend React 18.3.1, React Query 5, router7, Tailwind; package.json
declara Vite ^5.3.3. Layout mantiene shell/sesión/selector y Outlet;
ConversationsPage tiene lista/formulario/historial y AnswerEvidence. Es una
pantalla en /assistant, no panel global persistente. TenantScopedOutlet remonta
esa pantalla por tenant. Reubicarla sin replicar su lifecycle es riesgo inferido.

Propuesta: abrir/cerrar panel fijo v1 desde shell manteniendo estilo, accesibilidad,
rutas y scoping. Preview escritorio: mitad derecha (~50% ventana) y app visible en otra mitad,
confirmado PM15:25:33/TL15:25:57. Decidir atajo, animación, foco inicial/retorno,
reduced motion y móvil mediante demo; referencia Codex restante pendiente.
Una conversación visible fija v1 no equivale a retirar la API multiconversación.

### Auto-scroll y volver al final — foco humano dentro del punto 1

Fuente: prioridad Paris vía PM09/10/26 15:27:52, TL15:28:23. Problemas previos
reportados por Paris; no reproducidos ni certificados en este despacho.
Comprobado local: ConversationsPage renderiza messages.map en contenedor normal,
sin ref/efecto de seguimiento scroll propio; AnswerEvidence incluye enlaces a
fuentes que pueden alterar posición. No se ha medido comportamiento real.

Plan focal NOT_RUN para spike sintético en media pantalla:
- En spike posterior, seguir deltas/mensajes nuevos al estar al final; streaming
  real obligatorio ya confirmado. Fixture visual no sustituye integración real.
- Al subir a leer, suspender seguimiento y conservar lectura; mostrar botón
  volver abajo, reanudar solo por acción/retorno al final.
- Definir y mostrar comportamiento de envío propio cuando se lee arriba.
- Cargar/cambiar conversación sin heredar scroll de otra identidad o thread;
  historial largo y reload, app visible en otra mitad.
- Markdown/citas/detalles que cambian altura; apertura/cierre del panel y ajuste
  de viewport, sin saltos que desplacen lectura.
- Demostración teclado/foco/reduced motion del botón y panel, sin batería exhaustiva.

Fuentes externas verificadas PM, relayed TL09/10/26 15:29:29:
[Thread primitives](https://www.assistant-ui.com/docs/primitives/thread) y
[Thread API](https://www.assistant-ui.com/docs/api-reference/primitives/thread).
Documentación actual: Viewport sigue llegada progresiva hasta scroll manual
arriba; volver al fondo/ScrollToBottom reanuda. Expandir disclosure pausa;
nuevo run/cambio de conversación termina pausa. autoScroll por defecto true
con turnAnchor bottom y false con top; Thread actual usa top por defecto.
Flags independientes scrollToBottomOnRunStart/Initialize/ThreadSwitch default
true; runstart sin efecto en top. ViewportFooter mide composer y sticky depende
del CSS. Estos son hechos de docs PM, NO comportamiento observado en nuestra
versión, layout ni integración.

Contraste propuesto, no configuración aprobada: evaluar turnAnchor bottom y
autoScroll true contra default top; probar ScrollToBottom/primitivas nativas y
flags de inicio/cambio/initialize en media pantalla antes de introducir handlers
custom. Nuevo run reinicia pausa: definir política de envío propio mientras se
lee arriba y demostrarla, no asumir que defaults cumplen intención humana.
ViewportFooter/overflow/composer deben evaluarse dentro de mitad derecha y con
Markdown/citas/disclosures que crecen. Demo sintética del spike visual no es
aceptación de streaming real; conexión gateway→generador→backend→UI obligatoria.

Primitivas primero; adaptación local solo si pruebas muestran gap concreto
de reset/anchoring/altura. No nueva librería de scroll ni virtualización sin
evidencia y aprobación. Umbral de estar al final/política envío propio/posición
al recargar quedan decisiones UX. Versión/peers aún por verificar.

Esfuerzo inferido dentro del spike: 0.5–1 día para demostración focal; adaptación
posterior 0.5–2 días si primitivas son compatibles, mayor si anchoring de historial
largo requiere nuevo contrato/paginación. Un desarrollador, fixtures sintéticos,
solo demostración UI, pendiente del spike posterior; no acepta streaming real
y solapa esfuerzo UI, no sumar. Seguridad relativa:
scroll no autoriza datos; conservar scope/limpieza/late response de adapters.
Estabilidad depende de cambios de altura y reset: no prometer solución completa
sin observar la versión compatible. Primitivas documentadas por PM; compatibilidad/limitaciones reales por verificar
en spike autorizado. No ejecución de producto.

## 2. assistant-ui y spike previo

Decisión humana de Paris del 09/10/2026, transmitida por PM15:24:08 y TL15:24:35 Atlantic/Canary: «esta es la opcion: assistant-ui + nuestra API y base de datos, no nos vamos a casar con el cloud de otra empresa en un tfm». Arquitectura seleccionada: assistant-ui + API y Cockroach propios. No es aprobación del diseño técnico final, versión/dependencia, instalación, spike ejecutable o producto.

Paquete PM 09/10/26 15:15:04, transmitido TL15:15:38:
[Custom runtime](https://www.assistant-ui.com/docs/runtimes/custom/overview),
[LocalRuntime](https://www.assistant-ui.com/docs/runtimes/custom/local-runtime),
[MIT](https://github.com/assistant-ui/assistant-ui/blob/main/LICENSE).
LocalRuntime usa ChatModelAdapter.run con messages/abortSignal y puede devolver
texto de JSON completo, dato previo que no satisface streaming obligatorio;
lector/adaptación incremental por concretar en spike posterior. ExternalStoreRuntime conserva store externo.
Multiconversación necesita adapters history/threads; no queda resuelta por estado
local. Cloud/telemetría separadas, sin autorización de activación ni necesidad
demostrada. Preservar aviso MIT si se adopta. Versión/peers pendientes: la lectura
local del manifiesto NO demuestra compatibilidad de la librería actual.

| Alternativa | Solución | Seguridad prevista y motivo | Estabilidad prevista y motivo | Esfuerzo orientativo |
| --- | --- | --- | --- | --- |
| UI actual (solo fallback si incompatibilidad) | Conservar servicios/React Query/AnswerEvidence | Menor superficie nueva; mantener controles existentes, pruebas necesarias | Alta continuidad; más UI mantenida por equipo | Pendiente spike |
| assistant-ui ExternalStoreRuntime | Presentación sobre store/API actuales; traducción de mensajes/citas | Favorable sin Cloud, pero adaptación/metadata y reset deben validarse | Media hasta spike; menos estado duplicado | Pendiente spike |
| assistant-ui LocalRuntime | run con eventos incrementales más adapters history/threads persistentes | Condicionada al scoping/cancelación; estado adicional riesgo | Media-baja inicial por sincronización/hidratación | Pendiente spike |

Estimaciones UI anteriores sin tratamiento incremental retiradas: se afinarán
en spike posterior. No se investigan aquí ni se presentan como resultado de
compatibilidad. Rango streaming backend/conexiones revisado en punto3.

Plan de spike NOT_RUN (medio a un día técnico, excluye instalación/aprobaciones):
fijar versión/peers con PM; sandbox externo aprobado y sin datos reales; evaluar
ExternalStoreRuntime sobre API/DB propias primero, LocalRuntime si aporte claro.
UI actual solo referencia/fallback condicionado a incompatibilidad y decisión humana.
Fixtures sintéticos con texto/citas/metadata/no_data/error; rehidratar GET simulado,
switch conversación, tenant y usuario; abort/late response; inspeccionar foco,
teclado, móvil, estilo y composición/legibilidad con chat mitad derecha (~50%) y app visible, sin Cloud. Entregar capturas, mapa de adapters,
dependencias/licencia y resultado compatible/no compatible/pendiente.
Criterio de salida: sin pérdida de metadata ni mezcla de identidad, persistencia
backend como fuente de verdad y estados accesibles; si falla, informar incompatibilidad y proponer fallback a Paris sin sustituir su elección unilateralmente.
STOP antes de demo/backend, adopción o producto. Cada ejecución futura necesita
nuevo despacho/guard; aquí solo se redactó el plan.

## 3. Conexión directa: decisiones funcionales aprobadas y compatibilidad pendiente

## Decisión humana registrada — 09/10/2026 16:48:09 Atlantic/Canary

Paris confirma «nos quedamos con las opciones recomendadas», transmitido por PM.
Quedan aprobadas las decisiones funcionales: Detener explícito con propagación
best effort; ocultar el panel no cancela; interrupción conserva parcial identificado
como incompleto, fuera del contexto posterior; reintento humano crea otra generación
sin duplicar pregunta; persistencia inicial + terminal, sin checkpoints periódicos.
Se acepta perder el fragmento en RAM ante caída completa del servidor, preservando
la pregunta y las respuestas completadas persistidas.

No es aprobación pre-code del diseño completo ni permiso para implementar o hacer
inferencias. Compatibilidad real endpoint/gateway con streaming + schema sigue
pendiente de comprobación específica; contratos/transacciones y pruebas siguen
pendientes. Ocultar el panel conserva la generación y su estado: si realmente se
desconecta la sesión o transporte, se aplica el contrato de interrupción distinto
de la acción de ocultar.

Fuente de este encargo: Paris vía PM09/10/26 16:16:04, TL16:16:57
Atlantic/Canary. Conexión streaming directa preferida; RabbitMQ SOLO ingesta.
Arquitectura assistant-ui + API/Cockroach propios, streaming real y preview ~50%
siguen confirmados. Las decisiones funcionales 1–3 están aprobadas PM16:48:09; sus contratos técnicos y la compatibilidad real NO son diseño final aprobado.
assistant-ui/auto-scroll, instalación, ejecución y prueba real: spike posterior.

### Configuración pública comprobada, no secretos ni runtime inferido

| Fuente pública | Configuración declarada | Límite de la evidencia |
| --- | --- | --- |
| processor/core/config.py:26–33, Compose:167–174 y .env.example:66–83 | Default mock; llm_model economicon-chat; timeout30s, max_retries2, max_output_tokens800 | Defaults/techo real-provider; no lectura de dotenv real ni prueba de proceso activo |
| infra/litellm/config.example.yaml:2–13 | economicon-chat → openrouter/z-ai/glm-5.2; only deepinfra/fp4, require_parameters true, allow_fallbacks false | Compose normal monta este archivo readonly; overrides/despliegue efectivo no comprobados |
| config.example.yaml:17–26 | economicon-chat-deepseek → openrouter/deepseek/deepseek-v4-pro; allow_fallbacks false | Alias separado; no only/require_parameters equivalentes declarados, no fallback automático ni selección nueva |
| infra/litellm/docker-compose.yml:5 y ADR0016 | Digest f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd, identificado como LiteLLM1.103.2 | Imagen fijada en repo, no inspección de contenedor activo; conservar pin |
| requirements de backend/processor | FastAPI>=0.111.0, Uvicorn>=0.30.1, SQLAlchemy>=2.0.31, sqlalchemy-cockroachdb>=2.0.4,<3.0 | Rangos, no versiones resueltas; Starlette/Pydantic efectivos no se certifican |

economicon-embedding
→ openrouter/openai/text-embedding-3-small; no es modelo de generación.
Este mapa es público/configurado en repo; entorno runtime real y capacidades
no se deducen del nombre del modelo. No se consultaron .env, claves ni overrides
privados. README configuración evaluation rechaza mock; no se activa aquí.
Gateway/router retries0 en config; el cliente completo actual admite hasta2:
para camino streaming proponer cero reintentos automáticos de generación.

Comprobaciones locales previas se reutilizan: gateway client response.read/json.loads,
provider sin stream, runtime valida FinOpsResponse completo y cliente response.json.
Backend autentica tenant/usuario, guarda pregunta antes de retrieval; cada
append_message abre su propia transacción. Hay conversations/messages con
metadata JSONB pero no registro de generación ni garantía de idempotencia.
No afirmar que los métodos actuales ya implementan las propuestas.

### Decisión 1 funcional aprobada; contrato técnico pendiente — cancelación explícita y propagada

Botón Parar envía cancelación autenticada del generation_id propio al backend,
y aborta el lector de stream. Cancelación no lleva texto parcial del navegador.
Servidor comprueba tenant Y propietario, marca cancelled si sigue running y
ordena parar generador/relay/lectores y cerrar upstream. Solicitud repetida es
idempotente; al cerrar toma el buffer disponible del backend en la misma
transacción terminal (si no existe, parcial vacío), sin otra escritura posterior
para completar el borrador. Si completed ya ganó, devuelve completed y conserva
resultado, sin sobrescribirlo. Abort/disconnect sin orden confirmada se clasifica
interrupted; si cancelación explícita fue registrada, prevalece cancelled.

Propagar a processor/gateway con best effort y cleanup en finally. No garantía de
parar cómputo o coste upstream; reflejar usage disponible o unavailable, nunca
inventar cero ni contabilidad nueva. Si control cancelar falla401/red, UI puede
parar localmente pero el estado duradero solo se afirma tras confirmación/GET.
Propuesta asume despliegue TFM sin nuevas colas/servicios; señal local de proceso
no sustituye marcador DB compartido ni autoriza cancelación de otro usuario.

### Decisión 2 funcional aprobada; contrato técnico pendiente — parcial visible, terminal inequívoco

Estados de generación: running; terminal completed, cancelled, interrupted o
error. FinOpsResponse.status=partial puede ser respuesta COMPLETA validada con
cobertura parcial: no es el estado de transporte interrupted.
Deltas visibles son borrador; jamás respuesta validada por token. Conservar
scope y generación de sesión en cada frame, como en investigación anterior.

Cancelación o interrupción manejada: guardar una única instantánea final del
texto parcial en metadata.generation.partial_text, content vacío, estado/razón
saneada. Se muestra solo como respuesta incompleta si el cliente futuro aplica
el contrato; no se incorpora al contexto de nuevas preguntas, métricas ni citas
confirmadas. Error de schema/citas: guardar razón saneada, sin conservar como
content confirmado el texto rechazado. No se propone un filtro semántico por token
ni impedir mostrar fragmentos antes de validación final.
Legacy sin metadata.generation sigue legible, sin inventarle validación nueva.
Contexto conversacional041 sigue fuera del alcance: exclusión de incompletos es
restricción de los datos futuros, no implementación de memoria.

### Decisión 3 funcional aprobada; contrato técnico pendiente — inicio + cierre, sin checkpoints de cada delta

Reusar tables actuales, sin nueva tabla/cola ni migración dada por aprobada.
Inicio en una transacción nueva: comprobar propietario, serializar sobre fila
de conversación y reservar pregunta + mensaje assistant vacío con metadata
generation version1, request_id, question_message_id, state running y deadline.
generation_id puede ser ID de ese mensaje assistant. Es modificación futura
de método transaccional, no dos append_message independientes ya suficientes.

Cierre único y condicional: bajo el mismo ownership/transacción, completar
content + FinOpsResponse/citas validadas + metadata si sigue running; o terminal
cancelled/interrupted/error con sus metadatos. Emitir evento final UI únicamente
tras commit. Atomicidad/race requiere bloqueo/condición sobre fila de conversación
y actualización de estado; comprobar driver/Cockroach y serialización antes de
afirmar ausencia de duplicados. No asumir que un request_id en JSONB es constraint
UNIQUE. Si no se garantiza sin cambio de schema, devolver decisión de migración
al PM en lugar de prometer idempotencia.

Request_id reutilizado por mismo request de transporte, scoped a tenant+usuario+
conversación: recuperar misma generación/estado, no crear pregunta ni llamada
nueva; mismo ID con contenido distinto se rechaza. Una generación activa por
conversación, duplicado409 con referencia propia. No reconexión que regenere.
Reintentar requiere acción humana: nueva generación/request_id ligada a la
pregunta existente y ownership verificado, sin duplicar pregunta ni continuar
una respuesta cortada como si fuera la original. Historial conserva intentos.

Deltas solo en memoria. Caída de proceso antes del cierre: registro running
permanece hasta reconciliarlo por deadline/propietario con interrupted; el parcial
en RAM se pierde. Recuperación en reload/arranque no vuelve a llamar al modelo;
cierre conditional evita degradar un completed concurrente. En despliegue de
varios procesos, TTL/ownership de productor requiere diseño probado; no añadir
infraestructura ahora ni usar “no está en mi memoria” como prueba de caída.
Paris acepta esta pérdida parcial ante caída completa del servidor PM16:48:09.
Decisión aprobada: inicio + terminal, sin checkpoints periódicos; conservar
pregunta y respuestas completadas persistidas. No queda una pregunta pendiente
sobre ese tradeoff; compatibilidad real y diseño técnico siguen pendientes.

Final válido: validar FinOpsResponse1.0, pertenencia y citas025, persistir y
notificar una vez. finish_reason puede repetirse en chunk de usage: registrar
sin cerrar dos veces. Fin del protocolo y resultado válido preceden a completed;
HTTP 200, un finish_reason aislado o EOF prematuro no lo acreditan. Usage/coste
ausentes = unavailable; no prueba de coste cero.

### Decisión 4 propuesta — alias principal y gate real de compatibilidad

Mantener economicon-chat/GLM5.2/DeepInfra-fp4 y pin ya declarados; no cambiar
modelo/proveedor ni activar fallback. require_parameters true restringe rutas
que declaran soporte, no prueba stream+strict schema ni semántica FinOps.
Alias secundario DeepSeek no se toma como equivalente probado.

Datos PM16:16:41 vía TL16:17:13:
[Structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs),
[Routing](https://openrouter.ai/docs/guides/routing/provider-selection),
[LiteLLM JSON mode](https://docs.litellm.ai/docs/completion/json_mode),
[Streaming](https://openrouter.ai/docs/api_reference/streaming).
Schema depende endpoint/proveedor; stream:true permitido en compatibles.
get_supported_openai_params/supports_response_schema son declarativos; no prueban
stack. Usage final puede repetir finish_reason; terminal único como arriba.

PM16:19:01 vía TL16:19:42 consultó
[GLM providers](https://openrouter.ai/z-ai/glm-5.2/providers) y
[DeepSeek providers](https://openrouter.ai/deepseek/deepseek-v4-pro/providers):
lectores/API/DNS no aportaron parámetros verificables del endpoint concreto.
Resultado PENDING, no unsupported ni compatibilidad PASS. No repetir investigación
externa ni hacer inferencia para solventarlo sin autorización.

Gate futuro, no ejecutado: referencia saneada de alias/endpoint/imagen/versiones
efectivos; petición stream:true con schema COMPLETO FinOpsResponse1.0 y política
de rutas; comprobar deltas antes de terminar productor, schema preservado y
validación final/citas; error, cancelación, usage/terminal único. Documentación
o smoke JSON completo previo023 no sustituyen esta combinación. Requiere nuevo
despacho, permisos/budget si prueba real y evidencia saneada; no pedir nueva
elección del modelo si el ya configurado pasa. Si falla, retornar limitación
concreta al PM: endpoint aprobado compatible o variante narrativa+validación
de aplicación que requiere decisión de contrato024, sin degradación silenciosa.

### Transporte vigente y esfuerzo revisado

Candidato preferido POST fetch + SSE: auth Bearer/X-Tenant-Id existentes; backend
proxy de streaming directo gateway→processor→backend→UI. NDJSON es alternativa
de framing directo. Se retira RabbitMQ de opciones vigentes del chat: SOLO ingesta.
Guardrails JSON incremental/alternativa narrativa siguen en design; las fuentes
Fetch/FastAPI anteriores se preservan en el paquete histórico externo de entrada,
sin nueva investigación.

| Propuesta actual | Seguridad prevista y motivo | Estabilidad prevista y motivo | Esfuerzo inferido |
| --- | --- | --- | --- |
| Enlace directo SSE/fetch + inicio/cierre duradero | Condicionada a auth/ownership/CAS y validación final; no certificar borrador | Media: cleanup/reconciliación, sin cola chat ni checkpoints | 9–16 días |
| Mismo diseño NDJSON | Mismos permisos y estados; framing no autoriza datos | Media: decoder propio/UTF8 y EOF; misma persistencia | 9–16 días |

Rango revisa8–14 por cancelación controlada/marcadores/idempotencia/reload mínimos.
Un desarrollador, entorno operativo y compatibilidad del alias comprobada antes
de implementar; incluye transporte/iterador/cliente genérico, persistencia/
terminales y pruebas de enlace/concurrencia/Cockroach. Excluye spike/adapters UI,
036/037 pendientes, cambios de provider/migración, auditoría, revisión humana,
despliegue y esperas. No compromiso; trabajos solapados, no sumar.
Checkpoints de parcial o despliegue multiproceso podrían ampliar diseño/rango
y requieren decisión, sin introducirlos unilateralmente.

### Registro histórico de opciones retiradas

La comparación anterior del09/10/2026 proponía cola chat con deltas11–19 días y enlace
directo8–14; queda como registro de investigación sustituida, NO alternativa
vigente ni recomendación actual. El texto íntegro previo y hashes se conserva
en el paquete externo de entrada de este encargo (prior-documents/research.md)
y sus hashes; entrega del paquete al TL. RabbitMQ permanece en ingesta.

## 4. JUP-036 y JUP-037 P1

Paquete oficial PM 15:15:04: [PR69 JUP036](https://github.com/EconomiconFinOps/tfm-economicon/pull/69)
abierta DRAFT, head aee2571e038f2b6d7071a7cb055b06b968d67a0e, mergeable=false al
consultar; NO integrada en base. Gasto Azure ingerido por suscripción/cuenta de
facturación/servicio, periodo UTC/ámbito explícitos, SQL parametrizado, monedas
separadas y snapshots/ingestas persistidos. No NL libre ni Azure real.
JUP037 P1 por proyecto/app/cost center según export oficial16; dependencias por
refinar, rama/PR actual pendientes de confirmación PM. No disponibilidad supuesta.

Local: azure-cost-query-contract define simulador versionado, scope subscription,
Custom from/to, agregación actual, filtros/grupos permitidos y moneda. Contrato
FinOps limita SQL/HTTP/shell arbitrarios y cálculos hechos por código. Un spec no
es backend funcional. UI context no crea tags/dimensiones inexistentes.

Dependencia: conectar herramientas/coste solo tras integración verificada o
contrato aprobado de capacidad no disponible. Hasta entonces synthetic demo y
mensajes unsupported/no_data apropiados; no ficticios costes reales.
Pregunta PM: entrega/alcance exacto036/037 y política para capacidad pendiente.

## 5. Historial: corregir frente a sustituir

Comprobado database.py:
fetch_conversations y fetch_conversation WHERE tenant_id AND user_id;
append_message exige requester y propietario en INSERT SELECT y UPDATE;
assistant.user_id null no elude requester_id; fetch_messages JOIN conversación
con tenant/usuario. JSONB decodifica solo str y conserva objetos.
Backlog local RF087002 (fila126) Fixed, corrección086 y verificación104 reportadas,
pero sin test automatizado real Cockroach; no repetimos esas verificaciones ni
las certificamos. RF083002 (fila111) Open es visual/auth/datos, no prueba de bugDB.

SessionGate controla generaciones, invalida/limpia queries/mutaciones en logout
y reemplazo de identidad; TenantScopedOutlet remonta por tenant. Keys de chat
incluyen tenant/conversación, no user: evaluar en contexto lifecycle completo,
no afirmar filtración. Panel persistente debe preservar reset/ownership y
rehidratación; plan de pruebas en design.

Recomendación: conservar API/persistencia actual y planear regresión Cockroach
crear→enviar→leer→recargar contenido+metadata/citas; otro tenant y otro usuario
del mismo tenant 404; usuario no miembro403; logout/tokenexpiry/late replies.
Agregar clave/lifecycle explícito por identidad si el diseño global lo requiere.
Reparación localizada 1–3 días adicionales a UI/adaptador, asumiendo no migración;
sustitución 5–10+ días y diseño/migración autorizados solo si evidencia lo exige.
No necesidad comprobada de reemplazo ni garantía transaccional de turno completo:
ruta guarda user antes de retrieval, respuesta después; definir recuperación de
fallo y duplicados. No probar funcionalidad en esta fase.

## Historial assistant-ui sobre API y Cockroach propios — arquitectura seleccionada

Decisión humana de Paris del 09/10/2026, transmitida por PM15:24:08 y TL15:24:35 Atlantic/Canary: «esta es la opcion: assistant-ui + nuestra API y base de datos, no nos vamos a casar con el cloud de otra empresa en un tfm». Arquitectura seleccionada: assistant-ui + API y Cockroach propios. No es aprobación del diseño técnico final, versión/dependencia, instalación, spike ejecutable o producto.

Fuentes PM09/10/26 15:17:47, relayed TL15:18:16:
[Custom persistence](https://www.assistant-ui.com/docs/integrations/persistence/custom-adapter),
[Adapters](https://www.assistant-ui.com/docs/api-reference/adapters/persistence),
[Threads](https://www.assistant-ui.com/docs/runtimes/concepts/threads).
RemoteThreadListAdapter administra metadatos y ThreadHistoryAdapter mensajes
contra DB propia. Ejemplo session.user.id no demuestra nuestro tenant+usuario.
scopeId estable por thread/account/workspace y cambio antes de otro ámbito
controlan UI; NO autorizan backend. Sin adaptador, memoria se pierde al recargar.

Solución a concretar: sustituir experiencia/interfaz de historial con assistant-ui,
mantener endpoints/IDs y Cockroach como fuente de verdad, mapear thread metadata,
mensajes y citas, scopeId tenant+usuario+generación; evitar un segundo almacén.
Evaluar ExternalStoreRuntime para preservar React Query frente a LocalRuntime con
adapters persistentes. La corrección JSONB no impide reemplazar la experiencia.
No se estudia más Cloud: excluido por decisión humana.

| Integración seleccionada | Seguridad prevista y motivo | Estabilidad prevista y motivo | Esfuerzo inferido |
| --- | --- | --- | --- |
| assistant-ui + adapters a API/DB propia | Favorable condicionada: backend aplica tenant y propietario; verificar cada operación y cambio de scope/identidad, scopeId no es permiso | Media hasta spike; una DB y operación existente, nuevo mantenimiento adapters/versiones | 5–8 días (revisado por estado provisional/final) |

Rango orientativo posterior, no investigación UI de esta fase: un desarrollador
con entorno operativo, adapters/historial y estado provisional/final streaming; pruebas
básicas; excluye transporte gateway–processor–backend–UI estimado en punto3,
migración histórica material, revisión humana,
esperas y despliegue. Solapa rangos UI, no sumar. No hay migración aprobada ni
necesidad demostrada: historial/metadata existentes deben conservarse.

Spike futuro: tenants/usuarios sintéticos A1/A2/B1; listar/inicializar/leer/enviar
thread conservando permisos de todos los endpoints; rehidratar historia/citas;
otro usuario mismo tenant y otro tenant; cambio de scope durante petición,
cancelación/late reply, logout/relogin, recarga. Confirmar que scopeId cambia
antes de usar nuevo ámbito y que servidor rechaza ownership ajeno.
Version/peers y contrato detallado adapters siguen PENDING; no instalación,
servicio nuevo, ejecución ni aceptación funcional en este despacho.

## 6. UI Context Awareness, separado de JUP-041

| Alternativa | Solución | Seguridad prevista y motivo | Estabilidad prevista y motivo | Esfuerzo inferido |
| --- | --- | --- | --- | --- |
| Entrada explícita mínima (preferida) | Pantalla, periodo UTC, filtros/dimensiones elegidos y versión; usuario ve ámbito; servidor vuelve a validar | Favorable condicionada: datos cliente no autorizan; allowlist, membership y ownership servidor | Alta comparativa: schema pequeño y navegación conocida | 1–3 días |
| Referencia a snapshot autorizado | Backend resuelve ID de consulta/resultado del dashboard y comprueba tenant/usuario/caducidad | Favorable condicionada: menos datos manipulables, pero requiere resolver referencias | Media: snapshot reutilizable solo si contrato disponible, 036 no integrado | 3–5 días |
| Captura automática de DOM | Interpretación de pantalla/filas/HTML | Desfavorable: datos de presentación no confiables y riesgo de exposición innecesaria | Baja: cambios UI rompen extracción | 4–8+ días; no recomendada |

Rangos con entorno operativo, excluyen integración/esperas036 y UI base. Propuesta
mínima no incluye historial como memoria del modelo; JUP041 sigue fuera.
Servidor ignora cualquier tenant/user/role/control sugeridos por UI o LLM.
Contexto desconocido/stale/foreign: rechazo o solicitud de elección explícita
según contrato aprobado; nunca silently aplicar otro scope. No mandar tokens,
HTML ni filas completas, y no confundir datos sintéticos con dataset autorizado.
Confirmar pantallas/dimensiones v1, consentimiento/visualización y política
de contexto persistido en cada mensaje.

## 7. Demo sintética y aprobación antes de backend

NOT_RUN. Fixtures de conversación, costes ficticios, citas sintéticas y estados,
claramente rotulados; cero gateway, credenciales, datos reales o Cloud. Demo
sigue spike si se autoriza; mostrar panel abierto/cerrado/móvil, citas e historial,
y context Awareness visible. Paris aprueba antes de conectar backend.
Aprobación demo no sustituye aprobación diseño/dependencia/pre-code.

## Evidencia local reproducible (solo lectura)

- apps/frontend/src/pages/ConversationsPage.tsx: queries/mutations y AnswerEvidence.
- apps/frontend/src/layouts/Layout.tsx: shell y TenantScopedOutlet.
- apps/frontend/src/layouts/SessionGate.tsx: sesión, identidad, generaciones y cache.
- apps/frontend/src/services/api.ts y contracts.ts: rutas y metadata extensible.
- apps/frontend/src/components/AnswerEvidence.tsx: componente a preservar; no aceptación runtime aquí.
- apps/frontend/package.json: dependencias declaradas, sin instalar.
- apps/backend/app/api/routes/assistant.py, api/dependencies.py, services/assistant.py:
  autorización, retrieval/citas y respuesta plantilla.
- apps/backend/app/db/database.py: conversación/ownership/JSONB.
- apps/processor/app/main.py, workers/runner.py, graphs/pipeline.py:
  superficies actuales HTTP/ingesta, sin chat público inferido.
- apps/processor/app/agents/{service,providers,prompts,guardrails,schemas}.py:
  runtime de eventos, gateway y respuesta estricta.
- apps/processor/app/clients/{litellm,rabbitmq_queue}.py: transportes existentes.
- openspec/specs/{frontend-navigation-shell,answer-citations,semantic-retrieval,
  finops-response-guardrails,finops-agent-tool-contract,azure-cost-query-contract}/spec.md:
  contratos, no certificación de implementación.
- openspec/findings/backlog.md: RF083002 Open/RF087002 Fixed, hechos locales.
- apps/backend/tests/test_retrieval_contract.py y tenant_isolation_support.py:
  fuentes de estrategia existente; no ejecutadas ni sustituyen Cockroach real.

Fuentes/receipts/SHA256, integridad y comandos nativos se entregan externamente al
TL. Solo se escribieron documentos de este change; no evidencia de aceptación
funcional, seguridad certificada, spike ejecutado ni permiso de publicar.


## Actualización del 09/10/2026 — experimento y spike autorizado

Esta actualización sustituye los estados pendientes del ensayo real indicados en
las secciones históricas anteriores. Paris autorizó el ensayo sintético del
gateway mediante PM16:54:10, techo total 0,05 EUR, y el spike visual mediante
PM17:45:05; PM18:03:19 confirmó instalación únicamente experimental externa.
No confiere aprobación del diseño completo, adopción de producción o backend.

El Desarrollador ejecutó dos llamadas reales, sin retries automáticos, con el
mismo request, esquema FinOpsResponse completo, strict, alias, max_tokens=800,
pin LiteLLM1.103.2 y configuración. Primera: 103 deltas, 2,281 s al primer
fragmento, 5,828 s al cierre; el validador existente rechazó el final con
AgentResponseError. Su contenido no se conservó: causa UNKNOWN. Segunda:
84 deltas, 1,390 s al primer fragmento, 7,656 s al cierre; stop, DONE único y
EOF. JSON y parse_and_validate_response existentes, incluidos campos Pydantic,
model validators y guardrail numérico, PASS. Respuesta solo sintética conservada.
Una muestra válida acredita el recorrido mínimo observado, no fiabilidad general
ni causa del fallo previo. JSON Schema wire por separado NOT_ISOLATED, sin
instalar dependencia; proveedor upstream no informado por SSE, solo alias.

Contador total_spend acumulado del gateway: 0,00138396 USD (~0,001235 EUR con
1 EUR=1,1206 USD); no factura del proveedor ni tokens/usage de SSE. Reserva
conservadora de ambas llamadas, incluido fallo: 0,0160695 EUR ≤ 0,05 EUR.
Informe externo attempt2/experiment-report.json SHA256
e8edcfd7f9593040607d3b6f1ba1833da163c9c97bb055e498b73e2a1cbb6e68,
root del Desarrollador jup035-real-stream-experiment-20261009. Guard original
y control TL PASS sin cambios en 972 archivos; HEAD/branch/index preservados.

[OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
admite JSON parcial en streaming y condiciona strict al proveedor.
[Streaming](https://openrouter.ai/docs/api_reference/streaming) distingue errores
en HTTP 200 y usage final. [LiteLLM streaming](https://docs.litellm.ai/docs/completion/stream)
y [JSON mode](https://docs.litellm.ai/docs/completion/json_mode) describen deltas
y validación de esquema opcional. Docs actuales no prueban el pin por sí solas
ni sustituyen reglas propias. No se atribuye una causa no observada.

La caducidad local HTTP401/CREDENTIAL_EXPIRED originó
[RF-035-001](../../findings/backlog.md), Open, fuera de alcance, responsable por
acordar; seguimiento interno P2. La renovación autorizada de la misma clave por
24 horas no lo cierra ni impone autorrenovación. No caída de producción probada.

Spike visual externo en jup035-assistant-ui-spike-20261009/demo: assistant-ui
real 0.15.26, LocalRuntime sintético, React18.3.1/Vite5.4.21; dependencia transitiva
assistant-cloud declarada, sin servicio ni claves, cero tráfico externo runtime
por comprobar. Panel derecho 50vw, app sintética izquierda, historial fijo v1,
iconos abierto/cerrado, animación180ms/reduced-motion y atajo propuesto. Plan
comprueba seguir/pausar/reanudar scroll, envío, historial, citas, abrir/cerrar,
Stop/error y tamaños escritorio. Diseño externo preparado y guard PASS; demo
aún NOT_RUN a esta actualización. No backend/proveedor/pago ni adopción producción.


## Ajuste autorizado del spike — 09/10/2026

Paris, vía PM18:55:20 Atlantic/Canary, sustituye la lista fija del prototipo
por una barra de historial ocultable en el extremo derecho, superpuesta al chat
sin estrecharlo ni desplazar la app. Historial abre Nueva conversación/lista;
seleccionar otra conversación cierra la barra y mantiene el panel principal
abierto. Nueva conversación inicia un hilo vacío sintético. Esta instrucción
autoriza el ajuste experimental, no adopción o aprobación de producción.

Demo externa entregada a las 19:08:29: assistant-ui real, panel50vw, 31
comprobaciones afectadas PASS (apertura/cierre/selección/creación/foco/teclado,
geometría y scroll). No se repitieron las27 iniciales. Tipos/build PASS; warning
bundle689,67kB/207,33gzip conservado. Sin dependencias nuevas/backend/Cloud/pago.
Guard original y contraste TL PASS sin cambios; negativos preservados.
Informe externo spike-report.json SHA256
8851a93a6a3a6c5e0e99238a030fd1f1a05f7ace6eff773098093e73fd681b31.
API/DB/integración real, diseño definitivo y aceptación independiente siguen
pendientes. Esta actualización prevalece sobre historial fijo del spike anterior.


## Aprobación humana del spike — 09/10/2026

PM19:13:37 transmite Paris «me gusta aprobado» tras ver demo45135. Spike
cerrado satisfactoriamente: panel50%, estilo mostrado, historial ocultable
superpuesto derecho, selección cierra historial y mantiene chat abierto, Nueva
conversación. Conservar prototipo/evidencias; sin nuevas iteraciones ni pruebas
repetidas. No aprobación backend/migración/dependencia productiva ni aceptación
final. Propuesta consolidada y decisiones materiales pendientes en [design](design.md).


## Actualización vigente — diseños y caché 09/10/2026

Las comparaciones previas conservan su fecha y alcance. Estado vigente en [design](design.md),
[historial](history-persistence-design.md) y [prompts/contexto](prompt-context-design.md).
Adopción assistant-ui aprobada PM19:23:15; ExternalStoreRuntime seleccionado para
historial real, LocalRuntime queda como evidencia del spike. Paris delega diseño
de persistencia PM19:25:04 y aprueba función prompts/snapshot completo PM19:42:02.
No migración/producto autorizados. PR69 JUP-036 draft head aee2571e038f2b6d7071a7cb055b06b968d67a0e
sí tiene cost_query determinista/cost_evidence, sin NL/LLM; candidato conflictos no publicado,
no integración asumida (PM19:28:08). JUP-037 contrato no confirmado.

PM19:47:29 autoriza solo ensayo caché2 llamadas/0,01 EUR. Evidencia externa
C:/Users/Trabajo/.codex/visualizations/2026/10/04/01a10801-299d-7ee0-866d-0efd78b883e5/jup035-prompt-cache-spike-20261009/experiment-report.json
SHA15cc1d0d7c05bde728e62d1b30432016a27394f8afd8aa93dc55c6c48df3e3ed.
HTTP 200 prompt4053/completion2/cached_tokens0, luegoHTTP 429 sin usage; INCONCLUSIVE.
Reserva0,0084183 EUR incluye ambos; gatewaydelta0,0022834125 USD no factura certificada.
LiteLLM1.103.2/confige522a606…/imagenf63fb81b… sin cambios, dosrequests sintéticos
secuenciales/sufijo distinto, maxoutput16/retries0/sin nuevos parámetros de caché.
DeepInfra observado primera, upstream model no inferido desde alias. Guard original
a12c5c0864298f52aa05362f02257005f0144187061575ef87ebc5e64cf0af0e PASS sin cambios
y contraste TL preservados. No tercera inferencia ni compatibilidad general demostrada.

Diagnóstico TL solicitado PM19:59:56 en evidencia externa TLROOT/jup035-429-documentary-diagnosis.md.
Fuentes oficiales https://openrouter.ai/docs/api_reference/limits y
https://openrouter.ai/docs/api_reference/errors-and-debugging . Recibo no conserva
body/headers error: origen429indeterminado, maxparallel1 no causa probada.
Siguiente acción solo captura saneada en futuras pruebas ordinarias autorizadas.
Caché opcional/prefijo estable; no gate ni memoria conversacional041.


## Actualización final de caché — autorización PM20:09:10

Paris exige comprobar caché antes de implementación y autoriza hasta 10 inferencias
adicionales, levantando0,01 EUR solo para ese ensayo. Esto sustituye el anterior
estado de caché-no-gate humano; el funcionamiento seguirá correcto con cache miss.
Resultado HIT_OBSERVED tras **una** inferencia adicional y STOP temprano: HTTP 200,
4.053 tokens de entrada / 2 de salida, **3.840 cached_tokens**, proveedor DeepInfra reportado, alias
economicon-chat. Prefijo idéntico y pregunta/respuesta distintas del primer ensayo;
sin cache_control, retries, fallback o modificación de modelo/config/pin/clave.
Misma ruta configurada LiteLLM1.103.2→OpenRouterGLM5.2→deepinfra/fp4.
Tres intentos entre ambos ensayos (200sin cache,429sinusage,200hit), no12 ni diez
consumidos. Evidencia positiva de lectura de prefijo cacheado en esta combinación;
no hit universal, duración/umbrales garantizados o prueba de la vertical producto.

Coste reportado por gateway adicional0,0005266125 USD; reserva conservadora adicional
0,00420915 USD, no factura certificada. No confundir meter pendiente con coste cero.
Reporte externo jup035-prompt-cache-followup-20261009/experiment-report.json
SHA256 c2d5b84a284ac92638d52931be0e11757e925d04658a57e498e1267d884e3a3e.
El 429 anterior sigue de causa/origen indeterminados; captura de diagnóstico
saneada corregida para el followup, sin nuevo429 observado. No repetir para
diagnosticar el anterior. TL remite resultado positivo a PM para el gate solicitado
por Paris; no equivale a pre-code completo ni aceptación general.

## Reconciliación de conclusiones preliminares — 09/10/2026, 21:07–21:17

Los apartados anteriores conservan la investigación y las decisiones de sus fechas. Las frases «sin memoria» o «041 fuera» preliminares quedan sustituidas para el mínimo QA de JUP-035 por PM21:07:33: propuesta extractiva local persistida, sin inferencia adicional, originales intactos; memoria avanzada041 sigue fuera. La caché es opcional en producto; la condición del ensayo cache ya fue satisfecha y confirmada PM20:20:45.

Paris corrige global1: exclusión por conversación, chats privados concurrentes y scope completo; capacidad8 es propuesta operativa, proveedor no probado. Aprueba límites1MiB/8192 y JSON por pestaña, no reparto específico ni capacidad del alias. Elige red privada autenticada/HTTP interno en un DockerServer, sin certificados internos rutinarios; HTTPS externo y reevaluación entre hosts permanecen. Diseño vigente en [delta QA](context-compression-extension.md) y [plan de integración](integration-readiness-plan.md); no nueva evidencia conductual, infraestructura o gasto.

## Inspección actual y decisiones reconciliadas — PM21:33–21:54

Backend dosappend no atómicos; chat nuevo requiere operación durable y pareja final única. Cliente processor retries anidados y roles aplanados no cumplen chat, adaptador conservando roles y retries0 de transporte con retry funcional backend máximo4. DNS supervisado, framing/fences y scheduler descritos en plan actual. No investigación de esas piezas pospuesta a ejecución.

LiteLLM fallback de tokenizer no acredita GLM: elección tokenizers0.22.1+artefacto ZAI fijado aprobada PM21:54:52; fuentes/revisión/hashes y compatibilidad declarada en prompt-context-design.md, ejecución/build/conteo focal futuros. Resumen por LLM aprobado, fuente QA solamente y estimación/capacidad en delta; localextractivo retirado y cero coste previo no aplica a la solución vigente.

Registros/spikes anteriores conservan alcance y negativos: visual sintético, gateway mínimo y hitcache no aceptación vertical. Ninguno repetido. CompresorLLM, registrooperacional/migración en diseño,120×4 y contador ya aprobados; Retry-After era pendiente en ese registro y queda resuelto por PM22:37:04 abajo; detalles/cobertura/keys/budgets/capacidad/036/037/pre-code restantes en matriz, sin permiso de gasto/configuración por arrastre.

## Revisión de tres puntos — PM22:14:44

Cliente actual30s es total HTTP monotónico, no idle renovable; recomendación de chat recibe restante120s menos margen final5s sin clamp30/idle20, y override gateway server-side documentado, no ejecutado en pin. Resumen por ventana reciente no era acumulativo: se retira como propuesta vigente, recomendando anteriorQA válido+QA nuevos consecutivos, frontera/lineage/ledger, backlog y degradación explícitos, rebuild por fuente antigua y coste por lote. Los datos pantalla siguen excluidos.

Fuente oficial PM: relacionadas036037070, «lo que integren036037».036 contrato referencia de diseño sin esperar merge;037 condicional a capacidad/criterio confirmado, sin bloqueo universal inventado por relación/P1. Registros anteriores que asumían ausencia037 como gate son históricos retirados, no contrato vigente. Fuente pendiente distinta de aceptación conocida que no se probó. Sin nuevos ensayos, servicios, dependencias instaladas, cambios Git o gasto; originales preservados.

## Registro histórico Retry-After — PM22:37:04 (interpretación por intervalo sustituida por PM23:05:12)

Decisión humana PM22:37:04 del09/10/2026: espera automática Retry-After hasta120 s (dos minutos); si el proveedor exige más, pausa visible, conservando solicitud, contador y retry_at. Reanudar solo al alcanzar o superar la fecha mínima del proveedor. Este umbral de espera entre intentos es distinto del plazo de ejecución120 s por intento; máximo cuatro intentos intacto. Registro documental únicamente; no nuevos ensayos ni repetición de evidencia acreditada.

## Decisión vigente de esperas acumuladas — PM23:05:12

Paris vía PM09/10/2026 23:05:12 aprueba dos presupuestos independientes ACUMULADOS POR SOLICITUD:120 s de espera automática por capacidad local y120 s de espera automática del proveedor. No se reinician por retry, resume ni recuperación de la misma operación. Máximo240 s de esperas automáticas, no plazo total hasta respuesta. Se mantienen120 s de ejecución por intento e inicial+3/max4, sin retries anidados. Sustituye la interpretación por intervalo22:37:04. Espera local sin intento, pausa visible conservando pregunta al agotar saldo y sin bucle automático; resume explícito no renueva saldos, con saldo local agotado requiere plaza inmediata. Retry-After superior al saldo proveedor→pausa, resume solo≥retry_at. Capacidad8 configurable propuesta, no medida. Contrato vigente en historial/plan/matriz; sin nuevos ensayos/inferencias/spikes.
