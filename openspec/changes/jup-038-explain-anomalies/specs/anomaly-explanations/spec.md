## ADDED Requirements

### Requirement: Explain the observed rule match
The service MUST explain selected JUP-030 v1 alerts in Spanish from server-derived
evidence, retaining amounts as decimal strings, rule thresholds, UTC half-open
periods, currency, quality, source, and evidence identity.

#### Scenario: Two triggered rules
- **WHEN** an alert reaches its absolute threshold and satisfies the percentage and minimum-increase rule
- **THEN** both rules and their numeric evidence are explained without inferring a cause or a saving

#### Scenario: Rounded percentage at boundary
- **WHEN** a displayed percentage rounds to a threshold but the exact ratio does not reach it
- **THEN** the explanation preserves the untriggered state and does not claim that rule was met

### Requirement: Preserve uncertainty and snapshot identity
The service MUST distinguish a rule match from a demonstrated cause and MUST
retain unverified completeness, provisional quality and missing/nonpositive
baselines. It MUST reject stale, incompatible or inconsistent evidence.

#### Scenario: Evidence changed since detection
- **WHEN** reevaluation returns the same anomaly ID with a different evidence ID
- **THEN** the route returns 409 and writes no explanation

#### Scenario: Incomplete baseline
- **WHEN** an absolute-rule alert has no usable baseline
- **THEN** its explanation states that the increase cannot be evaluated without claiming zero or infinite growth

#### Scenario: Detector unavailable
- **WHEN** JUP-030 is absent or unavailable
- **THEN** the route returns 503 without a demo fallback or invented explanation

### Requirement: Authorized conversation evidence
The route MUST authenticate the user and active tenant and verify conversation
ownership before evaluating anomalies. It MUST persist the selected evidence
with the assistant answer, separately from corpus citations.

#### Scenario: Foreign conversation
- **WHEN** an authenticated user requests an explanation in another user's conversation
- **THEN** the route returns 404 before reading costs or writing messages

#### Scenario: Reopen history
- **WHEN** the authorized user reopens a conversation with an explanation
- **THEN** the original numeric snapshot and limitations remain available in message metadata
