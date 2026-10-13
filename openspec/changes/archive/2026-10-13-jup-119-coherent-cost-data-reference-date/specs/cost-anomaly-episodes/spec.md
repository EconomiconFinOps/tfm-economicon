## ADDED Requirements

### Requirement: The synthetic indicator also recognises demo subscriptions

The synthetic indicator that the episode listing returns SHALL be true when a completed ingestion of the active tenant either carries the synthetic mark in its request or belongs to a subscription whose identifier starts with the reserved prefix `synthetic-`, because the demo data are loaded through the ingestion and its request is the query definition, not a synthetic mark. A completed ingestion of any other subscription SHALL NOT set it, and the indicator SHALL remain scoped to the active tenant.

#### Scenario: Demo data loaded through the ingestion
- **WHEN** the active tenant holds a completed ingestion of the subscription `synthetic-anomalies` whose request has no synthetic mark
- **THEN** the episode listing reports the synthetic indicator as true

#### Scenario: An ordinary subscription does not set it
- **WHEN** the active tenant holds only completed ingestions of subscriptions that do not start with `synthetic-` and carry no synthetic mark
- **THEN** the synthetic indicator is false

#### Scenario: Another tenant's demo data do not set it
- **WHEN** only another tenant holds an ingestion of a `synthetic-` subscription
- **THEN** the indicator of the active tenant is false
