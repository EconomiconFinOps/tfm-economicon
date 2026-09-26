# Revision JUP-086

JUP: JUP-086
Trello: https://trello.com/c/bKxQK9HI

## Estado

**REVIEW_PASS tecnico del conjunto acotado, 26/09/2026.** Base3a1001d mas
diff local; revisiones previas reutilizadas para producto sin cambios.
Ratificacion detallada APPROVED. Sin nuevos hallazgos bloqueantes, defecto
de producto ni necesidad de ampliar pruebas. Reviewer readonly, guard exit0.

Reinicio real del Rabbit propio con mismo backend/publisher/owner, HTTP202
confirmado, estados scoped SQLite, generacion nueva y no replay. Frames
Blocked/Unblocked procesados por Pika; suspension/reanudacion, expiracion
3.001s, cierre0.181s, resultados terminales inmutables y cleanup comprobados.
Los limites y el reloj no cambian. Tres casos nuevos,11 afectados PASS;
144/146 fuentes sin cambios,15 cuerpos de test previos y681 IDs preservados.
Inventario684 (328+356),111 nuevos (60+51); no684 ejecuciones frescas.

Coder GREEN/NOOP; MUTATION_PASS con38 detecciones historicas reutilizadas
y un fallo dirigido separado detectado, no39 variantes distintas. TLS
Windows/loopback y397 comprobaciones complementarias previas reutilizadas,
sin atribuir nueva ejecucion. [Evidencia](../../../docs/evidence/JUP-086-validation.md#validacion-acotada-final).
Riesgos opcionales de la tabla vigente siguen no verificados; no waiver.
**QA_PASS final del alcance acotado**,26/09/2026, sin bloqueos ni excepciones.
Audita146 fuentes,34+4 artefactos, cuatro copias Linux,681 IDs/15 cuerpos
previos y108 referencias documentales; guard readonly y DoD code/stage qa
exit0. No repite suites ni mutantes. Post-QA humano APPROVED y publicacion
autorizada en el gate inferior; no reemplaza revision humana de PR ni merge.

## Reconciliacion documental anterior

**REVIEW_PASS documental, 26/09/2026**, para la reconciliacion con la tarjeta.
Sin hallazgos bloqueantes nuevos ni cambios de producto/tests. La
[tabla vigente](resource-matrix.md#aceptacion-acotada-vigente) mantiene
comportamiento, limites, inventario, DoD de codigo y aprobaciones humanas;
las matrices historicas dejan de exigir todas sus combinaciones.

Reutilizacion TLS aceptable: cuatro PASS Windows/loopback con script/XML/log,
seis hashes de producto y helpers comprobados; runtime CPython3.12.13/Pika1.4.4.
La fixture difiere solo en registro LC_CTYPE. No acredita TLS Linux/Rabbit real
ni una nueva ejecucion. Se conserva681 PASS/108 nuevos/38 mutantes detectados.
Quedan reinicio real del broker y Blocked/Unblocked/expiracion/cierre del
publisher, ratificacion detallada y QA/aprobacion final. No se cierra RF-086-003.
OpenSpec34/34, trazabilidad11, higiene658 y diff-check0; guards spec/reviewer
PASS. **QA documental PASS**, guard readonly exit0, sin defectos documentales
bloqueantes. QA global de JUP-086 incompleto: dos grupos runtime y gates
humanos pendientes, sin exencion, nuevas pruebas o cierre del finding.

## Revision anterior a la reconciliacion de criterios

**REVIEW_PASS acotado tras validacion real, 26/09/2026.** Base3a1001d mas
diff local identificado por hashes. Los tres hallazgos de preparacion de
tests quedan cerrados: idle30/62s real, ACK acelerado solo para su proxy con
heartbeat genuino en ventana y cleanup, start del publisher HTTP protegido,
y rechazo PermissionError exigido por el caso V01 existente.

JUnit confirma681 PASS/0 FAIL/ERROR/SKIP,325+356 IDs intactos y108 nuevos.
Solo tres tests cambiados;143 fuentes protegidas incluidas93 de producto
intactas,146 hashes actuales verificados. Coder NOOP y guards PASS. V01
ahora detecta el mismo operador mediante IntegrityError distinto del rechazo
de permisos exigido; no se restaura ningun caso ni modifica el producto.
Balance38 detecciones distintas =33 previas +4 reales anteriores +V01;
no son38 ejecuciones nuevas. Primer676/5 y V01 superviviente conservados.

No bloqueantes restantes en ese diff; **no es QA global ni cierre**. Faltan
TLS versionado, recursos Linux repetidos y escenarios restantes de broker,
HTTP/SQL/worker. Docker ya responde tras reinicio manual, sin tocar el socket
ni datos previos. [Evidencia](../../../docs/evidence/JUP-086-validation.md#validacion-con-servicios-reales).

QA del26/09: PASS tecnico acotado, **QA_FAIL / BLOCKED_ACCEPTANCE** global,
sin bloqueo de entorno ni dispensa. Confirma681 casos/38 detecciones y
hashes; se corrige su unica observacion documental rotulando como historico
el bloque de consolidacion de tasks.md. La aceptacion pendiente no se cierra.
Servicios de prueba retirados posteriormente; Cockroach salio137 durante
la parada acotada, registrado aparte y sin acreditar cierre gracioso.

### Estado anterior a los servicios reales

**REVIEW_PASS acotado de compatibilidad Linux, registro26/09 15:47 UTC.**
Solo cambia test_managed_resolver.py y un marcador de dns_child_fixture.py.
No hay debilidad bloqueante: la variable regional generada por CPython Unix
se admite solo con C.UTF-8/C.utf8/UTF-8, mientras Popen conserva keys/valores
exactos y las aserciones no-secret/cleanup permanecen. Mutante de herencia
detectado en la asercion no-secret sin modificarla. Coder NOOP; guards PASS.

Linux623 PASS/58 SKIP y35 focales superpuestos; Windows35 focales y backend
316 PASS/9 SKIP, processor Windows no repetido. 146 hashes posteriores
coinciden,144 fuentes intactas incluidas93 de producto; mismo inventario
108 nuevos/681 total y cuerpo publisher de R1 intacto. Se conservan el
aborto inicial del launcher Windows sin casos y el error del clasificador
externo Linux; los JUnit funcionales son validos, no errores ocultados.
La nueva deteccion se registra aparte de33/5 anteriores. No mutation PASS
global ni aceptacion completa: faltan servicios, TLS versionado, recursos
Linux repetidos y otros escenarios. Docker bloqueado por socket de telemetria,
recuperacion limitada pendiente de autorizacion; [evidencia](../../../docs/evidence/JUP-086-validation.md#validacion-linux-y-entorno).

QA readonly del 26/09/2026, registrado a las 16:00 UTC: auditoria documental
acotada PASS sin correcciones; **QA_FAIL global, BLOCKED_ACCEPTANCE /
BLOCKED_ENV**. Confirma JUnit, 681 IDs, 146 hashes y plan de 37 pasos/5 etapas.
Guard QA exit0, cero cambios. Permanecen las integraciones, cinco mutantes
y escenarios incompletos de TLS, recursos y recuperacion; arrancar Docker
no completa por si solo la aceptacion. Sin dispensa ni aprobacion post-QA.

### Estado previo de la restitucion

**REVIEW_PASS acotado de consolidacion; R1 resuelto con un caso recuperado.**
108 nuevos conservados,469 retirados,681 totales. Green final623 PASS/58 SKIP;
producto y heredados intactos. Balance de38 variantes:33 detecciones,
cero supervivientes conocidos y5 no ejecutadas por entorno. No es un minimo
demostrado, mutation PASS global ni aceptacion final. La restitucion tiene
aprobacion explicita; Linux/servicios reales y QA global siguen pendientes.

Auditoria QA del26/09, registrada14:55 UTC: restitucion local completa,
R1 cerrado; **QA_FAIL global, BLOCKED_ACCEPTANCE / BLOCKED_ENV**. Mantiene
las cinco variantes no ejecutadas, Linux/TLS/servicios reales y la incidencia
WinError10053 sin causa establecida. Verifica76 enlaces locales/32 anchors,
42 encabezados del plan e integridad146 archivos. Detecto un count operativo
680 en design.md, corregido a681 sin cambios funcionales. No QA PASS ni
gate humano final; RF-086-003 sigue abierto por aceptacion, sin dispensa.

## Revision de la consolidacion

26/09/2026, re-review de R1 sobre base3a1001d mas diff local. **R1 CLOSED**.
Solo se recupero el parametro `publisher` del test historico
`test_adversarial_cancel_before_spawn_and_cleanup_before_other_lane`.
Cuerpo identico al original; los680 node IDs previos siguen presentes.
Nuevo baseline resolver14 PASS; m33 produce13 PASS/1 FAIL en la asercion
`Spawn overtook pending cleanup`. Es deteccion del requisito de limpieza
antes de otro spawn, no un fallo de imports ni de entorno. No se justifica
mas restitucion por este hallazgo ni se modifica el producto.

145 fuentes intactas en esta restitucion, incluidas93 de producto; los146
hashes actuales coinciden con evidencia tras coder NOOP y tester post-Green.
Backend316 PASS/9 SKIP; processor final307 PASS/49 SKIP. Se conserva la
primera pasada processor306 PASS/1 FAIL/49 SKIP: WinError10053 al esperar
una respuesta HTTP loopback en el test heredado de redireccion, antes de
sus aserciones de seguridad. Un diagnostico individual y una repeticion
completa autorizados pasaron sin cambios. Causa no establecida: ni fuga
de token demostrada ni incidencia de entorno probada inocua. Disposicion:
mantener la incidencia intermitente visible para QA, sin waiver ni cierre
por repeticion; no reabre R1 y no se altera el test heredado.

Balance33 detecciones =32 anteriores adjudicadas abajo, sobre producto y
casos sin cambios, mas m33 recien ejecutado. No sumar intentos repetidos ni
los29 mutantes historicos. Cinco variantes siguen NOT_RUN_BLOCKED_ENV;
mutacion global no aprobada. Linux, TLS real versionado y servicios reales
siguen abiertos; RF-086-003 no se cierra. Reviewer readonly, guard sin cambios.
QA documental/aceptacion global y gate humano post-QA separados, sin permisos
de publicacion. [Evidencia actual](../../../docs/evidence/JUP-086-validation.md#consolidacion-aplicada).

### Historia del fallo con 107 casos

El bloque siguiente conserva el primer REVIEW_FAIL y la adjudicacion32/1/5;
su restitucion pendiente fue aprobada y aplicada en la re-review anterior.

26/09/2026, base3a1001d mas diff local. Alcance: los13 modulos nuevos de
la matriz, no reabrir producto ni implementar otras JUP. Revision readonly
y guard cero cambios. Evidencia independiente de seleccion, node IDs y
parametros exactos, cuerpos/asserts/helpers intactos,133 archivos protegidos
identicos (93 producto/40 tests). Los146 hashes permanecen iguales durante
mutacion y revision. Coder NOOP Green, sin cambios de producto.

**Hallazgo R1, Medium, en alcance y bloqueante:** falta la prueba de
cleanup antes de spawn entre plazas DNS. Al retirar el guard REAPING de
managed_resolver.py, las13 pruebas conservadas del modulo siguen pasando.
El requisito `Concurrent probes cannot monopolize publication or starve
peers` exige cleanup antes de spawn; design.md da prioridad a limpieza.
Arrancar otro Popen potencialmente bloqueante puede retrasar esa limpieza.
No es una preferencia interna ni un nuevo defecto observado en producto:
es cobertura perdida que invalida aceptar el recorte sin correccion/decision.

**Remediacion minima propuesta, aun sin aplicar:** restituir solo
`apps/backend/tests/test_managed_resolver.py::test_adversarial_cancel_before_spawn_and_cleanup_before_other_lane[publisher]`.
Su evidencia historica con el mismo operador detecta "Spawn overtook pending
cleanup"; debe comprobarse de nuevo sobre el codigo actual tras aprobacion.
Quedarian108 nuevos/681 total (backend325,processor356). No se justifica
restaurar mas variantes por este hallazgo. No hay waiver, nuevo ADR ni
autorizacion implicita para ampliar tests o publicar.

**Adjudicacion de mutacion:** el tester dejo m27/m28 inicialmente sin contar
por terminar en IndexError/TypeError. Ambos son detecciones significativas:
m27 permite callback antes de crear/limpiar el hijo y m28 excede el presupuesto
de lectura, provocando una respuesta de error en lugar del resultado valido.
Los baselines pasan y las mutaciones causan esos fallos observables; no son
errores de importacion/runner/entorno. Resultado revisado:32 detecciones,
1 superviviente confirmado dos veces,5 bloqueadas;38 variantes/34 intentos.
No hacen falta nuevas pruebas solo para transformar esos fallos en asserts.

La reutilizacion heredada sostiene los comportamientos acotados declarados,
no equivalencia global. La comparacion payload persistido/envelope fue
detectada por el rechazo `all-controls`, no inferida de positivos heredados.
OpenSpec34/34, trazabilidad11, higiene658 y diff check exit0. Linux,
Cockroach/Rabbit/pgvector y TLS real siguen pendientes;58 SKIP no son PASS.
No se repite QA final con este bloqueo conocido. Aprobacion post-QA PENDING.
Comandos y reportes en [evidencia del recorte](../../../docs/evidence/JUP-086-validation.md#consolidacion-aplicada).

## Revision DNS anterior al recorte

**REVIEW_PASS tecnico local, 25/09/2026, tras la segunda revision DNS.**
No quedan hallazgos bloqueantes de producto en la correccion revisada.
La aceptacion global sigue **BLOCKED_ACCEPTANCE / BLOCKED_ENV**: faltan
Linux, escenarios reales RabbitMQ/CockroachDB/pgvector y casos combinados
restantes. Auditoria QA completada: **QA_FAIL**, registro 17:17 UTC, por
aceptacion incompleta. No identifica nuevo defecto de producto ni
inconsistencia documental. No hay QA PASS, excepcion nueva, aprobacion
post-QA ni autorizacion de publicacion.

Se revisaron los tres modulos DNS/publicador y, en la segunda pasada, la
retencion del registro hasta terminar el hilo y acreditar limpieza de Pika.
No se afirma una nueva revision completa de los contratos tenant/SQL/API
anteriores. Los guards de coder/tester/reviewer pasan; el ultimo reviewer
no modifico ningun archivo. Base: 3a1001d mas diff local, sin commit nuevo.

Resultados del25/09: backend 517 PASS/133 SKIP, processor 366 PASS/134 SKIP:
883 PASS y 267 SKIP, 1.150 casos distintos. Mutacion actual: 29 variantes,
29 detecciones semanticas, cero supervivientes/excepciones. Cuatro pruebas
TLS temporales y diez ciclos DNS Windows se acreditan aparte, sin sumar
reruns, baselines o cifras historicas. Detalles, comandos, hashes y limites
en [evidencia DNS](../../../docs/evidence/JUP-086-validation.md#validacion-dns-local).

### Hallazgos DNS revisados

- Primera revision: helpers DNS Pika vivos tras close/retry. Corregido para
  el alcance Windows demostrado mediante hijos reales terminados/reaped
  antes de liberar las fixtures; no supone certificacion Linux.
- Segunda revision: un DNS ya cerrado permitia sustituir un publicador aun
  vivo tras close fallido. Reproducido en Red y corregido: el mismo criterio
  de retirada protege registro activo, cache y unregister. Exige hilo
  terminado y prueba de limpieza emitida por su propio owner; conserva
  referencias no verificadas. Un objeto NEW/probe no libera otro owner.
- La entrega ya IN_FLIGHT puede seguir siendo unknown y llegar tarde;
  no se cambia ese contrato ni se demuestra duplicacion o fuga entre tenants.
  Se rechaza el reemplazo hasta limpieza verificada, incluso si close fallo.
- La fixture reconoce solo el aborto terminal Windows 10053 observado;
  mantiene las aserciones independientes de resultado y limpieza del producto.

RF-086-003 sigue Open por aceptacion pendiente. TLS local real y plateau
Windows acotado ya tienen evidencia; no sustituyen broker real, Linux,
pruebas combinadas restantes ni aceptacion QA. Auditoria de solo lectura y
guard PASS, sin repetir suites/mutacion. El bloque humano post-QA sigue PENDING.

## Historia anterior a esta re-revision

Actualizacion de autorizacion: pre-code DNS **APPROVED** por Paris, registro
25/09/2026 14:51:40 UTC en proposal.md; ADR addendum Accepted. Comienzan
Red/correccion autorizados. El veredicto tecnico anterior REVIEW_FAIL y
dos Red no se cierran por esta aprobacion; nueva revision/QA pendientes.
No son cuotas por tenant ni garantia de escalabilidad; sin publicacion.
Los pendientes de preparacion siguientes quedan historicos.

Actualizacion documental posterior, 25/09/2026: **propuesta DNS preparada;
gate detallado pre-code PENDING**. Paris responde "adelante, pero documenta
todo lo necesario" tras explicitar proceso terminable y dependencia interna
acotada de Pika (registro 14:03:35 UTC; autorizacion en proposal.md). Resuelve
la eleccion que bloqueaba la redaccion, no acredita implementacion o QA.
Spec-planner entrega seis documentos coherentes, READY_FOR_PRE_CODE_GATE;
guard PASS, exactamente seis paths documentales y cero violaciones.
OpenSpec 34/34, trazabilidad 11, higiene 654 y diff check exit 0 observados
por el orquestador; no son pruebas de comportamiento ni re-review funcional.
La propuesta/ADR distinguen interfaces internas Pika de APIs stdlib publicas,
acotan procesos/probes, IPC, secretos, plazos y fallos OS, y fijan siete paths
futuros. No se ha cambiado codigo/tests; **REVIEW_FAIL sigue vigente**.

Origen del veredicto conservado: **REVIEW_FAIL / BLOCKED_DESIGN**, registro
del orquestador el 25/09/2026 a
10:49:57 UTC. El incremento esta implementado localmente, pero la revision
reproduce un limite de cierre DNS contrario al contrato. Dos regresiones
nuevas fallan; no hay correccion validada ni Green/QA actuales. Docker y
aceptacion real permanecen bloqueados por separado. Aprobacion post-QA,
publicacion, PR, merge y archivo pendientes, sin acciones externas.

La primera pasada offline dio 441 backend + 366 processor = 807 PASS y
267 SKIP; reviewer audito los JUnit y los 34 mutantes detectados en 35 intentos.
Es evidencia anterior al Red DNS, no aceptacion del incremento. Los cuatro
paths incrementales son publisher, lifespan, repositorio de jobs y ruta de
ingesta; los otros 87 archivos Python de producto coinciden con la copia
previamente revisada. Guard reviewer PASS, cero cambios; guard de la posterior
evaluacion coder de DNS PASS, cero cambios. Roles humanos no acreditados por
estas ejecuciones automatizadas. Detalles en [evidencia](../../../docs/evidence/JUP-086-validation.md#incremento-rf-086-003).

Los estados de preparacion y del 24/09 siguientes son antecedentes.

Pre-code del incremento APPROVED por Paris, registro 25/09 08:31:11 UTC
en proposal.md; ADR-0009 Accepted. El pendiente pre-code siguiente es historia
de preparacion. Review/QA/post-QA siguen pendientes de la nueva implementacion.

25/09/2026: **REVIEW_PENDING para el incremento RF-086-003**. Paris incorpora
la opcion 2 a JUP-086 antes de la PR, registro 08:11:57 UTC. Sustituye el
aplazamiento; finding Open, en alcance y aun sin corregir. Contrato ampliado
y [ADR-0009](../../../docs/adr/ADR-0009-rabbitmq-publisher-lifecycle.md) Proposed
pendientes de nuevo gate pre-code tras validacion documental. Red, Green,
mutacion y revision/QA afectadas pendientes; sin publicacion autorizada.

El resultado siguiente corresponde exclusivamente al alcance original del
24/09. Se conserva como antecedente, no como aceptacion del nuevo incremento:

**REVIEW_PASS tecnico**, re-revision del 24/09/2026. Base
`3a1001db857191f7abb6bb025e2fe8b04a50fe56` mas diff local en
`feat/JUP-086-tenant-isolation-contract`. Sin commit nuevo ni PR.
RF-086-001/002 corregidos localmente y re-revisados. La primera revision fue
REVIEW_FAIL; su historial se conserva abajo. Paris aprueba aplazar RF-086-003,
Medium heredado fuera de alcance, el 24/09/2026, registro 21:23:36 UTC.
El finding sigue Open, sin correccion. El contrato aprobado no cambia.
QA confirma **PASS_WITH_APPROVED_EXCEPTIONS** tras verificar la disposicion
y la integridad del codigo. Aprobacion humana final y publicacion pendientes.

[Propuesta y aprobacion](proposal.md), [diseno](design.md),
[contrato](specs/tenant-isolation/spec.md), [matriz](resource-matrix.md),
[tareas](tasks.md), [ADR-0008](../../../docs/adr/ADR-0008-tenant-isolation-boundaries.md)
y [evidencia](../../../docs/evidence/JUP-086-validation.md).

## Hallazgos

### RF-086-001

Medium, en alcance, **Fixed (local, sin integrar)**. Hallazgo inicial:
en `apps/processor/app/tasks/ingest.py::_identifier`,
un surrogate Unicode aislado supera la validacion. Un envelope cuyo `id`
procede de `json.loads(r'"\ud800"')` alcanza SQL: el driver falla con
`UnicodeEncodeError` y el worker usa `nack(requeue=True)`.
El reviewer reprodujo el caso con SQLite y confirmo el fallo de codificacion
en CockroachDB/psycopg. Un mensaje permanentemente invalido no debe reintentarse.

Correccion: rechazar identificadores no codificables antes de consultar SQL.
Regresiones para `id`, `tenant_id` y `created_by`: descarte definitivo,
jobs intactos y cero ejecuciones del pipeline. Implementado con UTF-8 estricto;
las pruebas exigen cero lookups SQL y conservan Unicode valido. Re-review PASS.

### RF-086-002

Medium, en alcance, **Fixed (local, sin integrar)**. Hallazgo inicial: en
`apps/processor/app/clients/rabbitmq_queue.py::blocking_pop`, el bloque del
decoder no captura `RecursionError`. El cuerpo
`b"[" * 10000 + b"0" + b"]" * 10000` provoca esa excepcion sin ack ni nack;
la entrega queda pendiente y puede reaparecer al reconectar.

Correccion: descartar permanentemente errores de profundidad del decoder y
continuar con el siguiente mensaje valido. Conservar la distincion entre
formato irrecuperable y fallos transitorios; sin nueva infraestructura de retries.
Implementado y comprobado con RabbitMQ real. Re-review PASS.

### RF-086-003

Discrepancia de soporte: AbstractIOServices esta declarada no publica, aunque
SelectConnection la acepte. La clasificacion publica previa era incorrecta.
Paris autoriza documentar la excepcion interna acotada (registro 14:03:35 UTC).
El [addendum DNS](design.md#rf-086-003-dns-addendum-propuesto) ya concreta
supervisor unico, dos plazas publisher/probe, cuatro probes FIFO, hijo stdlib
con PID comprobado, IPC acotado y cleanup antes de callback/reemplazo.
Si OS no permite lanzar/terminar/recolectar, retener recursos/admisiones
cerradas y fallar close saneadamente, sin declarar limpieza falsa. La cota
de cinco segundos presupone OS operativo; ese limite se presenta expresamente
en el nuevo gate. La decision de direccion no aprueba ese detalle ni corrige
los dos Red. Sin nueva JUP, dependencia/version ni cambio operativo.

Estado vigente tras implementar: **Medium, en alcance, Open; cierre bloqueado**.
El publicador gestionado, confirmaciones, resultados y SQL scoped estan en el
diff local. No se ha acreditado aun que el fallo original tras inactividad
quede resuelto con RabbitMQ real. No se reutiliza el aplazamiento anterior.

Subhallazgo de esta correccion, cierre DNS (no nueva tarjeta/namespace):
`rabbitmq_queue.py::_Session.finished` considera streams y conexion logica,
pero Pika 1.4.4 crea un Timer no daemon para getaddrinfo. Cancelarlo no
interrumpe una consulta ya ejecutandose. Reviewer observo un resolver vivo
tras close y dos despues de setup/retry; ambos cierres devolvieron en 0.219 s.
Tester conserva dos regresiones con Pika real y DNS retenido mediante Event:
immediate-close y setup-expiry-retry-close. Ambas FAIL semanticos, cero errores
o skips; finally libera y une todos los hilos. La segunda detecta solapamiento.
Impacto: un DNS bloqueado puede retrasar salida del proceso y acumular helpers.
No se afirma que suceda en un cierre sano ni que se haya observado un incidente
DNS real. Bloquea QA por contradecir la garantia de limpieza aprobada.

Coder evalua las APIs instaladas en modo solo lectura: cancel suprime callbacks,
pero no termina el resolver; no identifica correccion minima dentro de la
receta actual que preserve simultaneamente <=5 s y cero helpers vivos.
Opciones evaluadas antes de completar el addendum (historia):

1. Aislar solo DNS en un proceso propio terminable, mediante el hook interno
   getaddrinfo; exige controlar creacion, IPC, terminacion y recogida, conservar
   hostname/TLS y aplicar limpieza tambien al probe. Sin dependencia nueva
   prevista, pero nueva decision de ciclo de vida que necesita aprobacion.
2. Limitar expresamente la garantia DNS y acotar admision/seguimiento para no
   acumular resolvers. No declarar cierre limpio mientras sobreviva uno;
   puede retrasarse la salida del proceso y la recuperacion indefinidamente.
   Cambia el contrato y exige disposicion humana; daemonizar no lo corrige.

La opcion 1 fue elegida para preparar la propuesta; no esta implementada ni
aprobado su gate detallado. Tester/coder corregiran tras ese gate; reviewer
repetira revision y QA se ejecutara despues. No cambiar IPs,
.env, dependencias ni relojes como atajo. La decision no reabre contratos de
tenant, worker, estados SQL/HTTP ni confirma autorizacion de publicacion.

Registro anterior a implementacion (superado solo en cuanto a avance):

Estado vigente 25/09: **Medium, heredado, en alcance, Open**. Paris selecciona
opcion 2 y ordena aplicarla antes de la PR (registro 08:11:57 UTC). El nuevo
contrato del publisher esta propuesto en [design.md](design.md#rf-086-003-option2-contrato-propuesto):
conexion gestionada, confirmaciones y resultados explicitos, sin outbox ni
republicacion automatica de entregas inciertas. No se ha implementado ni
validado funcionalmente. La disposicion anterior conservada a continuacion
queda sustituida; requiere nuevas pruebas, revision y QA antes del cierre.

Antecedente del 24/09:

Medium, heredado, fuera del alcance aprobado, **Open; aplazamiento APPROVED**.
El publicador backend reutiliza una conexion inactiva que RabbitMQ ha cerrado
por falta de heartbeats. La primera ingesta devuelve 503 y deja un job `queued`
sin mensaje publicado; la segunda funciona. Health puede seguir positivo
porque `ping()` usa otra conexion. Los archivos
`apps/backend/app/services/rabbitmq_queue.py` y `apps/backend/app/api/routes/jobs.py`
no difieren de `3a1001d`. El reviewer confirma que no es regresion de JUP-086.

Paris responde expresamente **"aplaza el finding"**, registrado el 24/09/2026
a **21:23:36 UTC**, tras conocer el 503 y el job queued sin publicar.
Aprueba dejarlo para un alcance posterior por acordar, fuera de JUP-086;
no se modifica el publicador ni se introduce outbox. El riesgo permanece
y el finding no se cierra. No se asignan nueva JUP, persona o fecha.
La disposicion permite reanudar el cierre QA; no equivale a aprobacion
post-QA, publicacion, cambio de tracker, merge o archivado.
La evidencia conserva tanto el smoke fallido como el siguiente correcto.

Los tres registros se mantienen en el [backlog de findings](../../findings/backlog.md).
La responsabilidad operativa sigue en Trello; no se atribuye trabajo humano
a la automatizacion.

## Revision Realizada

Revisados 36 archivos, incluidos los no versionados: 14 de producto, 16 de
pruebas y seis documentos. Se contrastaron autorizacion, SQL, cola, estados,
transacciones, vector, logs y los limites aprobados de CLI y health.
JUP-014 se conserva; no se implementan KPIs JUP-026 ni tools JUP-084.

El reviewer cotejo los 60 registros de mutacion con JUnit: 55 detecciones
semanticas y cinco equivalentes defendibles. Los intentos previos invalidos
no se cuentan como detecciones. Equivalencias: B09/B10 por predicados tenant
redundantes; C03/C04 por rechazo scoped final y rollback; V05 por upsert
condicional y bloqueo del padre en la misma transaccion antes de borrar hijos.

Red inicial acreditado: 60 fallos semanticos, 55 casos correctos y 18 skips
por firmas aun inexistentes, que no se contaron como Red ni PASS.
Primer Green completo: backend 412 y processor 462 PASS, sin skips.
Estos resultados no detectaban los dos casos limite. Remediacion: 22 casos
nuevos, Red de 15 FAIL/7 PASS, luego 22 PASS; Green final completo
412 backend + 484 processor = **896 PASS**, cero fallos/errores/skips.
Cinco mutantes nuevos detectados y P05/P06/P21 reejecutados/detectados:
**65 distintos, 70 intentos, 60 KILLED y cinco equivalentes** acumulados.
Reviewer contrasto los ocho XML nuevos, JUnit completos y 101 hashes intactos.
Re-revision acotada a dos archivos de producto y el nuevo modulo de pruebas.
Evidencia y comandos en el enlace superior.

Guards de spec-planner, tester, coder y reviewer sin infracciones.
Reviewer no modifico archivos. El estado documental se sincronizo antes
de revisar; se conserva el historial de gates y no se reabre la aprobacion.

## Riesgos Y Limites

RF-085-002 permanece abierto y fuera de alcance; no se tocaron relojes ni
se acredita su estabilidad sostenida. El arranque smoke fue secuencial,
sin afirmar resuelta la carrera de migraciones de JUP-096.
Modelos/embeddings mock; no proveedor externo ni atomicidad entre stores.
La seleccion tenant-suscripcion del CLI sigue siendo responsabilidad del
administrador de confianza, conforme a ADR-0008.

## Gate Post-QA Humano

- Decision: APPROVED.
- Aprobador: Paris Arcos Martin; respuesta explicita "apruebo" al resultado
  final y a publicar la rama/abrir PR contra develop, sin hacer merge.
- Fecha: registro del orquestador 2026-09-26 20:01:21 UTC, no hora atribuida
  al mensaje humano.
- QA: **PASS**,26/09/2026, para el conjunto acotado aprobado, sin excepciones.
  El PASS_WITH_APPROVED_EXCEPTIONS del24/09 permanece historico; no sustituye
  este resultado ni acredita aprobacion humana.
- Autoriza commit/publicacion de la rama aprobada y PR contra develop.
  No autoriza tracker, merge, archivado ni cambios de alcance. La revision
  humana de PR y la participacion pendiente no se dan por realizadas.

## Resultado QA Historico Del Alcance Original

24/09/2026: comprobaciones tecnicas aceptadas completas. OpenSpec 34/34,
trazabilidad 11, higiene 650 archivos, politica PR/CI 19 PASS; nueve documentos,
56 enlaces locales y ocho anclas comprobados, sin errores. QA contrasto
75 JUnit y el historial de mutacion sin repetir las suites completas.
Guards qa-1/qa-2 sin escrituras. El primer intento se interrumpio por limite
de ejecucion sin dictamen; el segundo completo estas comprobaciones.

El dictamen anterior fue QA_BLOCKED_APPROVAL solo por RF-086-003; no fue PASS.
Tras la disposicion aprobada, QA obtiene PASS_WITH_APPROVED_EXCEPTIONS:
nueve documentos coherentes, 31/31 fingerprints intactos (14 producto y 17
pruebas) frente al snapshot QA anterior y 92/92 SHA-256 de producto intactos
frente al manifest del tester. OpenSpec 34/34, trazabilidad 11, diff y DoD
code/qa exit 0; guard sin cambios ni infracciones. No se repiten suites ni se
recrea infraestructura. Se conservan 896 PASS y 65 mutantes ya acreditados.
RF-086-003 no esta corregido. Aprobacion humana post-QA PENDING, gate separado;
no se ejecuta DoD final ni se autoriza publicacion por este dictamen.
