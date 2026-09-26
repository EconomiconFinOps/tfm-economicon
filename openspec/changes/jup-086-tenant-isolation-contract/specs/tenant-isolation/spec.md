## Context

Current verification contract, 2026-09-26: the bounded acceptance table in
[resource-matrix.md](../../resource-matrix.md#aceptacion-acotada-vigente) governs
evidence sufficiency and pending checks, ratified by Paris on 2026-09-26.
All retained isolation, authority, TLS, no-leak, no-replay and lifecycle
behavior and numeric bounds remain required. Earlier status/verification
matrices are history; their human records remain verbatim. RF-086-003 is an
explicitly approved add-on, not original-card necessity. This reconciliation
does not grant a non-code DoD exemption, final approval or closure. Both
bounded runtime groups now pass technical review; inventory684 (111 new),
11 freshly passed cases (3 new+8 regressions), prior681 passes reused.
Code QA PASS without exceptions; human post-QA APPROVED on 2026-09-26,
with branch publication and PR authorization, not merge or tracker changes.
Earlier implementation/status paragraphs are history.

Current local implementation evidence, 2026-09-25: technical REVIEW_PASS
after DNS-child cleanup and publisher-registration retention corrections.
883 repository tests pass; 267 live opt-ins are skipped, not accepted.
29 current mutations are detected. Windows TLS and bounded resource cycles
have evidence; Linux and real dependencies remain pending. Requirements,
approved limits and human approval records are unchanged. This is not QA,
full acceptance or a waiver. Earlier preparation-status paragraphs below
are historical; see review.md and the current validation evidence.

DNS addendum pre-code APPROVED by Paris, orchestrator record 2026-09-25
14:51:40 UTC in proposal.md. Detailed DNS requirements now govern its
implementation; following Proposed/PENDING preparation notes are history.
Approval does not prove runtime compliance or QA. The two-child cap applies
per backend process to DNS only, not to tenants/jobs; no new tenant quotas or
measured scalability/fairness guarantee is introduced.

Current DNS addendum: Proposed; detailed pre-code gate PENDING even after
document validation. Parent's 2026-09-25 14:03:35 UTC context permits drafting
the direction and narrow internal-Pika exception, not implementation. The
original Accepted decision and approval records below remain verbatim.
REVIEW_FAIL, two DNS Red cases and BLOCKED_ENV remain; 807 PASS/267 SKIP and
34 mutants predate those failures. No current Green or QA is inferred.
The new DNS requirements are proposed obligations effective only after the
separate gate. They replace DNS delegation/one-override instructions only,
preserving successful-close zero helpers and all SQL/API/outcome contracts.
Pika nbio/selector interfaces are INTERNAL; historical public-API wording is
not a current support guarantee. Python subprocess/pipe APIs are public stdlib.

Increment pre-code APPROVED by Paris, orchestrator record 2026-09-25
08:31:11 UTC in proposal.md; ADR-0009 Accepted. The following preparation
PENDING/Proposed notes are superseded for approval only. Increment tests,
implementation, review and QA still require evidence; requirements unchanged.

Current increment, 2026-09-25: RF-086-003 option2 scope incorporation is
communicated in proposal.md; its detailed pre-code gate remains PENDING after
validation. ADR-0009 is Proposed; ADR-0008 remains Accepted for original
isolation decisions. The new publisher requirements below govern this
increment; all following 2026-09-24 status/approval/evidence is preserved
history, including deferral, 896 passes and 65 mutants, not increment evidence.
No tester/coder before the new human gate. No product/test execution this phase.

Current status after re-review, 2026-09-24: technical REVIEW_PASS;
RF-086-001/002 fixed locally. Full Green: 896 passes, zero failures/errors/skips;
65 distinct mutants, 60 killed and five previously reviewed equivalents.
RF-086-003 remains Open, pre-existing/out-of-scope. Paris explicitly approved
deferral on 2026-09-24, recorded at 21:23:36 UTC; no fix or post-QA approval.
QA disposition is recorded in review/evidence. Review and evidence
now exist at `review.md` and `docs/evidence/JUP-086-validation.md` and supersede
the historical first-Green (874 cases) status below. Requirements unchanged.

JUP-086 acceptance contract, pre-code approval APPROVED by Paris on 2026-09-24,
recorded at 19:04:10 UTC in proposal.md. Existing scope, queue
and health policies are approved in proposal.md; CLI approval communicated by
the orchestrator establishes a trusted administrative operation. All four
policies are approved; proposal.md, section "Validacion documental consolidada",
preserves the historical documentary validation. Consolidated
ADR and global pre-code approval are recorded in "Registro de aprobacion
pre-code"; ADR-0008 is Accepted. The preparation baseline predates that approval.
resource-matrix.md preserves that snapshot and maps the locally implemented
surfaces after Green/mutation on 2026-09-24, before technical review;
future consumers below are contracts, not delivered code or JUP-086 closure blockers.
The reconciled baseline is `3a1001db857191f7abb6bb025e2fe8b04a50fe56`:
JUP-014 normalized hierarchy is present; JUP-026 KPIs and JUP-084 tools remain future.
JUP-085 auth/leeway/CORS and JUP-097 restrictive /me policy remain unchanged.

Documentation status only, 2026-09-24: the final tester report records 412 backend
and 462 processor passes (874 total, no failures/errors/skips), 60 distinct
mutants in 62 attempts, 55 semantic kills and five documented equivalents
(B09/B10, C03/C04, V05), none unresolved. The parent reports real isolated
CockroachDB/pgvector/RabbitMQ checks with two users/two tenants, replay,
permanent rejection, concurrency and PostgreSQL connection termination with
rollback/redelivery. SQL mutations use SQLite; full Green includes CockroachDB;
models/embeddings are mock. The health scenario's implementation/regression
"pending" phrase below is retained verbatim from pre-approval preparation;
current local evidence is recorded in design.md and resource-matrix.md.
All requirements and scenarios below remain unchanged. Technical review, QA,
post-QA human approval and publication remain pending. This documentation sync
runs no tests or validators; the parent validates after handoff. The JSONB read
adaptation does not close JUP-035/RF-087-002, and RF-085-002 remains Open and
out of scope without any host-clock stability claim.

## ADDED Requirements

### Requirement: The session authorizes one unambiguous tenant context

User-facing tenant data operations SHALL use the persisted bearer user and verify
`user_tenants` membership for a single well-formed selector. A body tenant
SHALL only confirm that context. Existing membership semantics SHALL remain:
roles do not bypass membership, and conversations remain private to their
owner within the tenant. Identity/bootstrap SHALL require no tenant selector.

#### Scenario: Membership discovery and existing roles

- **WHEN** a valid user calls `GET /tenants` without a selector
- **THEN** only that user's memberships are returned; `/me` remains identity-only.
- **AND** an admin without membership cannot access another tenant; an admitted member retains existing actions without new RBAC.

#### Scenario: Explicit error precedence

- **WHEN** a parseable request to a mounted data route has multiple invalid conditions
- **THEN** checks follow identity (401), selector (400), membership (403), body schema (422), tenant mismatch (400), then scoped lookup (404), without downstream effects after rejection.
- **AND** syntactically invalid JSON retains sanitized 422 before dependencies; CORS preflight and routing errors remain outside this ordering.

#### Scenario: Selector and payload validation

- **WHEN** the bearer is valid but the selector is absent, empty, duplicated or malformed as defined in design.md
- **THEN** return 400 without resource access.
- **WHEN** the selector is well formed but not a membership, including a nonexistent tenant
- **THEN** return the same generic 403 without tenant metadata.
- **WHEN** membership and schema are valid but ingestion body tenant differs
- **THEN** return 400 without job INSERT or publish.

#### Scenario: Preserve schema errors and reject authority injection

- **WHEN** membership is valid but required ingestion tenant/text, conversation title or message content is missing, invalid or blank where prohibited
- **THEN** return sanitized 422; missing body tenant is not a universal 400.
- **WHEN** a conversation/message body supplies unsupported tenant, user or roles fields
- **THEN** return sanitized 422 without applying them; documentary metadata is never merged into control fields.

### Requirement: Scoped predicates protect conversations and messages

Reads and writes SHALL include authorized tenant and conversation owner in
their authorization predicates, including child reads, INSERT and parent
UPDATE. Nullable assistant-message authors SHALL NOT replace the requester.

#### Scenario: Opaque conversation and owner isolation

- **WHEN** valid requests select a conversation of tenant B, another user in tenant A, or a nonexistent ID while authorized as user A
- **THEN** GET and valid-body message POST return indistinguishable 404 responses, with no messages, retrieval or writes.
- **AND** invalid message bodies return 422 before lookup for all those IDs.

#### Scenario: Repository invocation and inconsistent children

- **WHEN** a repository is called directly with an unauthorized parent or a child row whose tenant differs from its parent
- **THEN** reads expose no inconsistent/foreign child; writes change neither messages nor parent timestamps.
- **AND** a rejected INSERT/update rolls back together; no automatic legacy repair is implied.

### Requirement: Persisted job identity governs asynchronous execution

The producer SHALL publish the authorized tenant and persisted creator.
Before accessing state for replay/transitions or calling a pipeline, LLM or
vector store, the consumer SHALL validate the message, correlate job ID, tenant
and creator against the persisted job, and revalidate the creator's existence
and current tenant membership. Accepted execution content SHALL come from that persisted job;
duplicated controls and any payload copies used SHALL match it semantically.

#### Scenario: Coordinated envelope tampering

- **WHEN** an attacker substitutes job ID, creator, tenant in both envelope and body, source, artifact or execution content
- **THEN** correlation or consistency validation rejects the message before running/failed/completed updates or any pipeline/write; no foreign job is changed.
- **AND** agreement between two queue fields alone never authorizes execution.
- **AND** rejection is permanent: the message is discarded without requeue and the persisted job row is preserved.

#### Scenario: Valid delivery and isolated retry

- **WHEN** a persisted job, tenant and creator match the message and the creator still exists with current tenant membership before execution
- **THEN** its document, chunks and embeddings retain exactly that tenant; status transitions also constrain job ID, tenant and creator and check affected rows.
- **AND** retries/conflicts cannot reassign another tenant's data; SQL/vector are not claimed to form one transaction.

#### Scenario: Legacy message or authorization revoked before execution

- **WHEN** a delivery lacks a creator, its creator has been removed, its membership was revoked before execution, or its envelope is permanently invalid
- **THEN** the consumer permanently rejects and discards that message before state access/transitions or pipeline work, without rewriting or deleting the persisted job row.
- **AND** no silent legacy acceptance, indefinite permanent-error requeue, queue purge, implicit DLQ or new retry infrastructure is authorized.
- **AND** request correlation is validated/generated separately and is never authorization.

#### Scenario: Completed replay requires a consistent authorized context

- **WHEN** job, tenant, creator, duplicated controls and any execution copies used match persistence and the creator still has current membership, and the job is already completed
- **THEN** replay ends without pipeline execution or rewriting state, results, documents, chunks or embeddings.
- **AND** an inconsistent or unauthorized context is permanently rejected without changing that completed job; completed status does not bypass validation.

#### Scenario: Transient failure remains retryable

- **WHEN** an otherwise valid delivery encounters a transient dependency or execution failure
- **THEN** that failure remains retryable with isolation and context revalidation on the next delivery; it is not treated as a permanently invalid message.
- **AND** this contract introduces no retry limit, backoff policy, DLQ or new retry infrastructure.

#### Scenario: Revocation during an already running job

- **WHEN** membership is revoked after the validated job has already started running
- **THEN** this contract does not guarantee instantaneous revocation or immediate cancellation of that execution.
- **AND** any subsequent delivery revalidates the persisted job, tenant, creator and current membership before state or pipeline access.

### Requirement: Existing cost persistence enforces scope on every operation

Cost run and record repositories SHALL require authorized execution tenant and
subscription, including reads, failure cleanup, conflict updates and successful
completion. Deterministic IDs and globally keyed foreign keys SHALL NOT replace
scope predicates. For manual cost ingestion, scope SHALL be selected under the
approved trusted administrative boundary: an authorized administrator controls
CLI/runtime credentials and is responsible for checking the tenant-subscription
relationship. This is not session authorization or automated Azure ownership
verification. Operator trust SHALL NOT bypass repository isolation.

#### Scenario: Cross-scope run conflict or lookup

- **WHEN** start/fail/fetch is invoked using a run ID owned by another tenant or subscription
- **THEN** no foreign row is returned, reset, deleted or updated, with a generic internal denial/no-result.

#### Scenario: Completion requires a scoped parent

- **WHEN** completion targets a missing/foreign run or encounters an ownership conflict or unexpected affected-row count
- **THEN** the transaction creates no cross-scope records and rolls back its deletes/inserts.
- **AND** a retry within the same authorized scope remains idempotent.

#### Scenario: Manual cost ingestion is a trusted administrative operation

- **WHEN** a trusted administrator uses the manual cost CLI with control of its runtime credentials
- **THEN** that administrator is responsible for checking and selecting the tenant-subscription pair; the system does not detect an incorrect relationship selected by that administrator.
- **AND** syntactically valid IDs or upstream simulator credentials are not claimed as verified Azure ownership or CLI session authorization.
- **AND** this boundary introduces no end-user cost entry through UI/API, allowlist, new roles/auth identity, subscription registry or automated relationship check; a frontend/API/persistence relationship manager remains only a possible post-MVP improvement.

#### Scenario: Administrative trust does not authorize a foreign run

- **WHEN** the manual operation or a direct repository call uses a run ID belonging to a different tenant or subscription than its selected scope, including during a collision or retry
- **THEN** reads, writes, deletes and conflict updates retain scoped predicates, parent checks, transactional rollback and affected-row checks; the foreign run and its records remain unchanged and undisclosed.

### Requirement: Document replacement and retrieval preserve tenant ownership

Document, chunk and embedding writes SHALL enforce ownership through the
document parent, including replacement, uniqueness conflicts and concurrency.
Retrieval SHALL filter by tenant before ranking/limiting or exposing candidates.

#### Scenario: Foreign document collision and rollback

- **WHEN** a write/retry attempts to reuse another tenant's document/job ID
- **THEN** it cannot delete, reparent or replace that document or its children, including under concurrent attempts.
- **AND** a failed same-tenant replacement rolls back without damaging the prior document.

#### Scenario: Nearest vector belongs to another tenant

- **WHEN** tenant B has closer vectors than tenant A for A's query
- **THEN** every candidate, snippet, citation and final response context belongs to A, including empty results when A has no match.

### Requirement: Model and user data cannot substitute authorization

The current graph SHALL retain validated context independently of metadata,
document text and model insight. Future JUP-084 tools SHALL receive tenant,
user, roles and correlation from trusted runtime, outside model arguments.

#### Scenario: Existing pipeline substitution attempt

- **WHEN** metadata, prompt or model output supplies different tenant/user/job identifiers
- **THEN** store calls and job transitions retain the correlated persisted context, or execution is rejected without foreign effects.

#### Scenario: Future tool authority arguments

- **WHEN** a future enabled tool receives tenant/user/roles authority fields as model arguments
- **THEN** strict argument validation rejects the call before querying; subscription scope outside the runtime tenant returns generic `forbidden` without existence disclosure.
- **AND** no tool registry, provider or tool implementation is delivered by this specification phase.

### Requirement: Existing hierarchy and future cost consumers inherit isolation contracts

Existing JUP-014 normalized hierarchy persistence and future JUP-026 KPI
consumers SHALL authorize scope before relationship traversal, enumeration,
aggregates or caches. This requirement does not create endpoints, permissions,
hierarchy schema, a tenant-subscription authority registry or KPI calculations.
JUP-026 and JUP-084 implementation and evidence belong to their future changes
and SHALL NOT block JUP-086 closure for the approved existing scope.

#### Scenario: Reused dimensions and subscription identifiers

- **WHEN** two tenants share logical subscription/resource/project names or dimension values
- **THEN** relationships, conflict handling, costs and cached/aggregated outputs remain tenant-scoped; analytic hierarchy alone does not grant access.
- **AND** existing `resource_id`, `resource_name` and `resource_group_conflicts` retain their persisted tenant/subscription scope; cross-run hierarchy validation RF-014-001 remains Open.

#### Scenario: Future opaque resource endpoint

- **WHEN** a later change introduces job/document/chunk/message-ID reads or mutations
- **THEN** it must define visibility and test foreign/nonexistent IDs with the same 404 after valid authorization/schema checks; absent endpoints are not counted as implemented coverage.

### Requirement: Denials and operational surfaces do not disclose foreign data

Isolation failures SHALL expose only generic outcomes and safe correlation.
Logs SHALL exclude foreign identifiers/content, payloads, tokens, raw SQL and
exception data that could reveal them. Public operational business aggregates
from job counts SHALL NOT be queried or exposed by processor `/health`.
Processor health SHALL retain dependency status semantics; existing `/metrics`
and Prometheus/Grafana monitoring SHALL remain unchanged.

#### Scenario: Error and log sanitization

- **WHEN** API, persistence, worker or provider fails with foreign markers embedded in input or exception causes
- **THEN** responses and all log sinks contain no such markers, tokens or foreign existence details; untrusted request IDs are not logged verbatim.

#### Scenario: Processor health reports dependencies without global job counts

- **WHEN** processor `/health` in `apps/processor/app/api/routes/health.py` evaluates its dependencies
- **THEN** it retains database, RabbitMQ and vector-store `ok`/`failed` statuses and the existing aggregate `ok`/`degraded` semantics, without a `jobs` aggregate in the response.
- **AND** it does not call `fetch_job_counts()` or any replacement global job-count query; removing only the response field does not satisfy this contract.
- **AND** `/metrics`, Prometheus/Grafana and monitoring configuration remain unchanged; implementation and regression evidence remain pending.

### Requirement: Isolation acceptance requires real isolated dependencies

Negative evidence SHALL cover HTTP, repositories, worker, retrieval and logs
with separate users/tenants and real disposable CockroachDB, pgvector and
RabbitMQ, using the bounded acceptance table. Representative evidence MAY be
reused when its source, assertions, runtime and results are auditable and
match the current behavior; mocks alone, skipped integrations or document
validation SHALL NOT count as full isolation acceptance.

#### Scenario: Representative verification of retained behavior

- **WHEN** retained behavior is evaluated for closure
- **THEN** reviewers SHALL map each necessary boundary to the table's evidence or bounded pending check; an untested independent safety behavior remains pending, not passed.
- **AND** closure SHALL NOT require a full OS/failure Cartesian matrix, a new numeric test target or newly versioned duplicates of auditable matching evidence. Optional deeper checks retain explicit unverified risks; behavioral requirements and code QA gates remain mandatory.

#### Scenario: Planning-only delivery

- **WHEN** this OpenSpec change is reconciled before human pre-code approval
- **THEN** no product/test code is changed or executed, no migration/dependency is introduced, and functional acceptance remains pending.
- **AND** later Red/Green/mutation and real dependency checks use the bounded plan in design.md without shared migrations or clock changes.

### Requirement: RF-086-003 publication has a bounded owning lifecycle

The backend SHALL use one managed Pika SelectConnection owner thread per
lifespan/process with the numeric bounds and named Pika I/O-service/transport interfaces
in design.md. The owner SHALL service events while idle and while awaiting
confirms; all connection/channel/abort operations SHALL occur on that owner.
Admission SHALL be bounded and outcomes SHALL be immutable per ticket.

#### Scenario: Idle connection and broker restart in the same API process

- **WHEN** the same backend instance publishes, remains idle longer than two negotiated heartbeat intervals, and receives another request
- **THEN** the first post-idle request confirms without a stale-connection 503 while the broker is healthy; owner events continue during idle.
- **WHEN** the isolated broker restarts or disconnects the publisher
- **THEN** bounded reconnect recreates channel/declaration/confirm mode; a subsequent request in the same API process can confirm, without replaying an attempted message.

#### Scenario: Confirm withheld while heartbeats and close withholding continue

- **WHEN** Basic.Ack is withheld after send while heartbeats continue and the broker also withholds CloseOk
- **THEN** the owner timer expires within min(5 seconds, ticket time remaining), fixes unknown, aborts its captured transport through the named interface and remains able to reconnect; no blocking publish remains stuck behind a timed-out Future.
- **AND** no private socket access or cross-thread close is used; shutdown resolves waiters and joins within 5 seconds under a functioning scheduler.

#### Scenario: Concurrent admission and withdrawal race

- **WHEN** concurrent authorized requests exceed 16 live reservations/tickets or encounter stopping/dead owner
- **THEN** excess admission returns sanitized 503 without job INSERT or publish; at most one message is in flight per connection generation.
- **WHEN** deadline, local cancellation or stop races the owner send boundary
- **THEN** a withdrawal before IN_FLIGHT prevents every later send of that ticket; after that boundary the outcome is unknown unless a definitive result won first, with no automatic replay.
- **AND** all paths release reservations once, isolate request contexts and reject late confirmations from an obsolete generation.

#### Scenario: Startup, blocked connection and shutdown

- **WHEN** lifespan starts with an unavailable broker or a connection becomes blocked
- **THEN** the owner starts without import-time I/O, uses finite setup/backoff/blocked timers and reports no false publisher readiness; requests respect their 10-second ticket budget independently of SQL latency.
- **WHEN** shutdown or partial startup cleanup occurs in setup, idle or in-flight state
- **THEN** new admissions stop, unsent tickets resolve not_sent and sent unresolved tickets resolve unknown; workflow/transport abort and successful loop cleanup leave no owner thread or connection behind, with no queue drain after failure.

### Requirement: RF-086-003 DNS uses an owned terminable child

After its separate pre-code gate, the backend SHALL override getaddrinfo on
the existing SelectConnection adapter and return its own AbstractIOReference.
The narrow exception SHALL name the INTERNAL SelectorIOServicesAdapter,
AbstractIOServices, AbstractIOReference and nbio stream protocol/transport
interfaces. It SHALL NOT use private attributes or monkeypatch Pika.
Only the owned child SHALL call socket.getaddrinfo; Pika SHALL retain connection
sockets, TLS and AMQP. The trusted child SHALL use the direct Windows base
interpreter or actual resolved Linux interpreter, isolated flags, no shell,
no app boot/descendants, minimal environment and bounded JSON pipes from
design.md. A single tracked non-daemon supervisor SHALL own process resources.

#### Scenario: Owned child blocked in DNS during close and retry

- **WHEN** a real spawned fixture blocks inside the child resolver during immediate close or setup-expiry/retry
- **THEN** successful close requires the child dead and reaped, pipes closed and no owned helper/connection/loop remaining; a new generation cannot begin before the old generation's resources are cleaned.
- **AND** the two existing DNS regression intents remain required; a parent-only getaddrinfo monkeypatch does not prove child blocking or compliance.

#### Scenario: Cancel races launch, result and callback delivery

- **WHEN** cancellation occurs before spawn, during Popen, after ready/result or before owner delivery
- **THEN** the application reference fixes cancellation once, suppresses all subsequent on_done delivery and retains any starting/live child until terminate/kill/reap completes; a late Popen return cannot start resolution or escape accounting.
- **AND** owner-local token/generation checks reject stale completions, and successful completion wins at most once only after validated output and child cleanup.

#### Scenario: Process identity and data fidelity

- **WHEN** supported Windows and Linux deployments start the resolver, including a backend running in a Windows venv
- **THEN** the launched PID matches the PID performing DNS, with no redirector/grandchild or remaining descendants; metadata alone is insufficient evidence.
- **AND** host/port/family/type/proto/flags and ordered IPv4/IPv6 sockaddr values retain their meaning, including flowinfo/scope_id; numeric IP and negative DNS work through the same boundary, and TLS keeps the original hostname, SNI and certificate verification.

#### Scenario: Untrusted or incomplete child output

- **WHEN** IPC is partial, truncated, oversized, malformed, duplicated, outside its schema/error whitelist, or the child crashes or reports a different PID
- **THEN** bounded parsing rejects it, suppresses success and cleans or retains accounted failure; no raw content/cause chain escapes in logs or existing API errors.
- **AND** child argv/env/input contain no DSN/password/job/payload/token/request ID, application FD/handles or inherited server standard streams.

### Requirement: RF-086-003 resolver resources and deadlines are aggregate

The backend SHALL enforce the exact process-wide caps and absolute budgets
in design.md: one supervisor, two non-borrowable child slots (publisher/probe),
one active probe and at most four FIFO waiting probes. STARTING and REAPING
SHALL consume slots. All ping instances SHALL use the same registry, retain
independent Pika connections/results and preserve dependency-only semantics.
No cache, resolver service, dependency, settings, fixed IP or TLS bypass is
introduced. Ticket/setup/close bounds SHALL NOT restart at each DNS stage.

#### Scenario: Concurrent probes cannot monopolize publication or starve peers

- **WHEN** publisher setup and repeated concurrent ping calls contend
- **THEN** publisher keeps its reserved slot, cleanup precedes spawning, ready classes alternate, waiting probes are FIFO without overtaking and each completes or expires within its original budget; excess admission returns false immediately.
- **AND** waiting probes allocate no extra loops/helper threads; probe success neither completes nor replays a publication.

#### Scenario: Shared budgets preserve owner progress

- **WHEN** DNS admission, spawn, pipe transfer, connection setup and cancellation consume time
- **THEN** the design's 2.5-second DNS deadline and 0.5-second DNS cleanup reserve fit setup 5 seconds; ticket remains 10 seconds, probe includes FIFO and cleanup in 5 seconds, and shutdown shares one 5-second deadline across owners/probes/supervisor.
- **AND** the 100 ms Pika owner loop performs no resolver/pipe/process wait; 0.5-second launch/ready and later stages cannot extend outer budgets, and no application promise is inferred from the separate Docker health timeout.

#### Scenario: OS launch or termination cannot finish within budget

- **WHEN** process creation remains uninterruptible, termination/reap fails or exit cannot be established by the shared deadline
- **THEN** outstanding launch/process/pipe/slot references remain owned, new admission and replacement stop, ping is false and close raises the existing sanitized cleanup failure rather than claiming zero helpers.
- **AND** the one supervisor is not abandoned or replaced, cleanup continues if OS permits, successful repeated close still requires actual zero resources, and ticket outcomes stay immutable with no automatic replay.
- **AND** clean-close timing assumes operational OS launch, scheduling and termination; process isolation is not a formal guarantee under arbitrary OS failure and does not weaken the zero-helper criterion for any successful close.

#### Scenario: Compatibility and real acceptance remain separate gates

- **WHEN** the DNS implementation is verified after approval or a later Pika/Python upgrade is considered
- **THEN** real Pika compatibility, child PID/cleanup on Windows and Linux, IPC/security/cancellation/fairness and scoped mutations SHALL have representative evidence as defined in the bounded table; an upgrade requires revalidation of affected boundaries.
- **AND** auditable unchanged evidence MAY be reused, including real TLS evidence distinct from handoff inspection. Synthetic peers and simulated OS failures prove only their stated boundaries; required live checks, technical re-review, code QA and final human approval remain separate gates.

### Requirement: RF-086-003 confirms determine explicit publication outcomes

Publication SHALL use persistent messages, the existing durable queue/default
exchange, mandatory routing and publisher confirms. Only a matching positive
ack without return SHALL mean confirmed. Loss of certainty after the send
boundary SHALL mean unknown, never definitive failure. Negative confirmation
or return SHALL mean rejected; proven withdrawal before send SHALL mean
not_sent. The publisher SHALL NOT automatically retry an attempted message.

#### Scenario: Ack, negative confirm and mandatory return

- **WHEN** the matching ack arrives without a return
- **THEN** resolve confirmed; an async publish method returning normally alone is not success.
- **WHEN** Basic.Nack or Basic.Return arrives, including Return followed by Ack
- **THEN** resolve rejected and never 202; preserve any worker progress, since broker rejection is not proof that no execution effects occurred.

#### Scenario: Connection loss or confirm timeout after possible delivery

- **WHEN** publish crossed IN_FLIGHT and a connection loss, timeout, cancellation or shutdown prevents a definitive confirmation
- **THEN** return unknown without resending; ignore late ack for response/state purposes and retire that connection generation.
- **AND** a legitimately delivered job may still execute after the HTTP error; no exactly-once or safe automatic POST retry is claimed.

### Requirement: RF-086-003 SQL records publication without overwriting execution

New admitted jobs SHALL initially persist publish_pending and a fixed pending
publication indication in existing result JSONB. A parameterized CAS SHALL
constrain id, tenant_id, created_by and expected publish_pending state, mapping
confirmed to queued, not_sent/rejected to publish_failed, and unknown to
publish_unknown. No schema migration or new reconciliation policy is implied.

#### Scenario: Worker wins a publication update race

- **WHEN** a worker reaches running, completed or failed before any publisher result is stored
- **THEN** the publisher CAS affects zero rows, verifies only the same persisted identity and leaves status/result/timestamp untouched; it cannot overwrite worker results or another tenant/creator.
- **AND** unexpected zero/multiple-row or SQL failures never cause an unscoped fallback or broker republish.

#### Scenario: Unknown delivery executes under the existing authorization

- **WHEN** a delivered job is still publish_pending or publish_unknown and persisted identity, execution copies and current creator membership validate
- **THEN** the existing worker may mark running and later completed/failed, replacing transient publication result as usual.
- **AND** a revoked/deleted creator or tampered envelope is rejected without state changes; completed replay and legacy failed-job retry semantics remain unchanged.

#### Scenario: SQL finalization fails or the process crashes

- **WHEN** SQL cannot record a known publication result
- **THEN** return publication_state_unavailable with the known publication_outcome, never report 202 or downgrade ambiguity to definitive failed; publish_pending may remain as an explicit unresolved indication.
- **WHEN** the process crashes between DB commit, broker handoff, confirm and HTTP response
- **THEN** the residual database-broker/response window is admitted; no outbox, automatic reconciliation, guaranteed eventual execution or SQL-broker atomicity is claimed.

### Requirement: RF-086-003 API and diagnostics preserve isolation

202 SHALL retain the existing success shape and require confirmed publication
plus stored publication status or verified scoped worker progress. All other
publication outcomes SHALL return the bounded 503 shape in design.md, preserving
the detail string and adding a fixed code, this request's job_id or null, and
retryable=false. HTTP disconnect SHALL NOT introduce job cancellation.

#### Scenario: Sanitized errors and membership before admission

- **WHEN** auth, selector, membership, schema or tenant mismatch rejects a request
- **THEN** existing precedence applies before reserve/INSERT/publish, without revealing another job ID.
- **WHEN** publish/setup/close/SQL fails with secrets, broker reason or foreign markers
- **THEN** HTTP errors stay within 512 bytes and fixed fields; responses and logs contain no raw exception, SQL, payload, URL, token or foreign data, including Pika and owner-thread sinks.
- **AND** only confirmed acceptance increments the existing acceptance counter; no frontend, KPI/tool, endpoint or monitoring expansion is required.

#### Scenario: Dependency health is not a delivery receipt

- **WHEN** the independent health probe connects successfully while the publisher is recovering or an earlier delivery is unknown
- **THEN** dependency health may remain green without completing, retrying or changing that publication; no business counts, delivery guarantee or Prometheus/Grafana changes are introduced.

#### Scenario: Incremental evidence is independent of historical isolation results

- **WHEN** the retained increment is evaluated under the reconciled verification contract
- **THEN** semantic Red/Green, targeted mutation and real isolated RabbitMQ/Cockroach evidence SHALL be mapped to the current code and bounded acceptance table, reusing applicable results and completing its pending checks before code QA and final approval.
- **AND** original-isolation totals or exceptions alone do not prove RF-086-003. Representative evidence suffices for shared decisions; historical unconditional matrices are superseded as verification demands, without weakening any functional scenario or treating untested combinations as passed.
