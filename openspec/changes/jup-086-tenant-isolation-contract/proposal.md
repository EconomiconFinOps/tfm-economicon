JUP: JUP-086
Trello: https://trello.com/c/bKxQK9HI

## Aprobacion final y publicacion

Post-QA **APPROVED** por Paris Arcos Martin mediante "apruebo" al gate
final presentado. Autoriza publicar la rama y abrir PR contra develop, sin
merge, Trello ni archivado. Registro26/09/2026 20:01:21 UTC del orquestador;
no hora inferida del mensaje. [Gate completo](review.md#gate-post-qa-humano).
Los estados anteriores siguientes conservan la historia de cada fase.

## Ratificacion de aceptacion acotada

**APPROVED**, Paris Arcos Martin, respuesta "ok continua entonces" despues
de presentar las dos comprobaciones y aclarar que se conserva todo el codigo
y las pruebas actuales. Registro del orquestador: 26/09/2026 19:11:17 UTC;
no se atribuye esa hora al mensaje humano.
Autoriza completar exclusivamente reinicio real de RabbitMQ con el mismo
backend y bloqueo/desbloqueo del publisher, incluidos expiracion y cierre,
segun la tabla acotada ya validada y revisada. Reutilizar helpers/evidencia,
con servicios propios aislados y desechables; preservar datos, contenedores
previos y reloj. Declarar cualquier caso adicional, sin matrices exhaustivas.
Ante defecto nuevo o necesidad de ampliar comportamiento, volver a decision
acotada antes de corregir. Mantiene pendientes QA y aprobacion humana final;
no autoriza PR, Trello, merge ni archivado. Los PENDING de ratificacion
inferiores describen la preparacion anterior, no este gate aprobado.

Resultado tecnico: los dos grupos ratificados estan acreditados con tres
casos nuevos y ocho regresiones PASS, sin modificar producto. REVIEW_PASS;
QA y post-QA humano siguen separados. [Evidencia](../../../docs/evidence/JUP-086-validation.md#validacion-acotada-final).

## Reconciliacion con la tarjeta, 26/09/2026

La instruccion recibida "ok adelante con la recomendacion" autoriza esta
reconciliacion documental: cumplir la tarjeta original y conservar todo el
producto y las pruebas ya aprobados. RF-086-003 es un add-on aprobado
expresamente, no una necesidad de la tarjeta; conservarlo exige verificar
su seguridad y regresiones. No es aprobacion post-QA ni dispensa material.

La [aceptacion acotada](resource-matrix.md#aceptacion-acotada-vigente) y el
delta reconciliado fijan la demanda de verificacion vigente. Las matrices
amplias y estados anteriores quedan como historia; sus registros humanos
permanecen literales y validos para sus decisiones. No cambian garantias
funcionales, arquitectura ni limites numericos. El detalle necesita
ratificacion humana tras validacion y revision, antes de mas codigo/tests.
No hay cierre automatico, exencion global de DoD por ser documentos ni
permiso de PR/Trello. QA previo BLOCKED_ACCEPTANCE sigue siendo su dictamen
registrado hasta nueva evaluacion del orquestador/reviewer/QA.

Validacion posterior observada: OpenSpec34/34, trazabilidad11, higiene658
y diff-check exit0; guard spec-planner seis documentos, reviewer readonly
sin cambios. REVIEW_PASS documental; reutilizacion TLS Windows auditada,
sin ejecutar pruebas ni cambiar producto. Detalle listo para ratificacion;
no se registra una respuesta humana nueva ni aprobacion post-QA.

## Validacion con servicios reales, 26/09/2026

Paris reinicia Docker manualmente y pide reintentar. El motor responde; no
se aplica la recuperacion propuesta del socket. Se ejecutan servicios nuevos
aislados y desechables bajo su autorizacion previa, sin tocar datos o reloj.
Primera pasada676 PASS/5 FAIL; se corrigen tres archivos de tests existentes
tras revision: heartbeat de prueba, inicio del publisher HTTP y exigencia de
PermissionError en V01. Sin nuevas funcionalidades, casos, dependencias,
decisiones de arquitectura ni cambios de producto. No nuevo gate de alcance.

Resultado:681 PASS/0 FAIL/ERROR/SKIP, mismos108 nuevos; las38 variantes
planificadas estan detectadas tras corregir el V01 antes superviviente.
REVIEW_PASS acotado. Se preservan intentos anteriores; QA/aceptacion global
siguen pendientes por escenarios aun sin prueba versionada, no por Docker.
No dispensa, aprobacion final ni permiso de publicacion inferidos.
[Evidencia](../../../docs/evidence/JUP-086-validation.md#validacion-con-servicios-reales).

## Continuacion previa al reinicio, 26/09/2026

Paris pide "ok termina entonces con las validaciones" y autoriza por separado
arrancar Docker y servicios aislados. Se prepara un venv Linux temporal con
las dependencias ya declaradas, sin paquetes globales ni cambios de producto.
Una expectativa de test sobre el entorno visible del hijo se corrige para
la coercion regional de CPython Unix; no cambia el contrato ni el inventario:
108 nuevos/681 total. Linux completo623 PASS/58 SKIP; Windows focal35 PASS y
backend316 PASS/9 SKIP. REVIEW_PASS acotado; aceptacion global pendiente.

Docker falla antes de arrancar el motor al retirar su socket temporal de
telemetria. Se solicita autorizacion adicional para cerrar Docker, apartar
solo ese socket conservandolo y reiniciar; **PENDING**, no se ha aplicado.
Sin datos/volumenes/reloj/WSL modificados. Servicios reales, cinco variantes
de mutacion, TLS versionado, recursos Linux repetidos y otros escenarios
de aceptacion siguen pendientes, algunos aun sin prueba escrita. No se
dispensa ninguno ni se autorizan casos nuevos por inferencia.

## Aprobacion de restitucion de un caso

**APPROVED**: Paris Arcos Martin responde "aprobado" a recuperar solo
`test_adversarial_cancel_before_spawn_and_cleanup_before_other_lane[publisher]`
en `apps/backend/tests/test_managed_resolver.py`. Registro del orquestador:
26/09/2026 14:24:18 UTC, no hora inferida del mensaje. Objetivo: 108 nuevos
y 681 totales; conservar el cuerpo historico y solo el parametro publisher.
Autoriza baseline, mutacion m33, regresion, revision y QA afectados. No
autoriza otros casos, cambios de producto, pruebas heredadas, dependencias,
servicios, dispensas, publicacion, Trello, merge ni archivo. La restitucion
PENDING descrita en el resultado anterior queda aprobada; restitucion ya
aplicada y verificada localmente, segun el resultado siguiente.

## Aprobacion de consolidacion de pruebas

**APPROVED**: Paris Arcos Martin responde "me parece aceptable" al gate
validado de la seleccion de 107 casos nuevos. Registro del orquestador:
26/09/2026 13:34:53 UTC, no hora inferida del mensaje. Autoriza aplicar los
selectores de los 13 modulos de la matriz: 60 casos de aislamiento y 47 de
RabbitMQ/DNS; retirar 470 casos, preservar la base y su adaptacion +4.
Objetivo actual: 680 casos totales, 111 netos sobre base569. Acepta contrastar
el menor muestreo presentado mediante regresion, mutacion, revision y QA;
no aprueba supervivientes relevantes ni dispensas de requisitos.

No modificar producto, pruebas heredadas, helpers o defaults de fixtures.
Sin megatests, deseleccion, SKIP artificial, dependencias o servicios nuevos.
Los pendientes de aceptacion real siguen abiertos y podrian aumentar el
recuento; cualquier restitucion necesaria se comunicara antes de ampliar
la seleccion aprobada. No autoriza publicar, modificar Trello, merge,
archivo ni da aprobacion post-QA. Los PENDING siguientes conservan la
preparacion anterior a esta aprobacion, no el gate vigente de edicion.

## Resultado de la consolidacion, 26/09/2026

Tras la restitucion autorizada: **108 nuevos, 469 retirados y 681 totales**.
60 casos de aislamiento y 48 Rabbit/DNS; base569 mas4 netos adaptados.
Regresion final:623 PASS/58 SKIP, cero FAIL/ERROR. La primera pasada processor
tuvo un WinError10053 heredado; un diagnostico individual y una repeticion
completa autorizados pasaron, sin cambios. Causa no establecida; se conserva
el fallo original y no se presume inocuo.

**REVIEW_PASS acotado; R1 resuelto.** El unico caso recuperado mantiene su
cuerpo historico. Baseline del resolver14 PASS; el mismo mutante m33 ahora
produce13 PASS y1 FAIL semantico por spawn antes de cleanup. No se cambio
producto ni heredados, ni se restituyeron otras variantes.
Balance de38 operadores:33 detectados (32 previos revisados mas m33 nuevo),
cero supervivientes conocidos y5 no ejecutados por servicios reales. No es
mutation PASS global ni dispensa. QA/aceptacion real y aprobacion final
siguen pendientes. Detalles en [review.md](review.md#revision-de-la-consolidacion).

## Preparacion de la seleccion por comportamiento

**READY_FOR_PRE_CODE_GATE; aprobacion detallada de retirada PENDING.**
La direccion actual es acercar la suite a unos87 casos adicionales mediante
reutilizacion, sin convertir combinaciones existentes en obligaciones nuevas.
La propuesta de238 queda **sustituida, no implementada**. La peticion general
de continuar no aprueba aun esta seleccion ni dispensa requisitos.

Seleccion concreta: **107 casos genuinamente nuevos conservados**, separados
en **60 de aislamiento y 47 RF-086-003 Rabbit/DNS**, mas **4 netos** de la
adaptacion heredada seis->diez. Son **111 netos sobre base569; 680 totales**
(324 backend, 356 processor). Se retirarian **470 de 577 casos nuevos, 81,5%**.
No confundir107 nuevos con107 netos: el objetivo historico87 netos equivalia
a83 nuevos+4. Esta seleccion queda24 netos por encima; no afirma un minimo.

El margen conserva comprobaciones con riesgos concretos: diez rechazos
tenant/subscription de cinco operaciones de costes, siete regresiones R2,
dos DNS Red y dos regresiones de mensajes invalidos; ademas hay predicados
creator/tenant separados y rollback/concurrencia. No se exige mantener todas
sus combinaciones de motor, estado, campo o causa. La
[tabla exacta](resource-matrix.md#seleccion-practica-de-pruebas) permite aprobar
el retiro propuesto y sus limites, no una cifra abstracta.

Base569, diez casos adaptados, helpers y comportamiento por defecto de fixtures
permanecen protegidos. La seleccion se hara por parametros indirectos locales,
sin nuevos megatests, bucles de escenarios, deseleccion ni SKIP artificial.
No hay codigo/tests modificados en esta fase ni cupo inventado para tests
futuros: los pendientes de aceptacion se contaran cuando se escriban.

La seleccion debe superar regresion, mutacion sensible, revision y QA.
883 PASS/267 SKIP,29 mutantes y REVIEW_PASS local son historia, no resultado
del candidato. Linux, TLS real versionado y servicios/escenarios restantes
siguen pendientes; **QA_FAIL/BLOCKED_ACCEPTANCE_ENV** no se dispensan.
Los registros de aprobacion funcional siguientes se conservan literalmente.


## Estado actual: RF-086-003 option2, 25/09/2026

### Resultado local del addendum

Implementado y REVIEW_PASS tecnico tras corregir tambien la retirada
prematura del registro del publicador. Green actual: 517 backend y 366
processor PASS; 267 SKIP no acreditados. Mutacion: 29/29 detecciones;
TLS local y diez ciclos de recursos Windows comprobados por separado.
[Evidencia vigente](../../../docs/evidence/JUP-086-validation.md#validacion-dns-local).
RF-086-003 sigue Open: Linux, servicios reales y aceptacion restante/QA
pendientes, sin excepcion aprobada. No se ha publicado ni actualizado Trello.
La siguiente aprobacion pre-code permanece literal; no es aprobacion final.

### Aprobacion pre-code DNS

**APPROVED**: Paris Arcos Martin responde "ok adelante entonces" tras
presentar el addendum validado y aclarar el limite multitenant. Registro del
orquestador: 25/09/2026 14:51:40 UTC, no hora inferida del mensaje. Aprueba
los siete paths de la matriz, supervisor/DNS terminable, dependencia interna
acotada de Pika y fallo retenido ante OS no operativo. Autoriza Red, codigo,
Green, mutacion y re-review/QA del detalle. Las referencias Proposed/PENDING
inferiores se conservan como preparacion historica; no son el gate actual.

Dos hijos es limite DNS por proceso backend, no de tenants ni de ingestas;
conexion persistente compartida, 16 tickets y un envio in-flight permanecen.
La cifra no acredita escalabilidad medida ni equidad por tenant. Comprobar
carga compartida sin introducir cuotas, RBAC, conexiones por tenant o otro
alcance. No modifica el contrato de aislamiento de datos. No autoriza nuevas
dependencias, recuperar/resetear Docker, modificar servicios compartidos,
relojes, tracker, publicacion/PR, merge o archivo. Post-QA sigue PENDING.

### Registro de direccion DNS y gate pendiente

Paris Arcos Martin responde "adelante, pero documenta todo lo necesario"
tras la recomendacion de aislar solo DNS y aceptar una dependencia interna
acotada de Pika con control de compatibilidad. Registro del orquestador:
25/09/2026 14:03:35 UTC, no hora inferida del mensaje. Resuelve la eleccion
pendiente de la preparacion anterior. Autoriza completar/documentar la
propuesta; no representa el gate detallado posterior a su validacion.
**Pre-code del addendum DNS: PENDING.** No habilita codigo/tests nuevos,
recuperacion de Docker, dependencias/versiones, tracker, publicacion o merge.
Los registros humanos originales se conservan sin sustituirlos.

### Propuesta preparada

**Addendum DNS propuesto; gate detallado pre-code PENDING.** La direccion
y excepcion interna comunicadas por el orquestador (registro 25/09/2026
14:03:35 UTC, no hora inferida del mensaje) permiten completar la propuesta.
No habilitan tester/coder del nuevo detalle. [ADR-0009](../../../docs/adr/ADR-0009-rabbitmq-publisher-lifecycle.md#dns-addendum-proposed-pre-code-pending)
conserva Accepted para su decision original y anade esta ampliacion Proposed.
El bloqueo de redaccion siguiente es historia de 13:08; su decision pendiente
queda resuelta para preparar documentos, sin atribuir aprobacion de codigo.

Propuesta concreta en [design.md](design.md#rf-086-003-dns-addendum-propuesto):
conservar owner SelectConnection/delegado y aislar SOLO getaddrinfo en hijo
terminable, con supervisor unico contabilizado, dos plazas globales y probes
FIFO acotados. La dependencia Pika nombrada es interna, con pruebas de
compatibilidad; subprocess/IPC usan APIs publicas stdlib Python 3.12.
Child sin boot/secretos/jobs, PID real, hostname TLS original, cancelacion,
terminate/kill/reap antes de reemplazo; sin false cleanup. Arranque OS no
interrumpible o fallo de reap retiene recursos y falla cerrado. Este limite,
los presupuestos compartidos y los siete paths futuros de codigo/tests en
la [matriz](resource-matrix.md#addendum-dns-propuesto) requieren el nuevo gate.
No se relajan cero helpers tras close exitoso ni resultados inmutables.

Esta fase escribe solo ADR-0009 y proposal/design/tasks/resource-matrix/delta;
validacion documental no es aceptacion runtime ni aprobacion humana. No cambia
SQL/API, worker, membership, metricas, frontend, ADR-0008 o RF-085-002; sin
outbox/replay, dependencia/configuracion/migracion nueva. Parent actualiza
review/evidencia/plan tras guard. REVIEW_FAIL y los dos Red DNS siguen activos;
807 PASS/267 SKIP y 34 mutantes son anteriores; aceptacion real y QA pendientes.

**Preparacion DNS autorizada, ampliacion detallada bloqueada.** Paris responde
"si" a preparar ADR-0009 con DNS en proceso terminable; registro 12:58:26 UTC.
No autoriza codigo/tests nuevos ni acepta una garantia menor. Al contrastar
la receta, Pika 1.4.4 declara AbstractIOServices no publica; registro de
comprobacion 13:08:00 UTC. El uso del adaptador actual no puede presentarse
como public-only. Pendiente decidir si la propuesta solicita una excepcion
acotada de compatibilidad o replantea la integracion publica. No hay propuesta
DNS completa/validada ni nuevo gate pre-code concedido. Ver el
[addendum de estado ADR-0009](../../../docs/adr/ADR-0009-rabbitmq-publisher-lifecycle.md#dns-addendum-draft-blocked).
Las aprobaciones originales conservadas abajo no resuelven esta discrepancia.

**Estado de ejecucion: BLOCKED_DESIGN y BLOCKED_ENV**, registro del
orquestador 25/09/2026 10:49:57 UTC. Implementacion local en los cuatro paths
de producto autorizados; revision independiente REVIEW_FAIL por cierre DNS.
Pika puede dejar resolvers no daemon vivos despues de cerrar y acumularlos
al reintentar. Dos regresiones nuevas fallan semanticamente; la receta previa
del adapter no puede interrumpir un getaddrinfo ya en ejecucion. No se reduce
la garantia ni se introduce otro proceso sin nueva decision humana.
[Review](review.md#rf-086-003) y [evidencia](../../../docs/evidence/JUP-086-validation.md#incremento-rf-086-003)
registran los 807 PASS/267 SKIP anteriores, 34 mutantes detectados y el Red DNS
posterior. No son Green ni QA actuales. Docker tampoco esta disponible; quedan
escenarios reales por completar/escribir. RF-086-003 sigue Open, sin PR.
La aprobacion siguiente acredita el contrato original, no una solucion DNS
adicional ni una excepcion. ADR-0009 conserva su decision Accepted; no afirma
que la implementacion la cumpla. La propuesta DNS ahora detallada requiere
validacion/presentacion y su propio gate antes de implementarla.

**Pre-code del incremento: APPROVED.** Paris Arcos Martin responde "aprobado"
tras presentar ADR-0009, limites, estados, errores 503 y riesgo residual;
registro del orquestador 2026-09-25 08:31:11 UTC. ADR-0009 pasa a Accepted.
Autoriza Red, correccion, Green, mutacion, re-review y QA del contrato ampliado
validado, con los paths de la matriz y dependencias de prueba aisladas.
Se acepta la ventana SQL-broker sin outbox/recuperacion automatica. No autoriza
dependencias, migraciones, frontend, reloj, recursos compartidos, tracker,
publicacion, PR, merge ni archivo. Aprobacion humana post-QA sigue PENDING.
Las referencias PENDING/Proposed de preparacion que siguen quedan superadas
por este registro; el estado de ejecucion vigente se detalla arriba.

Incorporacion de alcance aprobada, comunicada por el orquestador: Paris Arcos
Martin selecciono option2 (publisher persistente con hilo propietario) y pidio
"ok pues aplica correccion ya antes de hacer la pr"; registro del orquestador
**2026-09-25 08:11:57 UTC**, no hora inferida del mensaje. Esta incorporacion
sustituye la disposicion de aplazamiento RF-086-003 registrada el 24/09 a
21:23:36 UTC; los registros humanos originales se conservan literalmente abajo.

**Nuevo gate pre-code detallado: PENDING tras validacion documental.** La
incorporacion no acredita aprobacion del diseno detallado ni permite iniciar
tester/coder. RF-086-003 sigue Open, pendiente de implementacion y evidencia.
896 PASS/65 mutantes, REVIEW_PASS y excepciones QA son historia del aislamiento
original; no validan este incremento. ADR-0008 permanece Accepted para sus
decisiones originales, sin reaprobarlas; [ADR-0009](../../../docs/adr/ADR-0009-rabbitmq-publisher-lifecycle.md)
queda Proposed. Review/evidencia/backlog sincronizados con esta incorporacion.

Validacion documental observada por el orquestador el 25/09/2026, registro
08:28:23 UTC: OpenSpec estricto 34/34, trazabilidad de los 11 cambios activos,
higiene 651 archivos y `git diff --check`, todos exit 0. Diez documentos,
71 enlaces locales y 12 anclas comprobados sin errores. Guard spec-planner
exit 0, siete documentos autorizados, cero violaciones. Corepack fallo antes
de validar por EPERM en sandbox; repetido con ejecucion autorizada, sin red
ni instalaciones. No son pruebas funcionales, review de producto ni QA.
Nuevo gate pre-code pendiente de presentacion/aprobacion; codigo intacto.

El incremento propone un owner Pika con eventos/heartbeats, confirms, reconexion
y admision acotadas; resultados `confirmed`, `not_sent`, `rejected`, `unknown`;
202 solo confirmado, y SQL compare-and-set por job/tenant/creador sin pisar al
worker. Reutiliza `jobs.status` y `result` JSONB; marca incertidumbre persistida
sin impedir una entrega legitima. El gate debe aprobar el adapter/limites,
estados y ampliacion compatible del error 503 descritos en
[design.md](design.md#rf-086-003-option2-contrato-propuesto).

Sin outbox, atomicidad SQL-broker, exactly-once, reconciliacion/autoreplay ni
nueva politica de cancelacion/reintentos del worker. Sin dependencias,
migraciones, frontend, endpoints, tools/KPIs ni cambios de settings externos,
Prometheus/Grafana o infraestructura compartida. Persiste una ventana de caida
entre DB/broker/HTTP; un estado `publish_pending` abandonado no se recupera solo.
Paths exactos y pruebas previstas en la matriz; tareas incrementales pendientes
al final de tasks.md. Esta entrega solo modifica los siete documentos permitidos.

### Errata de integracion RF-086-003, 25/09/2026

La evidencia del tester (`jup086-rf086003-runtime-protocol-handoff.md` y helpers
`runtime_` de `apps/backend/tests/test_rabbitmq_publisher.py`) corrige la receta
para Pika instalado 1.4.4, no 1.4.1: constructor directo, adapter capturador y
delegado nbio interno descritos en design.md/ADR-0009. Siete casos: 5 PASS/2 FAIL;
los tres del delegado pasan, incluidos handshake retenido y AMQP abierto sin
CloseOk; los dos fallos conservan las hipotesis previas de close en handshake
y abort sin delegado. Es factibilidad con peer sintetico, no Green ni confirms
con RabbitMQ real; Docker sigue no disponible segun el handoff del orquestador.
Clasificacion tecnica: errata de implementacion; el delta no exige una factory
concreta y conserva abort publico/ownership/plazos. Limites, estados, SQL/API,
seguridad, aceptacion y exclusiones permanecen intactos. ADR-0009 sigue Accepted
para la arquitectura; esta nota no registra nueva aprobacion ni revision humana
del helper. La aprobacion original de 08:31:11 UTC se conserva literalmente.

## Historia conservada del aislamiento original

## Estado Vigente Tras Re-Review

24/09/2026: REVIEW_PASS tecnico, RF-086-001/002 corregidos localmente.
896 PASS sin skips, 65 mutantes distintos (60 detectados/cinco equivalentes).
RF-086-003 es Medium heredado fuera de alcance; Paris aprueba su aplazamiento
el 24/09, registro 21:23:36 UTC. Sigue Open, sin corregir ni ampliar JUP-086.
Estado QA en review/evidencia; post-QA y publicacion pendientes.
[Review](review.md) y [evidencia](../../../docs/evidence/JUP-086-validation.md)
ya existen y son el registro vigente. Las notas siguientes "antes de reviewer",
874 casos y evidencia futura son historicas de la primera pasada Green.
No cambian requisitos, politicas aprobadas ni el registro pre-code.

## Why

El baseline autoriza `X-Tenant-Id` y filtra conversaciones y retrieval, pero
no cierra todos los limites de escritura, cola y persistencia. Un ID opaco,
un envelope RabbitMQ o un argumento del modelo no acreditan pertenencia.

## Reconciliacion y gate

Reconciliacion documental del 24/09/2026 sobre
`3a1001db857191f7abb6bb025e2fe8b04a50fe56` (`origin/develop` con
JUP-085/JUP-069/JUP-014 integrados), rama
`feat/JUP-086-tenant-isolation-contract`. El contrato original procede de
JUP-088; sus tareas historicas marcadas no acreditan implementacion JUP-086.
El inventario historico y el mapa de estado local actual estan en
[resource-matrix.md](resource-matrix.md).

Fuente de alcance: tarjeta oficial enlazada arriba, descripcion completa
seleccionada por JUP-086 y shortLink `bKxQK9HI` en el export suministrado con
fecha 24/09/2026. Es una fuente fechada, no una consulta en vivo. No se copian datos
privados del tablero. Se conservan los roles propuestos por la tarjeta:
Paris, liderazgo; Victor, pairing; Alejandro, revision; Lucia, QA/documentacion.
Esto no acredita participacion ni modifica asignaciones o estado operativo.

**Pre-code approval: APPROVED.** Paris autoriza iniciar pruebas e implementacion
del alcance consolidado y aceptar ADR-0008, segun el registro siguiente. Las
referencias PENDING/Proposed conservadas mas abajo son historia de preparacion;
este registro las resuelve sin acreditar implementacion ni QA.

## Registro de aprobacion pre-code

- Aprobador: Paris Arcos Martin. Respuesta: "ok adelante", tras la solicitud
  explicita de aprobar ADR-0008 e iniciar pruebas/implementacion y las
  aclaraciones sobre health y exclusion de KPIs/herramientas futuras.
- Registro del orquestador: 2026-09-24, 19:04:10 UTC; hora de registro.
- Decision: ADR-0008 Accepted; autorizado el flujo tester Red, coder Green,
  tester mutacion, revision y QA conforme a design.md y al delta validados.
- Alcance: API/repositorios, mensajes, jobs/cola, costes existentes, vector y
  retrieval, logs y health; CLI administrativo de confianza sin allowlist.
- Excluidos: gestor de suscripciones, KPIs/tools futuros, frontend, auth/CORS,
  cambios de relojes, nuevas migraciones/dependencias/identidades e infraestructura
  compartida. Pruebas reales solo en recursos aislados y desechables, con schema
  existente y limpieza limitada a los recursos de la prueba.
- Esta aprobacion no permite publicar, crear PR, actualizar Trello, fusionar,
  archivar, purgar colas existentes ni cerrar hallazgos ajenos. Aprobacion humana
  final tras QA sigue PENDING; los roles de Trello no acreditan trabajo realizado.

## Registro de aprobacion CLI

- Aprobador: Paris Arcos Martin, mediante respuesta explicita a la pregunta
  de alcance y riesgo de la ingesta manual en esta conversacion.
- Registro comunicado por el orquestador: 2026-09-24, 17:37:11 UTC; no es la hora
  exacta del mensaje. Respuesta: "Si, como operacion administrativa de confianza".
- Decision: para el MVP, la ingesta manual queda reservada a administradores
  de confianza, responsables de comprobar la relacion tenant-suscripcion.
  No se anaden gestor ni lista de permisos. El sistema no detecta una pareja
  equivocada elegida por ese administrador; consultas y escrituras mantienen
  su aislamiento tenant/suscripcion.
- Limite: no acredita propiedad real Azure ni autorizacion de sesion del CLI;
  no habilita una entrada de usuario final ni nueva identidad administrativa.
  La posible mejora post-MVP no se convierte en un entregable.
- Esta decision resuelve el pendiente CLI del registro parcial anterior,
  conservado abajo. No reabre las otras tres politicas ni autoriza operaciones
  sobre datos/colas existentes, publicacion, migraciones o dependencias nuevas.
- Las cuatro politicas pueden consolidarse en OpenSpec/ADR. El gate pre-code
  global sigue pendiente de presentacion tras validacion documental.

## Registro de aprobacion parcial

- Aprobador: Paris Arcos Martin, mediante mensaje explicito en esta conversacion.
- Registro del orquestador: 2026-09-24, 17:32:42 UTC; hora de registro, no del mensaje.
- Decision: aprobado el resto de la propuesta salvo la gestion tenant-suscripcion.
- Alcance aprobado: proteger todas las operaciones existentes, incluida la
  jerarquia JUP-014; JUP-026/JUP-084 heredan el contrato, sin implementar sus
  funcionalidades futuras en JUP-086.
- Cola aprobada: cotejar trabajo persistido, creador y permisos vigentes antes
  de ejecutar; rechazar mensajes manipulados o antiguos sin creador sin reintentos
  indefinidos. Los trabajos completados no se reescriben, conforme a la propuesta
  previa a la que responde "el resto esta aprobado"; el mensaje de aprobacion
  termina esa frase en "Los trabajos ya completados".
- Salud aprobada: conservar estado de dependencias en processor `/health`,
  retirar conteos globales de trabajos y conservar Prometheus/Grafana.
- Limites ya presentados: no cancelacion instantanea de trabajos en ejecucion;
  un rechazo definitivo puede descartar el mensaje sin borrar el trabajo
  persistido. No autoriza purgas de colas existentes ni reprocesos operativos.
- Esta aprobacion permite documentar estas decisiones en OpenSpec y el ADR;
  no aprueba la lista manual de permisos, una nueva identidad, la frontera CLI
  pendiente ni el gate pre-code global. No atribuye revision o QA a otros roles.

## What Changes

Nota historica: los pendientes del parrafo de preparacion siguiente corresponden
al 24/09/2026, antes del registro pre-code de 19:04:10 UTC. El alcance descrito
se conserva; su implementacion local y pruebas constan en "Estado local tras
Green y mutacion". No son pendientes actuales del ADR ni del gate pre-code.

Alcance, cola y salud aprobados segun el registro anterior; aprobacion CLI
comunicada por el orquestador como operacion administrativa de confianza.
Las cuatro politicas estan aprobadas; implementacion y evidencia funcional
pendientes, con revision consolidada del ADR y gate pre-code global PENDING:

- Cerrar las superficies existentes: membership API, discrepancia cabecera/body,
  conversaciones privadas del usuario, mensajes, jobs, worker, SQL de costes,
  documentos/chunks/embeddings y retrieval. Incluir conflictos, updates,
  reemplazos y llamadas directas a repositorio, no solo filtros de lectura.
- Correlacionar job, tenant y creador del mensaje con el trabajo persistido y
  revalidar membership vigente antes de acceder al estado para replay o
  transiciones, pipeline, LLM o escritura. Ninguna copia del tenant es autoridad
  por coincidir solo con otra copia controlada por el emisor. Rechazar de forma
  definitiva mensajes manipulados, legacy sin creador o creadores sin permiso
  vigente; descartar el mensaje preserva la fila del job, sin requeue indefinido.
  Replay de completed solo con contexto consistente y autorizado, sin ejecutar
  ni reescribir. Errores transitorios siguen siendo reintentables, sin definir
  nueva politica o infraestructura de retries/DLQ. Sin purgas de cola ni
  cancelacion inmediata de trabajos ya en ejecucion.
- Precisar precedencia `401`/`400`/`403`/`422`/`404`, no enumeracion y logs
  sanitizados, con pruebas Red/Green/mutacion e integracion real aislada futuras.
- Aplicar estas garantias a la jerarquia normalizada JUP-014 ya integrada y
  mantener el contrato para futuros calculos JUP-026 y herramientas JUP-084,
  sin reimplementar la jerarquia ni construir esas funcionalidades futuras.
  Su implementacion y evidencia futura no bloquean el cierre de JUP-086.
- Conservar solo salud de dependencias en processor `/health`, retirar la
  consulta y exposicion de conteos globales de jobs y conservar las metricas
  y la monitorizacion Prometheus/Grafana existentes.
- Reservar la ingesta manual de costes a administradores de confianza que
  controlan el CLI y las credenciales de runtime y comprueban la relacion
  tenant-suscripcion al seleccionar la pareja. El sistema no detecta una pareja
  equivocada elegida por ese administrador ni verifica ownership Azure o sesion
  para el CLI. No se habilita entrada de costes de usuario final por UI/API ni
  se crean allowlist, roles, identidad, registro o comprobacion automatica de
  asociaciones. La confianza operativa no permite tocar un run ajeno por ID:
  permanecen exigibles todos los predicados, conflictos, rowcounts y rollback
  del repositorio de costes.

El minimo incluye hardening del escritor de costes que ya existe, aunque los
KPIs reales no existan. `/billing/summary` solo cuenta jobs por tenant y devuelve
importes de demostracion; no se presenta como lectura de costes normalizados.

## Posible mejora post-MVP

Paris decide registrar la gestion de asociaciones tenant-suscripcion, incluidos
frontend, API, persistencia y permisos de administracion, como POSIBLE mejora
post-MVP por considerarla excesiva para el MVP. Queda fuera del alcance y los
entregables de JUP-086, sin crear un nuevo backlog numerado/JUP ni aceptar una
arquitectura. La allowlist manual fue una propuesta del asistente, no aprobada
ni autorizada para implementar. La aprobacion CLI comunicada por el orquestador
resuelve la frontera MVP como operacion administrativa de confianza, sin gestor
ni lista de permisos. La limitacion de seleccion manual no elimina el aislamiento
de consultas/escrituras. La referencia a revision consolidada del ADR y pre-code
PENDING pertenece a la preparacion del 24/09/2026 anterior a 19:04:10 UTC;
el registro de aprobacion pre-code anterior conserva la decision vigente.

## Estado de decisiones y gates

Snapshot historico de preparacion del 24/09/2026, anterior a 19:04:10 UTC.
Se conserva la tabla; sus pendientes de implementacion, ADR y pre-code no
describen el estado local tras Green/mutacion, indicado mas abajo.

| Decision | Politica y estado | Pendiente para entrega |
| --- | --- | --- |
| Alcance y aceptacion de la tarjeta completa | APROBADO: endurecer todas las superficies existentes, incluida la jerarquia JUP-014; JUP-026/JUP-084 heredan solo el contrato futuro. | Implementacion y evidencia de aislamiento de las operaciones existentes pendientes. Los consumidores futuros no bloquean el cierre de JUP-086 ni se cuentan como cobertura implementada. |
| Autoridad asincrona y compatibilidad | APROBADO: job persistido, tenant y creador correlacionados, con membership vigente antes del estado/pipeline; rechazo permanente de mensajes manipulados o sin creador/permiso vigente; completed consistente sin reescritura. | Implementacion y evidencia pendientes. Mensaje descartado con fila conservada, sin purgas ni DLQ/retries nuevos; errores transitorios reintentables y sin cancelacion inmediata a mitad de ejecucion. |
| Ingesta de costes por CLI y suscripciones | APROBADO segun comunicacion del orquestador: operacion administrativa de confianza, reservada al operador que controla CLI/credenciales y comprueba la pareja tenant-suscripcion. Sin entrada de usuario final UI/API, allowlist, nuevos roles/identidades ni registro/comprobacion automatica de asociaciones. | No detecta una pareja erronea del administrador ni acredita ownership Azure o autorizacion de sesion. Hardening y evidencia del aislamiento del repositorio siguen pendientes: ningun ID ajeno permite saltarse scope, conflictos o transacciones. |
| Superficie operativa | APROBADO: processor `/health` conserva salud de dependencias y elimina consulta/exposicion de conteos globales; Prometheus/Grafana se conservan. | Implementacion en `apps/processor/app/api/routes/health.py` y regresion pendientes: mismos estados de dependencias, cero consulta de conteos globales y metricas/monitorizacion sin cambios. |
| ADR y pre-code | [ADR-0008](../../../docs/adr/ADR-0008-tenant-isolation-boundaries.md) consolida las cuatro politicas ya aprobadas y permanece Proposed durante revision. | Validacion/presentacion final, revision del registro consolidado y aprobacion pre-code global PENDING. No reabrir las cuatro politicas; la autorizacion documental no habilita tester/coder ni acredita implementacion. |

No se propone dependencia de produccion ni migracion. Si los contratos no se
pueden cumplir con predicados/transacciones y columnas actuales, detenerse y
presentar por separado el cambio de schema, impacto y compatibilidad.

## Capabilities

### New Capabilities

- `tenant-isolation`: autorizacion y propagacion de contexto tenant verificables
  en todos los limites de datos del MVP.

### Modified Capabilities

- None.

## Impact

- Plan y superficies: [design.md](design.md) y [resource-matrix.md](resource-matrix.md).
  La preparacion del 24/09/2026 anterior a 19:04:10 UTC solo modificaba OpenSpec
  y el entonces Proposed [ADR-0008](../../../docs/adr/ADR-0008-tenant-isolation-boundaries.md).
  El ADR esta Accepted; esta sincronizacion documenta la implementacion local
  posterior y modifica exclusivamente los seis documentos autorizados.
- JUP-085 aporta bearer, claims, leeway nativo de 5 s y CORS/ADR-0007; reutilizarlos
  sin cambios. Mantener `/me` y `/tenants` paralelos y logout ante cualquier error
  de la query `/me`, incluso transitorio, segun JUP-097/JUP-085. Un `403` de datos
  no cambia esa politica ni introduce roles nuevos.
- RF-085-002 (RF085002), reloj Cockroach local, queda **OUT OF SCOPE**. No cambiar
  relojes, infraestructura temporal ni cerrar hallazgos relacionados o ajenos.
- Sin nuevos endpoints de costes, listado/detalle de jobs, documentos o chunks;
  sin herramientas LLM, KPIs, nuevas jerarquias, RBAC nuevo, RLS, firma de colas,
  outbox, aprovisionamiento Azure o administracion multi-organizacion implicitos.

## Dependencias y trabajo concurrente

La historia Git de la base exacta confirma estas integraciones:

- JUP-085/#43: `a89f405602db8c2ca036f53e7deb01ca0521ca4b`; su arbol coincide
  con el de la base anterior `d9fc0ee1926f7ff3fd61d4e21c7fd799d4c12e7f`.
- JUP-069/#39: `4b7d0a4961b0796666a80df0d5b48f62cd96dd28`; incorpora
  `docs/validation/` con 28 preguntas sinteticas, `tools/validation-questions.mjs`
  y los comandos `validation-questions:validate`/`validation-questions:test`
  en package scripts y CI. Validan el corpus, no el aislamiento JUP-086.
- JUP-014/#41: `3a1001db857191f7abb6bb025e2fe8b04a50fe56`; incorpora migration
  004, normalizador y repositorio con `resource_id`, `resource_name` y
  `resource_group_conflicts`. El CLI agrupa por `ResourceId` y `ResourceGroup`,
  sin solicitar `ServiceName`. Es baseline existente, sin registro autoritativo
  tenant-suscripcion ni endpoint jerarquico implicitos; no reimplementar.

RF-014-001 sigue Open: detectar conflictos dentro de una tanda no valida
jerarquias entre ingestas. No se cierra aqui ni se amplian los criterios de
cierre aprobados de JUP-086. KPIs JUP-026 y runtime de tools JUP-084 siguen futuros
y no son bloqueos de cierre de este cambio.

Antecedente historico anterior a estas integraciones, conservado literalmente
por su referencia de aprobacion ajena; no describe el estado actual de la base:

El orquestador informa el 24/09 que `develop` sigue en `3a08d60` y PR #41
(JUP-014) esta open/unmerged, `mergeable=true`, head
`2c01f770464f4b7882d3bd8c54aa5eb40afbe896`, base `3a08d60`. Informa tambien nueva
aprobacion de Paris a las 15:52:06Z; no es aprobacion JUP-086. No se afirma que
existan conflictos. La comparacion local de ese head confirma cambios en
`apps/processor/app/normalization/azure_cost.py`, `repositories/azure_cost.py`,
`run_azure_cost_ingestion.py`, `db/migrations/004_resource_hierarchy.py`,
`db/migration_safety.py` y pruebas. No forman parte del baseline inventariado.
Antes de coder: comprobar integracion y reconciliar firmas/SQL/normalizacion
contra el head vigente, evitando duplicar el escritor o colisionar numeracion
de migraciones. No integrar ni reimplementar PR #41 en esta fase.

## Criterio de entrega

Validar documentos no equivale a cumplir los criterios funcionales de Trello.
La validacion documental historica consta abajo; el estado local posterior
consta en el apartado siguiente. Revision tecnica, QA, aprobacion humana
post-QA y publicacion siguen pendientes. La sesion principal ejecutara los
validadores y el guard tras esta sincronizacion y escribira review/evidencia
despues de reviewer. `docs/evidence/JUP-086-validation.md` aun no esta creado.
No hay commit, push, cambio de tracker, PR, merge ni archivo autorizados aqui.

## Estado local tras Green y mutacion

Sincronizacion documental del 24/09/2026, posterior a la aprobacion de 19:04:10
UTC y a Green/mutacion, antes de reviewer. El diff local contiene 14 archivos
de producto con el alcance implementado resumido en la matriz. La lectura del
informe final del tester confirma backend 412 PASS (259 existentes + 153 nuevos)
y processor 462 PASS (304 existentes + 10 de ingesta reconciliados + 148 nuevos):
874 casos, cero fallos, errores o skips. Mutacion: 60 variantes distintas en
62 intentos, 55 KILLED semanticos y cinco equivalentes concretos
(B09/B10, C03/C04, V05), sin casos sin resolver. El informe conserva 91 hashes
Python de producto y 98 de fuentes/documentos sin cambios durante el tester.

La sesion principal comunica opt-ins DB aislados completos y recorrido real
ASGI HTTP -> RabbitMQ -> worker -> CockroachDB/pgvector -> retrieval con dos
usuarios/dos tenants, replay, rechazo permanente, concurrencia vectorial y
terminacion real de conexion PostgreSQL con rollback/redelivery. SQL mutado usa
SQLite; Green completo incluye CockroachDB real. Modelos/embeddings son mock;
la campana de mutacion es acotada, no exhaustiva. Detalles y comprobaciones
suplementarias comunicadas por la sesion principal en design.md.

La normalizacion JSONB en lecturas de mensajes y conflictos de costes tocadas
habilita el camino positivo con DB real; no cierra JUP-035/RF-087-002. RF-085-002
permanece Open y fuera de alcance, sin afirmar estabilidad del reloj anfitrion.
No se atribuyen ejecuciones automatizadas a los roles humanos de Trello.
Esta sincronizacion no ejecuta tests ni nuevos validadores y no acredita
revision tecnica, QA, aprobacion post-QA ni publicacion.

## Validacion documental consolidada

Registro historico de preparacion, anterior a la aprobacion pre-code. Se
conservan sus resultados y pendientes tal como se observaron; no validan esta
sincronizacion ni sustituyen el estado local tras Green/mutacion.

Observada por el orquestador el 24/09/2026, registro 17:42:53 UTC, sobre base
`3a1001d` mas los cinco documentos del cambio y ADR-0008 locales, sin commit:

- `corepack pnpm openspec:validate`: exit 0, 34/34. Binarios existentes,
  telemetria desactivada y ejecucion autorizada fuera del sandbox; sin instalar.
- `node tools/jup-check.mjs --all`: exit 0, 11 cambios activos incluido JUP-086.
- `node tools/jup-cleanup-check.mjs`: exit 0, 637 archivos.
- `git diff --check`: exit 0.
- Existen los destinos de 15 enlaces Markdown locales en los seis documentos;
  no es comprobacion de enlaces externos ni de todas las anclas.
- Controles de limites de edicion correctos: spec-planner solo cinco documentos
  OpenSpec y ADR-0008; registro humano del orquestador solo proposal.md/ADR-0008.
  El registro parcial anterior permanece intacto y la aprobacion CLI es separada.

La revision documental confirma que el conjunto refleja las cuatro decisiones
explicitas, sin crear gestor/allowlist, identidad, migracion o dependencia.
No es revision tecnica de producto, QA ni evidencia de seguridad funcional.
En ese registro de las 17:42:53 UTC, el ADR permanecia Proposed y el pre-code
global PENDING para su presentacion; la aprobacion de 19:04:10 UTC figura arriba.
Las anotaciones previas a este registro describen el momento de preparacion;
este apartado conserva la referencia de aquella validacion consolidada.
