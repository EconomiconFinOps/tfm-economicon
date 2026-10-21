## MODIFIED Requirements

### Requirement: Explicit health sources and semantic states
Operational diagnostics SHALL describe backend API, database, queue, processor API, vector storage, simulated Azure API, LiteLLM gateway and an independently identified OpenRouter observation. Every observation SHALL have a closed id/status/reason and timestamp with declared live/simulated/mock/unverified provenance. Status SHALL be one of ok, degraded, failed or unknown.

#### Scenario: Real provider check distinct from gateway
- **WHEN** an authorized panel opening, visible periodic deadline or manual update admits a provider check
- **THEN** one real synthetic inference is sent through the pinned economicon-chat alias to deepseek/deepseek-v4.1-flash, with disabled reasoning/retries/fallbacks and no user data
- **AND** a valid functional response through the configured route marks OpenRouter ok with its own verified_at independently of returned model spelling or cost information; mock/liveliness cannot satisfy the real-provider requirement
- **AND** configured models/routing, access controls, fixed payload and usage limits remain enforced; returned model name does not certify executed model identity

#### Scenario: Reachable gateway without current real inference
- **WHEN** gateway liveliness succeeds but no real result exists or the latest admitted real attempt failed or timed out
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
