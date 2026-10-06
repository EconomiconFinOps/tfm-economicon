# llm-provider-routing Specification

## Purpose
Definir la integracion del processor con proveedores reales de chat y embeddings
a traves de LiteLLM/OpenRouter, sus limites de transporte, privacidad y coste,
sin alterar los contratos publicos ni convertir los mocks en fallback.

## Requirements
### Requirement: Adaptadores reales compatibles con el processor

El processor SHALL conectar las factorias existentes a LiteLLM mediante HTTP
stdlib sin SDK, manteniendo `invoke(prompt, response_format=...)` y `embed(text)`.
SHALL conservar FinOpsResponse 1.0 y los guardrails existentes. Este delta de
JUP-023 extiende `llm-provider-routing` de JUP-078 sin redefinir sus politicas.

#### Scenario: Chat estructurado valido
- **WHEN** la ruta LiteLLM recibe un prompt y su response_format estricto
- **THEN** envia alias y formato a `/v1/chat/completions`, entrega contenido
  textual a los guardrails y devuelve la respuesta validada sin cambiar contrato

#### Scenario: Embedding valido o incompatible
- **WHEN** `/v1/embeddings` devuelve el vector del texto solicitado
- **THEN** solo se acepta una lista de exactamente 1536 numeros finitos, sin
  booleanos ni strings; cualquier estructura incompatible falla antes de persistir

### Requirement: Limites reales y reintentos sin multiplicacion

La ruta real SHALL rechazar configuracion superior a 30 s por intento, dos
reintentos o 800 tokens de salida; SHALL permitir valores inferiores validos
sin clamp silencioso. Solo errores transitorios de transporte/timeout, HTTP 429
y 5xx SHALL ser elegibles para retry acotado. Gateway/router SHALL tener retries
efectivos cero. SHALL rechazarse redirecciones y cualquier fallback.

Cada intento de transporte HTTP SHALL tener un unico deadline monotono que
abarque conexion de socket, recepcion de cabeceras y lectura completa del cuerpo.
La resolucion DNS del sistema no es cancelable por este arreglo: este requisito
no garantiza un plazo total incluyendo DNS ni acredita aceptacion humana de esa limitacion.
La llegada de bytes o el cambio de fase SHALL NOT reiniciar el plazo. Al vencer, el cliente SHALL
interrumpir la operacion bloqueada y cerrar su transporte, sin dejar lecturas
activas tras terminar el intento. El vencimiento SHALL clasificarse como
timeout; agotados los retries permitidos SHALL lanzar ProviderError('timeout')
saneado. Cada retry SHALL recibir su propio deadline; el total SHALL NOT
superar `llm_max_retries + 1` intentos con el backoff acotado existente.

#### Scenario: Configuracion supera el techo
- **WHEN** se selecciona LiteLLM con timeout, retries o tokens por encima del limite
- **THEN** falla explicitamente antes de emitir una solicitud, sin modificar ajustes Azure

#### Scenario: Error transitorio persistente
- **WHEN** la operacion agota dos reintentos configurados tras el intento inicial
- **THEN** termina con ProviderError tras como maximo tres intentos y ningun retry adicional del gateway

#### Scenario: Fallo no reintentable
- **WHEN** hay error de autenticacion, request 4xx distinto de 429, redirect o respuesta invalida
- **THEN** falla sin retry, cambio de alias, mock ni reenvio de la clave a otro origen

#### Scenario: Cuerpo HTTP con goteo continuo
- **WHEN** un servidor HTTP loopback entrega bytes cada 0,03 s durante mas
  de 0,05 s y el timeout configurado es 0,05 s con cero retries
- **THEN** el cliente interrumpe la lectura y cierra el transporte al deadline,
  termina con ProviderError('timeout') y una sola solicitud, con elapsed
  monotono dentro del plazo mas tolerancia pequena explicita de planificacion,
  sin esperar los 0,42/4,4 s de los cuerpos de 14/140 bytes

#### Scenario: Cabeceras HTTP con goteo continuo
- **WHEN** el mismo goteo retrasa completar las cabeceras mas alla del plazo
- **THEN** vence el mismo deadline desde el inicio de conexion, interrumpe
  la lectura y cierra el transporte aunque aun no haya response disponible,
  con categoria timeout y el mismo limite de elapsed e intentos

#### Scenario: Deadline renovado solo para un retry permitido
- **WHEN** se configuran dos retries y cada intento excede su deadline
- **THEN** termina con ProviderError('timeout') tras tres intentos como maximo,
  cada transporte cerrado antes del siguiente, y elapsed total acotado por
  los tres plazos mas backoff y tolerancia explicita, sin requeue del job

#### Scenario: Respuesta HTTP completa dentro de plazo
- **WHEN** el servidor loopback entrega una respuesta JSON valida antes del deadline
- **THEN** la operacion termina correctamente en un intento, libera el transporte
  y conserva el contrato de respuesta sin timeout espurio

### Requirement: Fallos reales terminales sin alterar otros errores

El sistema SHALL convertir el fallo de salida de `parse_and_validate_response`
solo en ruta LiteLLM a ProviderError saneado. IngestTask SHALL conservar ese tipo
al registrar `failed`/`ingestion_failed`; worker SHALL ejecutar nack con
`requeue=False`. Otros errores y mocks SHALL conservar su comportamiento.

#### Scenario: JSON incompatible despues de invoke
- **WHEN** el contenido LiteLLM llega al runtime pero incumple schema o guardrails
- **THEN** falla como ProviderError sin retry ni requeue, sin relajar guardrails
  ni incluir la respuesta en logs o excepciones

#### Scenario: Error tipado atraviesa ingestion
- **WHEN** chat o embeddings falla con ProviderError, incluido agotamiento transitorio
- **THEN** ingestion registra failed sin perder el tipo y el worker rechaza sin reencolar

#### Scenario: Exito y errores ajenos
- **WHEN** se procesa un exito, un InvalidJobMessage o un error ajeno a proveedores reales
- **THEN** se mantienen respectivamente ack, rechazo existente y tratamiento generico vigente

### Requirement: Integracion aislada con imagen aprobada

El despliegue adicional SHALL ser opt-in, con red propia, administracion loopback,
health sin LLM y PostgreSQL exclusivo para claves virtuales separado de pgvector.
SHALL conservar defaults mock y schema de 8 dimensiones. SHALL requerir version
y digest corregidos aprobados tras revisar todos los advisories y compatibilidad;
la baseline 1.82.6 SHALL NOT ejecutarse. No se admite `latest`.

#### Scenario: Candidato aun sin aprobar
- **WHEN** no existe aprobacion de version y digest tras el preflight de seguridad
- **THEN** no se inicia Docker, ni siquiera con upstream falso; las pruebas offline
  pueden continuar tras su gate pre-code

#### Scenario: Gateway con upstream falso
- **WHEN** se prueba el gateway aprobado sin acceso OpenRouter
- **THEN** se comprueban configuracion efectiva, privacidad JUP-078, claves virtuales
  y retries cero sin consumo externo ni atribuir evidencia de proveedor real

### Requirement: Endpoint explicito del principal sin cambiar contrato

Para la prueba aprobada, `economicon-chat` SHALL usar el mismo GLM-5.2 mediante
OpenRouter con `provider.only: [deepinfra/fp4]` y `require_parameters: true`.
SHALL conservar schema estricto completo, ZDR, `data_collection: deny`,
`allow_fallbacks: false`, `reasoning.enabled: false`, 30 s y maximo 800 tokens.
Los alias secundario y embeddings SHALL permanecer sin cambios.

#### Scenario: Ruta principal compatible
- **WHEN** se prepara la solicitud del principal para la prueba aprobada
- **THEN** se transmite el schema completo intacto con la restriccion al unico
  endpoint y los parametros anteriores, sin conectar directamente a DeepInfra

#### Scenario: Endpoint incompatible o sin margen contable
- **WHEN** la ruta no satisface el contrato o no se han conciliado reservas y
  acreditado margen bajo los caps vigentes
- **THEN** no se repite una llamada real ni se cambia modelo, schema, privacidad,
  endpoint o caps para continuar; el uso observado cero no libera reservas

### Requirement: Preservacion de fallos y costes sin contenido upstream

El gateway SHALL sanear texto arbitrario de errores upstream antes de persistir
SpendLogs mediante callback publico soportado, preservando filas de exito y
fallo, estado, modelo, request ID, tiempo, duracion y tokens/coste disponibles y
validados. SHALL NOT activar `disable_error_logs` ni suprimir registros de coste.
Datos ausentes SHALL permanecer desconocidos, nunca asumirse cero. El callback
SHALL inicializarse fail-closed y su orden previo a persistencia SHALL verificarse
en Docker simulado antes de cualquier llamada real.

#### Scenario: Error upstream conserva trazabilidad sin contenido
- **WHEN** el upstream simulado devuelve un error con texto sensible sintetico
  y metadatos/tokens/coste conocidos que la ruta de fallo entrega
- **THEN** se conserva la fila de fallo con esos datos validados y sin texto
  arbitrario upstream en SpendLogs ni consola, incluidos campos anidados

#### Scenario: Configuracion inicial invalida
- **WHEN** falta el modulo del callback o falla su import/registro al inicializar
- **THEN** el gateway no sirve trafico de modelos

#### Scenario: Prueba detecta proteccion invalida
- **WHEN** el hook falla en pruebas, no se verifica su orden previo a persistencia
  o las rutas normales de error del proveedor conservan contenido upstream
- **THEN** falla la validacion y el uso real sigue bloqueado; se documenta el
  comportamiento observado y se escala con evidencia, sin exigir circuit breaker,
  autorrecuperacion ni callback infalible en runtime, ni parchear el proveedor,
  monkeypatch o descartar registros para ocultar el fallo de privacidad

### Requirement: Smoke real acotado y evidencia saneada

Antes de cualquier PR o cierre SHALL existir smoke real con principal FinOpsResponse valido,
embeddings1536 y recorrido processor sobre texto sintetico con pgvector
desechable1536. El secundario SHALL seleccionarse explicitamente para evaluacion,
nunca como fallback. Uso real SHALL esperar resolucion de ADR-0002/privacidad,
claves limitadas, disponibilidad y compatibilidad; no se infiere aprobacion del ADR.
La validacion SHALL limitarse a 0,50 EUR agregados, incluidos retries y fallos
cobrados, con limites upstream/virtual verificables, precios actuales, conversion
conservadora, ejecucion secuencial y margen reservado antes de cada operacion.

#### Scenario: Resultado real verificable
- **WHEN** se completa el smoke con todos los gates satisfechos
- **THEN** la evidencia identifica SHA, digest/config saneada, limites, resultado
  de guardrails, dimension/persistencia, job finalizado y coste total conciliado
  sin prompts, respuestas, textos privados ni claves

#### Scenario: Coste o compatibilidad desconocidos
- **WHEN** no se puede acotar consumo, verificar limites/margen, o cumplir ZDR y structured output
- **THEN** se detiene sin otra llamada ni relajacion de politicas y se escala;
  saldo de cuenta o presupuesto mensual no sustituyen el techo de esta validacion

#### Scenario: Telemetria incompleta
- **WHEN** una llamada no entrega tokens o coste utilizable
- **THEN** solo se registra estado, alias, duracion y metadatos saneados disponibles;
  el consumo desconocido no se contabiliza como cero ni habilita mas gasto

#### Scenario: Pruebas reales pendientes o fallidas
- **WHEN** solo existen simulaciones o no se han superado las pruebas reales
  con su evidencia y consumo registrados
- **THEN** no se da por terminada la implementacion ni se abre PR, tampoco en
  borrador; superar las pruebas no sustituye autorizacion de publicacion ni
  revision y validacion humanas
