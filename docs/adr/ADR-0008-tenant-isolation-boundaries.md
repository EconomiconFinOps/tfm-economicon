# ADR-0008: Tenant isolation boundaries

- Status: Accepted
- Date: 2026-09-24
- Related JUP/OpenSpec: JUP-086, [jup-086-tenant-isolation-contract](../../openspec/changes/jup-086-tenant-isolation-contract/proposal.md), [design](../../openspec/changes/jup-086-tenant-isolation-contract/design.md)
- Trello: https://trello.com/c/bKxQK9HI
- Supersedes: none
- Superseded by: none

Estado actual, 25/09/2026: este ADR permanece **Accepted** para las cuatro
decisiones originales, sin reabrir su aprobacion. RF-086-003 option2 se incorpora
segun el [estado actual de JUP-086](../../openspec/changes/jup-086-tenant-isolation-contract/proposal.md);
su ciclo de publisher y tratamiento de `503 + queued` se proponen aparte en
[ADR-0009](ADR-0009-rabbitmq-publisher-lifecycle.md), **Proposed**, con nuevo gate
pre-code PENDING. El aplazamiento, resultados y consecuencias de publicacion
conservados a continuacion son historia original, no evidencia del incremento.

Estado vigente de implementacion tras re-review, 24/09/2026: REVIEW_PASS
tecnico, 896 PASS sin skips; RF-086-001/002 corregidos localmente.
Paris aprueba aplazar RF-086-003 fuera de alcance el 24/09, registro 21:23:36 UTC;
sigue Open sin corregir. Estado QA en [Review](../../openspec/changes/jup-086-tenant-isolation-contract/review.md)
y [evidencia](../evidence/JUP-086-validation.md) ya existen y prevalecen sobre
las notas historicas siguientes de la primera pasada Green, 874 casos y
revision pendiente. La decision Accepted y sus limites no cambian.

## Context

Contexto historico de preparacion del 24/09/2026 anterior a la aprobacion de
19:04:10 UTC. Describe la base sin el diff JUP-086; el estado local posterior
a Green/mutacion figura en "Estado local de implementacion" al final.

La base `3a1001db857191f7abb6bb025e2fe8b04a50fe56` incorpora JUP-085,
JUP-069 y la jerarquia normalizada JUP-014. Membership y algunos filtros tenant
ya existen, pero no acreditan aislamiento de escrituras, conflictos, cola ni
reemplazos vectoriales. El envelope no acredita por si solo autoridad sobre el
job persistido. Processor `/health` consulta conteos globales de jobs. El CLI de
costes recibe tenant y suscripcion del operador sin sesion ni registro que
verifique su relacion.

Estas fronteras afectan a tenancy, persistencia y ejecucion asincrona y requieren
un registro duradero. Este ADR consolida las politicas ya aprobadas sin modificar
el producto ni afirmar que las garantias propuestas esten implementadas.

## Decision

Aceptado por Paris Arcos Martin tras las aclaraciones de alcance; respuesta
"ok adelante", registrada el 24/09/2026 a 19:04:10 UTC en
[aprobacion pre-code](../../openspec/changes/jup-086-tenant-isolation-contract/proposal.md#registro-de-aprobacion-pre-code).
Se autoriza iniciar pruebas e implementacion, no publicacion ni merge.
Los parrafos de preparacion siguientes conservan su contexto historico:
Proposed/PENDING del gate previo quedan resueltos por esta aceptacion, sin
acreditar implementacion ni QA. Las cuatro decisiones no cambian.

El subconjunto de alcance, cola y salud ya esta aprobado segun el
[registro autoritativo del orquestador](../../openspec/changes/jup-086-tenant-isolation-contract/proposal.md#registro-de-aprobacion-parcial),
que permanece historicamente intacto. La
[aprobacion CLI](../../openspec/changes/jup-086-tenant-isolation-contract/proposal.md#registro-de-aprobacion-cli)
registrada por el orquestador establece la operacion administrativa de confianza.
Las cuatro politicas estan aprobadas y no se reabren aqui. Este texto las
reconcilia; no crea ni sustituye un registro de aprobacion humana.

Nota historica: el parrafo siguiente conserva el estado de preparacion del
24/09/2026 anterior a 19:04:10 UTC; la aceptacion registrada arriba resolvio
esos pendientes sin cambiar las cuatro decisiones.

El registro consolidado permanece **Proposed** durante revision. La validacion
y presentacion final, revision del ADR y aprobacion pre-code global siguen
**PENDING**; no hay autorizacion para tester/coder ni evidencia de implementacion.

1. Alcance existente: proteger todas las operaciones inventariadas, incluida
   la jerarquia JUP-014, sin reimplementarla. JUP-026/JUP-084 heredan contratos;
   sus funcionalidades y evidencia futuras no bloquean el cierre JUP-086.
   Conservar privacidad de conversaciones por usuario dentro del tenant,
   membership y precedencia/no enumeracion de errores del delta.
2. Cola: cotejar job, tenant y creador contra persistencia y revalidar existencia
   del creador y membership vigente antes de acceder al estado para replay o
   transiciones, pipeline, LLM o stores. Usar contenido persistido; controles
   duplicados y copias usadas deben coincidir semanticamente. Manipulacion,
   legacy sin creador, creador eliminado o membership revocada antes de ejecutar
   implican rechazo permanente: descartar ese mensaje sin requeue y conservar
   la fila del job, sin borrarla ni marcarla failed. Solo un replay completed
   consistente y autorizado termina sin pipeline ni reescritura de estado,
   resultados o datos. Un contexto invalido no obtiene un bypass por completed.
   Fallos transitorios siguen reintentables con revalidacion en la siguiente
   entrega; no se define nuevo limite, backoff o infraestructura de retries.
   Sin purgas de colas existentes, DLQ implicita, firma ni outbox. La validacion
   previa no garantiza revocacion instantanea ni cancelacion inmediata de un
   trabajo ya iniciado. `request_id` solo sirve para correlacion saneada.
3. Salud: en `apps/processor/app/api/routes/health.py`, retirar `jobs` y su
   consulta global, conservando `status`/`services` de database, RabbitMQ y
   vector store con la semantica existente. `/metrics`, Prometheus/Grafana y
   configuracion de monitorizacion se conservan, sin una nueva frontera de
   autenticacion para probes ni sustitucion de ADR-0005.
4. CLI: reservar la ingesta manual de costes a administradores de confianza que
   controlan CLI/runtime y sus credenciales, responsables de comprobar y elegir
   la pareja tenant-suscripcion. El sistema no detecta una pareja equivocada del
   administrador ni acredita ownership Azure verificado o autorizacion de sesion
   CLI. No habilitar entrada de costes de usuario final por UI/API, allowlist,
   nuevos roles/identidades de auth, registro de suscripciones ni comprobacion
   automatica de la relacion. La confianza del operador no permite acceder o
   alterar un run ajeno por ID: lecturas, escrituras, borrados, conflictos y
   reintentos requieren predicados tenant+suscripcion, comprobacion del padre,
   rowcounts y rollback transaccional. El gestor de asociaciones con frontend,
   API y persistencia sigue siendo solo una posible mejora post-MVP.

## Consequences

La politica aprobada reduce la autoridad atribuida a IDs opacos, envelopes y
argumentos del modelo; la implementacion y pruebas locales del 24/09/2026
constan al final, con revision tecnica y QA pendientes. Los
documentos/chunks/embeddings deben mantener ownership en reemplazos y conflictos,
y retrieval debe filtrar por tenant antes de ranking o exposicion de candidatos.

SQL y vector no forman una transaccion atomica entre stores. INSERT del job y
publish tampoco son atomicos: el fallo de publish conserva la fila queued y el
503 existentes. No se introduce outbox. Descartar un mensaje permanentemente
invalido conserva su fila; no promete ejecutar ese trabajo, reparar legacy ni
autoriza purgas o reprocesos operativos. Tampoco se promete cancelar una ejecucion
ya iniciada cuando cambia membership.

El error de seleccion tenant-suscripcion del administrador queda fuera de la
deteccion automatica del MVP. Esa limitacion de confianza no exime del aislamiento
del repositorio dentro del scope seleccionado ni acredita ownership de Azure.

Se conservan JUP-085 (bearer, claims, leeway nativo de 5 s, CORS/ADR-0007) y
JUP-097 (`/me` y `/tenants` paralelos, logout ante cualquier error de query `/me`).
RF-085-002 (RF085002), reloj Cockroach local, queda OUT OF SCOPE. RF-014-001 sigue
Open; no se resuelve la validacion de jerarquia entre ingestas. No se autorizan
dependencias, migraciones, RLS, nuevas identidades o infraestructura adicional.
`docs/architecture.md` no cambia. La referencia de preparacion a registro
Proposed/producto intacto correspondia al 24/09/2026 antes de 19:04:10 UTC;
el estado actual del ADR sigue Accepted.

## Alternatives Considered

- Autoridad basada solo en envelope o en coincidencia de sus copias: no satisface
  el cotejo aprobado contra persistencia, creador y membership vigente.
- Autorizacion durable solo al encolar: no elegida; la politica aprobada revalida
  antes de ejecutar, con la limitacion explicita sobre trabajos ya iniciados.
- Reencolar indefinidamente mensajes invalidos o purgar colas para compatibilidad:
  fuera de la politica aprobada; se descarta el mensaje y se conserva el job.
- Mantener conteos globales en health o protegerlos mediante una frontera nueva:
  no elegido; se retiran consulta y exposicion y se conserva monitorizacion.
- Bloquear JUP-086 hasta entregar KPIs/tools futuros: no elegido; sus cambios
  heredan el contrato sin convertirse en entregables ni bloqueos de este cambio.
- Gestor tenant-suscripcion: posible mejora post-MVP, no entregable actual.
  La allowlist manual no esta aprobada; no se introduce como solucion CLI.

## Evidence And Follow-up

Plan historico de evidencia del 24/09/2026, anterior a 19:04:10 UTC. Las
referencias siguientes a gaps, regresion futura, presentacion del ADR y gate
describen aquella preparacion; el estado local posterior se detalla al final.

La [matriz](../../openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md)
separa salvaguardas presentes de gaps y evidencia pendiente. El
[delta](../../openspec/changes/jup-086-tenant-isolation-contract/specs/tenant-isolation/spec.md)
y las [tareas](../../openspec/changes/jup-086-tenant-isolation-contract/tasks.md)
conservan aceptacion negativa HTTP/repositorios/worker/retrieval/logs, dos tenants
y usuarios distintos, conflictos/reintentos concurrentes, rollback y filas ajenas
intactas, con CockroachDB, pgvector y RabbitMQ reales aislados tras el gate.
Mocks, skips y validacion documental no acreditan aislamiento funcional.

La regresion futura de health debe conservar `ok`/`failed` por dependencia y
`ok`/`degraded` global, demostrar ausencia de conteos y de llamadas a
`fetch_job_counts()` o consulta global equivalente, y conservar metricas y
Prometheus/Grafana. Los escenarios de cola exigen rechazo previo a estados,
membership vigente, descarte permanente con job preservado, replay completed
consistente sin reescritura y errores transitorios reintentables.

El spec-planner no ejecuto tests ni validadores al preparar esta reconciliacion.
Los resultados historicos en tasks 1.5/1.7 no validan este lote. La validacion
independiente posterior y el gate actual se registran en proposal.md. Los dos
registros humanos anteriores conservan las decisiones aprobadas; el conjunto
se presenta para revision del ADR y gate pre-code global. Esta fase no ejecuta
operaciones administrativas, cambia credenciales ni publica artefactos.

## Estado local de implementacion

Sincronizacion documental del 24/09/2026 tras Green/mutacion, antes de reviewer.
Las cuatro decisiones Accepted se mantienen. La
[matriz](../../openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md)
anade el mapa actual: selector/autoridad estrictos, mensajes con scope y
transaccion, correlacion persistida y membership antes del trabajo, rechazo
permanente con job intacto, completed sin reescritura, costes/CLI scoped,
upsert vectorial condicionado, logs genericos y health solo de dependencias.

Informe final del tester leido: backend 412 PASS, processor 462 PASS, total 874
sin fallos/errores/skips; 60 variantes/62 intentos, 55 KILLED y cinco equivalentes
concretos B09/B10, C03/C04, V05, sin pendientes. La sesion principal comunica
dos usuarios/dos tenants con CockroachDB/pgvector/RabbitMQ reales aislados,
replay, rechazo permanente, concurrencia vectorial y terminacion real de
conexion PostgreSQL con rollback/redelivery. SQL mutado usa SQLite; Green
incluye CockroachDB real y modelos/embeddings mock. El
[diseno](../../openspec/changes/jup-086-tenant-isolation-contract/design.md)
recoge fuentes, limites y smoke Docker complementario comunicado por la sesion
principal; los nombres de Trello siguen siendo asignaciones, no prueba de
participacion humana.

La adaptacion JSONB de lecturas de mensajes/conflictos de costes tocadas
permite el camino positivo real sin cerrar JUP-035/RF-087-002. RF-085-002 sigue
Open y fuera de alcance, sin afirmar estabilidad del reloj del host.
Revision tecnica, QA, aprobacion humana post-QA y publicacion siguen pendientes;
`docs/evidence/JUP-086-validation.md` se escribira por la sesion principal
despues de reviewer. Esta sincronizacion no ejecuta tests ni nuevos validadores;
la sesion principal validara el lote tras el handoff. No se registra ni se
infiere una nueva aprobacion humana.
