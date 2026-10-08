# Dashboard de salud del sistema — JUP-047

La ruta `/system-health` está dentro de la sesión autenticada y del ámbito del cliente. El enlace «Salud del sistema» utiliza el layout, tarjetas y colores existentes. La API responde al navegador; el navegador nunca conecta directamente con bases de datos, RabbitMQ, LiteLLM ni OpenRouter.

## Contrato y significado

| Operación | Efectos y autorización |
| --- | --- |
| `GET /health` | Contrato público anterior `status/services/checked_at`, conservado. No sustituye el diagnóstico autenticado. |
| `GET /health/status` | Bearer y `X-Tenant-Id` de un tenant autorizado. Probes de lectura y resúmenes SQL parametrizados. Sin generación, embeddings, ingestas, publicaciones ni escrituras de datos. |
| `POST /health/provider-check` | Misma autorización. Cuerpo únicamente `{"idempotency_key":"accion-opaca"}`; ASCII alfanumérico, `_` y `-`, de 1 a 128 caracteres. El servidor fija destino, modelo y mensaje. Puede consumir crédito solo después de admisión y reserva. |

Token ausente/inválido: 401; ámbito ausente/malformado: 400; tenant ajeno: 403. Se aplica autorización antes de probes y reservas. Los dos endpoints operativos responden con `Cache-Control: no-store`. El diagnóstico puede responder 200 aunque una dependencia falle; ese 200 no acredita disponibilidad de todos los servicios. El POST rechaza campos adicionales.

Las observaciones tienen `id/status/reason_code/source_kind/checked_at/latency_ms`. Los identificadores son backend, database, rabbitmq, processor, vector_store, azure_cost_api, litellm y openrouter. Los estados son `ok/degraded/failed/unknown`. Un timeout es «No verificado», sin afirmar caída. Fallo confirmado de DB/RabbitMQ/pgvector/processor hace fallido el agregado; otros fallos, limitaciones o desconocidos lo degradan. Todos desconocidos producen desconocido. Resúmenes incompletos o fallos recientes requieren atención, sin demostrar que un worker esté caído.

| Fuente | Qué demuestra | Límite |
| --- | --- | --- |
| Backend | La API actual responde | No todos sus flujos de negocio |
| CockroachDB | `SELECT 1` y lectura acotada de resúmenes | No escribe ni migra por diagnosticar |
| RabbitMQ | Una conexión diagnóstica propia | No publica ni consume mensajes |
| pgvector | Conexión, extensión `vector`, tablas knowledge_documents/document_chunks/chunk_embeddings | No inserta embeddings ni expone corpus |
| Processor | Su API health es alcanzable | `worker_status=unknown`: no hay señal verificable del worker |
| Azure Cost API | Health del simulador configurado | Procedencia `simulated`, no disponibilidad ni permisos de Azure real |
| LiteLLM | GET /health/liveliness no generativo: HTTP200 y string JSON exactamente "I'm alive!" | Adaptador exclusivo de LiteLLM; gateway vivo no prueba OpenRouter. Processor/Azure conservan objeto JSON status ok/healthy/degraded |
| OpenRouter | Respuesta funcional real válida por la ruta configurada; identidad/coste informativos | Mock/simulador o body con nombre de modelo no acreditan upstream real |

`source_kind` distingue live, simulated, mock y unverified. La UI conserva texto e icono además del color. Datos desconocidos, inválidos o ausentes no se convierten en verde ni en ceros.

## Actividad y fechas

`window.end=checked_at` y `window.start=end-24h`, en UTC. Jobs cuenta publish_pending/publish_failed/publish_unknown/queued/running/completed/failed/other. Fallos de las últimas 24 h incluyen failed y publish_failed por updated_at. Publish_unknown es una publicación indeterminada que requiere atención. La última actualización corresponde a datos, no al refresco.

Ingesta cuenta running/completed/failed/other; un fallo usa completed_at y, si falta fecha terminal, started_at. La última ingesta corresponde exclusivamente a un registro completed con completed_at. Tabla o consulta ausente/fallida: `data_status=unavailable`, conteos y fechas nulos. Tabla vacía: empty y ceros explícitos. No se devuelven documentos, payloads, resultados, URI de artefactos, suscripciones ni errores libres.

OpenRouter añade `verified_at/last_attempt_at/expires_at/check_id`. GET no renueva verified_at. verified_at significa última respuesta funcional real válida, no identidad ni coste confirmado. Se conserva sin TTL hasta otro resultado real. Un timeout nuevo produce unknown/timeout y conserva el último éxito como historia, sin afirmar éxito del intento nuevo. Un rechazo busy/cooldown/budget_unavailable que no envía muestra un aviso y conserva el resultado real. checked_at corresponde a la finalización del último intento real y last_attempt_at a su inicio; GET no renueva estas fechas. expires_at es null en el backend; se mantiene nullable por compatibilidad y no define caducidad. El check_id es una correlación opaca propia, enviada al gateway como `X-Request-ID`, sin sesión ni tenant. El responsable debe demostrar su correlación con los recibos reales del gateway/proveedor antes de dar por válido un ensayo real.

## Plazos, carga y cancelación

Cada probe dispone por defecto de 8 s, configurables mediante HEALTH_PROBE_TIMEOUT_SECONDS entre 2 y 8 s inclusivos, y la agregación de 18 s después de la autorización. El presupuesto incluye el arranque del proceso y sus importaciones; seis sondas se distribuyen en dos oleadas de hasta cuatro. Máximo cuatro operaciones activas por proceso; saturación devuelve unknown/busy sin una cola de espera. Las operaciones de red/driver viven en procesos desechables con deadline total incluyendo DNS, conexión, lectura y cierre; al vencer se terminan y se recogen antes de liberar el slot. SQL usa conexiones propias, transacciones read-only, connect_timeout y statement_timeout. No cambia el engine del negocio. La autenticación heredada ocurre antes y no tiene este presupuesto: no interpretar dieciocho segundos como límite total de petición.

El cliente aborta GET a los 20 s y POST a los 35 s; servidor POST tiene 30 s. Abortar el navegador no demuestra coste cero. Apertura y Actualizar realizan una intención POST y GET; StrictMode no duplica la apertura. Polling visible cada 30 s hace solo GET. Al ocultar se detiene polling; logout, unmount y cambio de tenant/sesión cancelan solicitudes, detienen timers y descartan respuestas anteriores. No hay reintentos automáticos de inferencia.

## Configuración opcional

Valores heredados siguen funcionando: todas estas opciones son adicionales. Destinos no configurados producen unknown/not_configured.

| Variable | Valor inicial / función |
| --- | --- |
| `PROCESSOR_HEALTH_BASE_URL` | Ausente; URL completa del health interno processor |
| `AZURE_COST_HEALTH_BASE_URL` | Ausente; URL completa del health interno del simulador |
| `HEALTH_PROBE_TIMEOUT_SECONDS` | 8; presupuesto total de cada sonda de lectura, finito entre 2 y 8 s; no modifica el POST generativo |
| `HEALTH_GATEWAY_PROBE_ENABLED` | false; permite GET a `/health/liveliness` del host LiteLLM configurado |
| `HEALTH_PROVIDER_ENABLED` | false; permite evaluar el gate de inferencia, sin conceder crédito por sí solo |
| `HEALTH_PROVIDER_API_KEY` | Ausente; credencial propia del gateway, dedicada y limitada al alias; SecretStr y redacción existente |
| `HEALTH_PROVIDER_POLICY_PATH` | Ausente; certificado operativo privado, de solo lectura, fuera de Git |

Las URLs de health son HTTP(S) de servidor, sin credenciales, query, fragmento ni redirecciones. No son parámetros del cliente. HTTP interno solo en red controlada; el responsable configura TLS/accesos apropiados antes de producción. Nunca proporcionar una key OpenRouter o master key al backend/cliente. La credencial diagnóstica no es la del embedding ni la del processor.

El Compose general no activa estas variables automáticamente. Para el entorno autorizado, preparar un override **fuera de Git**, con las variables anteriores en el servicio backend y el certificado montado de solo lectura. Por ejemplo, solo los probes no generativos:

```yaml
services:
  backend:
    environment:
      PROCESSOR_HEALTH_BASE_URL: http://processor:8001/health
      AZURE_COST_HEALTH_BASE_URL: http://azure-cost-api:8002/health
      HEALTH_GATEWAY_PROBE_ENABLED: 'true'
      HEALTH_PROVIDER_ENABLED: 'false'
```

El Compose local inseguro exige las identidades externas y el opt-in ya documentados en el README raíz. Usar un proyecto nuevo, recursos propios, puertos loopback distintos, envfile sintético y red interna sin egress para la fase falsa. No reutilizar servicios, redes, volúmenes ni `.env` de otra tarea. No volcar `docker compose config`, entornos, DSN, claves, prompts ni cuerpos de upstream en evidencias públicas.

## Admisión real y certificado operativo

Perfil inicial: un proceso, una réplica y una credencial diagnóstica limitada al alias, con admisión/ledger propios. Apertura/manual/periódica comparten una llamada activa global, cooldown de 60 s, seis envíos/hora y 24/día. Duplicados sesión+tenant+acción no envían de nuevo; busy devuelve 409, cooldown o presupuesto/certificado no demostrables devuelven 429 y un reason_code cerrado, con Retry-After si procede.

El responsable entrega un JSON privado de máximo 16 KiB, montado read-only. No existe certificado válido por defecto ni tarifa/budget de producción hard-coded. La configuración no reemplaza evidencia externa: el responsable debe verificar las garantías del gateway, precio, admisión diagnóstica y techo realmente exigible con controles ya comprobados, sin nuevas garantías no comprobadas ni auditoría global de gasto; una soft-key-budget o una afirmación en un JSON por sí sola no prueban control financiero.

Campos obligatorios del certificado:

| Grupo | Campos y comprobación |
| --- | --- |
| Identidad | instance_id del proceso actual; single_replica_verified, single_process_verified, credential_dedicated y credential_alias_only verdaderos; credential_id; credential_sha256 SHA256 de la credencial y gateway_base_url igual al configurado |
| Evidencia | execution_id, ledger_reference, authorization_reference no vacíos; routing_config_sha256 de la configuración verificada; conservar originales y recibos privados por coordinación |
| Vigencia UTC | price_checked_at ≤ valid_from ≤ ahora < valid_until ≤ price_checked_at + 24 h; Verificar precio actual, no copiar precios históricos del ADR |
| Routing | routing_alias=economicon-chat; routing_model=openrouter/z-ai/glm-5.2; routing_provider=deepinfra/fp4; gateway_retries/router_retries enteros 0, reasoning_enabled/allow_fallbacks falsos, privacy_verified verdadero |
| Cotas | input_envelope_certified verdadero; input_tokens_upper entero 1..1024 incluyendo envoltorio; output_tokens_upper entero 800..1000000 certificado aunque se soliciten 32; input_price_per_million_usd/output_price_per_million_usd positivos y fees_upper_usd explícito |
| Dinero | budget_usd positivo; additional_limits_usd lista no vacía con los límites concurrentes aplicables; known_spend_usd, uncertain_usd, pending_usd obligatorios; uncertain_usd puede ser no cero y se conserva íntegro; pending_usd no cero bloquea por operación pendiente |
| Ejecución | execution_calls_limit entero 1..24 y known_execution_calls entero 0..limit, acumulativo desde el inicio de la ejecución autorizada; fallos posibles cuentan como envío |
| Garantías | price_verified, routing_verified, effective_cap_verified, exclusive_accounting_verified, enforceable_cost_ceiling_verified verdaderos, respaldados por comprobaciones del responsable |

Importes como strings decimales, nunca floats: finitos, no negativos, máximo 40 dígitos significativos, 18 decimales y orden ≤ 10^12. Cotas fuera del dominio se rechazan sin envío. La aritmética de reserva/contabilidad utiliza precisión explícita de 80 dígitos para esos operandos, sin redondear una cota máxima hacia abajo.

Antes de **cada** envío se relee certificado, hash, vigencia y configuración. Cambiar el archivo después de activar el proceso bloquea nuevos envíos por digest distinto, sin recarga silenciosa de presupuesto. No editarlo para renovar presupuesto en caliente. El nonce instance_id se anuncia una vez cuando el gate se consulta habilitado sin certificado válido; ese estado no envía. Tras reinicio el nonce cambia: no reaplicar crédito ni reservas viejos como cero. Conservar fielmente gasto, reservas y contador anteriores al preparar el certificado ordinario actual; no exigir conciliar U por sí solo ni inventar conciliación. Con varias réplicas/procesos no activar este perfil: exige otra solución de admisión global verificada.

Reserva atómica con Decimal antes de cualquier byte: `(Nin_upper*Pin_upper + Nout_upper*Pout_upper)/1000000 + fees_upper`, comparada con el mínimo de límites menos gasto y reservas. El POST fija un único mensaje user ASCII: "Return exactly the two uppercase letters OK. Do not include punctuation, quotes, whitespace, or any other text.", max_tokens=32, sin herramientas/stream/contexto/identidad de usuario; exige reasoning desactivado, privacidad y proveedor único, parámetros requeridos y max_price certificado. El gateway puede aplicar un cap efectivo distinto: certificarlo, no inferirlo de la petición.

Respuesta funcional válida exige HTTP200, JSON≤16384bytes, exactamente una choice, finish_reason=stop, contenido exactamente OK tras strip y uppercase (OK. o texto añadido se rechazan; aclarar el mensaje no garantiza obediencia remota) e id no vacío≤256caracteres, por la ruta configurada. El nombre informado no es gate de igualdad/prefijo/versión ni certificación remota. reported_model es string seguro≤256 o null; el transporte descarta cualquier nombre que contenga la credencial diagnóstica completa, exacta o incrustada, antes de devolver o retener el recibo y model_identity siempre unconfirmed. reported_cost_usd/cost_status distinguen dato decimal del gateway, ausente e inválido; cost_confirmation siempre unconfirmed. Un header calculado nunca se afirma cargo upstream confirmado.

La liquidación sigue separada: uso entero no negativo dentro de cotas y total positivo, coste utilizable positivo≤reserva y ruta válida permiten mover solo la nueva reserva a gasto. Coste/usage no utilizables (incluido cero con uso positivo) o posible timeout/error conservan la reserva nueva completa como incierta; no presumen gratis ni reintentan. Éxito funcional actualiza verified_at independientemente de liquidación; identidad/coste no degradan disponibilidad. Intento inválido/error/rechazo conserva la fecha anterior solo como historia.

Admisión ordinaria H+U+P+R≤B con Decimal: H gasto conocido, U incertidumbre histórica íntegra, P reservas pendientes y R cota nueva; B menor límite finito asignado al diagnóstico. Igualdad admite con los demás gates, exceso rechaza sin envío. U no cero o ausencia de conciliación no son veto automático. reservation_state_reconciled/reconciled_at no son requisitos ni se rellenan falsamente; no hay flags/fechas nuevos, excepción financiera por llamada, certificado especial de incertidumbre cero ni auditoría global de gasto. La key upstream OpenRouter es compartida: exclusive_accounting_verified describe admisión/ledger diagnósticos, no propiedad exclusiva de esa key. Estado ausente/ilegible y P pendiente siguen bloqueados. No eludir cooldown/concurrencia/ventanas/contador reiniciando. El preflight operativo del segundo ensayo conserva la hora del primer envío y comprueba el cooldown; no añade un esquema temporal nuevo al certificado. El backend no escribe un ledger ni devuelve facturación/recibos privados; coordinación retiene y concilia los recibos del gateway/proveedor correlacionados antes/después. Un body falso con modelo/uso/coste solo prueba contrato sintético.

## Comprobaciones reproducibles

Con las dependencias del checkout instaladas conforme a los README existentes, desde `apps/backend`:

```text
python -m pytest tests/test_system_health_jup047.py tests/test_system_health_boundaries_jup047.py tests/test_health_provider_admission_jup047.py tests/test_health_provider_response_jup047.py tests/test_health_provider_policy_jup047.py -q
python -m pytest tests
python -m compileall app
```

Desde la raíz:

```text
corepack pnpm --filter @finops/frontend test
corepack pnpm --filter @finops/frontend typecheck
corepack pnpm --filter @finops/frontend lint
corepack pnpm --filter @finops/frontend build
corepack pnpm jup:check:all
corepack pnpm pr:check:test
corepack pnpm ci:check:test
corepack pnpm repository:governance:test
corepack pnpm openspec:validate
corepack pnpm test
corepack pnpm build
```

Pruebas focales usan auth/SQL SQLite y transportes sintéticos sin red. Las regresiones Cockroach/pgvector/RabbitMQ requieren los entornos exclusivos y variables documentados por sus tests/README, no servidores compartidos. Fijar cwd/PYTHONPATH al checkout o copia nativa actual; verificar ruta de módulos y SHA256 antes de ejecutar. Una imagen reutilizada aporta dependencias, no acredita el código del checkout. No ejecutar desde otro workspace aunque se haya añadido PYTHONPATH. Registrar command/cwd/source hash/exit y skips; un skip no es PASS.

En el stack local exclusivo, comprobar DB, extensión/esquema, broker, processor y simulador Azure; leer antes/después filas de datos y comprobar que GET/POST no las escriben. Capturar payload/cap/routing, admisión/reserva, rechazos y coste incierto contra gateway falso en red sin egress. Provocar parada/recuperación solo de servicios propios, DNS/lectura lenta y errores; verificar deadline total y ausencia de hijos/sockets huérfanos. No cambiar tests ni modificar servicios ajenos para obtener resultados. En frontend jsdom verifica semántica, no píxeles: comparar visualmente con páginas existentes a 390/768/1440 px, teclado y overflow del panel/shell por separado durante validación independiente.

## Ensayo real, revisión y M5

La autorización humana del 08/10/2026 mantiene **0,20 EUR acumulados, incluidos los intentos previos**, separados del presupuesto habitual. Sustituye el anterior techo humano de0,40 USD y el cupo de13; los planes previos son historia, sin reset de contador ni reservas. El cierre de validación local registra **6 intentos reales** y una cohorte terminada6/6, sin envíos restantes. No se autoriza una séptima petición por esta documentación. El cap efectivo de la clave diagnóstica en el ensayo fue0,03 USD; no es el presupuesto humano ni habilita nuevos ensayos. Cualquier futura cohorte requiere coordinación, controles y preflight vigente dentro del techo, conservando H/U/P, historial, cooldown y límites de admisión.

La sexta petición fue iniciada manualmente desde «Salud del sistema» y acreditó HTTP200, JSON válido, una elección, finish_reason=stop y contenido exacto OK. La quinta conserva HTTP429 como error; los cuatro intentos anteriores no se convierten en éxitos. LiteLLM registró28 tokens de entrada y2 de salida, con coste informado0,00001935 USD concordante con el delta de su clave diagnóstica. No se obtuvo factura emitida por OpenRouter ni confirmación de identidad del modelo. El ledger final conserva H=0,000050625 USD, U=0,010080 USD y P=0; no libera la incertidumbre histórica. El certificado previo a la sexta permanece como evidencia5/6 y el ledger final6/6 es un artefacto distinto.

La observación funcional válida se conserva **sin caducidad por antigüedad** hasta otra observación real. GET devuelve su resultado y fechas originales; un timeout real posterior produce unknown/timeout y conserva verified_at y check_id del éxito como historia. Esta evolución sustituye el anterior TTL de60 segundos. GET/polling no realiza otra inferencia. La sonda no generativa de LiteLLM acreditó gateway saludable, diferenciada de la respuesta funcional de OpenRouter.

La revisión técnica interna afectada fue favorable con214 pruebas propias. La validación local afectada completó214 PASS,0 FAIL/SKIP, en cuatro ejecuciones (102+33+29+50); la ejecución conjunta sin resultado se conserva sin contar como PASS. Implementación: Red143 PASS/38 fallos significativos, Green214 PASS y15 mutantes detectados, con controles37/37, conservados en E12. La evidencia final E13 conserva los dictámenes independientes originales y el error real429. No se repitieron viewport390/768/1440 ni teclado; el hallazgo móvil diferido conserva su estado. DockerServer M5, CI remota, aprobación final, archivo específicamente autorizado, PR vinculada y las dos reviews humanas continúan pendientes.

Registrar revisión/config/ruta/cap/precio vigente, fecha, correlación, uso, coste observado y derivado distinguidos, reservas/ledger antes y después, y ausencia de llamadas por polling. Conservar capacidad asignada al diagnóstico y límites; no auditar gasto ajeno de la key compartida ni reutilizar permisos de otra JUP. Error posiblemente facturado retiene la cota y consume su envío acumulado. Se rechaza cualquier envío que agote el límite finito de su cohorte operativa o no cumpla los demás gates; el antiguo veto a una tercera llamada correspondía al plan histórico de dos y ya no representa el cupo humano vigente. U histórico por sí solo no bloquea otra comprobación autorizada con margen ordinario suficiente. No publicar datos de facturación de terceros, claves o prompts.

Docker local no acredita DockerServer M5. Antes de desplegar, Paris y Alejandro coordinan responsable/acceso/proyecto/red/puertos/TLS/secretos/identidad/revisión autorizada, presupuesto habitual, rollout y rollback. Verificar allí ruta autenticada, aislamiento y fuentes reales/simuladas declaradas y conservar evidencia fechada. No trasladar Compose local inseguro al servidor. Separar entrega técnica local y comprobación externa Alejandro: M5 sigue criterio oficial pendiente, sin borrarlo ni aprobarlo. Reutilizar simulación local vigente y repetir solo afectados/controles requeridos por proceso, sin SSH ni repetición sistemática. Revisión técnica y validación de aceptación son independientes; las pruebas de implementación/CI no las sustituyen. Archivo, publicaciones, reviews humanas y merge requieren las autorizaciones/proceso vigentes.

Decisiones transmitidas por PM07/10/2026: criterio funcional independiente22:47:49; reserva histórica no bloqueante aprobada por Paris «ok vamos a ello»23:23:23 Atlantic/Canary (prefijo23:20:00 corregido); preparación mínima, reutilización local y consolidación de evidencia23:31:51. Fuentes y recibos privados fuera de Git. Conservar evidencia vigente no afectada y revisión/validación independientes de la corrección. La conformidad visual de Paris sobre preview23:44:59 no es aceptación funcional/final. No reabrir el hallazgo móvil diferido; publicación con pendientes mantiene controles humanos. Ningún ejemplo autoriza inferencia, archivo o PR.

El adaptador de LiteLLM acepta solo HTTP200 y el string JSON exacto documentado; otros strings/tipos/status HTTP, redirects, JSON inválido o cuerpo>16384bytes no son éxito. Conserva deadline/DNS aislado, cierre, no redirección y redacción del probe genérico. GET/poll no generan llamadas ni actualizan verified_at de OpenRouter. Antes de un ensayo con runtime modificado, retirar o actualizar explícitamente cualquier helper externo vinculado al SHA anterior; no reutilizar instrumentación silenciosamente inactiva.


## Retención y ciclo visible — cambio aprobado 08/10/2026

El panel autenticado envía una comprobación por entrada lógica visible y otra cada **600000 ms** desde el último POST. Una acción manual reinicia ese plazo. La coordinación en memoria evita duplicados entre consumidores, StrictMode y remontajes de la misma entrada; una navegación nueva abre una vez. No hay monitor fuera del panel ni coordinador entre pestañas: siguen vigentes los límites globales del backend.

Ocultar la pestaña pausa GET y POST; una solicitud en curso puede terminar. Al volver se lee el diagnóstico y se hace como máximo un POST vencido, sin catch-up; si todavía no venció, se espera el tiempo restante. Desmontar cancela temporizadores, escuchas y solicitudes propias. Cambiar sesión/token/tenant oculta los datos anteriores y descarta resultados tardíos.

Un timeout del cliente deja el intento no verificado. Un GET anterior no puede recuperar el estado verde: hace falta una observación coherente del intento enviado o una nueva acción completada. Un rechazo de admisión conserva el último resultado real y muestra el motivo de la acción rechazada.

Estados, fechas y métricas comparten el instante de recepción y una tolerancia futura inclusiva de **1000 ms**. Fechas malformadas, no UTC, ausentes o futuras en1001 ms no verifican la fila afectada. Las fechas antiguas válidas se conservan, sin recorte ni diagnóstico inventado del reloj. Azure mantiene el rótulo **SIMULADO**; la sonda no generativa de LiteLLM sigue separada de la inferencia.

Pruebas reproducibles con transportes sintéticos: los archivos backend test_health_provider_admission_jup047.py, test_health_provider_response_jup047.py y test_system_health_jup047.py; frontend src/services/api.test.ts y tests/system-health-jup047.test.tsx. Los registros de fases, origen de copia y comandos completos quedan en el handoff externo; el cambio requiere revisión y validación afectadas independientes. La evidencia real E13 y los límites financieros anteriores permanecen sin ampliación; este cambio no autoriza otro ensayo real.
