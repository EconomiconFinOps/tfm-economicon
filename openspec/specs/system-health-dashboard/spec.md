# system-health-dashboard Specification

## Purpose
TBD - created by archiving change jup-047-system-health-dashboard. Update Purpose after archive.
## Requirements
### Requirement: Integrated system health page
The application SHALL expose an authenticated `/system-health` page through its existing shell/navigation, with connector diagnostics, tenant job/ingestion summaries and explicit data provenance. It SHALL reuse the application's cards, buttons, typography, spacing and theme tokens and SHALL have no dependency on unmerged JUP-055 code.

#### Scenario: Operator opens the page
- **WHEN** an authenticated operator with an active tenant selects Salud del sistema
- **THEN** the existing Layout remains and the panel presents component states, job/ingestion activity and last diagnostic update
- **AND** health data comes from the operational endpoint rather than demonstration constants

#### Scenario: No active tenant
- **WHEN** there is no active tenant
- **THEN** the page presents the existing tenant-selection pattern and issues no tenant diagnostic request

#### Scenario: Visual and accessible continuity
- **WHEN** the panel is viewed beside existing dashboards at390,768 and1440px or operated by keyboard
- **THEN** card surfaces, spacing, typography, button styles, tokens and focus remain consistent with the application
- **AND** the panel adds no horizontal overflow and every state has visible text beyond color
- **AND** existing StatusPill consumers keep their prior appearance if health-specific tones are added

### Requirement: Refresh, retained results and visible periodic provider checks
The scoped authenticated panel SHALL initiate one provider-check intent on its logical visible navigation opening and then at600000 ms from the most recently dispatched opening/manual/periodic intent while it remains mounted and visible. Visible30000 ms GET polling SHALL remain non-generative. Hidden or closed panels SHALL initiate no background checks or monitor. Ordinary backend admission,35 s POST and7 s GET waits, scope isolation and non-overlap SHALL remain authoritative. The latest real result SHALL remain dated without a 60 s TTL; later timeout/failure SHALL replace current availability while retaining the last successful response as history.

#### Scenario: Opening and exact periodic boundary
- **WHEN** a valid scoped visible navigation entry opens and its opening POST is dispatched at t0
- **THEN** exactly one intent is created, no periodic POST occurs at t0+599999 ms and one occurs at t0+600000 ms if still eligible
- **AND** the next deadline uses the latest dispatch time rather than GET, render, completion or verified_at

#### Scenario: Hidden pause and resumed visibility
- **WHEN** the panel is hidden before opening or while a deadline is pending
- **THEN** it starts no GET/manual/periodic POST while hidden and pauses timers without restarting an already sent request
- **AND** becoming visible reads GET and sends at most one opening/due intent; an unexpired deadline waits its remaining duration and missed intervals are not replayed

#### Scenario: Manual and simultaneous triggers
- **WHEN** manual Actualizar, opening, periodic deadline or duplicate consumers compete
- **THEN** synchronous scope ownership permits one active POST with one idempotency action; manual dispatch resets nextDue to its own time plus600000 ms
- **AND** in-flight overlap is coalesced, refusals expose their reason without immediate retries and every later actual inference still requires ordinary admission

#### Scenario: Remount and navigation episode
- **WHEN** StrictMode or remount recreates the same navigation entry, or the same history entry is resumed
- **THEN** the existing episode opening mark, last dispatch and deadline prevent another opening POST and a due check is coalesced once
- **AND** a new navigation entry opens one new episode; same-document coordination shares operation ownership without persisting tokens or diagnostic data

#### Scenario: Non-generative polling and retained results
- **WHEN** visible30000 ms GET polling runs or an observation ages beyond sixty seconds
- **THEN** GET alone performs no inference and result/verified_at/check_id remain tied to the real attempt rather than the GET
- **AND** a nullable or legacy UTC expires_at does not impose local expiry

#### Scenario: Retained and contradictory results
- **WHEN** the first valid result arrives, a later real attempt times out/fails or admission refuses without sending
- **THEN** initial unknown becomes the received result, later real timeout/failure becomes the current non-ok result, and refusal is shown separately without fabricating another observation
- **AND** last successful verified_at/check_id remain clearly historical after a contradictory result and pending checking does not claim a new success

#### Scenario: Old GET after client timeout
- **WHEN** a client check times out and an older GET snapshot later arrives
- **THEN** current unknown/timeout and its historical success are not replaced by that old ok
- **AND** only a coherent server result for that dispatched attempt, with last_attempt_at at least dispatch UTC minus1000 ms, or a subsequent completed action can reconcile the timeout

#### Scenario: Scope cleanup and expired session
- **WHEN** unmount, logout, tenant change or session generation change abandons the panel
- **THEN** its timers/listeners are removed, its requests are aborted or ignored and no late result crosses scopes
- **AND**401 follows existing session expiry and403 remains access failure without falsely logging out; no session/tenant means no diagnostic request

#### Scenario: Failed GET preserves dated history
- **WHEN** a GET times out or fails after a prior successful diagnostic
- **THEN** current diagnostic is unknown with a visible failure notice while stored history keeps its original date
- **AND** it does not fabricate new success or spin a paid retry

#### Scenario: Bounded future observations
- **WHEN** a valid UTC observation is within1000 ms future inclusive of one captured reception clock
- **THEN** its original date, component state, label and metric remain mutually consistent, including healthy SIMULADO Azure and live LiteLLM
- **AND**1001 ms or greater future, invalid UTC/calendar or absent required dates are not displayed as healthy; no date is clamped and one invalid component does not erase healthy sibling observations

### Requirement: Separate functional availability identity and cost display
The panel SHALL show availability independently of informational model identity and cost, using the same selected attempt/tenant observation as the existing hook. It SHALL NOT claim verified model identity or confirmed upstream cost from matching names, configured routes or gateway headers. Missing or invalid informational fields SHALL be safely normalized without invalidating otherwise valid availability; invalid functional states/structure/timestamps SHALL retain rejection.

#### Scenario: Available response with unconfirmed model
- **WHEN** a current valid response reports an alias, canonical, versioned or different model name
- **THEN** the provider displays Disponible and Respuesta válida a with its functional verified_at
- **AND** Modelo informado shows only sanitized reported_model or Modelo no informado alongside Identidad no confirmada even for a matching name
- **AND** configured model name or returned spelling is not presented as proof of actual model execution

#### Scenario: Cost does not determine availability
- **WHEN** a valid functional response has gateway-reported, unavailable or invalid cost information
- **THEN** Disponible remains the availability label while cost is shown separately as Coste informado por el gateway with No confirmado, Coste no disponible or Dato de coste no válido
- **AND** estimates and missing/zero costs are not presented as confirmed billing or free calls
- **AND** financial refusal of a later call retains explicit refusal/history semantics without rewriting the earlier result

#### Scenario: Informational fields unavailable and retained attempts
- **WHEN** informational fields are absent/malformed or GET and POST refer to different attempts/scopes
- **THEN** missing information is shown safely as unconfirmed/unavailable or invalid and only fields from the selected current attempt/tenant are combined
- **AND** age alone does not expire observations; cancellation, generation checks and truthful latest-attempt versus historical-response labels remain effective
- **AND** invalid functional responses never display a new successful timestamp

### Requirement: Reproducible validation and required M5 deployment
JUP-047 SHALL retain reproducible tests and independent evidence for healthy, failure, timeout, empty and recovery behavior, isolation and visual continuity. It SHALL also be deployed and observed on DockerServer M5 with the responsible operator, authorized configuration and exact revision recorded. Local isolated Docker evidence SHALL NOT replace that external deployment criterion.

#### Scenario: Isolated local equivalent
- **WHEN** technical scenarios run in an authorized unique local Docker project with synthetic credentials and fake LLM upstream
- **THEN** the evidence identifies the tested sources, real commands/exits, deadlines and recovery
- **AND** shared services remain unchanged and skipped cases are not marked passed
- **AND** fake upstream evidence does not replace the separately budgeted real OpenRouter trial or required M5 deployment
- **AND** currently available M5-related evidence is labelled local simulation; actual DockerServer M5 work remains external-pending with Alejandro and is not claimed completed

#### Scenario: Deployment not yet accessible
- **WHEN** M5 access, configuration or deployment authorization is missing
- **THEN** the required deployment task remains external-pending with its cause, impact and required owner action
- **AND** the change is not accepted as deployed because local tests passed
- **AND** the technical local delivery may proceed separately while Alejandro retains the external check; no SSH is requested and current local simulation is reused without systematic repetition

#### Scenario: Authorized M5 observation
- **WHEN** the approved revision is deployed on M5 under its agreed secure topology
- **THEN** evidence records responsible operator, authorization, exact revision/date, authenticated page/API observations, declared real/simulated sources and rollback procedure
- **AND** the independent validator separately records each card criterion and any untested external-provider behavior

### Requirement: Historical accounting does not rewrite availability or authorize extra calls
The panel SHALL retain the first attempt as historical evidence without retroactive PASS or fabricated reconciliation. Historical uncertainty SHALL NOT by itself prevent an otherwise admitted new explicitly authorized action; ordinary backend admission remains authoritative. Cost/provenance SHALL remain informational and separate from availability.

#### Scenario: New action after historical uncertain attempt
- **WHEN** the ordinary backend admits a separately authorized action while retaining all previous reserves/history
- **THEN** the panel displays the selected new attempt with its own pending/result/time and independent cost/identity information
- **AND** it does not reuse an earlier attempt as current success, discard historical reserves, reset the cumulative allowance or trigger any extra unrequested inference

#### Scenario: Remaining ordinary gate refuses action
- **WHEN** cooldown, active operation, cumulative call limit, insufficient capacity or invalid current preflight refuses the action
- **THEN** the existing explicit refusal and historical-time semantics remain and polling performs no inference
- **AND** no special financial override or reconciliation claim is shown

### Requirement: Local delivery and external deployment evidence remain distinct
The technical local delivery SHALL reuse current applicable local simulation evidence and repeat only affected checks or process-required controls. Real DockerServer observation SHALL remain Alejandro's external pending check, with no SSH request or automatic repetition of local simulation. The official remote deployment criterion SHALL remain pending until actually demonstrated.

#### Scenario: Local correction delivered while remote observation is pending
- **WHEN** local correction evidence is delivered with current local simulation and affected independent review/validation
- **THEN** local results and the external DockerServer pending check are reported separately
- **AND** local simulation is not labelled remote deployment PASS and no official criterion is deleted or self-approved

### Requirement: Gateway compatibility does not relax provider verification
The panel SHALL continue to display the gateway observation separately from real provider availability when the backend adapts LiteLLM liveliness. Clarifying the fixed synthetic request SHALL NOT create a client prompt control, a weaker OK criterion, new polling inference or an implied remote success.

#### Scenario: Gateway becomes healthy while provider response is invalid
- **WHEN** GET reports gateway ok from the exact supported liveliness response and the selected provider attempt is invalid_response including punctuation or extra text
- **THEN** the gateway can display Correcto while OpenRouter remains No verificado with no new successful verified_at
- **AND** model/cost remain informational, updates retain current scope/history semantics and polling causes no inference

#### Scenario: Later real check still needs ordinary admission
- **WHEN** an operator opens or updates the panel after a clarified request is deployed
- **THEN** a single intent remains subject to authorization, cumulative allowance and all financial/frequency/privacy gates
- **AND** insufficient capacity causes explicit refusal without an inference; previous invalid responses do not become success because the prompt changed
