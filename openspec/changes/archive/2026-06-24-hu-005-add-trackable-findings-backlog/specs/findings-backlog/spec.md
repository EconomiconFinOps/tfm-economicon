## ADDED Requirements

### Requirement: Findings backlog exists

The project SHALL maintain a central findings backlog for unresolved, deferred, or accepted-risk findings discovered during HU reviews.

#### Scenario: Review finds an out-of-scope issue

- **WHEN** a HU review detects an issue outside the approved HU scope
- **THEN** the issue is recorded in the HU `review.md`
- **AND** added to `openspec/findings/backlog.md` with a stable ID.

### Requirement: Findings are traceable to origin and fix

Each backlog finding SHALL include enough metadata to trace where it was found and how it will be resolved or closed.

#### Scenario: Finding is added to the backlog

- **WHEN** a finding is added
- **THEN** it includes ID, date, origin, type, severity, scope, status, owner, action, and change/fix.

### Requirement: HU reviews classify findings

HU reviews SHALL classify findings by scope and backlog decision.

#### Scenario: Review is completed

- **WHEN** a HU review is documented
- **THEN** each finding is marked as in scope or out of scope
- **AND** unresolved out-of-scope findings are linked to the central backlog.
