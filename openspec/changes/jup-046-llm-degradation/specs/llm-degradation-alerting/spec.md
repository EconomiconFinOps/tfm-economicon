## ADDED Requirements

### Requirement: Logical provider observations

Backend query embeddings and processor embeddings and AgentRuntime generation SHALL
expose a counter and latency histogram for real LiteLLM logical operations through
the existing metrics endpoint, including retries and response validation.

#### Scenario: Retry recovers
- **WHEN** an upstream attempt fails and a retry returns a valid response
- **THEN** exactly one successful operation is recorded with total elapsed time

#### Scenario: Provider or response fails
- **WHEN** retries exhaust or the vector or FinOps response is invalid
- **THEN** exactly one terminal failure is recorded with a bounded safe category

#### Scenario: Local configuration or mock
- **WHEN** the provider is mock, required configuration is absent or input is rejected before invocation
- **THEN** no real provider observation or degradation is fabricated

### Requirement: Sustained degradation and recovery

Grafana SHALL provision error and p95 latency rules evaluated every minute per
job, instance and operation with a five minute window and at least five operations.
Errors above 20 percent, embedding p95 above 10 seconds and generation p95 above
20 seconds SHALL enter Pending and fire only after two sustained minutes.

#### Scenario: Error threshold and sample boundary
- **WHEN** errors are exactly 20 percent or fewer than five operations are observed
- **THEN** the degradation rule does not fire

#### Scenario: Sustained latency
- **WHEN** sufficient samples exceed the operation latency threshold for two minutes
- **THEN** its latency rule fires independently of other services and operations

#### Scenario: Recovery
- **WHEN** fresh observations make the condition false after a firing episode
- **THEN** the rule returns to Normal on evaluation without application restart

#### Scenario: Missing telemetry
- **WHEN** the Prometheus expression has no series or the query fails
- **THEN** Grafana displays NoData or Error respectively, distinct from measured degradation

### Requirement: Operator diagnostics and bounded telemetry

The repository SHALL provide a dashboard, runbook and content-free diagnostics
without adding an external notification receiver. Existing health and offline
quality evaluation SHALL remain distinct from observed runtime degradation.

#### Scenario: Investigating an alert
- **WHEN** the operator inspects a firing rule
- **THEN** the operation, target, window, threshold and runbook are available without prompts or credentials

#### Scenario: Safe verification
- **WHEN** automated degradation and recovery tests execute
- **THEN** synthetic observations exercise the actual rule expressions without paid inference or real notifications
