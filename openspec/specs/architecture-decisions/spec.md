## Purpose

Define how Economicon records durable architecture decisions without requiring an ADR for every local implementation detail.

## Requirements

### Requirement: Architecture decisions use ADRs

The project SHALL record durable, cross-cutting architecture decisions as ADR files under `docs/adr/` and link each decision to its Trello task and OpenSpec change.

#### Scenario: Contributor records a durable architecture decision

- **WHEN** a Trello task introduces or changes a durable architecture decision
- **THEN** the contributor creates or updates an ADR and links it from the corresponding OpenSpec `design.md`.

### Requirement: Architecture decisions remain tool-independent

The project SHALL preserve accepted architecture decisions in Git-tracked documentation rather than depending on a personal assistant, local memory service or proprietary agent configuration.

#### Scenario: Contributor accepts an architecture decision

- **WHEN** the team accepts an architecture decision during review
- **THEN** its rationale and consequences are available in an ADR, OpenSpec artifact or other Git-tracked project documentation.

### Requirement: ADRs are not required for local implementation details

The project SHALL keep ADR usage lightweight by requiring records only for durable or cross-cutting architecture choices.

#### Scenario: Contributor makes a local implementation decision

- **WHEN** a decision concerns one Trello task and has no durable cross-task architecture impact
- **THEN** the contributor may record it only in `design.md` and declare `ADR: not applicable`.
