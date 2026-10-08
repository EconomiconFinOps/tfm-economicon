## ADDED Requirements

**Estado final local — 08/10/2026; evidencia E13**

Resultado vigente comunicado por PM09:40:27/TL09:43:52 Atlantic/Canary: revisión técnica interna afectada favorable y validación funcional local acreditada. Hay **6 intentos reales acumulados**, sin reset: la sexta petición, iniciada manualmente desde «Salud del sistema», recibió HTTP200, JSON válido, una elección, finish_reason=stop y contenido exacto OK. La quinta conserva HTTP429 como caso de error; los cuatro anteriores no se convierten retrospectivamente en éxitos. GET/polling no genera inferencias.

La observación válida caduca contractualmente a los **60 segundos**: después se presenta unknown/stale conservando verified_at y check_id. Este comportamiento y el criterio funcional permanecen intactos. Modelo y coste siguen siendo informativos, con identidad y facturación upstream no confirmadas. Se conserva la reserva incierta histórica; la cohorte operativa terminó **6/6, sin envíos restantes**, y no se autoriza una séptima petición.

E13 acredita revisión interna con214 pruebas propias y validación afectada con214 PASS en cuatro ejecuciones completas (102+33+29+50); la ejecución conjunta sin resultado no cuenta como PASS. E12 conserva Red143 PASS/38 fallos significativos, Green214 PASS y15 mutantes detectados, con controles37/37. No se repiten suites de producto en esta consolidación documental.

Siguen pendientes DockerServer M5 con Alejandro, CI remota, aprobación humana final, archivo específicamente autorizado en la misma rama, PR vinculada y las dos reviews humanas. La asignación Paris/Víctor/Alejandro/Lucía no acredita participación efectiva. Los bloques siguientes, incluso cuando dicen «vigente» o «pendiente», son historia fechada de sus fases; E13 actualiza sus hechos de ejecución, no sus decisiones ni requisitos/escenarios. El techo humano sigue siendo **0,20 EUR acumulados incluyendo intentos anteriores**; no equivale a0,20 USD.

**Estado vigente tras implementación — 08/10/2026**

Fuente: PM03:31:30 transmitido por TL03:32:20 Atlantic/Canary: Paris autoriza las pruebas necesarias para completar JUP-047 hasta **0,20 EUR acumulados, incluyendo los intentos previos**. Sustituye el anterior presupuesto humano de 0,40 USD y el cupo humano de 13 llamadas. El contador verdadero sigue en **4 intentos reales**, sin reset ni éxito retrospectivo. La equivalencia conservadora fechada en USD corresponde al PM y no se calcula ni incorpora aquí. TL coordina cohortes operativas finitas dentro del techo; no se presenta un resto fijo de nueve ni un veto a la tercera llamada como autorización vigente. El contador y límite operativo de cada cohorte siguen siendo finitos y fieles, con admisión ordinaria, cooldown, frecuencia, cero retries/fallbacks y reservas intactos.

La autonomía local transmitida por PM03:34:40/TL03:35:12 permite pasos locales ordinarios dentro del alcance y proceso; no es aprobación funcional ni permiso de publicación, nuevos accesos remotos o cambios materiales. El cap diagnóstico de **0,03 USD** previamente aprobado permanece **sin aplicar** en esta consolidación; H=0.000031275 USD, U=0.008064 USD y P=0 se conservan. La captura cuarta no aporta un texto literal conocido ni respuesta funcional válida.

Los apartados y bloques anteriores conservados más abajo, incluso si usan «vigente», 4/13, dos envíos o 0,40 USD, son antecedentes fechados de su fase. Sus importes/cupos quedan sustituidos por esta nota; las aprobaciones históricas no se reescriben. No se modifica el criterio funcional, arquitectura, producto, pruebas, routing, privacidad o política de admisión.

La corrección offline está implementada: **Red 143 PASS / 38 fallos significativos; Green afectado 214 PASS; mutación nueva 15/15 KILLED; control original y restaurado 37 PASS cada uno**. No errores ni SKIP en el Green o controles. Guard conjunto de mutación con cero cambios y 852 fuentes/4 tests fijos; referencias originales intactas. Primer Green parcial con timeout y primer guard rechazado por interfaz se conservan como no satisfactorios; su corrección está descrita en E12. Cero nuevas llamadas, gasto, servicios o cambios de cap. Revisión y validación independientes afectadas siguen pendientes; E10 no las anticipa.

E12: `jup047-prompt-liveliness-implementation-20261008/delivery-handoff.json`, SHA256 `fb1a45b669d7ea9eda87baeac6f6157e78a464befe110d2d6a6f22721b2b12de`; índice de 151 artefactos `artifact-sha256.json`, SHA256 `b0c4491afde9637f92128b57c276cd6612d19d77f7be3d9cd2c74d819bb0e776`. Referencias externas entregadas al TL; no se copian recibos privados al producto. Rama `feat/JUP-047-system-health-dashboard`, HEAD `f0cacddb037dcb38878dd02de8adf5aff479d1b6`, cambios sin commit; Python 3.12 aislado Windows, transportes/procesos simulados y fixtures de denegación de red conservadas. No prueba remota ni aceptación por el Desarrollador. M5/Alejandro, CI remoto, aprobación final, archivo específico y reviews humanas permanecen pendientes.

### Requirement: Authenticated operational health diagnostics
The backend SHALL provide GET `/health/status` for an authenticated user and an authorized active tenant, without changing the public GET `/health` semantics or timestamp requirements. GET diagnostics SHALL be read-only and SHALL NOT invoke ingestion, publication, chat or embedding. A separately authenticated POST `/health/provider-check` SHALL perform one admitted real OpenRouter inference through LiteLLM, subject to prior cost reservation and limits.

#### Scenario: Authorized tenant
- **WHEN** a valid user requests operational health for a tenant they may access
- **THEN** the response contains the tenant, aggregate status, UTC-aware checked_at, observation window and component diagnostics
- **AND** an unhealthy dependency is represented in the body without hiding the healthy observations

#### Scenario: Missing credentials or unauthorized scope
- **WHEN** the request lacks credentials, has an invalid tenant selector or selects a forbidden tenant
- **THEN** the existing authentication/scope protocol returns401,400 or403 respectively before tenant diagnostic queries
- **AND** no tenant summary is disclosed and authentication failures are not bypassed for monitoring

#### Scenario: Existing health consumers
- **WHEN** an existing client or Docker healthcheck calls GET `/health`
- **THEN** status remains ok only when its original three services are healthy and degraded otherwise
- **AND** services and checked_at retain their existing contract, with no new tenant requirement

### Requirement: Explicit health sources and semantic states
Operational diagnostics SHALL describe backend API, database, queue, processor API, vector storage, simulated Azure API, LiteLLM gateway and an independently identified OpenRouter observation. Every observation SHALL have a closed id/status/reason and timestamp with declared live/simulated/mock/unverified provenance. Status SHALL be one of ok, degraded, failed or unknown.

#### Scenario: Real provider check distinct from gateway
- **WHEN** an authorized panel opening or manual update admits a provider check
- **THEN** one real synthetic inference is sent through the pinned economicon-chat alias to z-ai/glm-5.2, with disabled reasoning/retries/fallbacks and no user data
- **AND** a valid functional response through the configured route marks OpenRouter ok with its own verified_at independently of returned model spelling or cost information; mock/liveliness cannot satisfy the real-provider requirement
- **AND** configured models/routing, access controls, fixed payload and usage limits remain enforced; returned model name does not certify executed model identity

#### Scenario: Reachable gateway without current real inference
- **WHEN** gateway liveliness succeeds but the real inference is absent, failed, timed out, blocked or stale
- **THEN** gateway availability remains distinct and OpenRouter has the corresponding explicit non-ok result
- **AND** a prior successful verified_at is not advanced or described as the result of the new attempt

#### Scenario: Vector and simulator scope
- **WHEN** vector database connectivity succeeds but required extension/schema is missing, or the configured Azure service is a simulator
- **THEN** vector readiness exposes the schema limitation and the Azure result is explicitly simulated
- **AND** no embeddings are inserted and no real Azure availability is claimed

#### Scenario: Aggregate precedence
- **WHEN** all observations are unknown, a critical DB/queue/vector/processor API has a confirmed failure, or another observation is not ok
- **THEN** aggregate status is respectively unknown, failed, or degraded
- **AND** aggregate ok requires every required observation to be valid and ok

#### Scenario: Historical operational failure
- **WHEN** a dependency is reachable but the tenant has recent failed jobs or ingestions
- **THEN** the activity summary is degraded and exposes the failure count/window
- **AND** a historical failure does not by itself assert that the database or worker is currently down

### Requirement: Functional availability independent of model identity and cost information
For an admitted provider check, availability SHALL depend on the valid functional HTTP/result contract, not exact equality, prefix, version, marker or allowlist of the returned model name. The server SHALL retain configured alias/model/routing and preflight guarantees. verified_at SHALL mean the latest valid real functional response, not verified model identity or confirmed cost. Identity and cost information SHALL NOT degrade an otherwise valid functional availability result or aggregate.

#### Scenario: Alias versioned or different returned model
- **WHEN** a valid admitted functional response reports economicon-chat, the canonical model, a versioned name or a different name
- **THEN** availability is ok/none and verified_at advances for that response
- **AND** reported_model is bounded sanitized information with model_identity=unconfirmed even when it equals the configured name
- **AND** configured model/routing and prohibition of client-selected model remain enforced

#### Scenario: Missing or unsafe informational model
- **WHEN** an otherwise valid functional response has no usable string model name or has an unsafe/oversized name
- **THEN** reported_model is null and model_identity remains unconfirmed without failing availability
- **AND** raw unsafe data is not exposed in response/logs

#### Scenario: Functional response is invalid
- **WHEN** HTTP is not200, transport times out, JSON/body exceeds16384bytes or is invalid, there is not exactly one choice, finish_reason is not stop, normalized message.content is not OK, or id is not a nonempty string of at most256characters
- **THEN** the existing closed error/non-success state is retained and verified_at does not advance
- **AND** a matching model name or positive cost cannot turn that invalid response into success

#### Scenario: Cost is independently reported
- **WHEN** a valid functional response includes usable gateway cost, omits it or reports an invalid monetary value
- **THEN** availability remains ok and the observation separately contains reported_cost_usd nullable decimal string, cost_status gateway_reported/unavailable/invalid and cost_confirmation=unconfirmed
- **AND** a gateway value including a calculated estimate is never described as upstream-confirmed or manufactured from policy prices
- **AND** a reported zero does not imply free execution or release of a reservation

#### Scenario: Functional success with uncertain accounting
- **WHEN** the functional response is valid but cost or usage does not satisfy existing conservative financial receipt checks
- **THEN** availability and verified_at reflect functional success while the full uncertain reserve remains held; a further explicitly authorized request uses ordinary admission with the reserve included in remaining capacity, without requiring reconciliation solely because uncertainty is nonzero
- **AND** Decimal checks, positive cost not greater than reserve, integer bounded positive total usage, valid configured route/transport and prior admission guarantees remain effective
- **AND** the earlier uncertain trial reservation and ledger remain unchanged and this design itself sends no real request
- **AND** accepting new financial evidence or changing reconciliation policy requires a separate PM decision

### Requirement: Tenant-scoped job and ingestion summaries
The diagnostic SHALL summarize persisted jobs and Azure ingestion runs only for the authorized tenant, using parametrized read-only queries, a24-hour UTC failure window and available latest timestamps. It SHALL distinguish available, empty and unavailable data, with unknown timestamps represented by null.

#### Scenario: Two tenants with different histories
- **WHEN** two authorized tenants have different job/run statuses and dates
- **THEN** each response reports only its tenant counts and timestamps, including jobs by current status and Azure runs by known status
- **AND** failed_last_24h uses the declared inclusive UTC observation window

#### Scenario: No history or missing schema
- **WHEN** the tenant has no jobs/ingestions or the source table cannot be queried
- **THEN** valid empty data has zero counts and null latest timestamps, while unavailable data is explicitly unavailable and not fabricated as zero

#### Scenario: Failed or indeterminate job publication
- **WHEN** tenant jobs have publish_failed or publish_unknown status
- **THEN** recent publish_failed jobs are included with failed jobs in the24-hour failure count using updated_at
- **AND** publish_unknown remains an explicit indeterminate publication count requiring attention, not a confirmed success/failure
- **AND** native queued/running/completed/publish_pending statuses remain represented and unexpected statuses are safely grouped as other

#### Scenario: Latest ingestion distinct from refresh
- **WHEN** the dashboard refreshes after an older completed ingestion
- **THEN** checked_at reflects this diagnostic evaluation and last_completed_at remains the actual persisted ingestion completion time
- **AND** failed/running runs do not replace the last completed timestamp

### Requirement: Bounded and sanitized diagnostics
Operational aggregation SHALL use real transport/query deadlines and bounded concurrency without unlimited retries or queues. The proposed contract SHALL cap each probe at two seconds, aggregation after successful authorization at five seconds, and active probes at four per backend process. It SHALL return closed reason codes and SHALL exclude secrets, DSNs, destination URLs, payloads and upstream free-form responses from diagnostics/logs.

#### Scenario: Slow probe and resource recovery
- **WHEN** a dependency stalls in DNS, connection, read or query, or probe slots are saturated
- **THEN** its observation becomes unknown/timeout or unknown/busy within the aggregate budget while other available observations remain visible
- **AND** sockets/connections/slots are released after cancellation and repeated stalls cannot create unbounded background work

#### Scenario: Synthetic private data in upstream failure
- **WHEN** a probe failure includes a synthetic credential, URL, document text or provider message
- **THEN** only the closed reason is exposed in response/logs, not the private marker
- **AND** requests use configured destinations without client-selected URLs or followed redirects

#### Scenario: Repeated non-generative reads
- **WHEN** GET diagnostics or automatic30second polling is repeated
- **THEN** product data, queue messages, vector contents and generative costs are unchanged
- **AND** no LLM/OpenRouter inference is caused by the GET or polling

### Requirement: Real inference admission and conservative cost reservation
Every real provider request SHALL authenticate and authorize before cost, use a fixed short synthetic payload without client-selected prompt/model, request max_tokens32, and reserve a verified conservative maximum before sending. Known spend plus pending/uncertain reserves SHALL never exceed the authorized remaining limit; missing price, billable token/fee bounds, effective cap, diagnostic admission accounting or enforceable cost ceiling SHALL block sending and require consultation. Uncertain cost SHALL remain reserved until trustworthy reconciliation.

#### Scenario: Safe admission
- **WHEN** current verified prices, all billable bounds/fees, effective routing/caps and remaining credit permit a conservative reserve
- **THEN** the reserve is acquired atomically before request transmission, including input envelope and the800token configured output maximum unless another safe maximum is established
- **AND** only one call is active with no retries/fallbacks; synthetic requests have no user data and all keys remain server/gateway-side

#### Scenario: Cost cannot be guaranteed
- **WHEN** price/accounting/cap is unverifiable, remaining limit is insufficient, or recorded spend plus uncertain/pending reserves plus the next conservative reserve exceeds any applicable limit
- **THEN** no new real request is sent, no reservation is silently released, and the operator/coordinator receives an explicit unavailable/consultation condition
- **AND** zero/missing reported cost with positive usage is not treated as a free call

#### Scenario: Idempotency, frequency and restart
- **WHEN** duplicate actions, busy/cooldown conditions, more than6calls/hour or24/day per diagnostic credential, or lost reservation state after restart occur
- **THEN** no overlapping/unaccounted call is admitted; idempotency is scope-bound, cooldown is60seconds, and restart requires truthful ordinary ledger-state capture including uncertainty, cumulative count and existing frequency limits before real calls resume, without requiring uncertain amounts to be reconciled
- **AND** a rejected/coalesced action is not presented as a newly executed verification

#### Scenario: Separate trial and deployed budgets
- **WHEN** JUP-047 real trials or deployed operation is configured
- **THEN** trials use an external private cumulative ledger with limit0.40USD and an initial plan of TWO real requests, including failures/uncertain costs without reset
- **AND** further trial requests require explicit cumulative authorization without resetting spent calls or historical reserves, while deployed operation requires its own finite explicitly authorized budget and cannot inherit trial credit as unlimited allowance


### Requirement: Ordinary admission retains historical uncertainty without automatic veto
The ordinary certificate and admission SHALL preserve historical receipts, known spend, uncertain and pending reservations, cumulative execution count and frequency history. A recorded historical uncertain reserve or lack of reconciliation SHALL NOT by itself block a new explicitly authorized check. Admission SHALL require exact conservative H+U+P+R<=B, all other safety gates and remaining authorized calls. No per-call financial exception, fabricated reconciliation, reset or zero-uncertainty certificate SHALL be used. Upstream key sharing SHALL NOT require upstream exclusivity; accounting scope SHALL be the authorized diagnostic execution.

#### Scenario: Authorized check with historical reserve
- **WHEN** the ordinary current certificate truthfully records previous calls/receipts/reserves and its authorized cumulative limit, has a remaining call, no active pending call and sufficient capacity under every applicable cap
- **THEN** admission retains the history/reserves unchanged and atomically reserves the next request and increments the true cumulative count before transmission
- **AND** cooldown60seconds, one active call,6/hour,24/day, auth/tenant/isolation, routing and zero retries/fallbacks remain enforced
- **AND** earlier UI results are never retrospectively marked PASS; any new inference requires a separate authorized execution dispatch, affected review/validation and independent PM guards/current ordinary preflight

#### Scenario: Exact remaining capacity and exhausted count
- **WHEN** H+U+P+R equals B, exceeds B, or the cumulative execution count has reached its authorized limit
- **THEN** exact equality permits admission only with all other gates; excess or exhausted count rejects without transport and without changing historical accounting
- **AND** no call beyond the currently authorized cumulative limit is admitted even if monetary capacity remains; explicit extension never resets earlier calls

#### Scenario: Ordinary certificate records uncertainty truthfully
- **WHEN** an operator emits the ordinary bounded certificate for the current instance
- **THEN** existing finite nonnegative known_spend_usd/uncertain_usd/pending_usd, references and strict cumulative counter preserve prior state without new certificate flags, timestamps, financial exception or spending audit
- **AND** reservation_state_reconciled=true, reconciled_at and uncertain_usd=0 are not admission requirements and are never fabricated
- **AND** existing credential hash/alias, single process/replica, routing/privacy/price/cap guarantees, validity and unchanged digest preflights remain mandatory

#### Scenario: Restart or subsequent uncertain response
- **WHEN** state is missing/invalid, a prior pending operation remains, certificate expires/changes, or an admitted request lacks a usable financial receipt
- **THEN** missing state/pending operation/invalid preflight rejects without transport; a possibly sent request retains its conservative reserve and incremented cumulative count
- **AND** restart with lost state remains blocked until existing state/limits are faithfully recovered; no reset of H/U/P, cumulative count or cooldown/hour/day limits and no treatment of unconfirmed cost as zero is allowed
- **AND** nonzero U alone is never a rejection predicate


### Requirement: Unambiguous fixed request preserves the functional criterion
The provider diagnostic SHALL send exactly one fixed user message with content "Return exactly the two uppercase letters OK. Do not include punctuation, quotes, whitespace, or any other text.". Its normalized response criterion SHALL remain content.strip().upper()==OK, with the existing HTTP200, bounded JSON, single choice, finish_reason stop and bounded nonempty ID requirements. The clarified request SHALL NOT change routing/model, max_tokens32, retry/fallback policy, input/output bounds, privacy or conservative admission.

#### Scenario: Exact synthetic message on the wire
- **WHEN** an authorized diagnostic is admitted
- **THEN** the serialized wire JSON contains the fixed message and existing alias/parameters, without client or tenant text
- **AND** the full input envelope remains inside the verified input bound before sending; clarification alone does not guarantee model compliance

#### Scenario: Punctuation or additional response text
- **WHEN** an HTTP200 response has content OK. or other text that is not exactly OK after the existing strip and uppercase normalization
- **THEN** it remains invalid_response with no new verified_at/check_id success
- **AND** model spelling, gateway cost and a successful liveliness probe cannot override rejection; existing lowercase/outer-whitespace normalization is unchanged

### Requirement: LiteLLM liveliness uses its specific non-generative contract
Only the configured LiteLLM GET /health/liveliness probe SHALL accept the pinned endpoint contract HTTP200 with a JSON string exactly equal to "I'm alive!". This selection SHALL be explicit and internal, never inferred from arbitrary destinations or exposed to clients. The generic processor/Azure HTTP probes SHALL retain their existing JSON object status ok/healthy/degraded contract. Both SHALL preserve bounded reads, deadlines including isolated DNS, no redirects, connection cleanup, redaction, authentication/scope boundaries and zero generation.

#### Scenario: Exact LiteLLM response
- **WHEN** the enabled configured LiteLLM liveliness endpoint returns HTTP200 and the exact JSON string "I'm alive!"
- **THEN** only the gateway observation is ok/none
- **AND** OpenRouter state, real-response timestamps and inference count do not change

#### Scenario: Other strings types HTTP and resource boundaries
- **WHEN** LiteLLM returns any other string, JSON object/array/null/number/bool, invalid JSON, over16384bytes, non200 HTTP, a redirect, timeout or connection failure
- **THEN** it cannot become gateway success and the existing appropriate closed reason is returned within the isolated deadline
- **AND** the connection and operation resources close; no raw body, URL or secret appears in diagnostics/logs and no inference/retry follows

#### Scenario: Generic and disabled probes remain compatible
- **WHEN** processor or simulated Azure is probed, or LiteLLM probing is disabled
- **THEN** the generic JSON status contract and explicit disabled/unconfigured result remain unchanged
- **AND** a LiteLLM string is not accepted by the generic parser and a generic status object is not accepted by the LiteLLM parser; public health/auth/tenant contracts remain unchanged


### Nota de evidencia de implementación — E12

La implementación local de los requisitos de petición fija y LiteLLM específica está acreditada por E12: Red143/38, Green214PASS,15kills dirigidos, controles37/37 y guard conjunto cero cambios/852fuentes/4tests fijos. No se modifica ningún Requirement ni Scenario en esta consolidación. El cap0.03, conversión monetaria y próxima cohorte son operación separada; la cabecera sustituye importes/cupos humanos históricos sin cambiar la admisión genérica. Revisión/validación afectadas y respuesta funcional real pendientes.
