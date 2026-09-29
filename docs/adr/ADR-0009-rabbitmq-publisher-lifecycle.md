# ADR-0009: RabbitMQ publisher lifecycle

- Status: Accepted
- Date: 2026-09-25
- Related JUP/OpenSpec: JUP-086, [proposal](../../openspec/changes/jup-086-tenant-isolation-contract/proposal.md), [design](../../openspec/changes/jup-086-tenant-isolation-contract/design.md#rf-086-003-option2-contrato-propuesto)
- Trello: https://trello.com/c/bKxQK9HI
- Supersedes: none; complementa [ADR-0008](ADR-0008-tenant-isolation-boundaries.md), que permanece Accepted.

## Verificacion reconciliada, 26/09/2026

Decision Accepted, comportamiento y limites intactos. RF-086-003 es el
incremento expresamente aprobado, no necesidad de la tarjeta original.
La [tabla acotada](../../openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md#aceptacion-acotada-vigente)
define evidencia reutilizable, pendientes y validacion opcional con riesgos;
las matrices/listas de verificacion inferiores son historia de sus gates.
Se preservan literalmente los registros humanos. Ratificacion APPROVED26/09;
reinicio real con mismo backend y Blocked/Unblocked/expiracion/cierre probados,
REVIEW_PASS. Tres casos nuevos,11 afectados PASS, sin cambios de producto o
limites. [Evidencia vigente](../evidence/JUP-086-validation.md#validacion-acotada-final).
QA final PASS sin excepciones; post-QA APPROVED26/09 segun review.md.
No se reabre arquitectura ni concede cierre o merge.

## Implementacion local comprobada

25/09/2026: addendum implementado y REVIEW_PASS tecnico local; no QA ni
aceptacion global. [Evidencia](../evidence/JUP-086-validation.md#validacion-dns-local):
883 PASS/267 SKIP, 29 mutantes detectados, cuatro casos TLS locales y
diez ciclos DNS Windows. Linux y servicios reales siguen pendientes.
Los titulos/estados de preparacion inferiores se conservan como historia y
para mantener sus enlaces; no sustituyen el registro de aprobacion.

Dos detalles realizan el contrato ya aprobado, sin nueva decision:
Windows usa CREATE_NO_WINDOW | DETACHED_PROCESS para evitar conhost adicional
manteniendo los stdhandles redirigidos; retirar el supervisor DNS no retira
por si solo el publicador. El registro activo/cache se conserva hasta
terminar su hilo y acreditar limpieza Pika en el propio owner. Retener
referencias no verificadas impide sustitucion prematura tras close fallido.
No cambian los plazos, limite por proceso, outcomes ni riesgo OS aceptado.

## DNS Addendum: Proposed, Pre-Code Pending

**Estado vigente del addendum: Accepted para implementacion.** Paris aprueba
el gate detallado con "ok adelante entonces", registro 25/09/2026 14:51:40 UTC
en proposal.md, tras aclarar que dos hijos es una cota DNS por proceso y no
por tenant. Acepta excepcion interna Pika y limite OS explicitados. No hay
garantia de escalabilidad/equidad medida: 16 tickets compartidos y un envio
in-flight permanecen, sin cuotas nuevas. Las notas Proposed/PENDING siguientes
son preparacion historica; no acreditan ejecucion, Green, QA o publicacion.

Registro humano de direccion, por el orquestador: Paris Arcos Martin responde
"adelante, pero documenta todo lo necesario" tras recomendar DNS en proceso
terminable y explicitar la dependencia interna acotada de Pika. Registro
25/09/2026 14:03:35 UTC, no hora inferida del mensaje. Autoriza completar esa
propuesta y documentar su riesgo de compatibilidad. No acredita implementacion,
pruebas ni aprobacion del detalle que aun no se habia presentado/validado.
El gate separado de implementacion del addendum sigue PENDING; la decision
Accepted original y su aprobacion de 08:31:11 permanecen intactas.

Direccion/excepcion comunicadas por el orquestador, registro 25/09/2026
14:03:35 UTC (hora de registro): permiten preparar este detalle, no implementar.
La decision original sigue Accepted; el gate de ESTA ampliacion permanece
PENDING despues de validacion documental y debe presentarse por separado.
El bloqueo de redaccion de 13:08 queda superado por ese contexto; REVIEW_FAIL,
dos Red DNS y BLOCKED_ENV no se resuelven. Sin Green nuevo ni QA.

Proponer DNS exclusivamente en un hijo stdlib terminable por consulta, con
un supervisor no daemon por backend. SelectConnection directo, su owner y
el delegado de transporte permanecen; TCP/TLS/AMQP sigue en Pika. El segundo
override getaddrinfo devuelve AbstractIOReference propio. La excepcion es
EXPLICITAMENTE interna: SelectorIOServicesAdapter, AbstractIOServices,
AbstractIOReference y los interfaces nbio de protocolo/transporte. No afirma
API publica estable ni permite atributos privados o monkeypatches Pika.

El [diseno DNS](../../openspec/changes/jup-086-tenant-isolation-contract/design.md#rf-086-003-dns-addendum-propuesto)
fija ejecutable base directo Windows/real Linux, PID comprobado, hijo sin
boot/secretos/jobs/descendientes, IPC JSON acotado por pipes no bloqueantes,
hostname TLS intacto y terminate/kill/reap antes de callback o reemplazo.
Dos plazas globales separadas publisher/probe, cuatro probes esperando FIFO;
cleanup prioritario y turnos alternos impiden monopolio entre clases.
Conservar 10 s por ticket, setup 5 s y close 5 s con deadlines compartidos;
el subpresupuesto DNS no renueva fases. Un close exitoso exige cero helpers.

Popen no ofrece cancelacion portatil del arranque. El supervisor unico puede
quedar bloqueado por OS, conserva plaza/referencias y no se reemplaza; fallo
de lanzamiento/kill/reap deja cleanup_failed, admision cerrada y error saneado,
nunca un close exitoso ficticio. Cotas de limpieza presuponen creacion,
scheduling y terminacion OS operativos. El gate debe aceptar esta limitacion
explicita, no una promesa absoluta frente a cualquier fallo del kernel.

Razon: aislar la llamada bloqueante permite terminar el trabajo DNS sin
alterar DNS del sistema ni implementar su protocolo. Mantener threads Pika,
Future timeout, daemonizar o esperar indefinidamente no cumple cero helpers.
IP fija/desactivar TLS/cambiar settings, nuevo servicio/dependencia y DNS
propio quedan descartados. Migrar todo el adapter o aislar AMQP completo
ampliaria esta correccion; no se propone. Hay coste de crear interprete,
latencia y posible false/degraded por admision de probes; no cache ni pool.
No es aislamiento de seguridad frente a kernel/usuario local comprometido.

Riesgo de soporte: versiones Pika futuras pueden romper esos interfaces.
Exigir compatibilidad con Pika real y la matriz Windows/Linux antes de
aceptar upgrades controlados; no editar pin/version aqui. Fuentes, paths
exactos, criterios IPC/secretos/fallos y pruebas en diseno y
[matriz DNS](../../openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md#addendum-dns-propuesto).
La factibilidad de implementacion requiere Red/Green tras gate; DNS no
sustituye aceptacion pendiente RabbitMQ/Cockroach, re-review ni QA.
SQL/API/outcomes/worker/membership/metricas, ADR-0008 y RF-085-002 intactos;
sin outbox/autoreplay. Solo tras aprobar el addendum quedarian sustituidas
las instrucciones originales de delegar DNS y usar un unico override.

Texto siguiente conservado como historia, incluida la premisa erronea de
API publica en la receta original y TODOS los registros humanos. No es la
clasificacion normativa actual de esos interfaces ni aprobacion del addendum.

## DNS Addendum: Draft Blocked

Paris autoriza preparar la opcion de DNS en un proceso propio terminable
con "si"; registro del orquestador 25/09/2026 12:58:26 UTC. Es autorizacion
de propuesta, no aprobacion del diseno detallado ni de implementacion.
La decision Accepted original y su registro de 08:31:11 se conservan.

Inspeccion de Pika 1.4.4, registro 13:08:00 UTC: `AbstractIOServices`, en
`pika/adapters/utils/nbio_interface.py:26-32`, declara "This is not a public API".
Aceptar ese objeto en custom_ioloop no convierte su contrato en publico.
Las referencias siguientes a adapter/API publica son la premisa historica
incorrecta de la receta, no una garantia vigente de soporte publico.
Esto afecta al adaptador usado por el codigo local, no solo al hook DNS.

La ampliacion debe resolver expresamente si propone una excepcion acotada
para esa interfaz interna, con riesgo de compatibilidad y sin acceso a
atributos privados, o replantea la integracion con APIs publicas. Decision
consultada, PENDING; ninguna excepcion inferida del "si" anterior. No hay
receta DNS detallada validada ni gate listo para programar. El proceso DNS
sigue candidato, sin implementacion o nuevas pruebas. [Review](../../openspec/changes/jup-086-tenant-isolation-contract/review.md#rf-086-003)
conserva el bloqueo de limpieza y esta discrepancia de soporte.

## Context

RF-086-003: el backend conserva una BlockingConnection entre requests sync sin
owner/eventos idle/confirms; un broker puede cerrarla mientras un probe nuevo
sigue verde. El INSERT anterior al publish deja queued ante 503. La eleccion
option2 y su incorporacion se comunican en proposal.md; el detalle requiere
un nuevo gate pre-code, no hereda aprobacion ni evidencia del aislamiento.

## Proposed Decision

Un hilo propietario por lifespan/proceso gestiona **SelectConnection de Pika
existente**, canal/cola durable, confirms mandatory, heartbeat y reconexion.
API sync con tickets acotados y un solo envio in-flight; limites, estados,
shutdown, forma 503 y CAS normativos en design.md. Solo el owner hace I/O Pika.

Un timeout de Future no detiene un publish bloqueante esperando confirm.
SelectConnection mantiene timers activos incluso con heartbeats sin ack.
Errata de integracion, Pika instalado 1.4.4: el constructor directo acepta
servicios I/O publicos en `custom_ioloop`; la factory `create_connection`
no preserva ese adapter. Mantener el workflow interno default. Extender
SelectorIOServicesAdapter solo en `create_streaming_connection`: envolver
protocol_factory con un delegado publico AbstractStreamProtocol y conservar
el transporte/delegado; on_done entrega a Pika transporte/protocolo originales.
El delegado reenvia callbacks, argumentos y retornos; solo traduce
connection_lost(None) a ConnectionAbortedError fijo saneado tras nuestro
abort externo marcado localmente; preserva cualquier otro error.
Antes del stream, Connection.close() cancela el workflow; con stream, el owner
marca el flag local y ejecuta transport.abort(), procesa callbacks y termina
el loop sin CloseOk. Detalle y limites de prueba en design.md. Sin API/estado
privados, sockets manuales, monkeypatches, I/O fuera del owner ni cambios
de version/dependencias. Se corrige la receta, conservando esta arquitectura.

Resultados explicitos confirmed/not_sent/rejected/unknown. Nunca republicar
tras send incierto; 202 solo con confirm. Reutilizar STRING status y result
JSONB: publish_pending inicial, CAS por id/tenant/creador/estado hacia
queued/publish_failed/publish_unknown, preservando progreso del worker.
Los errores 503 anaden codigo fijo, job_id propio/null y retryable=false al
detail string actual; SQL no disponible anade outcome conocido sin fingir 202.
Un job legitimo desconocido puede ejecutarse con la autorizacion existente.

## Consequences And Alternatives

La conexion persiste sin compartir I/O entre threads; limites evitan espera
indefinida por confirm, saturacion o shutdown. Un in-flight limita throughput
y puede generar rechazos bajo carga; las constantes propuestas no son SLO.
El hook publico de transporte requiere tests de compatibilidad/cleanup.
No conservar BlockingConnection con solo lock, Future timeout o timer anidado:
no cubre ack ausente con heartbeats vivos. Una conexion nueva por publish no
es la opcion elegida. No se incorporan librerias ni cambia el consumidor.

DB, broker y respuesta HTTP siguen sin transaccion conjunta. Puede quedar
publish_pending tras caida; confirm perdido puede corresponder a ejecucion
real. Sin outbox, exactly-once, reconciliacion/autoreplay, cancelacion nueva,
migraciones o endpoints para consultar/reintentar jobs. Health sigue indicando
dependencias, no durabilidad de una entrega; monitorizacion permanece igual.

## Approval And Verification

**APPROVED**: Paris Arcos Martin responde "aprobado" tras validar/presentar el
contrato ampliado; registro del orquestador 2026-09-25 08:31:11 UTC en proposal.md.
Aprueba mecanismo publico de lifecycle, limites, estados CAS, ampliacion 503
y riesgo residual sin outbox. Autoriza pruebas e implementacion, no acredita
su resultado ni aprueba post-QA/publicacion. Aceptacion
en el [delta](../../openspec/changes/jup-086-tenant-isolation-contract/specs/tenant-isolation/spec.md)
y paths/pruebas en la [matriz](../../openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md):
Red/Green/mutacion, RabbitMQ real idle/restart/confirm perdido, concurrencia,
cancel/shutdown, SQL races, membership y secretos, re-review y QA incrementales.
