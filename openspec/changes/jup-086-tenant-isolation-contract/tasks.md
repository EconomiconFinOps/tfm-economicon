JUP: JUP-086

## Aceptacion vigente

Solo la [tabla acotada](resource-matrix.md#aceptacion-acotada-vigente) define
verificacion pendiente; checks/estados anteriores conservan historia, no
ordenan reimplementar producto ni repetir combinaciones. Todos los tests y
codigo retenidos siguen protegidos; no hay nuevo objetivo numerico.

- [x] JUP-086 validar/revisar documentos y obtener ratificacion humana del detalle; APPROVED26/09 antes de los tres casos nuevos, no post-QA.
- [x] JUP-086 acreditar reinicio real del broker con el mismo backend, HTTP202 confirmado, estados scoped y ausencia de replay.
- [x] JUP-086 acreditar Blocked/Unblocked, expiracion y cierre con Pika real;11 casos afectados PASS, producto intacto, coder NOOP y sensibilidad detectada.
- [x] JUP-086 reviewer audita reutilizacion TLS/helpers/hashes,681 IDs conservados y684 actuales; REVIEW_PASS sin hallazgos bloqueantes.
- [x] JUP-086 QA final PASS: evidencia/gates auditados, DoD code/stage qa exit0; sin dispensa, nuevas matrices o aprobacion humana inferida.
- [x] JUP-086 aprobacion humana post-QA y publicacion autorizadas por Paris mediante "apruebo", registro26/09/2026 20:01:21 UTC.
- [ ] JUP-086 publicar rama y abrir PR contra develop, verificar CI; revision humana, merge y tracker conservan sus gates separados.

Los estados pendientes inferiores son registros historicos de cada fase;
no sustituyen este checklist vigente ni conceden aprobacion humana.

## Validacion con servicios reales, 26/09/2026

- [x] JUP-086 comprobar Docker tras reinicio manual; usar tres servicios aislados, sin modificar contenedores previos, datos del proyecto o reloj.
- [x] JUP-086 ejecutar los681 casos existentes: primera pasada676 PASS/5 FAIL; conservar los fallos y el V01 superviviente.
- [x] JUP-086 corregir solo tres archivos de tests existentes (heartbeat, start HTTP y rechazo PermissionError);108 nuevos/681 total sin incremento ni cambios de producto.
- [x] JUP-086 validar Linux325 backend+356 processor PASS, sin fallos/errores/skips; los58 casos antes omitidos pasan.
- [x] JUP-086 completar las38 detecciones planificadas, incluidas las cinco antes bloqueadas; conservar el primer V01 superviviente y la prueba separada de entorno.
- [x] JUP-086 coder NOOP, auditoria post-Green y REVIEW_PASS acotado;143 fuentes protegidas incluidas93 de producto intactas.
- [ ] JUP-086 completar los pendientes vigentes de la tabla acotada; el listado amplio de aceptacion anterior queda sustituido, sin atribuir nueva cobertura.
- [ ] JUP-086 obtener QA global y aprobacion humana final; no publicar o cerrar por el resultado de la suite existente.

## Validacion Linux y entorno, 26/09/2026

- [x] JUP-086 preparar entorno Linux temporal con dependencias declaradas y versiones del entorno Windows; no paquetes globales ni cambios de producto.
- [x] JUP-086 ejecutar35 focales Linux:34 PASS/1 FAIL por LC_CTYPE generado por CPython; corregir solo la expectativa de test y su marcador, conservando entorno exacto de Popen y no-secret.
- [x] JUP-086 comprobar Linux35 focales PASS y suites623 PASS/58 SKIP; Windows35 focales PASS y backend316 PASS/9 SKIP. Inventario108 nuevos/681 total, sin casos nuevos ni producto cambiado.
- [x] JUP-086 comprobar mutante de herencia de entorno detectado y re-review acotado PASS; prueba separada del balance previo33 detectados/5 no ejecutados.
- [x] JUP-086 intentar arranque Docker autorizado e identificar error del socket temporal de telemetria; no se provisionaron servicios.
- [x] JUP-086 bloqueo Docker resuelto por reinicio manual del usuario; recuperacion del socket innecesaria y no aplicada.
- [x] JUP-086 completar58 casos dependientes de servicios y cinco variantes antes no ejecutadas, segun lote real anterior; mantener separados TLS versionado, recursos Linux repetidos y escenarios aun sin prueba escrita.
- [ ] JUP-086 QA final y aprobacion humana tras aceptacion completa; sin excepcion, publicacion o casos nuevos implicitos.

## Historial de consolidacion anterior a los servicios reales

**Seleccion108 aprobada y aplicada; REVIEW_PASS acotado, R1 resuelto.**
Regresion final:623 PASS/58 SKIP, ningun FAIL/ERROR. Seleccion108 nuevos:
60 aislamiento+48 RF-086-003; +4 netos heredados, base569,total681.
Primera pasada processor:306 PASS/1 FAIL WinError10053/49 SKIP; un diagnostico
y una repeticion completa pasaron sin cambios. Causa no establecida.
La propuesta238 no se implemento y queda sustituida. Preservar historia/Red;
883 PASS/267 SKIP y29 mutantes no acreditan la suite propuesta.

- [x] JUP-086 validar documentos y presentar tabla exacta, reutilizacion y riesgos; aprobacion explicita de Paris registrada el26/09 13:34:53 UTC antes de editar tests.
- [x] JUP-086 tester protege baseline569, adaptacion6->10, helpers y fixtures/defaults; aplica SOLO los selectores de los13 modulos en resource-matrix.md con parametrizacion indirecta por test.
- [x] JUP-086 tester confirma inventario completo325 backend+356 processor=681 tras recuperar un caso autorizado; los680 node IDs previos se conservan, sin deseleccion, ocultacion de SKIP ni agregacion artificial.
- [ ] JUP-086 tester ejecuta regresion y mutaciones sensibles de design.md, incluyendo las validaciones especificas de reutilizacion; restituye casos ante huecos concretos, sin waiver y con recuento actualizado.
- [x] JUP-086 coder NOOP Green sin cambios de producto; re-review confirma R1 resuelto con el unico caso recuperado, REVIEW_PASS acotado y145 archivos protegidos intactos.
- [x] JUP-086 Paris aprueba restituir solo test_adversarial_cancel_before_spawn_and_cleanup_before_other_lane[publisher], registro26/09 14:24:18 UTC. Aplicado:108 nuevos/681 total, baseline14 PASS y mutante13 PASS/1 FAIL semantico; regresion y revision afectadas comprobadas. Sin waiver ni otras restituciones.
- [x] JUP-086 QA audita la restitucion local: completa, R1 cerrado; QA_FAIL global por aceptacion pendiente. Confirma integridad/inventario y evidencia, sin nuevas pruebas; count operativo680 corregido a681 en design.md.
- [ ] JUP-086 completar aceptacion Linux/TLS/Rabbit/Cockroach/pgvector y cinco mutantes no ejecutados. Contar aparte futuros casos cuando se escriban, sin reserva ficticia ni cierre por numero de tests.
- [ ] JUP-086 actualizar evidencia/revision y presentar aprobacion final tras verificacion, sin tracker/PR/publicacion implicitos.

Evidencia/revision actualizadas:38 variantes,33 detecciones (32 previas
revisadas y m33 nuevo), cero supervivientes conocidos y5 no ejecutadas por
entorno. No mutation PASS global ni aprobacion final. QA audita el resultado
local y mantiene abiertos los pendientes reales; no se provisionan servicios.


## Estado actual del incremento RF-086-003

25/09/2026: DNS y retencion del publicador implementados, REVIEW_PASS tecnico
local. Backend 517/processor 366 PASS; 267 SKIP no aceptados. Mutacion actual
29/29 detecciones, TLS local y diez ciclos Windows comprobados. Linux y
servicios reales siguen pendientes; no QA/aprobacion post-QA/publicacion.
[Evidencia actual](../../../docs/evidence/JUP-086-validation.md#validacion-dns-local).
4.10/4.11/4.13 acreditan solo el trabajo local descrito; 4.12/4.14 siguen
abiertas por su aceptacion completa. Las notas anteriores siguientes son
historia y no invalidan ni amplian la aprobacion pre-code original.

Gate DNS **APPROVED** por Paris, registro 25/09/2026 14:51:40 UTC en proposal.md.
ADR-0009 addendum Accepted; comienza Red, sin atribuir aun Green/mutacion/QA.
Los PENDING de preparacion inferiores son historia. Alcance DNS por proceso,
sin cuotas/equidad por tenant nuevas ni escalabilidad medida implicita.

Addendum DNS detallado Proposed, preparacion permitida segun contexto del
orquestador de 25/09/2026 14:03:35 UTC. Su gate pre-code sigue PENDING despues
de validacion/presentacion; no hereda el gate original de 08:31:11. Tareas
DNS al final de seccion 4, sin ejecucion ni evidencia nueva en esta fase.
La nota fechada siguiente conserva el bloqueo de producto: dos Red DNS y
REVIEW_FAIL/BLOCKED_ENV siguen activos; solo el bloqueo de redactar la
excepcion interna esta resuelto. No marcar completas las tareas de producto.

25/09/2026, registro 10:49:57 UTC: implementacion local y primera mutacion
acotada realizadas, pero **REVIEW_FAIL / BLOCKED_DESIGN** por resolvers DNS
no daemon que sobreviven al cierre. Dos regresiones nuevas en Red; sin
disposicion aprobada. Los 807 PASS/267 SKIP y 34 mutantes anteriores no
acreditan Green actual. Docker y escenarios reales pendientes por separado.
Ver review/evidencia; no marcar 4.4-4.8 completas ni iniciar otra arquitectura
de resolucion sin decision humana. No se ha publicado ni actualizado Trello.

Pre-code APPROVED por Paris, registro 25/09/2026 08:31:11 UTC en proposal.md;
ADR-0009 Accepted, Red autorizado. Las notas de preparacion siguientes no
reabren ese gate ni acreditan ejecucion de las tareas pendientes 4.3-4.8.

25/09/2026: option2 incorporada segun proposal.md; detalle pre-code PENDING
tras validacion. No iniciar tester/coder. Se conservan literalmente los checks
originales; 896 PASS/65 mutantes y review/QA previos no cubren este incremento.
ADR-0008 Accepted; ADR-0009 Proposed. Las tareas nuevas estan en seccion 4.
Las siguientes notas de aplazamiento/review son historia del alcance original.

## Estado de esta reconciliacion

Estado vigente tras re-review: REVIEW_PASS tecnico, RF-086-001/002 corregidos,
896 PASS sin skips; 65 mutantes distintos, 60 detectados y cinco equivalentes.
Paris aprueba aplazar RF-086-003 fuera de alcance el 24/09, registro 21:23:36 UTC;
sigue Open, sin corregir. QA PASS_WITH_APPROVED_EXCEPTIONS tras revalidar
disposicion/integridad; aprobacion humana final pendiente. [Review](review.md) y
[evidencia](../../../docs/evidence/JUP-086-validation.md) prevalecen sobre los
resumenes historicos siguientes de la primera pasada Green (874 casos).

Pre-code approval: **APPROVED**, Paris, 24/09/2026 a 19:04:10 UTC, ver registro
en proposal.md. Se autoriza comenzar pruebas/implementacion, sin acreditarlas.
Los pendientes historicos del gate quedan resueltos. Los checks 1.1 y 1.2 se
conservan literalmente como historia del contrato preparado en JUP-088;
no significan inventario ejecutable previo, pruebas ni implementacion actual.
La reconciliacion tecnica historica del 24/09/2026 compara `d9fc0ee` con la base integrada
`3a1001db857191f7abb6bb025e2fe8b04a50fe56`, descrita en la matriz.
La revalidacion documental sobre esta nueva base fue observada por la sesion
principal el 24/09/2026 (1.7); los resultados 33/33 de 1.5 pertenecen
exclusivamente a `d9fc0ee`. Green/mutacion locales constan abajo; revision/QA y
aceptacion humana post-QA siguen pendientes.
Alcance existente, cola y salud tienen aprobacion parcial en proposal.md;
la aprobacion CLI comunicada por el orquestador fija una operacion administrativa
de confianza. Las cuatro politicas estan aprobadas. El registro vigente de
validacion documental y gate es proposal.md, seccion "Validacion documental
consolidada" y "Registro de aprobacion pre-code". ADR-0008 Accepted;
tester/coder autorizados para el alcance aprobado, sin reabrir esas politicas.
Los roles siguen en Trello: Paris lead, Victor pair, Alejandro review y Lucia
QA/docs; los nombres no acreditan ejecucion de estas tareas.

Sincronizacion documental del 24/09/2026 tras Green/mutacion y antes de reviewer:
informe final del tester leido, backend 412 PASS y processor 462 PASS, total 874
sin fallos/errores/skips; 60 mutantes distintos en 62 intentos, 55 KILLED y cinco
equivalentes (B09/B10, C03/C04, V05), sin pendientes. La sesion principal confirma
integracion real aislada con dos usuarios/dos tenants y guards tester/coder PASS;
resultados, limites y comprobaciones suplementarias en design.md. Los checks
nuevos de este lote se apoyan en esa evidencia local, sin ejecutar pruebas aqui.

## 1. Inventario y contrato

1.5, 1.7 y 1.8 conservan literalmente el estado documental de preparacion del
24/09/2026 anterior a 19:04:10 UTC. Sus PENDING/Proposed son historicos y quedan
resueltos por 1.6; no reabren la aprobacion ni describen el estado actual.

- [x] 1.1 JUP-086 inventariar sesion, cabecera, payloads, jobs y stores tenant-aware.
- [x] 1.2 JUP-086 definir fuente de autoridad, propagacion, matriz de errores y no enumeracion.
- [x] 1.3 JUP-086 preparar resource-matrix.md contra d9fc0ee y reconciliar los cambios integrados en 3a1001d, separando salvaguardas, gaps, pruebas existentes y superficies futuras; roles segun la tarjeta fechada, sin afirmar publicacion externa ni QA.
- [x] 1.4 JUP-086 reconciliar proposal/design/delta con la tarjeta completa del export 24/09, precedencia 422, limites SQL/cola/vector/LLM y la base integrada JUP-085/#43, JUP-069/#39 y JUP-014/#41; solo inspeccion estatica.
- [x] 1.5 JUP-086 validacion documental historica sobre d9fc0ee, comunicada por el orquestador el 24/09/2026: guard spec-1 PASS (exactamente 5 paths); `corepack pnpm openspec:validate` exit 0 (33/33), usando binarios existentes y telemetria desactivada en ejecucion autorizada fuera del sandbox; `node tools/jup-check.mjs --change jup-086-tenant-isolation-contract` exit 0; `node tools/jup-cleanup-check.mjs` exit 0 (616 archivos); `git diff --check` exit 0. Los intentos iniciales de OpenSpec terminaron antes de validar por EPERM del sandbox: fallos de tooling, no de especificacion. Estos checks no acreditan validacion funcional ni resuelven decisiones humanas, ADR o pre-code approval, que siguen PENDING.
- [x] 1.6 JUP-086 propuesta validada/presentada y ADR-0008 Accepted; aprobacion pre-code registrada por el orquestador tras respuesta explicita de Paris, sin reabrir las cuatro politicas aprobadas.
- [x] 1.7 JUP-086 revalidacion documental observada independientemente por la sesion principal el 24/09/2026 sobre 3a1001d, antes de esta nota: guard spec-develop-3a1001d PASS (exactamente 5 documentos, cero violaciones); `corepack pnpm openspec:validate` exit 0 (34/34), con binarios existentes de `node_modules/.bin` de la raiz en PATH, telemetria desactivada y escalacion autorizada; `node tools/jup-check.mjs --change jup-086-tenant-isolation-contract` exit 0; `node tools/jup-check.mjs --all` exit 0 (11 cambios activos); `node tools/jup-cleanup-check.mjs` exit 0 (636 archivos); `git diff --check` exit 0; existen los destinos de 5 enlaces Markdown locales en los 5 documentos (anclas y enlaces externos no comprobados); `node tools/validation-questions.mjs validate` exit 0 (28 consultas, 7 categorias). Sin pruebas de producto ejecutadas; no acredita aceptacion funcional ni resuelve decisiones de seguridad, ADR o pre-code, que siguen PENDING.

- [x] 1.8 JUP-086 reconciliar documentalmente las politicas aprobadas de alcance existente (incluido JUP-014; JUP-026/JUP-084 solo contrato futuro), cola/revocacion previa a ejecucion, salud de dependencias y CLI como operacion administrativa de confianza; crear ADR-0008 Proposed y preservar el registro historico de aprobacion. No acredita implementacion, validacion nueva ni gate pre-code.

## 2. Implementacion local comprobada tras Green y mutacion

- [x] 2.1 JUP-086 aplicar tenant autorizado a costes, jobs, conversaciones y mensajes.
- [x] 2.2 JUP-086 propagar contexto inmutable por RabbitMQ, processor y persistencia.
- [x] 2.3 JUP-086 asegurar documentos, chunks, embeddings, retrieval y herramientas del agente.

2.1 incluye `fetch_messages`, `append_message`, update del padre, estados de job
y start/complete/fail/fetch de costes con contexto en predicados y conflictos.
No incluye construir KPIs JUP-026. 2.2 exige cotejar persistencia/creador antes
de acceder al estado/pipeline y revalidar membership vigente. Mensajes manipulados,
legacy sin creador o sin permiso vigente se descartan definitivamente sin cambiar
la fila persistida; completed consistente no se reejecuta ni reescribe. Fallos
transitorios siguen reintentables, sin nueva politica/infraestructura de retries,
DLQ, purgas ni cancelacion inmediata de trabajos en curso. SQL/vector no son
atomicos entre stores. 2.3 incluye reemplazo vectorial transaccional y retrieval
actual; herramientas inexistentes quedan como contrato futuro JUP-084, nunca
se marcaran implementadas por la mera presencia de un spec.

El check 2.3 corresponde exclusivamente a documentos/chunks/embeddings y
retrieval existentes; no acredita implementacion de herramientas JUP-084.

- [x] 2.4 JUP-086 reconciliar documentalmente la base integrada 3a1001d con JUP-085, JUP-069 y JUP-014, escritor de costes y migracion 004 existentes; sin reimplementacion, ejecucion de migraciones ni aprobacion de seguridad o producto. Revalidacion documental observada en 1.7; el bloqueo de coder por 1.6 era historico, anterior a la aprobacion de 19:04:10 UTC del 24/09/2026.
- [x] 2.5 JUP-086 tras 1.6, aplicar las politicas aprobadas de cola y salud: `apps/processor/app/api/routes/health.py` conserva estados de dependencias, elimina consulta/exposicion de conteos globales y preserva metricas/Prometheus/Grafana; mantener CLI como operacion administrativa de confianza y endurecer todos los predicados/conflictos/transacciones de costes. Detenerse ante necesidad de dependencia, schema, RLS o nueva identidad no aprobados.

El operador administrativo controla CLI/credenciales y comprueba la pareja
tenant-suscripcion; el sistema no detecta su seleccion erronea ni verifica
ownership Azure o sesion CLI. No hay entrada de costes UI/API de usuario final,
allowlist, roles/identidades nuevos, registro o comprobacion automatica de
asociaciones. Esa confianza no permite alterar un run ajeno por ID; el gestor
frontend/API/persistencia sigue posible mejora post-MVP.

## 3. Verificacion

- [x] 3.1 JUP-086 añadir pruebas cruzadas de lectura, escritura, IDs opacos y jobs manipulados.
- [x] 3.2 JUP-086 verificar que logs y errores no contienen datos de otro tenant.
- [ ] 3.3 JUP-086 ejecutar tests, build, lint, OpenSpec, trazabilidad y publicar evidencia.

- [x] 3.4 JUP-086 tras aprobacion, tester obtiene Red de escenarios del delta con auth real en API y pruebas directas de repositorio; no aceptar fallos por entorno como Red. Registro durable en docs/evidence/JUP-086-validation.md: 60 fallos semanticos; 18 skips por firmas ausentes excluidos de Red/PASS.
- [x] 3.5 JUP-086 coder obtiene Green del alcance aprobado; tester comprueba mutaciones de membership, creador, filtros, upsert/delete, precedencia y sustitucion de tenant sin introducir dependencias no aprobadas.
- [x] 3.6 JUP-086 validar con dos tenants y usuarios distintos CockroachDB, pgvector y RabbitMQ reales y desechables; verificar filas ajenas intactas, rollback, replay, errores y logs; un skip no es PASS.
- [x] 3.7 JUP-086 reviewer/QA verifican delta, matriz, resultados y gaps de las operaciones existentes, incluida la jerarquia persistida JUP-014. JUP-026/JUP-084 heredan el contrato y verificaran su evidencia en sus propios cambios; no bloquean el cierre JUP-086.

3.7 completado tecnicamente: reviewer PASS y QA PASS_WITH_APPROVED_EXCEPTIONS;
RF-086-003 sigue Open con aplazamiento aprobado. 3.3 conserva pendiente solo
la publicacion de evidencia: validadores y evidencia local ya comprobados,
sin autorizacion de publicacion. No se repiten suites sin cambios de codigo.
El Red inicial de 3.4 se acredita por
el handoff tester y una repeticion independiente backend, no por inferencia
del Green. Review y evidencia conservan ambos dictamenes y los resultados actuales.
Aprobacion humana post-QA y publicacion pendientes; alcance aprobado intacto.

Comandos, casos de mutacion y aislamiento de infraestructura se detallan en
design.md. Ninguna prueba de producto se crea ni se ejecuta durante esta
sincronizacion; no se ejecutan validadores ni se atribuyen nuevos resultados
a 1.5/1.7.

## 4. Incremento RF-086-003 option2, pendiente

- [x] 4.1 JUP-086 guard spec-planner PASS, OpenSpec 34/34, trazabilidad 11, higiene 651 y diff exit 0; sincronizacion registrada en proposal/evidencia el 25/09 a 08:28:23 UTC.
- [x] 4.2 JUP-086 nuevo gate pre-code APPROVED por Paris, registro 25/09 a 08:31:11 UTC: ADR-0009 Accepted, owner SelectConnection/abort publico, limites, SQL CAS/estados, 503 y riesgo SQL-broker aprobados; habilita tester/coder.
- [x] 4.3 JUP-086 tester tras 4.2 obtiene Red semantico de escenarios RF-086-003 del delta; comprueba APIs publicas en runtime existente y adapta doubles sin contar fallos de setup/import/firmas como Red.
- [ ] 4.4 JUP-086 coder implementa solo los paths de producto incrementales de la matriz: owner/lifespan, admision/confirms/abort/reconexion, ruta y estados SQL scoped; obtiene Green sin dependencias, migraciones ni cambios de worker/frontend.
- [ ] 4.5 JUP-086 verificar el incremento retenido mediante la tabla acotada vigente: reutilizar evidencia aplicable y completar reinicio real y Blocked/Unblocked; no exigir todas las combinaciones historicas.
- [ ] 4.6 JUP-086 tester ejecuta mutacion acotada del nuevo contrato y regresion backend/processor, conserva pruebas originales, aporta resultados separados; supervivientes semanticos vuelven a correccion, excepciones requieren decision humana.
- [ ] 4.7 JUP-086 re-review tecnico del diff ampliado, guard y evidencia incremental del orquestador; QA nueva con dependencias reales aisladas y limitaciones explicitas, sin heredar PASS ni excepcion RF-086-003 anterior.
- [ ] 4.8 JUP-086 presentar gate humano post-QA sobre resultado ampliado; publicar/PR/commit/merge/archivo requieren la autorizacion aplicable y no se ejecutan en esta fase.

Avance parcial: 4.4 implementado localmente, Green anterior de 441 backend y
366 processor, pero pendiente correccion DNS. 4.5 conserva 267 skips reales
y casos por escribir; peer sintetico no sustituye RabbitMQ. 4.6: 34 mutantes
distintos detectados en 35 intentos (uno inicialmente invalido, excluido y
repetido correctamente), sin excepciones; repetir lo afectado por remediacion.
4.7: reviewer identifica el bloqueo, evidencia reconciliada; QA no iniciada
para este incremento porque la revision no esta aprobada.

### Addendum DNS propuesto, posterior al gate separado

- [x] 4.9 JUP-086 seis documentos/guard validados, OpenSpec 34/34 y trazabilidad 11; Paris aprueba el gate DNS detallado tras aclaracion multitenant, registro 25/09 14:51:40 UTC en proposal.md. Excepcion Pika y limite OS incluidos; no acredita implementacion ni QA.
- [x] 4.10 JUP-086 tester tras ese gate adapta las dos regresiones DNS al hijo realmente bloqueado usando los paths de la matriz; conserva las aserciones de cero helpers, no overlap de generaciones y plazos, sin contar monkeypatch parental como DNS del hijo.
- [x] 4.11 JUP-086 coder tras Red integra getaddrinfo/AbstractIOReference en rabbitmq_queue.py y los dos modulos DNS propuestos: supervisor unico, ejecutable/PID, admision publisher/probes, IPC acotado, deadlines y cancel/kill/reap con contabilidad retenida. Solo los paths DNS de la matriz, no SQL/API/worker/main ni configuracion.
- [ ] 4.12 JUP-086 auditar evidencia DNS/TLS/recursos segun la tabla vigente; cleanup real Linux ya tiene prueba, TLS TEMP requiere trazabilidad verificable. Matriz OS/IPC completa y plateau Linux repetido son validacion opcional no acreditada. Health Docker 5 s permanece sin cambios.
- [x] 4.13 JUP-086 mutacion DNS acotada: omitir cancel/token/generacion, reap/retencion de plaza, cap/equidad, deadline compartido, validacion IPC/PID, env minimo o hostname TLS. Green baseline y deteccion semantica separadas; no atribuir cobertura DNS a los 34 mutantes anteriores.
- [ ] 4.14 JUP-086 completar 4.5/4.12 conforme a la tabla vigente, re-review/QA/guard y evidencia por parent; reutilizacion no equivale a QA PASS. Sin exencion de gates de codigo, post-QA ni autorizacion implicita de PR/tracker/publicacion.
