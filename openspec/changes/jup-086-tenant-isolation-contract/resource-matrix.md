JUP: JUP-086
Trello: https://trello.com/c/bKxQK9HI

# Matriz endpoint, recurso y contexto

## Aceptacion acotada vigente

Contrato de verificacion ratificado por Paris el26/09, registrado en proposal.md.
Sustituye las demandas combinatorias de las matrices historicas inferiores;
conserva aislamiento, autoridad del job/creador, no enumeracion/fugas, TLS,
no replay, lifecycle y todos los limites aprobados. Inventario actual:684
(328 backend+356 processor),111 nuevos (60 aislamiento+51 RF-086-003).
Se conservan todos los681 casos anteriores. Ejecucion nueva:11 PASS/0 SKIP
(3 nuevos+8 regresiones);681 PASS anteriores y38 variantes detectadas se
reutilizan, no son684 ejecuciones nuevas. Un fallo dirigido adicional fue
detectado y se cuenta aparte, sin afirmar39 variantes distintas.
La tarjeta original exige aislamiento, matriz, negativos, gates y PR;
RF-086-003 permanece como incremento aprobado y retenido.

| Frontera y motivo | Evidencia existente o comprobacion acotada necesaria | Estado para aceptacion |
| --- | --- | --- |
| Aislamiento de la tarjeta | [Lote real](../../../docs/evidence/JUP-086-validation.md#validacion-con-servicios-reales): HTTP, Cockroach, pgvector, cola/worker con dos tenants, creador/membership, no enumeracion/logs, replay y rollback. Los60 casos nuevos y heredados conservan predicados y negativos segun el inventario inferior. | REVIEW_PASS; evidencia y revisiones previas reutilizadas por identidad del producto, sin duplicar combinaciones. |
| Resultados y autoridad RF-086-003 | `test_job_publication.py`: cuatro outcomes HTTP, CAS foreign por tenant/creador, carrera completed en Cockroach y fallo SQL unknown simulado. `test_tenant_isolation_jobs.py::test_publication_diagnostic_does_not_replace_worker_authorization`: pending/unknown ejecutan bajo autoridad persistida. Peer Pika: NACK, cancel/stop y cierre sin CloseOk; Rabbit real: idle, ACK perdido con entrega/recuperacion sin replay y Return. | REVIEW_PASS reutilizado y ramas relevantes contrastadas. No acredita outage SQL real, NACK de Rabbit ni el flujo combinado unknown->worker. |
| DNS, TLS y recursos retenidos | Linux/Windows: `test_real_blocked_child_has_expected_os_pid_no_descendants_and_shared_close_budget` y los dos `product_real_pika_stalled_dns...`; PID, reap/pipes, generaciones y cierre reales. Resolver conserva cap/FIFO, IPC/env, cancelacion y fallo OS retenido. [TLS del25/09](../../../docs/evidence/JUP-086-validation.md#validacion-dns-local): script TEMP, JUnit/log de cuatro PASS (valido/SNI, hostname incorrecto, CA no confiable, TLS con AMQP retenido/cierre); seis hashes de producto coincidentes. Diez ciclos Windows son evidencia historica acotada. | Reutilizacion aceptada por reviewer tras comprobar helpers/runtime/artefactos. No ejecucion nueva, TLS Linux/Rabbit real ni plateau repetido Linux demostrado. |
| Reinicio del broker con backend vivo | Un caso nuevo: reinicio real del Rabbit aislado propio con mismo PID/app/publisher/owner; siguiente HTTP202 confirmado, estados SQL SQLite scoped, generacion nueva y sin replay. Identidad/StartedAt y retirada comprobadas. | PASS y REVIEW_PASS; [evidencia acotada](../../../docs/evidence/JUP-086-validation.md#validacion-acotada-final). No es un nuevo lote Cockroach ni todos los puntos posibles de caida. |
| Bloqueo del publisher | Dos casos nuevos con frames Blocked/Unblocked serializados y Pika real: suspension/reanudacion una vez, expiracion3.001s y cierre0.181s, outcomes inmutables, sin replay/helpers residuales. Limites y reloj intactos. | PASS y REVIEW_PASS; fallo dirigido detectado al eliminar la condicion de bloqueo. No se afirman alarmas reales de Rabbit ni cruce de fases/OS. |
| Gates de la tarjeta y del incremento | Ratificacion APPROVED, coder NOOP, MUTATION_PASS y REVIEW_PASS con evidencia anterior auditada y tres casos nuevos. OpenSpec34/34, trazabilidad11, higiene658, diff-check0 y QA_PASS del conjunto bajo perfil code, sin exencion. | DoD code/stage qa PASS. Post-QA APPROVED26/09 y publicacion de PR autorizada; CI remoto/revision humana de PR pendientes. Sin cierre operativo ni merge implicitos. |

La evidencia representativa basta cuando observa la misma decision del codigo
actual y conserva resultados/comandos auditables. No se exigen tests nuevos
versionados duplicados ni un objetivo numerico nuevo. Un hueco independiente
de seguridad, fallo o prueba no auditable se mantiene pendiente y se escala
con el chequeo minimo concreto; no autoriza reparacion ni dispensa implicita.

Validacion mas profunda **opcional y no verificada**: matriz completa OS/IPC/
carreras y plateau Linux repetido (riesgo de fugas acumulativas/plataforma);
TLS en Linux o Rabbit real (variaciones de entorno); NACK/alarma/recovery
reales y carga con probes Pika simultaneos (integracion y contencion);
desconexion HTTP real, outage SQL y unknown->worker de extremo a extremo
(interacciones no observadas conjuntamente). No se afirman esas garantias
probadas por composicion ni se eliminan sus contratos funcionales. No crean
otro JUP, responsable o fecha; cualquier promocion a requisito bloqueante
necesita un riesgo concreto y decision humana, sin cierre automatico.

## Seleccion practica de pruebas

Inventario historico108/681 conservado; ahora se agregan tres casos en los
dos modulos publisher (22 en unitario,5 en integracion). Las instrucciones
de recorte siguientes son historia, no permiso para retirar mas pruebas.

Validacion Linux con servicios aislados:681 PASS/0 FAIL/ERROR/SKIP, mismos
108 nuevos;38 variantes distintas detectadas. Tras la correccion regional
Unix anterior, se corrigen tres tests existentes: heartbeat, inicio del
publisher HTTP y rechazo PermissionError de V01. No nuevos casos ni cambios
de producto; R1 intacto. Las afirmaciones de cuerpos/helpers intactos del
recorte describen aquella fase, no estas correcciones posteriores.

**Seleccion108 aprobada y aplicada; R1 resuelto, aceptacion real pendiente.**
Actual108 nuevos: **60 aislamiento+48 RF-086-003**, mas4 netos heredados.
Base569; resultado**681** (325 backend+356 processor), neto**112**.
Retiro aplicado469/577 nuevos (81,3%). No llamar108 nuevos108 netos:
87 netos equivaldria a83 nuevos+4; esta seleccion supera esa orientacion
en25. No es un minimo ni una certificacion de equivalencia. Sustituye la
propuesta238, que no se implemento; no modifica requisitos funcionales.

Regresion previa sin servicios623 PASS/58 SKIP; primer WinError10053 processor y sus dos
comprobaciones posteriores se conservan en evidencia, causa no establecida.
Balance de mutacion de esa fase:33 detecciones (32 previas revisadas y m33 nuevo), cero
supervivientes conocidos y5 variantes no ejecutadas por entorno.
Restitucion **APPROVED y aplicada** sobre los107: se recupera solo
`apps/backend/tests/test_managed_resolver.py::test_adversarial_cancel_before_spawn_and_cleanup_before_other_lane[publisher]`.
Fila actual14, total108 nuevos/681 (325+356), sin producto, heredados ni
otras variantes. Baseline14 PASS; m33 con13 PASS/1 FAIL semantico. R1 cerrado,
REVIEW_PASS acotado, no mutation PASS global ni QA/aceptacion real:
[revision](review.md#revision-de-la-consolidacion).

### Tabla ejecutable para tester

Solo los13 paths siguientes se consolidaron tras el gate. Se conservaron
EXACTAMENTE estas funciones/parametros; retirar los otros casos de estos
modulos, nunca sus helpers compartidos. Los demas tests, la adaptacion6->10
completa, conftest y defaults de fixtures quedan protegidos.
En la tabla se omite el prefijo `test_` de cada funcion. Los corchetes son
los sufijos literales del node ID; `()` es un caso sin parametros, `*`
son TODOS los parametros actuales de esa funcion segun el inventario
aportado, no parametros futuros. No hay parametros implicitos de otro motor.
Aplicar parametrizacion indirecta explicita por test, sin cambiar fixtures
heredadas, deseleccionar, añadir SKIP ni agrupar escenarios en megatests.

| Path | Grupo | Antes | Conservados | Funciones y selectores exactos |
| --- | --- | ---: | ---: | --- |
| `apps/backend/tests/test_job_publication.py` | RF-086-003 | 102 | 10 | `http_outcome_is_persisted_and_only_confirmed_is_accepted` `[cockroach-confirmed-confirmed-queued]`, `[sqlite-not_sent-deadline_before_send-publish_failed]`, `[sqlite-rejected-broker_nack-publish_failed]`, `[sqlite-unknown-confirm_timeout-publish_unknown]`; `cas_zero_row_read_cannot_accept_foreign_progress` `[sqlite-publish_pending-scope0]`, `[sqlite-publish_pending-scope1]`, `[sqlite-completed-scope0]`, `[sqlite-completed-scope1]`; `worker_wins_between_send_and_http_finalization` `[cockroach-confirmed-confirmed-completed]`; `sql_finalization_failure_is_503_with_known_outcome` `[sqlite-unknown-confirm_timeout]` |
| `apps/backend/tests/test_managed_resolver.py` | RF-086-003 | 61 | 14 | `real_blocked_child_has_expected_os_pid_no_descendants_and_shared_close_budget` (); `real_child_order_ipv4_ipv6_pid_environment_and_owner_callback` (); `two_lanes_fifo_four_waiters_and_one_supervisor` (); `stalled_popen_retains_supervisor_and_slot_until_late_return_is_reaped` (); `timeout_reaps_before_eai_again_and_waiting_probe_deadline_is_not_reset` (); `adversarial_partial_pipe_io_and_would_block_keep_offsets_and_budgets` (); `adversarial_wrong_pid_retains_admission_in_isolated_process` (); `adversarial_launch_error_is_sanitized_and_does_not_poison_empty_slot` (); `adversarial_cancel_before_spawn_and_cleanup_before_other_lane` `[publisher]`; `cancel_wins_before_delivery_without_late_callback_or_early_slot_reuse` `[result-ready]`; `os_cleanup_failure_is_retained_and_never_claims_success` `[reap]`; `invalid_child_output_is_reaped_and_only_fixed_gaierror_delivered` `[oversize]`, `[malformed]`, `[unknown-error]` |
| `apps/backend/tests/test_rabbitmq_publisher.py` | RF-086-003 | 68 | 20 | `owner_registration_survives_failed_close_after_dns_thread_exits` *; `owner_thread_must_exit_after_pika_cleanup_proof_before_replacement` (); `non_owner_close_cannot_release_registration_and_clean_restart_is_allowed` *; `dead_owner_without_cleanup_proof_cannot_release_registry` *; `product_real_pika_stalled_dns_leaves_no_helpers_or_overlapping_resolvers` *; `product_real_pika_delivery_and_abort_without_closeok` *; `confirm_deadline_retires_generation_and_late_ack_cannot_complete_next` (); `capacity_is_16_including_reserved_tokens_and_cancel_releases_once` (); `cancel_before_send_prevents_every_later_send` (); `pika_log_sanitization_removes_arguments_body_and_exception_chain` (); `loss_after_entering_send_is_unknown_and_never_replayed` () |
| `apps/backend/tests/test_rabbitmq_publisher_integration.py` | RF-086-003 | 7 | 4 | `dns_tls_handoff_preserves_original_hostname_and_certificate_checks` (); `same_backend_first_post_idle_request_and_persisted_orphan` `[cockroach]`; `ack_withheld_while_heartbeat_alive_is_bounded_unknown_and_not_replayed` `[True]`; `real_mandatory_return_beats_ack` () |
| `apps/backend/tests/test_tenant_isolation_api.py` | Aislamiento | 120 | 9 | `ingest_error_precedence_without_effects` `[sqlite-True-tenant-b-body3-403]`, `[sqlite-True-tenant-a-body7-400]`; `authority_fields_are_forbidden_not_ignored` `[sqlite-/assistant/conversations-body0-user_id-bob]`, `[sqlite-/assistant/conversations/own/messages-body1-tenant_id-tenant-b]`; `foreign_other_owner_and_missing_ids_are_indistinguishable` `[sqlite-GET-None-404]`, `[sqlite-POST-body1-404]`; `conversation_list_is_private_even_for_multitenant_user` `[cockroach-multi-tenant-a-expected1]`; `billing_counts_only_selected_tenant_and_preserves_placeholder_contract` `[cockroach]`; `resource_dependency_failure_never_leaks_business_markers` `[sqlite]` |
| `apps/backend/tests/test_tenant_isolation_repository.py` | Aislamiento | 30 | 8 | `scoped_child_read_contract` `[sqlite-foreign-marker]`, `[sqlite-other-owner]`; `rejected_message_changes_neither_child_nor_parent` `[sqlite-other-owner-tenant-a-alice]`, `[sqlite-own-tenant-b-alice]`; `scoped_fetch_does_not_disclose_legacy_inconsistent_child` `[sqlite]`; `nullable_assistant_author_requires_requester_contract` `[sqlite-other-owner]`; `requester_cannot_attribute_a_message_to_another_user` `[sqlite]`; `message_rowcount_rejection_rolls_back_both_writes` `[cockroach-UPDATE CONVERSATIONS]` |
| `apps/backend/tests/test_tenant_isolation_vector.py` | Aislamiento | 3 | 1 | `filter_precedes_nearest_limit_and_excludes_foreign_context` `[tenant-a-expected0]` |
| `apps/processor/tests/test_tenant_isolation_costs.py` | Aislamiento | 65 | 14 | `start_conflict_cannot_reset_foreign_run` `[cockroach-run-b]`, `[cockroach-run-other-sub]`; `complete_foreign_parent_cannot_insert_cross_scope_records` `[sqlite-run-b]`, `[sqlite-run-other-sub]`; `scoped_failure_cleanup_and_lookup_contract` `[sqlite-run-b-fail_run]`, `[sqlite-run-other-sub-fail_run]`, `[sqlite-run-b-fetch_run]`, `[sqlite-run-other-sub-fetch_run]`, `[sqlite-run-b-fetch_records]`, `[sqlite-run-other-sub-fetch_records]`; `record_lookup_requires_matching_parent_even_when_child_scope_matches` `[sqlite-tenant_id-tenant-b]`; `cleanup_preserves_inconsistent_cross_scope_children` `[sqlite-complete-tenant_id-tenant-b]`, `[sqlite-fail-subscription_id-other-subscription]`; `insert_failure_rolls_back_prior_deletion` `[cockroach]` |
| `apps/processor/tests/test_tenant_isolation_health.py` | Aislamiento | 8 | 2 | `health_preserves_dependency_status_without_querying_business_counts` `[states0]`, `[states1]` |
| `apps/processor/tests/test_tenant_isolation_integration.py` | Aislamiento | 7 | 3 | `two_tenant_http_ingest_worker_retrieval_and_completed_replay` (); `real_broker_permanent_rejection_discards_without_persisted_effects` `[revoked]`; `real_vector_connection_loss_rolls_back_then_broker_redelivery_succeeds` () |
| `apps/processor/tests/test_tenant_isolation_jobs.py` | Aislamiento | 76 | 17 | `permanent_rejection_preserves_all_rows_and_never_executes` `[sqlite-tenant-both]`, `[sqlite-creator]`, `[sqlite-all-controls]`, `[sqlite-legacy]`, `[sqlite-deleted-creator]`, `[sqlite-revoked-member]`; `direct_job_lookup_requires_matching_scope` `[sqlite-tenant-b-alice]`, `[sqlite-tenant-a-bob]`; `direct_status_transition_requires_matching_scope` `[sqlite-tenant-b-alice]`, `[sqlite-tenant-a-bob]`; `completed_replay_never_overwrites_state_or_result` `[sqlite-revoked]`; `publication_diagnostic_does_not_replace_worker_authorization` `[sqlite-authorized-publish_pending]`, `[sqlite-authorized-publish_unknown]`; `transient_failure_requeues_then_revalidates_on_next_delivery` `[sqlite]`; `metadata_and_model_output_cannot_replace_pipeline_authority` `[sqlite]`; `worker_diagnostics_do_not_render_foreign_ids_or_untrusted_request_id` `[sqlite]`; `worker_loop_sanitizes_dependency_exception_and_cause` `[sqlite]` |
| `apps/processor/tests/test_tenant_isolation_malformed_queue.py` | Aislamiento | 22 | 2 | `unpaired_surrogate_identifier_is_discarded_before_lookup` `[sqlite-high-created_by]`; `json_depth_error_is_discarded_once_then_next_delivery_is_returned` () |
| `apps/processor/tests/test_tenant_isolation_vector.py` | Aislamiento | 8 | 4 | `foreign_global_document_id_cannot_reparent_or_delete_children` (); `foreign_global_job_id_collision_preserves_every_row` (); `failed_same_tenant_replacement_rolls_back_deletion_and_children` (); `concurrent_foreign_replacements_preserve_existing_owner` () |
| **Total nuevos** | **60+48** | **577** | **108** | **469 casos retirados; solo los13 modulos autorizados modificados.** |

Inventarios existentes: backend259->650; processor310->500. La base real
es569, no573. Conservar los diez casos adaptados agrega4 netos, no diez.
Los selectores son casos colectados, incluidos opt-ins/SKIP. El count681
no incluye casos futuros aun no escritos; cuando se incorporen se declarara
el incremento, sin cupo ficticio ni limite oculto.

### Por que no recortar solo por el numero

Esta seleccion conserva diez rechazos directos de costes: cinco operaciones
por tenant/subscription, no diez permutaciones de un unico guard. Mantiene
siete casos R2 (cache/active, owner vivo, cierre no propietario y falta de
cleanup Pika), dos DNS Red (close inmediato y setup/retry) y dos regresiones
RF-086-001/002 (surrogate y profundidad JSON). Son riesgos concretos de fuga,
escritura ajena o recurso retenido, no diagnosticos de fixtures. No se afirma
que esos bloques prueben matematicamente la necesidad del total108.

Predicados tenant/creator permanecen separados en read/write del worker,
mensajes y CAS. Costes conserva los dos scopes en start/complete/fail/fetch;
parent lookup y cleanup de children se muestrean una vez por comportamiento,
sin volver a cruzar todos los scopes/estados/motores. El flujo integrado
conserva replay, rechazo real por revocacion y rollback/redelivery real.
RF-086-003 conserva cuatro outcomes HTTP, seis del peer Pika, late ACK,
no replay, capacidad, limpieza, PID/env/IPv4/IPv6 y hostname TLS handoff.

### Reutilizacion y riesgos que se presentan al gate

| Retirada/reutilizacion | Riesgo residual y comprobacion concreta |
| --- | --- |
| Positivos schema/envelope/pipeline/retry | Reutilizar los569 heredados y diez adaptados identificados en design.md; verificar que siguen colectados y pasan. No repetir cada positivo por engine/tenant. |
| Matriz HTTP por ruta y cada forma de autoridad | Membership/mismatch se ejercitan en ingest; extra authority en ambos schemas; GET/POST opacos y scope SQL separados. Revisar que las otras rutas usan las mismas dependencias, y que ambos schemas rechazan extras de cualquier nombre. La seleccion no vuelve a probar cada cableado ni cada campo. |
| Source/artifact/content y estados worker cartesianos | Contexto persistido/modelo, controles coordinados, creator y membership tienen representantes; heredados prueban contenido valido e invalido. Validar con mutacion el cotejo comun de copias de ejecucion. Una omision especifica de un campo podria requerir restituir un caso; no esta demostrada equivalencia completa. |
| Estados/outcomes SQL completos | CAS mutable/lectura foreign se mantienen; carrera usa completed y fallo SQL usa unknown. Running/failed y SQL-error confirmado no tienen caso dedicado retenido. Revisar la decision compartida y mutar la prohibicion de sobreescribir progreso/atribuir exito incierto. |
| Doble motor, recetas Pika y diagnosticos | Una decision SQL se selecciona en un motor; Cockroach conserva conflictos, rollback, lectura/API y carrera. Peer real sustituye recetas y dobles repetidos, no aceptacion RabbitMQ. Servicios ausentes no convierten SKIP en PASS. |
| Matrices DNS/IPC/OS y carreras secundarias | Mantener hijo real, cap/FIFO, PID/env, timeout, spawn tardio, reap fallido, partial IO, resultado cancelado, size/JSON/error whitelist. No se mantienen todas las variantes de flags/numeric IP, lanes, frames, kill o callback antiguo. Mutar limites/contabilidad/validacion; si un riesgo independiente queda sin deteccion, restituir un caso y comunicar el total. |
| Health, surrogate y vector combinatorios | Un estado sano/degraded, surrogate representativo, filtro tenant y conflictos/rollback/concurrencia. Menor muestreo de dependencias/campos y resultado vacio; ninguna garantia funcional se elimina. |

Estas comprobaciones son condiciones de verificacion, no un resultado ya
obtenido ni permiso de renunciar a un requisito. Un hueco confirmado o
superviviente relevante vuelve a decision explicita sobre casos/riesgo;
no ocultarlo con un bucle, otra suite no contada o aprobacion inferida.

### Aceptacion aun pendiente

Pendientes y limites exclusivamente en la [tabla vigente](#aceptacion-acotada-vigente).
Las matrices amplias siguientes conservan el plan original, sustituido en
su demanda de verificacion; no ordenan completar todas sus combinaciones.

## Addendum DNS propuesto

Estado implementado 25/09: los siete paths autorizados ya existen; coder y
tester preservan las superficies excluidas. REVIEW_PASS tecnico local,
883 PASS/267 SKIP y 29 mutantes detectados. TLS local real y diez ciclos
Windows con plateau estan comprobados; Linux y la aceptacion con servicios
reales siguen pendientes. [Evidencia vigente](../../../docs/evidence/JUP-086-validation.md#validacion-dns-local).
El registro de publicador se retiene hasta comprobar fin del hilo y limpieza
Pika, no solo DNS cerrado. Las menciones a paths futuros/pre-code pendiente
inferiores describen la preparacion historica, no el estado de ejecucion.

Gate detallado **APPROVED** por Paris, registro 25/09/2026 14:51:40 UTC en
proposal.md. Los siete paths siguientes quedan autorizados para tester/coder;
los pendientes de preparacion inferiores son historia, no resultados actuales.
Pruebas de carga compartida observan contencion sin introducir cuotas por
tenant ni afirmar equidad/escalabilidad que esta matriz no ha medido.

Detalle pre-code PENDING, incluso tras validacion documental. Direccion y
excepcion Pika interna comunicadas por parent (25/09/2026 14:03:35 UTC)
permiten redactar; no extienden los permisos de implementacion originales.
Estado de producto REVIEW_FAIL/dos Red DNS; evidencia previa 807 PASS/267 SKIP
y 34 mutantes no prueba la nueva frontera. Fuentes/limites exactos en
[design.md](design.md#rf-086-003-dns-addendum-propuesto), decision en
[ADR-0009](../../../docs/adr/ADR-0009-rabbitmq-publisher-lifecycle.md#dns-addendum-proposed-pre-code-pending).

| Path futuro exacto, solo despues del nuevo gate | Propietario y responsabilidad |
| --- | --- |
| `apps/backend/app/services/rabbitmq_queue.py` | Coder: segundo override getaddrinfo y AbstractIOReference; token/generacion, finished real, registro/cierre del supervisor en start/close y leases de ping. Conservar delegado, owner y resultados. |
| `apps/backend/app/services/managed_resolver.py` (nuevo) | Coder: unico supervisor/registro por proceso, dos plazas, FIFO, Popen y ejecutable confiable, codec/validacion IPC, presupuestos y terminate/kill/reap. Separar ownership OS del publisher justifica el modulo. |
| `apps/backend/app/services/dns_resolver_child.py` (nuevo) | Coder: entrypoint absoluto solo stdlib, import sin efectos, ready/PID, una consulta getaddrinfo y una respuesta acotada; sin boot/import app. Separarlo impide importar el backend/secretos en el hijo. |
| `apps/backend/tests/test_rabbitmq_publisher.py` | Tester: adaptar los dos Red actuales, mismo fallo observable con hijo real; Pika real, cancel/start/resultado tardio, setup retry y close, ping independiente/concurrente. |
| `apps/backend/tests/test_managed_resolver.py` (nuevo) | Tester: codec, cap/FIFO/prioridad, deadlines, launcher/PID/env/FDs y cleanup Windows/Linux real; dobles acotados solo para errores OS no reproducibles de forma segura. |
| `apps/backend/tests/fixtures/dns_child_fixture.py` (nuevo) | Tester: entrypoint controlado solo de test que instala bloqueo getaddrinfo EN EL HIJO y ejecuta el entrypoint productivo con runpy; modos de fallo IPC separados. Marcador en TEMP acredita entrada al bloqueo. |
| `apps/backend/tests/test_rabbitmq_publisher_integration.py` | Tester: hostname/SNI/certificado original y regresion de conexiones reales/independencia de probes; completar matriz RabbitMQ existente, sin sustituir evidencia Cockroach. |

Estos siete paths son propuesta de implementacion/pruebas, no archivos creados
ahora. Tests seleccionan el entrypoint fixture mediante sustitucion del builder
de comando en su propio harness; lanzan Popen real y conservan supervisor/IPC/
cancel/kill/reap productivos. Fixture instala socket.getaddrinfo bloqueante
dentro del hijo antes de runpy; no monkeypatch Pika ni modos/env de test en
producto. El fixture tiene cleanup externo acotado incluso si falla la asercion.
Tests de comportamiento normal usan el entrypoint productivo sin sustitucion.

| Aceptacion DNS historica, demanda sustituida por tabla vigente | Evidencia y limite original |
| --- | --- |
| Dos Red originales | Immediate-close y setup-expiry/retry: observar marcador del hijo dentro de DNS; exigir muerto/reaped y sin pipes/threads/descendientes al close exitoso, antes de liberar fixture. Antes de retry, generacion anterior totalmente limpia. |
| Concurrencia y equidad | Publisher mas probes solapados: <=2 hijos contando STARTING/REAPING, un supervisor, un probe activo +4 FIFO; exceso false inmediato, clase publisher reservada, alternancia/FIFO y expiracion sin adelantamientos. No confundir overlap legitimo entre clases con resolver abandonado. |
| Carreras | Cancel antes de admision/spawn, durante Popen, al recibir ready/resultado y al despachar on_done; completion gana una vez o cancel suprime toda entrega. Shutdown simultaneo, start/close repetidos y error de startup mantienen plazas/referencias hasta cleanup. |
| IPC y fallos | Lecturas/escrituras parciales, EOF truncado, bytes extra, oversize, JSON duplicado/malformado, error fuera de whitelist, crash/exit no cero, ready PID distinto, spawn/kill/reap fallidos. Sin hangs en owner ni contenido crudo en logs/cause chains. |
| Plataformas reales | Python 3.12 Windows/Linux con ejecutable directo: Popen.pid=PID observado dentro de DNS, censo OS del arbol propio sin descendientes/supervivientes; repetir ciclos y comparar FD/handles/threads. Incluir Windows desde venv redirector y creacion oculta. Metadatos y dobles no acreditan esta fila. |
| Datos/seguridad | Numeric IP, DNS negativo, family/type/proto/flags, orden IPv4/IPv6 y flowinfo/scope_id/canonname; TLS con hostname original, verificacion habilitada. Marcadores de secretos en env/errores parentales no llegan a hijo/argv/IPC/logs; solo stdhandles propios y sin app boot. |
| Limites y fallo retenido | Setup/ticket/probe/close usan deadlines comunes; supervisor demorado/OS fallido simulado no se abandona, plaza sigue ocupada, no reemplazo y close falla saneado. Separar esa simulacion del kill/reap real con scheduler operativo. No prometer 5 s bajo fallo OS arbitrario. |
| Compatibilidad y mutacion | Pika instalado real acepta constructor directo/delegado/getaddrinfo interno; comprobar firma/cancel/callback y aborto TLS/AMQP. Mutar ramas de cancel/token, reap/plaza, cap/FIFO, IPC/env/PID/TLS y presupuesto; nuevas cifras separadas de 34 mutantes historicos. |
| Aceptacion RF-086-003 completa | RabbitMQ real idle/restart, ack perdido, nack/return/blocked y probes; Cockroach CAS/API/carreras/worker, secretos y cierre. Siguen pendientes la matriz original y re-review/QA; ningun PASS DNS los sustituye. |

Escritura actual exactamente: ADR-0009 y los cinco documentos OpenSpec
proposal/design/tasks/resource-matrix/specs/tenant-isolation/spec.md.
SQL/API/main/worker/membership/metricas/frontend/ADR-0008/RF-085-002 solo
contexto/regresion, sin cambios DNS. No tocar dependencias/CI/Docker/settings
ni evidence/review/plan/backlog. El inventario original siguiente es historia
del alcance anterior; su aprobacion no autoriza estos siete paths futuros.

## Incremento RF-086-003 option2, 25/09/2026

Pre-code APPROVED por Paris a 08:31:11 UTC (registro en proposal.md),
ADR-0009 Accepted. Se autorizan los paths/pruebas definidos abajo; los
PENDING/Proposed de preparacion quedan superados, no la evidencia pendiente.

Contrato propuesto, no implementacion: detalle pre-code PENDING; estado y
registro comunicado en proposal.md. El inventario historico inferior no
acredita cobertura de RF-086-003. Paths relativos a raiz, lista cerrada para
el incremento; no todos los tests existentes requieren edicion.

| Clase | Paths exactos y responsabilidad prevista tras gate |
| --- | --- |
| Producto backend | `apps/backend/app/services/rabbitmq_queue.py`: owner SelectConnection, interfaces I/O Pika internos, tickets, confirms, limites y probe; `apps/backend/app/main.py`: start/stop en lifespan. |
| Producto backend SQL/API | `apps/backend/app/db/database.py`: INSERT publish_pending y finalizacion CAS; `apps/backend/app/api/routes/jobs.py`: reserva/publicacion/resultado 202 o 503 saneado. |
| Tests backend nuevos | `apps/backend/tests/test_rabbitmq_publisher.py`, `apps/backend/tests/test_job_publication.py`, `apps/backend/tests/test_rabbitmq_publisher_integration.py`. |
| Tests backend a reutilizar/adaptar | `apps/backend/tests/test_ingest_tracing.py`, `apps/backend/tests/test_domain_metrics.py`, `apps/backend/tests/test_tenant_isolation_api.py`, `apps/backend/tests/test_tenant_isolation_repository.py`, `apps/backend/tests/test_secret_boundaries.py`, `apps/backend/tests/test_cors.py`; fixtures `apps/backend/tests/tenant_isolation_support.py` solo si necesario para concurrencia SQL real. |
| Tests processor a reutilizar/adaptar | `apps/processor/tests/test_ingest_task.py` (doble del publisher backend), `apps/processor/tests/test_tenant_isolation_jobs.py`, `apps/processor/tests/test_tenant_isolation_integration.py` (harness HTTP backend persistente en vez de proceso nuevo por request). |
| Lectura/regresion, sin cambio de producto | `apps/processor/app/db/database.py`, `apps/processor/app/repositories/jobs.py`, `apps/processor/app/tasks/ingest.py`, `apps/processor/app/workers/runner.py`, `apps/processor/app/clients/rabbitmq_queue.py`, `apps/backend/app/core/config.py`, `apps/backend/app/schemas/jobs.py`, `apps/backend/app/api/routes/health.py`, `apps/frontend/src/services/api.ts`. |
| Docs de esta fase | `openspec/changes/jup-086-tenant-isolation-contract/proposal.md`, `openspec/changes/jup-086-tenant-isolation-contract/design.md`, `openspec/changes/jup-086-tenant-isolation-contract/tasks.md`, `openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md`, `openspec/changes/jup-086-tenant-isolation-contract/specs/tenant-isolation/spec.md`, `docs/adr/ADR-0008-tenant-isolation-boundaries.md` (solo estado/crossref), `docs/adr/ADR-0009-rabbitmq-publisher-lifecycle.md` (Proposed). |

Review/evidencia/backlog/plan quedan bajo el orquestador despues del guard,
fuera de esta escritura. Sin cambios a schemas/migrations, manifests/settings
externos, CI, monitorizacion, frontend, tools/KPIs o endpoints adicionales.

| Aceptacion incremental historica, demanda sustituida por tabla vigente | Unitario / real previsto originalmente |
| --- | --- |
| Ownership y lifecycle | Asercion de thread en toda operacion Pika; start/close repetidos, error antes de yield, setup cancelado, cero threads/conexiones vivos al terminar; loop procesando sin requests. |
| Idle/restart | RabbitMQ aislado, misma instancia backend: publicar confirmado, idle >2 heartbeats negociados, primer request posterior confirmado; restart solo broker propio, reconexion y siguiente request confirmado sin reiniciar API. |
| Confirm que nunca llega | Fixture stdlib filtra ack/CloseOk preservando heartbeats: limite confirm, 503 unknown, abort del transporte capturado y owner disponible; entrega realmente presente puede ejecutar. No sirve solo cerrar toda la conexion ni expirar Future. |
| Nack/unroutable/blocked | Basic.Nack inyectado determinista y RabbitMQ propio con cola de prueba max-length/reject-publish; Basic.Return real por ruta ausente, aun con ack; bloqueo de broker propio, plazos y recuperacion. No crear esas politicas en colas existentes. |
| Capacidad/concurrencia | Mas de 16 solicitudes, dos tenants y creadores, barreras deterministas: admision fail-fast sin INSERT, una publicacion in-flight, confirm/generacion correctas, liberar tokens una vez. |
| Timeout/cancel/shutdown | Barreras a ambos lados de IN_FLIGHT; nunca enviar tras not_sent, unknown tras send; ack tardio, stop en setup/idle/blocked/confirm, no drain oculto, sin replay al recuperar. Cliente desconectado no cancela trabajo entregado. |
| SQL/worker | SQLite y Cockroach real: CAS por triple/estado, DB cae al finalizar, rowcount 0/>1, worker running/completed/failed gana; pending/unknown legitimos ejecutan, completed/retry legacy se conservan; timestamps/result ajenos intactos. |
| Seguridad/API/health | Auth/membership/mismatch antes de reservar/escribir, membership revocada antes de consumir, creador alterado rechazado; 202 solo ack; 503 fijo y job_id propio; secretos/cause-chain/logs Pika sin marcadores; health solo dependencias, Prom/Grafana intactos. |

El test real de nack puede usar una cola distinta predeclarada para el fixture
o politica exclusiva de su broker desechable; no modificar el contrato durable
de la cola de aplicacion. Los proxy/fault doubles viven en tests y verifican
ambos casos: mensaje entregado con ack perdido, y envio sin entrega observable.
No inferir exactly-once de contar mensajes en una ejecucion. Los skips/fallos
de entorno se reportan como gaps; no son Red semantico ni PASS de aceptacion.

## Historia conservada del aislamiento original

Estado vigente del 24/09 tras re-review: RF-086-001/002 corregidos localmente,
REVIEW_PASS tecnico; 896 PASS y 65 mutantes distintos (60 detectados/cinco
equivalentes). RF-086-003 sigue Open fuera de alcance con aplazamiento aprobado
por Paris el 24/09, registro 21:23:36 UTC, sin correccion. Estado QA en [Review](review.md) y
[evidencia](../../../docs/evidence/JUP-086-validation.md) ya existen y
prevalecen sobre los resumenes historicos siguientes de la primera pasada
Green, 874 casos y revision pendiente. No cambia la matriz de requisitos.

## Snapshot historico de preparacion, 24/09/2026

El inventario y todas las tablas siguientes hasta "Estado local tras Green y
mutacion" conservan la inspeccion previa a la aprobacion de 19:04:10 UTC.
"Presente", "pendiente", PENDING y las referencias a pruebas futuras en ese
snapshot describen la base sin el diff de implementacion JUP-086. El mapa
anadido al final recoge el estado local posterior; ADR-0008 esta Accepted y
pre-code APPROVED segun el registro intacto de proposal.md.

Inspeccion estatica 24/09/2026, base
`3a1001db857191f7abb6bb025e2fe8b04a50fe56`: actualizacion acotada del inventario
de `d9fc0ee` a las integraciones JUP-085/#43, JUP-069/#39 y JUP-014/#41.
No es evidencia runtime ni resultado
de pruebas. Paths relativos a la raiz; las funciones identifican los puntos
concretos sin depender de numeros de linea cambiantes. `Backend` significa
`apps/backend/app/`; `Processor`, `apps/processor/app/`. Alcance, cola y salud
estan aprobados segun proposal.md; la aprobacion CLI comunicada por el orquestador
establece la operacion administrativa de confianza. Implementacion/evidencia
pendientes; revision consolidada del ADR y pre-code global PENDING.
Validacion futura: Paris/Victor, implementacion y
pairing; Alejandro, revision; Lucia, QA/docs segun tarjeta, sin atribuir trabajo.

## HTTP existente

| Endpoint / recurso | Fuente ejecutable y contexto real | Salvaguarda presente | Gap / aceptacion pendiente |
| --- | --- | --- | --- |
| `POST /auth/login`, `GET /me` / identidad | Backend `api/routes/auth.py`, `api/dependencies.py::get_current_user`, `core/security.py` | Login wrapper, perfil directo, bearer y usuario persistido; sin selector tenant. | Regresion JUP-085 intacta: claims, leeway=5 y errores; no redisenar auth. |
| `GET /tenants` / membership | Backend `api/routes/tenants.py`, `db/database.py::fetch_tenants` | JOIN `user_tenants` por usuario de sesion; no necesita `X-Tenant-Id`. | Probar que usuario A no descubre memberships B, incluso con selector ajeno enviado. No devuelve `user_tenants.role`. |
| Todas las rutas de datos siguientes | Backend `api/dependencies.py::get_active_tenant`, `Database.user_has_tenant` | Usuario JWT + `(user_id, tenant_id)`; falta/empty selector 400, no membership 403. | Selector es `str`, sin contrato explicito de duplicados/whitespace. Roles persistidos no se evalúan: membership no equivale a RBAC nuevo. |
| `GET /billing/summary` / resumen y jobs | Backend `api/routes/billing.py`, `Database.fetch_billing_summary` | `count(jobs) WHERE tenant_id`; datos de todo el tenant, no solo creador. | `monthly_spend=184250`, `savings_identified=23500`, `currency=USD` son constantes; `open_ingestions` cuenta todos los estados. No consulta `azure_cost_records`. JUP-026 debe definir KPIs reales; JUP-086 verifica aislamiento del count, no corrige su semantica. |
| `POST /jobs/ingest` / job documental | Backend `api/routes/jobs.py`, `schemas/jobs.py`, `Database.create_job`, `services/rabbitmq_queue.py` | Membership; payload tenant igual a cabecera o 400; `text_content` obligatorio/no blanco (422); UUID de servidor y `created_by` de sesion persistidos antes de publish. | Repositorio acepta tenant del payload sin contexto separado. Respuesta 202 no prueba ejecucion. Envelope publicado omite `created_by`; publish fallido deja fila queued y devuelve 503. No outbox propuesto. |
| `GET /assistant/conversations` / conversaciones | Backend `api/routes/assistant.py::list_conversations`, `Database.fetch_conversations` | SQL por tenant **y** usuario; privacidad por propietario dentro del tenant. | Probar usuario A/B en mismo tenant y usuario multi-tenant. No ampliar lectura al resto de miembros. |
| `POST /assistant/conversations` / conversacion | Mismos modulos, `create_conversation` | Tenant de dependencia y propietario de sesion; ID servidor; `title` no blanco. | Repository no revalida membership. Schema ignora extras actualmente; un `tenant_id` extra no cambia el contexto. Contratar rechazo de campos de autoridad no admitidos. |
| `GET /assistant/conversations/{conversation_id}` / conversacion y mensajes | `get_conversation`, `fetch_conversation`, `fetch_messages` | Padre buscado por `(id, tenant, user)`; ajeno/inexistente 404 identico. | `fetch_messages` solo filtra `conversation_id`; registros inconsistentes o llamada directa no quedan protegidos por tenant. Requerir predicado hijo + padre/propietario. |
| `POST /assistant/conversations/{conversation_id}/messages` / mensajes y retrieval | `send_message`, `append_message`, Backend `services/vector_store.py::search_chunks`, `services/assistant.py::answer` | Verifica padre scoped antes de escribir; envia tenant autorizado al vector store; respuesta usa chunks recuperados. | INSERT de mensaje no comprueba padre en su transaccion; UPDATE del padre solo por ID; `user_id=None` en mensaje assistant no debe eliminar control del solicitante. Escribe mensaje de usuario antes de retrieval; no atribuir atomicidad global. |
| Backend `GET /health`, `GET /metrics` / operaciones | `api/routes/health.py`, `core/metrics.py`, `main.py` | Health solo estados de dependencias/fecha; metricas agregadas tecnicas. | Publicos, no son listados tenant. No introducir datos de negocio/IDs en metricas; no alterar CORS o auth para probes. |
| Processor `GET /health`, `GET /metrics` / operaciones | `apps/processor/app/api/routes/health.py`, Processor `db/database.py::fetch_job_counts`, `core/metrics.py`, `main.py` | No respuesta con filas/IDs individuales. Health consulta estados de database/RabbitMQ/vector store. | Health sin auth aun lee `jobs GROUP BY status` **global**. Politica aprobada, implementacion pendiente: eliminar `jobs` y la consulta de conteos, conservar `status`/`services` y su semantica. Regresion: cero llamadas a conteos globales y sin cambios a `/metrics`, Prometheus/Grafana o monitorizacion. |
| Simulador `POST /subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query` | `apps/azure-cost-api/app/main.py`, `auth.py`, `repository.py` | Credencial de simulacion y filtrado por suscripcion de dataset publico. | No usa sesion Economicon ni `user_tenants`. Es upstream del CLI, no API tenant-autorizada ni enlace tenant-suscripcion. No cambiar su contrato ni confundir su 403 con membership. |

Frontend `apps/frontend/src/services/api.ts` consume exactamente identidad,
tenants, billing, ingesta y conversaciones anteriores; las pantallas no prueban
que existan endpoints adicionales. CORS y `/me` conservan JUP-085/JUP-097.

## Persistencia, cola, vector y agente existentes

| Recurso / operacion | Fuente / autoridad recibida | Salvaguarda presente | Residual concreto |
| --- | --- | --- | --- |
| `users`, `user_tenants` | Backend `db/migrations/001_initial.py`, `db/database.py` | PK membership `(user_id, tenant_id)`; rol global y rol membership almacenados. | Sin FK de membership a user/tenant en esta migracion. Politica aprobada: revalidar creador y membership vigente antes de ejecutar; sin revocacion/cancelacion instantanea a mitad de trabajo ni nuevos roles o administracion. |
| `jobs` INSERT / estado | Backend `Database.create_job`; Processor `db/database.py::update_job_status`, `repositories/jobs.py` | Tenant y creador NOT NULL, ID global PK. | UPDATE running/completed/failed solo por job ID; falta cotejo de job/tenant/creador y membership vigente antes de acceso al estado/pipeline, updates scoped y rowcounts. Politica aprobada: replay completed solo consistente/autorizado, sin reescritura; rechazo permanente conserva fila. `request_id` no se persiste ni autoriza. |
| Enqueue/dequeue documental | Backend `services/rabbitmq_queue.py::publish`; Processor `clients/rabbitmq_queue.py::blocking_pop`, `workers/runner.py::_process_message` | Cola durable, mensaje persistente, ack tras task; correlacion de logs. | JSON sin schema de confianza; `request_id`/ID proceden del mensaje; errores se reencolan. Politica aprobada pendiente: validar contra job persistido/creador/membership antes de estados/pipeline; manipulado, legacy sin creador o sin permiso vigente se descarta definitivamente conservando el job, sin bucle de retries. Fallos transitorios reintentables, sin nueva politica/infraestructura, DLQ ni purga. |
| Task y graph | Processor `tasks/ingest.py::execute`, `graphs/pipeline.py` | Usa tenant/ID/source del envelope, no controles anidados; metadata no se combina con controles. | `mark_running` ocurre antes de leer payload y no valida creador. Envelope manipulado puede modificar estado ajeno y escribir en otro tenant. Igualdad envelope/payload sola no basta: cotejar job/tenant/creador y membership vigente; sin pipeline/reescritura en replay completed consistente. SQL/vector no son atomicos entre stores. |
| `conversations`, `messages` | Backend migration 001 y `Database` | Conversacion tiene tenant/propietario; mensaje guarda tenant. | Sin FK tenant-aware padre/hijo; `fetch_messages` y UPDATE padre globales; INSERT permite pareja inconsistente si se llama directamente. Solucion candidata por consultas/transacciones, no migracion automatica. |
| `azure_cost_ingestion_runs` | Processor `db/migrations/002_azure_cost_ingestion.py`, `repositories/azure_cost.py` | Tenant/suscripcion persistidos; `ingestion_run_id` incluye ambos y query canonical. | `start_run ON CONFLICT(id)` resetea fila sin cotejar tenant/suscripcion; `fail_run` actualiza por ID; `fetch_run` solo por ID. UUID determinista no es autorizacion. |
| `azure_cost_records` | Mismo repositorio, migrations 002/003/004 | `complete_run` DELETE y UPDATE de run usan tenant+suscripcion; valores insertados vienen de parametros del servicio; transaccion local. Persiste/recupera tambien `resource_id`, `resource_name` y `resource_group_conflicts`. | No comprueba run scoped antes de insertar ni rowcount final; FK solo `ingestion_id`; record ID deriva run/index/hash, no tenant separado. `fail_run` borra por run global y `fetch_records` lee por run global. Una colision/reintento directo no debe tocar otro scope ni dejar filas huerfanas de contexto. |
| Jerarquia normalizada JUP-014 existente | Processor `normalization/azure_cost.py`, `repositories/azure_cost.py`, `db/migrations/004_resource_hierarchy.py`; `openspec/specs/azure-cost-normalization/spec.md` | Promueve `resource_id`/`resource_name`, conserva filas y senala conflictos de resource group dentro de una tanda; migration 004 incorpora las columnas e indice `(tenant_id, resource_id)`. | No hay registro autoritativo tenant-suscripcion ni API jerarquica. Igual identificador logico en dos tenants no concede acceso; proteger los campos y conflictos en las operaciones existentes de coste. RF-014-001 sigue Open para validacion entre ingestas; no reimplementar jerarquia ni resolver ese finding aqui. |
| Ingesta coste CLI | Processor `run_azure_cost_ingestion.py`, `tasks/azure_cost_ingest.py::ingest`, `clients/azure_cost.py`, `normalization/azure_cost.py` | Rechaza scope vacio/control/whitespace; canonicaliza suscripcion; normaliza filas; run ID incluye scope. Grouping por defecto: `ResourceId` + `ResourceGroup`; ya no solicita `ServiceName`. | Frontera aprobada: administradores de confianza controlan CLI/credenciales y comprueban la pareja tenant-suscripcion; seleccion erronea no detectada por el sistema, sin verificar ownership Azure ni sesion. No entrada de costes UI/API de usuario final, allowlist, roles/identidades nuevos ni registro/check automatico. Distinta de `POST /jobs/ingest`, sin RabbitMQ/documentos. La confianza no permite acceder/alterar un run ajeno por ID: todo hardening de costes permanece exigible. Gestor de relaciones posible post-MVP. |
| `knowledge_documents` / reemplazo | Processor `vector_store/pgvector_store.py::store_document`, vector migration 001 | `document_id=job_id`; tenant en padre; transaccion y validacion cantidad chunks/embeddings. | `DELETE ... WHERE id` global antes de insertar permite reasignacion entre tenants; UNIQUE job_id y conflictos deben comprobar ownership sin borrar primero. Reintento propio preserva aislamiento y rollback. |
| `document_chunks`, `chunk_embeddings` | Mismo store/migration | FK a padre con cascade; IDs deterministas, embedding unico por chunk; tenant heredado del documento, no columna propia. | No inventar tablas futuras: estas ya existen. Proteger cadena padre-hijo en todos los writes/deletes/conflictos; no exigir columnas duplicadas sin aprobar migracion. |
| Retrieval vectorial / citas | Backend `services/vector_store.py::PgVectorQueryStore.search_chunks` | JOIN documento -> chunk -> embedding, `WHERE kd.tenant_id` antes de ORDER/LIMIT. | Falta evidencia real de dos tenants con vectores cercanos. Ningun candidato/cita ajeno debe llegar a respuesta ni a modelo. Store interno recibe tenant del caller, no autentica sesion. |
| Respuesta assistant backend | Backend `services/assistant.py` | Respuesta determinista con snippets y chunk IDs recibidos; sin herramienta ni LLM externo. | Preservar resultado limitado al retrieval autorizado; no presentar este servicio como runtime JUP-084. |
| Analisis processor | Processor `agents/service.py`, `guardrails.py`, `schemas.py`, `providers.py` | Proveedor soportado solo mock; tenant no vacio en preflight; metadata delimitada/sanitizada, output estricto; insight no reemplaza tenant del graph. | Comprobar no vacio no acredita membership. Metadata puede contener texto/tenant ajeno; no se convierte en control. No existe `ToolExecutionContext` ejecutable ni registro/bucle de tools. |
| Logs y errores | Backend/Processor `core/request_context.py`, `core/logging.py`, `core/runtime_secrets.py`; worker | 422 sanitizado, 500 generico, rutas parametrizadas y redaccion de secretos/URLs. | Redaccion de secretos no garantiza eliminar contenido de negocio en excepciones SQL/worker. Worker interpola job ID y exception; request_id de cola sin validar. Necesarias pruebas con marcadores ajenos en body/metadata/IDs/errores/cause-chain y outputs. |

## Superficies futuras, sin endpoint implementado en esta base

JUP-026/JUP-084 heredan el contrato; su implementacion y evidencia corresponden
a sus cambios futuros y no bloquean el cierre de JUP-086.

| Superficie | Estado y relacion | Contrato exigible al consumidor futuro |
| --- | --- | --- |
| KPIs y consulta de costes JUP-026 | Solo placeholder billing actual; no endpoint de costes reales ni agregador KPI ejecutable en backend. | Membership antes de dimensiones, agregados, conteos o caches; todo predicado incluye tenant; validar suscripcion dentro del tenant sin enumeracion. Dos datasets con importes/mismas dimensiones no se mezclan. Formulas/moneda/periodo las define JUP-026. |
| Herramientas JUP-084 | Spec y `docs/architecture/finops-agent-tools.md`, sin registro/runtime de tool calling. | Contexto tenant/usuario/roles/correlation ID inyectado por runtime fuera de argumentos; extras de autoridad rechazados; `forbidden` para suscripcion no autorizada, sin consultar ni revelar existencia. Retrieval/citas scoped igual que el camino actual. |
| GET/list/detail de jobs, documentos/chunks/embeddings; mensajes por ID; delete/update publicos | No rutas publicas en `main.py` y routers actuales. Documentos y vectores si existen internamente. | Si otra tarjeta los crea, opaque foreign/nonexistent -> mismo 404 tras auth/membership; operaciones internas equivalentes devuelven no encontrado/denegado, no un HTTP ficticio. Diseñar visibilidad de jobs por tenant/creador antes de exponerla. |

## Pruebas presentes frente a aceptacion pendiente

| Fuente de pruebas leida | Lo que cubre su codigo | Lo que no demuestra |
| --- | --- | --- |
| Backend `tests/test_auth_api.py`, `test_security_utils.py`, `test_cors.py` | Auth/perfil/claims/leeway/errores/CORS. | Aislamiento completo de recursos. No se ejecutaron en esta fase. |
| Backend `test_jobs_schema.py`, `test_ingest_tracing.py`, `test_domain_metrics.py` | Texto no blanco; envelope real con engine MagicMock; propagacion request_id y contadores mediante llamadas de funcion. | Middleware/membership real, creador en cola, persistencia y acceso negativo de dos usuarios. |
| Processor `test_ingest_task.py`, `test_embedding_pipeline.py`, `test_worker_tracing.py` | Handoff real del productor a pipeline con DB/queue/vector doubles, nested controls ignorados y retries. | Cotejo con fila real/creador, tampering coherente del envelope, rollback SQL/vector o RabbitMQ real. Test invalid envelope espera running/failed: debera reconciliarse con rechazo antes de estados. |
| Processor `test_azure_cost_ingestion.py`, `test_azure_cost_normalized_schema.py`, `test_azure_cost_cockroach_integration.py`, `test_run_azure_cost_ingestion.py` | Scope bien formado, ID scoped, normalizacion, schema, round-trip/migraciones sobre Cockroach opt-in; JUP-014 incorpora identidad de recurso, conflictos por tanda, columnas/indice 004 y grouping CLI. | No demuestra aislamiento de ataques directos a start/fail/fetch/conflictos entre tenants. La frontera administrativa CLI no verifica automaticamente relacion tenant-suscripcion, ownership Azure ni sesion; responsabilidad del operador aprobada, sin afirmar garantia tecnica. Skip sin URL no acredita integracion. Ninguna prueba ejecutada en esta reconciliacion. |
| Corpus JUP-069: `docs/validation/JUP-069-questions.json`, `tools/validation-questions.mjs` y su test | La sesion principal observo el 24/09/2026 sobre 3a1001d `node tools/validation-questions.mjs validate` exit 0: 28 consultas sinteticas, 7 categorias; validacion estructural de fuentes, cobertura y rubricas. | Tests unitarios del validador y assistant no ejecutados. El PASS estructural no demuestra aislamiento tenant, KPIs reales o runtime JUP-084; aceptacion funcional pendiente. |
| Processor `test_agent_runtime.py`; ambos servicios `test_secret_boundaries.py`, `test_logging_config.py`, `test_request_id_middleware.py` | Prompt/output guardrails y sanitizacion de secretos/error existentes. | Tool calling futuro, pertenencia de toda evidencia o ausencia general de contenido de otro tenant en todos los sinks. |
| `scripts/smoke_document_ingestion.py` | Smoke positivo HTTP -> worker -> DB/vector con tenants suministrados. | Negativos de ownership, retrieval hostil, tampering de cola o aislamiento mediante usuarios distintos; no ejecutado aqui. |

No se infieren conteos de tests, cobertura ni seguridad a partir de nombres de
archivos. El delta y design.md definen Red e integracion pendientes.

## Estado local tras Green y mutacion, 24/09/2026

Diff local sobre `3a1001d`, posterior a la aprobacion y anterior a reviewer.
El snapshot anterior se conserva para comparar el baseline con este mapa.
Las filas describen implementacion y comprobacion local, sin acreditar revision
tecnica, QA, aprobacion post-QA ni publicacion.

| Superficie | Estado local implementado y comprobado |
| --- | --- |
| Selector y autoridad HTTP | Selector unico estricto; rechazo de duplicados, listas, whitespace/control y campos de autoridad extra. Contexto de sesion/membership y precedencia aprobada conservados. |
| Conversaciones y mensajes | Lecturas con scope hijo/padre/propietario; INSERT y UPDATE scoped atomicos en su transaccion; solicitante distinto del autor nullable. Lecturas JSONB adaptadas para el camino positivo real. |
| Productor, consumidor y estados de jobs | Creador publicado; correlacion con job/tenant/creador persistidos y membership vigente antes de estado/pipeline. Rechazo permanente descarta el mensaje conservando el job; completed consistente no se reejecuta ni reescribe; updates scoped y fallos transitorios reintentables. |
| Costes existentes y CLI | Start/complete/fail/fetch y lecturas CLI scoped por tenant/suscripcion, conflictos/rowcounts y rollback. JUP-014 y su grouping conservados; lectura JSONB de conflictos adaptada. Frontera administrativa de confianza sin gestor/allowlist ni verificacion automatica de propiedad Azure. |
| Vector y retrieval | Upsert condicionado por tenant/job, ownership bajo concurrencia y reemplazo transaccional; rollback sin dano a datos previos/ajenos. Filtro tenant antes de ranking conservado y comprobado con pgvector real. |
| Worker, logs y contexto | Rechazos y errores con logs genericos y correlacion saneada; metadata/modelo no sustituyen contexto. Pruebas con marcadores ajenos y mutantes de logging/contexto en Green. |
| Processor health y metricas | Solo estado de dependencias, sin `jobs` ni consulta global de conteos; regresion `ok`/`failed`, `ok`/`degraded`. `/metrics` y configuracion Prometheus/Grafana conservados. |
| Limites que siguen vigentes | SQL/vector y INSERT/publish no son atomicos entre sistemas; sin cancelacion instantanea de trabajos en curso. JUP-026/JUP-084 siguen futuros; RF-014-001 y RF-085-002 siguen Open. Adaptacion JSONB no cierra JUP-035/RF-087-002. |

Informe final del tester leido: backend 412 PASS (259 existentes + 153 nuevos),
processor 462 PASS (304 existentes + 10 reconciliados + 148 nuevos), total 874,
sin fallos/errores/skips. Mutacion: 60 variantes/62 intentos, 55 KILLED y cinco
equivalentes concretos B09/B10, C03/C04, V05, sin pendientes. Mutacion SQL con
SQLite; Green tambien con CockroachDB real; modelos/embeddings mock.

La sesion principal comunica opt-ins aislados completos, dos usuarios/dos
tenants en ASGI HTTP -> RabbitMQ -> worker -> CockroachDB/pgvector -> retrieval,
replay/rechazo permanente, concurrencia y terminacion real de conexion
PostgreSQL con rollback/redelivery. Tambien comunica smoke Linux de Dockerfiles
reales: dos jobs/dos tenants con un usuario, 38 chunks/38 embeddings mock de ocho
dimensiones, servicios healthy, ambos `/metrics` 200 y health processor sin jobs;
14 hashes de producto coinciden con contenedores. Design.md detalla ese smoke
complementario y los 1271 casos distintos actuales, de los que 874 son el nucleo
de JUP-086. Asignaciones Trello: Paris lead, Victor pair, Alejandro reviewer y
Lucia QA; no se atribuyen actividades humanas a estas ejecuciones automatizadas.
Esta sincronizacion no ejecuta pruebas ni validadores; la sesion principal
validara el lote y escribira review/evidencia despues de reviewer.
