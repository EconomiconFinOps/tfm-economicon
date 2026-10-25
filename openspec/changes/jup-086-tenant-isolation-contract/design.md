JUP: JUP-086

## Verificacion vigente

La [tabla de aceptacion acotada](resource-matrix.md#aceptacion-acotada-vigente)
es la unica lista de evidencia necesaria y pendientes de esta reconciliacion.
Conserva todo el comportamiento, arquitectura y limites numericos siguientes;
RF-086-003 es el add-on aprobado retenido. Las recetas de pruebas/estados
anteriores son historia, sin nuevas ordenes de codigo/tests. Ratificacion
APPROVED; dos grupos runtime completos, REVIEW_PASS sin cambiar producto.
Inventario684/111 nuevos;11 ejecuciones actuales PASS (3 nuevos+8 regresiones),
681 PASS previos reutilizados. [Evidencia](../../../docs/evidence/JUP-086-validation.md#validacion-acotada-final).
QA final PASS, sin exencion DoD de codigo; post-QA APPROVED y publicacion
autorizada segun review.md. CI/revision humana de PR y merge separados.

## Seleccion por comportamiento y reutilizacion

Historia de la seleccion108/681 previa a los tres casos de aceptacion final;
no es el inventario actual ni una instruccion de repetir sus pendientes.

Validacion Linux con servicios aislados,26/09:681 PASS/0 FAIL/ERROR/SKIP,
108 nuevos sin incremento;38 variantes distintas detectadas. Tres defectos
de tests corregidos tras676/5 y V01 superviviente: idle30/62s real, ACK con
heartbeat2 solo en la URL de prueba, inicio del publisher HTTP y rechazo
PermissionError preciso. Producto, heartbeat30/confirm5 y diseno intactos.
REVIEW_PASS acotado; pendientes reconciliados en la tabla vigente.
[Evidencia](../../../docs/evidence/JUP-086-validation.md#validacion-con-servicios-reales).

**Aplicada tras aprobacion; R1 de cobertura DNS resuelto localmente.**
Se conservan108 casos nuevos
(60 aislamiento,48 RF-086-003), mas4 netos de la adaptacion heredada: base569,
neto112,total681. Retirados469 de577 (81,3%). La seleccion238 anterior no
se implemento; estas cifras no son minimos demostrados. Tabla exacta en
[resource-matrix.md](resource-matrix.md#seleccion-practica-de-pruebas).

Resultado anterior sin servicios:623 PASS/58 SKIP. La primera pasada processor registro
WinError10053 en una prueba heredada; diagnostico y unica repeticion completa
pasaron sin editarla, pero no establecen su causa ni prueban que sea inocuo.
La unica restitucion autorizada y aplicada es el parametro
`publisher` de `test_adversarial_cancel_before_spawn_and_cleanup_before_other_lane`:
baseline14 PASS y m33 con13 PASS/1 FAIL semantico. REVIEW_PASS acotado, R1
cerrado; no cambia diseno/producto ni justifica mas restituciones.
Balance de esa fase:33 operadores detectados (32 previos revisados y m33
nuevo), cinco no ejecutados. La validacion real posterior completa38
detecciones; conserva el primer V01 superviviente y su correccion de test.
La aceptacion restante sigue pendiente, sin excepcion. Los pasos futuros
describen comprobaciones requeridas, no resultados ya aprobados.

### Reutilizacion concreta

| Pruebas heredadas intactas | Comportamiento reutilizado; limite |
| --- | --- |
| Backend test_jobs_schema.py, accepts_text_content / rejects_blank_text_content | Schema de texto valido/blanco; no volver a multiplicarlo por motor. No prueba membership. |
| Backend test_ingest_tracing.py, payload_carries_the_current_request_id / payload_has_no_request_id_when_none_is_bound | Envelope, job ID, payload y correlacion del productor; dobles, no confirmacion broker. |
| Processor test_ingest_task.py, cuatro funciones/diez casos actuales | Productor real aislado -> contexto persistido -> pipeline, opcionales, envelope invalido sin writes, retry/correlacion. Mantenerlos completos; no duplicar positivos por cada engine/tenant. |
| Processor test_worker_tracing.py | Contexto y ausencia de mezcla entre entregas; conservar aparte el nuevo rechazo de request ID hostil. |
| Processor test_azure_cost_ingestion.py y test_azure_cost_cockroach_integration.py | Ingesta, normalizacion, round-trip e idempotencia propios del scope. No sustituyen los diez rechazos foreign de la nueva seleccion. |
| Auth, logging/secret_boundaries y metrics heredados | Contratos comunes sin cambios; los nuevos marcadores de negocio, Pika y worker conservan representantes propios. |

Los nombres de funciones abreviados en las dos primeras filas llevan test_
y el prefijo ingest_job_request_ / ingest_job_ respectivamente. Los569 objetivos
heredados no se recortan, ni sus fixtures globales. La adaptacion6->10 se
conserva como esta, contando+4, sin restaurar el contrato antiguo.

### Criterio y limites

Conservar una prueba por decision relevante, no cada combinacion: API para
membership/mismatch/extra authority y opacidad; repositorios para predicados
que un guard HTTP ocultaria; worker para correlacion, pertenencia, replay y
efectos; costes para ambos scopes en cada operacion. CAS mutable y lectura
tras cero filas conservan ambos predicados. R2/DNS Red no se muestrean fuera.
Se elige un motor por caso: Cockroach para conflicto, rollback, lectura SQL
y una carrera de finalizacion, mas integracion; no duplicar validacion pura.

Esto reduce muestreo real: wiring de auth/selector en cada ruta, todas las
clases de campos extra, variantes source/artifact/content, estados worker
running/failed, errores SQL por cada outcome, matrices IPC/OS y carreras
secundarias ya no tendran cada una un node ID nuevo. No afirmar que los
heredados prueban lo que no ejercitan. El contrato sigue intacto: revisar
implementaciones compartidas y aplicar mutantes representativos a esas
decisiones. Si un hueco de seguridad o mutante relevante queda sin deteccion,
restituir un caso concreto y publicar el nuevo total antes de aceptar el
recorte; no disimularlo agregando escenarios independientes en un test.

Validaciones especificas de esa reutilizacion: misma dependencia de sesion/
tenant en rutas omitidas; extras prohibidos por ambos schemas; cotejo comun
de copias de ejecucion en worker; invariantes de CAS para estados ya iniciados;
parser IPC limitado y owner que progresa ante errores/cleanup. Son revisiones
y pruebas pendientes, no equivalencia acreditada por esta fase ni autorizacion
para omitir comportamiento obligatorio en QA.

### Ejecucion posterior al gate

Tester conserva inventarios/Red y modifica exclusivamente los13 modulos de
la matriz. Usa parametrizacion indirecta explicita por test, sin cambiar
fixtures heredadas/defaults, hooks de collection, filtros ni SKIP artificial.
Comprueba coleccion completa681, incluyendo opt-ins y todos los parametros,
y todos los helpers importables; ni borrar archivos compartidos ni crear
bucles/megatests. Separar el recuento de futuros casos de aceptacion.

Regresion y mutacion sobre el candidato: retirar tenant/creator/subscription
de entradas distintas; omitir parent/rollback, membership o rechazo permanente;
reintroducir requeue infinito; pisar progreso worker, replay o unknown->failed;
aceptar generacion tardia; liberar registro R2/plaza DNS sin cleanup; saltar
limite de recursos, deadline, validacion IPC o redaccion. Baseline Green y
fallo semantico sensible por operador; errores de entorno/importacion o SKIP
no matan mutantes. Casos Cockroach requieren servicio real, no equivalencia
inferida desde SQLite. Los29 mutantes anteriores no validan este conjunto.

Coder sin cambios de producto previstos; defecto nuevo se trata por separado.
Reviewer audita seleccion, perdidas, conteos y mutaciones. QA repite gates
afectados y completa Linux/Rabbit/Cockroach/pgvector y TLS real. Ningun count
cierra esa aceptacion; sin nuevos ADR, dependencias, servicios ni cambios al
contrato. Aprobacion final sigue separada de la aprobacion del recorte.


## RF-086-003 DNS: addendum propuesto

Implementacion local comprobada el 25/09: REVIEW_PASS tecnico, Green offline
883 PASS/267 SKIP y 29 mutantes detectados. TLS y plateau Windows acotados
demostrados; Linux y dependencias reales pendientes, no QA ni aceptacion
global. [Evidencia actual](../../../docs/evidence/JUP-086-validation.md#validacion-dns-local).
La segunda revision exige conservar registro activo/cache hasta terminar
el owner y verificar su limpieza Pika, independientemente del fin de DNS.
El owner publica esa prueba solo tras cerrar su loop/conexion/streams;
no se consultan objetos Pika desde otro thread. Referencias no verificadas
se retienen. Se conserva el error historico de close fallido aunque una
limpieza tardia verificada permita despues otro lifecycle.
Las referencias de preparacion inferiores son antecedentes del mismo contrato.

Pre-code DNS **APPROVED** por Paris, registro 25/09/2026 14:51:40 UTC en
proposal.md; ADR-0009 addendum Accepted. Habilita pruebas/codigo del detalle,
no acredita resultados. Las notas de preparacion PENDING siguientes son
historia. La cota de dos hijos es por proceso backend, no por tenant/trabajo;
no hay garantia medida de escalabilidad ni cuotas/equidad por tenant nuevas.

**Estado actual: propuesta; gate detallado pre-code PENDING, incluso tras
validar documentos.** La direccion y excepcion interna pueden documentarse
segun el contexto comunicado por el orquestador (25/09/2026 14:03:35 UTC,
hora de registro). No registra aqui una aprobacion humana nueva. ADR-0009
sigue Accepted para su decision original; este addendum es Proposed.
REVIEW_FAIL, dos Red DNS y BLOCKED_ENV siguen vigentes; 807 PASS/267 SKIP y
34 mutantes son evidencia anterior. Los registros de aprobacion inferiores
son historia del contrato original, no autorizacion de este detalle.

### Frontera Pika y propietario

Conservar SelectConnection directo, su owner no daemon, workflow interno
default y delegado de transporte. Proponer un segundo override,
`getaddrinfo(host, port, on_done, family=0, socktype=0, proto=0, flags=0)`,
que devuelve un AbstractIOReference propio y nunca invoca el resolver Pika.
La excepcion acotada comprende SelectorIOServicesAdapter, AbstractIOServices
(incluido getaddrinfo), AbstractIOReference, AbstractStreamProtocol y AbstractStreamTransport;
son interfaces internas, no un contrato publico estable. Sin atributos
privados ni monkeypatch de Pika; no usar la factory create_connection.
Pika conserva sockets de conexion, TCP/TLS/AMQP y transporte; el hijo ejecuta
solo socket.getaddrinfo. Mantener hostname original en parametros/SNI y
verificacion de certificado, sin sustituirlo por la IP resuelta.

Un supervisor no daemon por proceso backend posee TODOS los Popen, pipes,
spawn/terminacion/reap y registros pendientes; no uno por lookup/request.
Se crea explicitamente con start del lifespan, nunca al importar. El owner
arranca sin esperar DNS y conserva su limite de 1 s; ping sin servicio iniciado
o en stopping devuelve false. Un publisher registrado por proceso; todas
las instancias/probes consultan el mismo registro, no pools independientes.
Supervisor sondea cada <=50 ms; owners sondean buzones propios cada <=100 ms.
Solo el owner llama Pika/on_done; el supervisor no accede a conexiones ni
contextos de requests. Locks cortos protegen registros, nunca rodean Popen,
I/O, joins o callbacks. Si el supervisor falla, no se crea un reemplazo vivo.

### Admision y equidad

Dos plazas globales no prestables: una publisher y una probe. Cada plaza
cuenta desde antes de Popen hasta reap/cierre de pipes; un lanzamiento sin
handle retornado tambien ocupa plaza. Maximo dos hijos, un spawn simultaneo,
un supervisor y cero threads lectores/resolvers auxiliares de aplicacion.
La plaza probe es un lease hasta terminar tambien su conexion/loop Pika:
un ping activo y cuatro esperando FIFO, sin crear loops ni threads propios
para los que esperan; el caller sync espera Event solo hasta su deadline.
El quinto en espera, stopping o fallo retenido devuelve false inmediatamente.
Publisher tiene plaza reservada; probes no consumen sus 16 tickets ni pueden
bloquearla por volumen. Cleanup/cancel tiene prioridad sobre spawn; entre
clases listas se alterna (publisher primero solo en empate inicial), FIFO
dentro de probes. No se adelantan nuevas llegadas ni se reinicia su plazo.
Cada admitido recibe turno o expira; no se promete exito bajo saturacion o
fallo OS. Un fallo de cleanup congela nuevas admisiones de ambas clases.
Independencia de ping significa conexion/resultado propios: no comparte
canal, confirma tickets ni repara jobs. El supervisor comun solo limita recursos.

### Ejecucion e IPC

Python 3.12 existente: Windows usa `Path(sys.base_exec_prefix)/"python.exe"`
de la instalacion base confiable; Linux usa `Path(sys.executable).resolve(strict=True)`
de la instalacion confiable. Validar ruta absoluta/binario esperado antes de
admitir trabajo; sin PATH, shell, py/uv, redirector venv, sys._base_executable
ni Windows Job API. Layout no soportado falla cerrado, no busca otro launcher.
Ejecutar `[interpreter, "-I", "-S", "-B", absolute_child_script]` con
`Popen(shell=False, stdin=PIPE, stdout=PIPE, stderr=DEVNULL, bufsize=0,
close_fds=True, cwd=trusted_script_directory, env=child_env)`.
Windows anade CREATE_NO_WINDOW | DETACHED_PROCESS y env contiene SOLO SystemRoot valido de la
instalacion OS; Linux env vacio. No heredar PATH/PYTHON*, DSN, credenciales,
tokens, handles/FDs de aplicacion ni stdin/stdout/stderr del servidor.
Script absoluto fijo del paquete, stdlib solamente; guard main, sin imports
de app/settings/site, boot, logging, subprocess de segundo nivel ni descendientes.
El hijo envia primero `{kind:"ready",pid:os.getpid()}`; debe coincidir con
Popen.pid ANTES de transmitir la consulta. Mismatch es fallo de ownership:
retener registro/fallo, no afirmar cleanup completo por matar solo el launcher.
La identidad y ausencia de descendientes requieren prueba real por plataforma;
ni metadatos/tamano de ejecutable ni ese handshake son prueba OS completa.

IPC local por dos pipes anonimos, no protocolo DNS de red. Cada frame lleva
longitud uint32 big-endian y JSON UTF-8 estricto. Request <=2048 bytes, claves
exactas host, port, family, socktype, proto, flags; host string <=1024 bytes
sin NUL, port entero 0..65535, enteros no bool para los otros argumentos.
Familias UNSPEC/INET/INET6; type 0/STREAM/DGRAM, proto 0/TCP/UDP y flags
limitados a la mascara de socket.AddressInfo de ese OS; nunca quitar flags.
No enviar URL, password, job/envelope/payload, tenant, token o request_id.
Ready <=128 bytes; despues exactamente un resultado <=65536 bytes y EOF:
`{kind:"ok", answers:[...]}` o `{kind:"error", code:"..."}`, sin extras.
Maximo 64 tuplas en orden original (family,type,proto,canonname,sockaddr);
conservar IPv4 (host,port) e IPv6 (host,port,flowinfo,scope_id), IP numerica,
port 0..65535, flowinfo 0..1048575, scope_id uint32 y canonname <=1024 bytes.
Sin truncar/reordenar. Whitelist EAI: AGAIN/NONAME/NODATA/FAIL/FAMILY/ADDRFAMILY/
SOCKTYPE/SERVICE/BADFLAGS/MEMORY/SYSTEM/OVERFLOW (solo si existen en socket),
mas INVALID_REQUEST/RESOLVER_FAILURE; mapear a socket.gaierror con texto
constante. Ninguna excepcion, traceback, razon OS o JSON crudo cruza logs.
Rechazar claves duplicadas, NaN, esquema/rangos/tipos invalidos, frames extra,
longitud excesiva o EOF parcial antes de aceptar; limites antes de alloc/parse.
IPC/crash/INVALID_REQUEST/RESOLVER_FAILURE usan EAI_FAIL; timeout DNS usa
EAI_AGAIN tras reap si la referencia no fue cancelada. Texto siempre fijo;
sin nuevos codigos HTTP/outcomes (antes de envio: connect_failed/not_sent).

Supervisor aplica os.set_blocking(fd, False) a ambos extremos del padre;
os.read/os.write parciales, offsets persistidos y BlockingIOError reintentable.
Por ciclo y por hijo: como maximo 8192 bytes leidos y 2048 escritos, sin bucle
de drenaje ilimitado; parser solo sobre frame completo acotado. Cerrar stdin
tras request completo. Nunca buffered read/recv/communicate ni esperas de
pipes/proceso en owner; el hijo puede bloquear en resolver/I/O y es terminable.
Exito/error validos se entregan al owner solo tras EOF, exit 0, reap y pipes
cerrados. Exit no cero, salida incompleta o no salir dentro de plazo son fallo.
No cache, pool persistente, DNS manual, IP fija, configuracion o dependencia nueva.

### Plazos, cancelacion y cleanup

Todos son deadlines monotonic absolutos, sin conceder cinco segundos por fase.
Generacion: Dsetup=t0+5 s. DNS (admision, spawn, handshake y resultado) hasta
t0+2.5 s; cleanup DNS hasta t0+3 s. TCP/TLS/AMQP consume solo lo restante:
si no ready a Dsetup-0.5 s, abort/cleanup hasta Dsetup. Timers Pika mas largos
no amplian ese limite. Ticket sigue 10 s desde reserva, confirm <=5 s o resto,
dos setups maximo y backoff existente; DNS nunca renueva el ticket.
Popen+ready tiene subpresupuesto 0.5 s desde inicio de lanzamiento, siempre
recortado por deadline DNS. Ping: Dprobe=entrada+5 s incluye FIFO, DNS,
conexion/declaracion y cleanup; DNS hasta min(inicio del lease+2.5 s,Dprobe-1 s),
reap hasta min(DNSdeadline+0.5 s,Dprobe-0.5 s); abort de probe a Dprobe-0.5 s.
No iniciar fase sin resto positivo. El timeout Docker health de 5 s es un
limite externo de la peticion completa, no este presupuesto solo RabbitMQ;
SQL/HTTP/scheduling pueden consumirlo. No se modifica Docker ni se promete
que todo /health concluya en 5 s. Son presupuestos internos, no SLO.

Referencia: WAITING -> STARTING -> RUNNING -> REAPING -> DONE; cancel es
terminal para delivery pero NO acredita cleanup. cancel() true solo si gana
antes de entrega/cancel previo; false en los demas casos. Cada owner serializa
cancel/completion y verifica token local + generacion + stopping al despachar;
buzon ya listo no autoriza callback tardio. No transferir esos tokens al hijo.
Antes de spawn cancelar retira la espera; durante Popen retiene plaza y marca
cancelled: cuando retorna, no manda consulta ni callback, termina/recolecta.
Al cancelar/deadline/error: terminate una vez, gracia <=100 ms, kill si sigue
vivo, poll cada ciclo y wait(timeout=0) solo tras observar salida. Reap exige
returncode confirmado; cerrar pipes y soltar referencias Popen gestionadas por
stdlib. EOF, cancel true, is_closed o kill enviado no prueban hijo muerto.
No reemplazar generacion ni liberar plaza hasta cleanup real de sus recursos;
probes independientes pueden coexistir, resolvers abandonados de un mismo
owner no. Al completar DNS normalmente tambien se recolecta antes del callback.

close publica Dclose=ahora+5 s UNA vez para owner, TODOS los probes y supervisor;
frena admisiones, cancela pendientes, resuelve tickets segun frontera de envio
y aborta transportes en sus owners. Acorta los deadlines en curso, no los alarga.
El caller espera/join solo con resto comun; el owner nunca join/wait. Supervisor
sale cuando no queda spawn/hijo/pipe pendiente; close exitoso exige ademas cero
loops/conexiones/probes/owner/supervisor vivos. Probes no retornan true hasta
cleanup propio; el supervisor compartido persiste hasta close del lifespan.

Popen no es interrumpible en muchas APIs OS: el supervisor unico puede quedar
atascado y retrasar tambien cleanup de otro hijo. Owner conserva timers,
expira tickets y marca fallo; no lanza otro supervisor ni borra el pendiente.
Si lanzamiento/reap excede su plazo, kill falla o no hay prueba de salida,
retener handles/plazas/referencias, congelar admision, permanecer STOPPING con
cleanup_failed y close lanza StartupError fijo sin causa. Un ping devuelve
false; nunca reporta cero helpers. El supervisor continua cleanup si OS vuelve,
sin auto-replay/reconexion tras ese fallo retenido; close repetido solo puede
tener exito cuando compruebe cero recursos. Ningun deadline reinicia los anteriores.
La cota de cierre limpio presupone scheduler, creacion y terminacion/reap OS
operativos dentro del presupuesto; no garantiza OS arbitrario ni salida del
backend si Popen queda bloqueado. Este limite se presenta en el gate, sin
debilitar el criterio de cero helpers para cualquier close que tenga exito.

### Verificacion y soporte del addendum

La tabla vigente relaciona las dos regresiones con hijo bloqueado real,
compatibilidad Pika, PID/cleanup Windows/Linux y TLS auditable ya disponibles.
Un monkeypatch parental no prueba bloqueo del hijo. No exige la matriz
combinatoria original ni duplicar tests versionados para aceptar evidencia.
Una actualizacion Pika/Python requiere revalidar las fronteras afectadas;
fallo de compatibilidad vuelve a revision, sin pin/version nuevo aqui.
Fuentes: Pika instalado 1.4.4, nbio_interface.py:26-32,134-150,304-314 y
select_connection.py:97-124; [constructor](https://pika.readthedocs.io/en/stable/modules/adapters/select.html).
Python 3.12: [subprocess](https://docs.python.org/3.12/library/subprocess.html),
[pipes no bloqueantes](https://docs.python.org/3.12/library/os.html#os.set_blocking),
[venv](https://docs.python.org/3.12/library/venv.html),
[base_exec_prefix](https://docs.python.org/3.12/library/sys.html#sys.base_exec_prefix),
[aislamiento CLI](https://docs.python.org/3.12/using/cmdline.html#cmdoption-I),
[getaddrinfo](https://docs.python.org/3.12/library/socket.html#socket.getaddrinfo).
Estos textos acreditan APIs/limitaciones, no viabilidad ejecutada de la propuesta.

## RF-086-003 option2: contrato propuesto

Pre-code APPROVED por Paris, registro 25/09/2026 08:31:11 UTC en proposal.md;
ADR-0009 Accepted. El contenido tecnico siguiente se aprueba sin cambios.
Sus referencias PENDING/Proposed son preparacion historica; las pruebas,
implementacion y QA del incremento aun deben acreditarse.

Estado 25/09/2026: incorporacion comunicada en proposal.md; detalle pre-code
PENDING. [ADR-0009](../../../docs/adr/ADR-0009-rabbitmq-publisher-lifecycle.md)
Proposed, ADR-0008 Accepted solo para aislamiento original. Las secciones
historicas posteriores, incluido conservar `503 + queued`, no gobiernan este
incremento. No se ejecutan pruebas en esta fase; validacion/guard a cargo del
orquestador antes del gate.

### Publisher y limites

Baseline previo a la implementacion local: `RabbitMQQueue` compartia `BlockingConnection` entre threads
de rutas sync, sin bombeo idle ni confirms; `ping()` abre otra conexion.
`lifespan` ya dispone ExitStack, `create_job` hace commit antes del publish,
`status` es STRING sin CHECK y `result` JSONB nullable. Processor coteja
persistencia/membership, devuelve completed sin reescribir y permite
`mark_running` para no-completed. No necesita cambiar su politica de estados.

Un owner por instancia/lifespan/proceso, sin conexiones al importar. La API
sync usa una reserva y un ticket con lock/Event, nunca connection/channel.
Elegir **Pika SelectConnection**, ya incluida, con IOLoop en ese hilo: callbacks
de socket, heartbeat, confirm y timers siguen activos mientras falta un ack.
No usar `BlockingChannel.basic_publish` ni confiar en un timeout del caller:
`process_data_events` atiende idle en BlockingConnection, pero sus callbacks
de usuario se difieren dentro de llamadas bloqueantes anidadas; el timeout de
Connection.Blocked no limita una confirmacion ausente con heartbeats vivos.

Errata de integracion verificada en Pika **1.4.4**, version instalada sin
cambios de dependencia: construir `SelectConnection(..., custom_ioloop=...)`
directamente con `SelectorIOServicesAdapter` y
`internal_connection_workflow=True` (default). La factory `create_connection`
envuelve de nuevo el adapter y falla por ausencia de READ; no usarla para
esta composicion ni conservar un workflow retornado por ella.

La receta original usa `create_streaming_connection`; el segundo override
DNS anterior solo la ampliaria tras su gate. Este hook del adapter envuelve
`protocol_factory` con un delegado de la interfaz interna `AbstractStreamProtocol` y captura
el transporte/delegado propios. Su `on_done` reenvia errores sin alterarlos y,
en exito, entrega a Pika `(transport, original_protocol)`, ambos originales.
Socket/TLS/AMQP permanecen en Pika. Delegar DNS a Pika describe la receta
original; seria sustituido solo al aprobar el addendum DNS. El delegado reenvia `connection_made`,
`data_received` y `eof_received`, preservando argumentos y retornos.
En `connection_lost` solo traduce `None` a un `ConnectionAbortedError` fijo
saneado cuando su flag local acredita nuestro abort externo explicito;
cualquier otro error conserva identidad y `None` sin ese flag se reenvia.

Antes de existir stream, `Connection.close()` publico cancela el workflow
interno (verificado antes de iniciar I/O). Con stream, incluso en handshake,
el owner marca ese flag y llama al `transport.abort()` del interfaz interno capturado,
sin esperar CloseOk. Close durante handshake y abort sin delegado producen
assertions en este runtime. Procesar `connection_lost` y callbacks publicos
`on_open_error/on_close` antes de `IOLoop.stop/close`, todo en el owner;
no basta dejar una conexion olvidada o un hilo daemon. No acceder a `_impl`,
`_transport`, sockets privados, estado privado ni monkeypatches.
Tester verifico el delegado y teardown con Pika real/peer sintetico en
handshake retenido y AMQP abierto: EOF, is_closed, callbacks y salida limpia.
Esta factibilidad no acredita TLS, confirms, broker real ni Green de producto.

| Limite propuesto por proceso | Valor y motivo |
| --- | --- |
| Capacidad | 16 reservas/tickets vivos, incluido como maximo un publish in-flight; try-acquire inmediato, sin espera extra de admision. |
| Deadline de ticket | 10 s monotonic desde reserva, incluye espera de turno/setup; confirm como maximo 5 s y nunca mas que el plazo restante. No es un SLA para SQL/HTTP completo. |
| Eventos/admisiones | Tick del owner cada 100 ms; IOLoop permanece activo aunque no haya tickets. Callbacks no hacen SQL, logging pesado ni esperas bloqueantes. |
| Conexion | heartbeat solicitado 30 s, socket_timeout=3 s, stack_timeout=5 s, connection_attempts=1; setup completo incluido canal/declaracion/Confirm.SelectOk <=5 s por generacion. |
| Broker bloqueado | blocked_connection_timeout=3 s; no iniciar nuevos envios mientras blocked. El timer de confirm independiente cubre ausencia de ack sin Connection.Blocked. |
| Reconexion | Backoff interruptible 1, 2, 4, maximo 5 s; reset al quedar ready. Tickets no enviados observan como maximo dos setups y su deadline; nunca republicar un ticket que alcanzo send. |
| Startup/shutdown | start idempotente, owner vivo <=1 s; broker puede estar no disponible (degraded, sin fingir ready). stop/close idempotente, sin nuevas admisiones, resolver waiters y join <=5 s. |

Son constantes internas iniciales con inyeccion acotada para tests, no variables
de entorno ni cambios de broker/produccion. Aplicar limites tras parsear URL
sin modificar credenciales, host, vhost o TLS. Serializar/copiar el envelope
en el caller antes de entregarlo al owner; no retener copias adicionales ni
loggear cuerpos. Capacidad limita cantidad de tickets, no es un nuevo limite
de tamano HTTP; no se afirma memoria acotada en bytes para bodies ilimitados.

Estados del servicio: NEW -> STARTING -> CONNECTING -> READY; perdida/bloqueo
sale de READY; BACKOFF -> CONNECTING; cualquier estado -> STOPPING -> STOPPED.
READY exige canal abierto, cola durable existente declarada y Confirm.SelectOk.
Cada reconexion crea generacion/canal nuevos, reinstala callbacks y confirma
antes de enviar; no reutiliza delivery tags ni publica desde un canal retirado.
start no ocurre por request. El lifespan registra close antes de start y antes
de yield; un fallo local de arranque impide readiness con StartupError saneado.
Broker caido no impide arrancar el API; recupera en el mismo proceso. Shutdown
aborta setup/transport en el owner, no drena tickets pendientes al broker.

### Ticket, resultado y carreras

Contrato interno propuesto en el modulo de cola: `reserve()` obtiene token
o `not_sent`; `publish(job, reservation=token)` entrega un `PublishResult`
inmutable con outcome/code (sin bool implicito); `cancel(token)` retira trabajo
local segun fase; `start/close/ping` conservan responsabilidades explicitas.
Tras auth/schema/mismatch, reservar antes del INSERT. Rechazo por saturacion,
stopping/owner muerto: 503 sin INSERT ni publish; no requiere que READY ya sea
cierto, por lo que un ticket puede esperar reconexion dentro del limite.

RESERVED -> READY_TO_SEND -> IN_FLIGHT -> terminal. Transiciones, expiracion,
cancelacion y completion comparten lock corto; cada ticket tiene un unico
resultado. Bajo ese lock el owner comprueba plazo/stop y marca IN_FLIGHT justo
antes de `basic_publish`; desde esa frontera cualquier error no diagnosticado
es conservadoramente unknown, incluso si no puede probarse salida de bytes.
`basic_publish` async solo agenda I/O, su retorno no es confirmacion.
Una expiracion que gana antes de esa frontera fija not_sent y prohibe envio
posterior; despues fija unknown y solicita abort de la generacion. Un ack que
gana primero fija confirmed; un ack tardio no cambia resultado, SQL ni HTTP.

Usar exchange vacio, routing_key actual, cola durable, delivery_mode=2 y
mandatory=True. Un solo in-flight por generacion simplifica Basic.Return;
correlacionar ack/nack con generacion y secuencia, incluido multiple. Return
gana frente al ack posterior: no es exito. Retirar/abortar generacion ante
rechazo, timeout o perdida para que un callback tardio no complete otro ticket.
No hay reintento de `basic_publish` del mismo ticket; solo reconexion antes
de enviar. Reconexiones idle pueden continuar con backoff hasta stop, sin
releer DB, reapilar mensajes desconocidos ni crear un job sustituto.

| Resultado | Evidencia y codigo interno | Estado SQL objetivo |
| --- | --- | --- |
| confirmed | Ack de esta generacion/secuencia, sin Return; `confirmed`. | queued |
| not_sent | Ganar retirada antes de IN_FLIGHT; `capacity`, `stopping`, `owner_unavailable`, `deadline_before_send`, `connect_failed` o `serialization_failed`. | publish_failed si ya existe fila |
| rejected | Basic.Nack o Basic.Return correlacionado; `broker_nack` o `unroutable`. Rechazo del broker, no prueba de ausencia de efectos del worker. | publish_failed |
| unknown | Tras IN_FLIGHT sin resultado definitivo: `confirm_timeout`, `connection_lost`, `shutdown_in_flight` o `cancelled_in_flight`. | publish_unknown |

Desconexion del cliente HTTP no cancela el job: la ruta sync sigue hasta
finalizar el resultado acotado. Cancelar la espera local no autoriza declarar
not_sent despues de send ni detener un worker. En finally se retira cualquier
reserva no enviada; DB INSERT fallido no entrega ticket al owner. Expiracion y
shutdown resuelven los waiters, liberan tokens una sola vez y eliminan cuerpos;
un token expirado durante SQL nunca vuelve a ser enviable al acabar el INSERT.
Owner caido: no nuevas admisiones, resolver tickets por su ultima fase, error
generico; no arrancar otro owner mientras el anterior pudiera seguir enviando.

### SQL y API

Persistir el nuevo job inicialmente como `publish_pending`,
`result={"publication":{"outcome":"pending","code":"awaiting_publisher"}}`.
Solo entonces publicar. Envelope con los mismos campos actuales y valores de
id/tenant/created_by/payload/source/artifact/request_id; `status="queued"`
se conserva como indicacion de transporte no autoritativa, sin anadir result
ni controles de publicacion. El worker usa el estado SQL, nunca ese hint.

La ruta finaliza una sola vez mediante UPDATE parametrizado/transaccional:
`WHERE id=:id AND tenant_id=:tenant AND created_by=:creator AND status='publish_pending'`.
Solo ese CAS asigna estado de la tabla anterior, updated_at y
`result={"publication":{"outcome":...,"code":...}}`; no mezcla errores crudos.
Un rowcount=1 confirma escritura. Cero exige lectura con el mismo triple:
running/completed/failed del worker, o un resultado de publicacion ya finalizado,
se conservan byte por byte (tambien timestamps); no hacer UPDATE global ni
devolver payload/result leidos. Fila ausente/scope distinto, estado inesperado
o rowcount>1 son fallo generico de registro, con rollback. No se afloja el CAS
por fallos de serializacion SQL ni se reintenta publish al repetir SQL.

El worker puede ganar antes de ese UPDATE; una entrega autorizada en
publish_pending/publish_unknown conserva su camino actual a running/completed
o failed. mark_running limpia el result transitorio como ya hace; resultado
de ejecucion sustituye al de publicacion. No redefinir failed/replay legacy,
completed ni requeue del consumidor, ni bloquear una entrega legitima por
diagnostico tardio del productor. Membership/creador se revalidan antes de
estados/pipeline y replay como en ADR-0008; actualizar diagnostico de la fila
recien creada no vuelve a autorizar ejecucion tras revocacion.

202 mantiene `{job_id,status:"queued",queue}` y contador actual solo con
confirmed y CAS aplicado o avance scoped ya observado; no promete que el job
siga queued al responder. Para los demas outcomes, 503 JSON conserva el string
`detail="Unable to publish the job into RabbitMQ."` y anade campos top-level:
`code` (`publish_not_sent`, `publish_rejected`, `publish_unknown`),
`job_id` (UUID generado para esta solicitud o null si no hubo INSERT) y
`retryable:false`. No Retry-After ni autoretry; un nuevo POST crea otro job.
No exponer tenant/creador/URL/razon del broker. Body <=512 bytes; campos/codigos
fijos. El consumidor frontend actual acepta texto de error sin parsear shape;
no necesita cambios ni se construye un endpoint de consulta de jobs.

Si falla el registro SQL tras un publish, devolver 503
`code="publication_state_unavailable"`, mismo detail/job_id/retryable, mas
`publication_outcome` con el outcome ya conocido (tambien confirmed posible).
No convertir un ack perdido en failed ni ocultar fallo de DB como 202. La fila
puede seguir publish_pending con indicacion pendiente; no prometer repair.
Un INSERT de resultado incierto conserva el 500 generico existente, sin enviar.
Caida abrupta tras INSERT, send, confirm o antes de respuesta puede dejar
publish_pending, trabajo entregado o respuesta perdida: sin outbox no hay
atomicidad/exactly-once/recuperacion automatica, y se acepta ese riesgo en el gate.

### Salud, verificacion y fuentes

`ping()` conserva probe independiente de dependencia, con conexion propia
usada/cerrada en el hilo del probe y parametros finitos; nunca comparte canal
del publisher ni repara/republica jobs. Puede dar verde mientras falla el
publisher: significa dependencia accesible, no entrega durable ni throughput.
Sin nuevos campos/conteos de negocio en health, labels o cambios Prom/Grafana.
Errores owner/setup/close/DB, logs Pika y callbacks deben pasar sanitizacion
existente; no SQL, payload, broker text, secretos o cause chains. Request ID
validado copiado por ticket, sin heredar contexto de otro request del hilo.

Escenarios funcionales normativos en el delta; evidencia y pendientes solo
en la tabla vigente. Reutilizar Red/Green/mutacion trazables al codigo actual,
sin sumar conteos historicos como nuevas ejecuciones. Un fallo nuevo exige
correccion autorizada y repetir los gates afectados. La receta original
siguiente se conserva como referencia, no orden de ejecutar toda la matriz.

Comandos previstos tras gate, por separado en cada servicio con el Python del
entorno existente: `python -B -m pytest -p no:cacheprovider tests -q --tb=short`.
Focales backend: `tests/test_rabbitmq_publisher.py`, `tests/test_job_publication.py`,
`tests/test_rabbitmq_publisher_integration.py`; processor:
`tests/test_tenant_isolation_jobs.py`, `tests/test_tenant_isolation_integration.py`.
Reutilizar opt-ins `JUP086_COCKROACH_TEST_URL`, `PROCESSOR_COCKROACH_TEST_URL`,
`JUP086_VECTOR_TEST_URL`, `JUP086_RABBITMQ_TEST_URL` con recursos loopback unicos,
marca `processor-integration-tests` y schema existente; nada compartido ni .env.
Fixtures de fallo/timing en tests con stdlib/Pika, sin herramienta/dependencia
nueva. Instancia RabbitMQ desechable propia para restart/nack/blocked, sin
acciones sobre el broker habitual. No contar skips como PASS. Comandos docs:
`corepack pnpm openspec:validate`, `corepack pnpm jup:check -- --change jup-086-tenant-isolation-contract`,
`corepack pnpm jup:cleanup:check`, `git diff --check`; parent valida tras handoff.

Fuentes oficiales: [Pika blocking y callbacks](https://pika.readthedocs.io/en/stable/modules/adapters/blocking.html),
[SelectConnection/custom_ioloop](https://pika.readthedocs.io/en/stable/modules/adapters/select.html),
[confirms/returns](https://www.rabbitmq.com/docs/confirms#publisher-confirms),
[reliability](https://www.rabbitmq.com/docs/reliability).
Los limites numericos, adapter y politica sin replay son decisiones propuestas
de este cambio; no se atribuyen a esas fuentes.

## Historia conservada del aislamiento original

ADR: [ADR-0008](../../../docs/adr/ADR-0008-tenant-isolation-boundaries.md), Accepted; pre-code APPROVED por Paris, registro en proposal.md a 19:04:10 UTC el 24/09/2026.

## Estado y limites

Estado vigente del 24/09 tras re-review: REVIEW_PASS tecnico, 896 PASS sin
skips; RF-086-001/002 corregidos y 65 mutantes distintos (60 detectados/cinco
equivalentes). Paris aprueba aplazar RF-086-003 fuera de alcance el 24/09,
registro 21:23:36 UTC; sigue Open y sin corregir. QA se registra en los enlaces
siguientes; post-QA/publicacion pendientes. [Review](review.md) y
[evidencia](../../../docs/evidence/JUP-086-validation.md) ya existen y
prevalecen sobre las notas historicas siguientes de la primera pasada Green,
874 casos y "antes de reviewer". No se modifican decisiones ni alcance.

Diseno aprobado, **Pre-code approval: APPROVED**. Fuente ejecutable y paths en
[resource-matrix.md](resource-matrix.md); politicas aprobadas, gate, alcance y
base integrada `3a1001d` (incluida PR #41) en [proposal.md](proposal.md). No duplicar aqui el
inventario ni resolver capacidades futuras. Alcance existente, cola/revocacion
previa a ejecucion y salud tienen la aprobacion parcial registrada en proposal.md;
la aprobacion CLI comunicada por el orquestador fija la operacion administrativa
de confianza. Las cuatro politicas estan aprobadas; la implementacion local y
los resultados Green/mutacion del 24/09/2026 constan al final de este documento.
JUP-026/JUP-084 heredan solo el contrato y no bloquean el cierre. La preparacion
documental anterior a 19:04:10 UTC describia el ADR como Proposed; su estado
vigente es Accepted. La validacion documental historica consta en proposal.md,
seccion "Validacion documental consolidada".
La aceptacion del ADR y pre-code consta en proposal.md, "Registro de aprobacion
pre-code". Los pendientes del gate en el texto de preparacion quedan resueltos;
siguen pendientes revision tecnica, QA, aprobacion post-QA y publicacion.

Conservar JUP-085 (bearer, claims, leeway=5, CORS/ADR-0007) y JUP-097
(bootstrap paralelo, logout ante cualquier error de query `/me`).
`users.role` es perfil; `user_tenants.role` esta persistido pero membership,
no RBAC por accion, autoriza actualmente. Conversaciones siguen privadas del
usuario dentro del tenant; `admin` no da bypass. RF-085-002: OUT OF SCOPE.

## Precedencia HTTP

La tabla conserva el baseline y el objetivo del plan aprobado el 24/09/2026;
"Objetivo propuesto" es una etiqueta historica, no una decision pendiente.
El estado local posterior a Green/mutacion se resume al final.

Para JSON parseable en rutas de datos montadas: identidad -> selector ->
membership -> schema body -> discrepancia tenant -> lookup scoped -> accion.
Sin lecturas de recurso, writes o publish despues de una denegacion.
Excepcion de transporte conservada: JSON sintacticamente invalido puede producir
422 sanitizado antes de dependencias. No extender esta precedencia a preflight
CORS, rutas inexistentes o metodos no montados. Fallos internos: 500 sanitizado.

| Caso | Baseline leido, no ejecutado | Objetivo propuesto |
| --- | --- | --- |
| Bearer ausente/invalido, JSON parseable | 401 | 401 antes de selector/membership/recurso. |
| Bearer valido, selector ausente/vacio | 400 | 400, sin lookup recurso. |
| Header duplicado, whitespace exterior/control o lista | Sin rechazo especifico; whitespace no miembro llega a 403; duplicados dependen del parser. | 400, incluso duplicados iguales; no normalizar ID ni exigir UUID. |
| Tenant bien formado no miembro/inexistente | 403 | Mismo 403/body; no distinguir existencia ni evaluar recurso. |
| Membership valido, body sin tenant obligatorio, tipo invalido, texto/titulo/contenido ausente o blanco | 422 de schema | Mantener 422 sanitizado; no convertir todos los errores en 400. |
| Schema valido, tenant de ingesta distinto de header | 400 | 400 sin eco de IDs, INSERT ni publish. |
| Campos de autoridad extra en body conversacion/mensaje | Ignorados, no cambian contexto | 422; metadata documental sigue siendo datos, no controles. |
| Conversacion ajena, de otro usuario del mismo tenant o inexistente | 404 | Mismo 404/body, sin mensajes/citas. POST con body invalido da 422 antes de lookup; con body valido, 404. |
| Publish falla tras INSERT valido | 503 y job queued | Conservar; no afirmar atomicidad/outbox inexistentes. |

Combinar errores en Red: sin auth+selector ausente -> 401; auth valida+selector
ausente+body semanticamente invalido -> 400; tenant no miembro+body invalido ->
403; schema invalido+mismatch/ID ajeno -> 422. Jobs/documentos internos no son
endpoints HTTP. JUP-084 futuro conserva `forbidden` para suscripcion no
autorizada/desconocida, sin consultar datos ni revelar existencia.

## Cambios minimos candidatos

Plan historico del 24/09/2026, preparado antes de la aprobacion de 19:04:10 UTC.
Las referencias a politicas pendientes de implementar y al gate en esta seccion
describen ese momento; se conserva el plan aprobado y sus limites. El mapa
actual de implementacion local esta en resource-matrix.md.

- API: contexto explicito de sesion/membership hasta repositorio; body de ingesta
  solo confirma tenant. Selector unico y bien formado; no combinar metadata con
  controles. `/me` y `/tenants` siguen sin selector.
- Mensajes: lectura con tenant y padre/propietario; INSERT condicionado al padre
  y UPDATE scoped en la misma transaccion. Separar solicitante del autor nullable
  del mensaje assistant; cero filas no autoriza un INSERT parcial. No reparar
  datos legacy inconsistentes automaticamente.
- Jobs/worker: publicar creador; validar forma, cotejar
  `(id, tenant_id, created_by)` con job persistido y revalidar membership vigente
  del creador antes de acceder al estado para replay/transiciones, `mark_running`
  o pipeline/LLM/vector; controles duplicados deben coincidir con persistencia,
  no solo entre copias del mensaje. Usar payload/source/artifact persistidos;
  validar semanticamente cualquier copia usada. Estados/resultados recibidos no
  autorizan. Updates scoped y rowcounts; contexto invalido no modifica ningun job.
- Cola, politica aprobada pendiente de implementar: creador ausente/eliminado,
  membership revocada antes de ejecutar, legacy sin creador o mensaje manipulado
  implican rechazo permanente antes de estados/pipeline. Descartar ese mensaje
  conserva la fila persistida, sin marcarla failed ni reencolar indefinidamente.
  Solo un replay de completed con contexto consistente y membership vigente
  termina sin pipeline ni reescritura de estado, resultados o datos. Los fallos
  transitorios siguen siendo reintentables; no se inventan limites, backoff ni
  infraestructura nueva de retries. No purgar colas ni crear DLQ/firma/outbox.
  La revalidacion previa no garantiza revocacion instantanea ni cancelacion de
  trabajos ya en ejecucion. `request_id` no esta persistido: validar/generar para
  logs, nunca usarlo como autoridad. SQL/vector no son atomicos entre stores.
- Costes: scope tenant+suscripcion tambien en conflictos de `start_run`;
  validar padre scoped antes de DELETE/INSERT/`complete_run`, comprobar rowcount
  y rollback. `fail_run/fetch_run/fetch_records` reciben scope y verifican padre.
  UUID5, FK global o WHERE en un unico paso no bastan. Conservar los campos
  `resource_id`, `resource_name` y `resource_group_conflicts` ya persistidos por
  JUP-014/migration 004 y el grouping CLI `ResourceId` + `ResourceGroup`;
  `ServiceName` ya no se solicita por defecto. La jerarquia es existente,
  no acredita ownership Azure ni autoriza suscripciones por si misma.
- CLI, frontera aprobada: ingesta manual reservada a administradores de confianza
  que controlan CLI/runtime y sus credenciales, responsables de comprobar y elegir
  la pareja tenant-suscripcion. El sistema no detecta una pareja equivocada del
  administrador; no se afirma autorizacion por sesion ni verificacion automatica
  de ownership Azure. No es entrada de costes de usuario final por UI/API.
  Sin allowlist, nuevos roles, identidad de auth, registro de suscripciones ni
  comprobacion automatica de relacion. Esta frontera no relaja el repositorio:
  lecturas, escrituras, borrados, conflictos y reintentos conservan scope y
  transacciones con rowcounts; un run ajeno por ID sigue denegado. El gestor de
  relaciones frontend/API/persistencia permanece posible mejora post-MVP.
- Vector: ownership del documento/job/tenant en la transaccion de reemplazo,
  DELETE scoped y rechazo de colision global sin reasignar propietario.
  Rollback y concurrencia deben conservar documentos/chunks/embeddings ajenos.
  Mantener herencia por FK y filtro tenant previo a top-k en retrieval.
- LLM/logs: metadata, texto e insight no sustituyen identidad ni parametros de
  stores. Ningun candidato/cita ajeno llega al assistant. Logs solo operacion,
  clase/resultado y correlacion segura; no payload, SQL/parametros, excepcion
  cruda/cause-chain, prompt, contenido o IDs ajenos. Redaccion de secretos no
  basta para sanear datos de negocio.
- Salud, politica aprobada pendiente de implementar: en
  `apps/processor/app/api/routes/health.py`, conservar `status` y `services` de
  database/RabbitMQ/vector store con su semantica actual; retirar `jobs` y la
  llamada a `fetch_job_counts()`. Conservar `/metrics`, Prometheus/Grafana y su
  configuracion de monitorizacion, sin nueva frontera de auth para probes.

Usar schema/dependencias actuales. Si hacen falta RLS, constraints, backfill,
nuevas identidades o dependencias, detener y pedir aprobacion separada. La
politica aprobada de cola/health se implementara solo tras el gate global.

## Perimetro posterior al gate

Inventario candidato historico del 24/09/2026 anterior a 19:04:10 UTC, conservado
como plan. La aprobacion posterior resolvio el pendiente del gate; los paths
candidatos no significan que todos hayan requerido cambios.

Paths ejecutables concretos: filas de la matriz. Candidatos de cambio:
Backend `api/dependencies.py`, `api/routes/jobs.py`, `api/routes/assistant.py`,
`schemas/assistant.py`, `db/database.py`; Processor `workers/runner.py`,
`tasks/ingest.py`, `repositories/jobs.py`, `db/database.py`,
`repositories/azure_cost.py`, `tasks/azure_cost_ingest.py`,
`run_azure_cost_ingestion.py`, `vector_store/pgvector_store.py` y
`graphs/pipeline.py`; para salud, `apps/processor/app/api/routes/health.py`.
Queue clients, retrieval y puntos de error solo si Red muestra necesidad.
Health y CLI tienen politica aprobada; el gate global sigue pendiente.
Sin cambios implicitos en frontend, auth/CORS, migrations, manifests o CI.

Pruebas candidatas nuevas tras aprobacion:
`apps/backend/tests/test_tenant_isolation_api.py`,
`apps/backend/tests/test_tenant_isolation_repository.py`,
`apps/processor/tests/test_tenant_isolation_jobs.py` y
`apps/processor/tests/test_tenant_isolation_vector.py`.
Reutilizar y ajustar los tests existentes inventariados, no authored aqui.

## Red, Green, mutacion y validacion real

Plan de verificacion aprobado el 24/09/2026, conservado como referencia; las
menciones a reconciliacion de tests y ejecucion futura describen la preparacion.
Los resultados disponibles tras Green/mutacion se registran al final.

Fixtures: A/B con usuarios separados, otro usuario de A, multi-tenant y usuario
sin tenants; marcadores sinteticos reconocibles. API con bearer/dependencias
reales; dobles solo para observar ausencia de llamadas tras rechazo.
Red cubre el delta: precedencia, hijo/padre inconsistente, envelope/creador
tampered, conflictos start/complete/fail/fetch, reemplazo y retrieval cruzados.
Incluir creador eliminado o membership revocada antes de ejecutar, legacy sin
creador, rechazo permanente con mensaje descartado/fila intacta, replay completed
consistente sin reescritura y fallos transitorios reintentables. No prometer
cancelacion inmediata si se revoca membership durante un trabajo ya iniciado.
Para salud: mismos estados `ok`/`failed` por dependencia y `ok`/`degraded`
globales, ausencia de `jobs` y cero llamadas a conteos globales, con `/metrics`
y monitorizacion Prometheus/Grafana sin cambios.
Reconciliar test JUP-020 que hoy espera running/failed antes de validar envelope.
Un fallo de entorno no es Red. Green queda limitado al alcance aprobado.

Mutantes: quitar membership/tenant/owner/creator, invertir igualdad header/body,
marcar running antes de cotejo, omitir guard de conflicto/rowcount, DELETE vector
global, retirar filtro retrieval, mezclar metadata/modelo con contexto o loggear
excepcion cruda. Aserciones conductuales deben detectarlos. No hay runner Python
de mutacion en package scripts: tester define protocolo acotado; dependencia o
excepcion requieren aprobacion, sin inventar scores.

Exigir CockroachDB, PostgreSQL/pgvector y RabbitMQ reales desechables: bases,
colas/vhost, puertos loopback y recursos unicos, sin volumen compartido.
Aplicar solo schema existente en esos recursos; nunca migrar una DB compartida.
Validar HTTP -> job persistido -> queue -> worker -> vector -> retrieval con
dos tenants, tampering/replay, colisiones concurrentes, caida/reintento y rollback.
Comparar filas/timestamps/embeddings ajenos antes/despues y buscar sus marcadores
en resultados/logs. Limpiar solo recursos creados por esa ejecucion.

## Comandos

Validacion documental ejecutada y observada independientemente por la sesion
principal el 24/09/2026 sobre `3a1001d`, antes de esta nota, desde raiz:

| Comando | Resultado observado |
| --- | --- |
| `corepack pnpm openspec:validate` | Exit 0, 34/34. |
| `node tools/jup-check.mjs --change jup-086-tenant-isolation-contract` | Exit 0. |
| `node tools/jup-check.mjs --all` | Exit 0, 11 cambios activos. |
| `node tools/jup-cleanup-check.mjs` | Exit 0, 636 archivos. |
| `git diff --check` | Exit 0. |
| `node tools/validation-questions.mjs validate` | Exit 0, 28 consultas y 7 categorias; validacion estructural. |

OpenSpec uso los binarios existentes de `node_modules/.bin` de la raiz en PATH,
telemetria desactivada y escalacion autorizada. Guard y existencia de enlaces
locales constan en tasks.md, 1.7; anclas y enlaces externos no comprobados.
Estos resultados no acreditan aceptacion funcional ni aprobacion pre-code.
Son evidencia historica anterior a esta reconciliacion de decisiones aprobadas;
no se ejecutan aqui validadores ni pruebas. El registro mas reciente de validacion
documental y gate consta en proposal.md, seccion "Validacion documental consolidada".

Comandos candidatos historicos, preparados el 24/09/2026 antes de 19:04:10 UTC
para ejecutar tras aprobacion, en entornos existentes. No son un registro de
ejecucion de esta sincronizacion. Cada servicio tiene paquete `app`, por lo
que el plan los separaba:

```text
# apps/backend, y despues apps/processor
python -B -m pytest -p no:cacheprovider tests -q
# apps/processor, opt-in real aislado
python -B -m pytest -p no:cacheprovider tests/test_azure_cost_cockroach_integration.py -v
# raiz
corepack pnpm test
corepack pnpm build
corepack pnpm lint
corepack pnpm --filter @finops/frontend typecheck
```

Cockroach opt-in exige `PROCESSOR_COCKROACH_TEST_URL` a nodo desechable y marca
`processor-integration-tests`; seguir sus controles anti-base-compartida.
Skip sin URL no es PASS. Smoke `scripts/smoke_document_ingestion.py` complementa
positivos, no sustituye negativos. En la preparacion anterior a 19:04:10 UTC
los nuevos tests de integracion aun no existian y sus comandos quedaban para
tester tras el gate. Los resultados posteriores se detallan abajo; esta
sincronizacion no instala dependencias, altera relojes ni ejecuta pruebas.

## Estado local tras Green y mutacion, 24/09/2026

Fuente leida: informe final del tester
`C:/Users/Trabajo/AppData/Local/Temp/jup086-mutation-7s05kxzl/final-report.json`,
estado `MUTATION_PASS`. Sus comandos ejecutaron por separado backend y processor
con `python -B -m pytest -p no:cacheprovider tests -q --tb=short --disable-warnings`,
basetemp y JUnit aislados. Backend: 412 PASS = 259 existentes + 153 nuevos;
processor: 462 PASS = 304 existentes + 10 de ingesta reconciliados + 148 nuevos.
Total: 874, sin fallos, errores ni skips. El informe confirma 91 hashes Python
de producto y 98 hashes de fuentes/documentos intactos durante el tester.

Mutacion: 60 variantes distintas, 62 intentos, 55 KILLED semanticos y cinco
equivalentes, sin pendientes. B09/B10 conservan predicados que implican igualdad
tenant hijo/padre; C03/C04 conservan UPDATE final scoped con rowcount y rollback;
V05 conserva el bloqueo del upsert condicionado por tenant/job en la misma
transaccion y DELETE por el padre bloqueado. Los mutantes SQL usan SQLite;
Green completo tambien ejecuta CockroachDB real. Es una campana acotada de
decisiones de seguridad, no mutacion exhaustiva.

La sesion principal confirma todos los opt-ins DB aislados y el recorrido
ASGI HTTP -> RabbitMQ -> worker -> CockroachDB/pgvector -> retrieval con dos
usuarios/dos tenants, replay, descarte permanente, concurrencia vectorial y
terminacion real de conexion PostgreSQL con rollback/redelivery. Modelos y
embeddings son mock. Comunica guards tester/coder PASS y comprobaciones
suplementarias PASS: frontend 235/235, Azure API 59, Node 91 y colaboracion 12;
frontend lint/typecheck/build PASS, con el warning de chunk grande ya existente.
Son 1271 casos distintos en las ejecuciones actuales, sin sumar reruns; los
874 backend/processor son la evidencia central de JUP-086.

La sesion principal tambien comunica runtime Linux con builds de los Dockerfiles
reales y red interna aislada: login HTTP 200, ingesta 202 y dos jobs completed
en dos tenants sembrados con un usuario mediante el existente
`scripts/smoke_document_ingestion.py`; 38 chunks y 38 embeddings mock de ocho
dimensiones. Backend/processor healthy, ambos `/metrics` 200, processor `/health`
con `status=ok`, exactamente tres dependencias y sin `jobs`. Los hashes de los
14 archivos de producto coinciden con los contenedores. Este smoke positivo
complementa el ensayo de dos usuarios; `.env`, DB compartida y relojes intactos,
sin afirmar estabilidad del reloj del host ni cerrar RF-085-002.

El mapa actual refleja selector estricto, rechazo de autoridad extra, mensajes
scoped/atomicos, correlacion y membership antes del trabajo, estados scoped,
costes/CLI scoped, upsert vectorial condicionado, logs genericos y health solo
de dependencias. La adaptacion JSONB de lecturas de mensajes/conflictos de costes
tocadas permite el camino positivo real y no cierra JUP-035/RF-087-002.
Revision tecnica, QA, aprobacion humana post-QA y publicacion siguen pendientes.
La sesion principal ejecutara validadores/guard despues de esta sincronizacion;
review y `docs/evidence/JUP-086-validation.md` se escribiran tras reviewer.
No se ejecutan aqui nuevos tests ni validadores ni se atribuyen a roles humanos
los resultados automatizados comunicados.
