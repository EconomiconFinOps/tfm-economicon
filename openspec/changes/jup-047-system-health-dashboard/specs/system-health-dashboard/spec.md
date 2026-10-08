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

### Requirement: Refresh, freshness and session isolation
The panel SHALL initiate one real provider-check action when opened and one for each admitted manual Actualizar action, without render/StrictMode duplication. Automatic refresh every30seconds while visible/mounted with valid scope SHALL perform only non-generative GET diagnostics. It SHALL avoid overlapping calls/retries, use seven-second GET and35-second real-check client waits, show checked_at and provider verified_at separately, mark observations stale/unknown when their age is greater than or equal to 60 seconds (age < 60 seconds remains current) and discard abandoned tenant/session work.

#### Scenario: Open and manual provider check
- **WHEN** the authenticated scoped panel opens, or the operator manually updates after admission permits it
- **THEN** each action initiates exactly one real provider-check intent and shows its pending/result state with its own observation time
- **AND** repeats/renders/extra tabs do not cause duplicate or overlapping unreserved inferences

#### Scenario: Automatic polling does not spend
- **WHEN** the30second refresh runs
- **THEN** only GET diagnostics are requested and no real inference is triggered
- **AND** the real provider verified_at remains unchanged and becomes explicitly stale at exactly 60 seconds and thereafter, while remaining current before that boundary

#### Scenario: Real-check refusal or failure
- **WHEN** budget/cooldown/busy blocks the action or the real request errors/times out
- **THEN** the UI reports that result and preserves the last real verification time only as historical data
- **AND** neither a gateway success nor a recent GET timestamp replaces proof of the attempted provider verification

#### Scenario: Refresh fails after prior success
- **WHEN** a refresh times out or fails after a successful observation for the same tenant/session
- **THEN** any retained data remains labelled with the old update time and a visible failure/stale notice
- **AND** the page does not report the current refresh time as a successful health observation

#### Scenario: Tenant switches while response is pending
- **WHEN** the operator changes tenant or session before an older request settles
- **THEN** prior scope data is removed, prior timers/requests are cancelled or discarded, and only the new scope may populate the panel

#### Scenario: Expired session and forbidden scope
- **WHEN** an authenticated diagnostic request returns401 or403
- **THEN**401 follows existing session-expiry behavior and403 presents access failure without falsely logging out or exposing old tenant data
- **AND** logout/unmount stops diagnostic polling

#### Scenario: Invalid response or unavailable data
- **WHEN** required states/timestamps/counts are invalid or a summary source is unavailable
- **THEN** the panel shows explicit unknown/unavailable information rather than fabricated healthy states or zero activity
- **AND** invalid/future/absent timestamps are not displayed as fresh successful observations

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

#### Scenario: Informational fields unavailable and stale attempts
- **WHEN** informational fields are absent/malformed or GET and POST refer to different attempts/scopes
- **THEN** missing information is shown safely as unconfirmed/unavailable or invalid and only fields from the selected current attempt/tenant are combined
- **AND** expiry at exactly60seconds, cancellation, generation checks and historical failure/refusal labels remain unchanged
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


### Nota de evidencia de implementación — E12

E12 acredita backend afectado y ausencia de nueva generación por GET con pruebas sintéticas, sin cambiar cliente ni sus requisitos/escenarios. La clarificación del prompt no convierte respuestas anteriores en éxito y la liveliness del gateway sigue separada del proveedor. Red143/38, Green214PASS,15kills y controles37/37 no equivalen a aceptación visual, remota o independiente; M5/Alejandro y gates humanos pendientes. El presupuesto vigente y contadorreal4 están en la cabecera; no se inventa un cupo restante.
