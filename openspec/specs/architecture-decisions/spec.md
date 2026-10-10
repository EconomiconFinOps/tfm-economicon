JUP: JUP-061
Trello: https://trello.com/c/qXoHFxyy

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

### Requirement: Decision register is traceable and non-duplicating

The project SHALL maintain docs/adr/README.md as the canonical decision inventory,
linking each record to its date, recorded status, accountable source task, rationale,
alternatives and approval evidence or an explicit pending approval.

#### Scenario: Reader prepares the memory or a tutor response

- **WHEN** a reader consults a technical choice
- **THEN** the inventory links the existing authoritative decision and its evidence
- **AND** it does not create a second copy of the decision or memory text.

### Requirement: Approval and implementation evidence remain distinct

The project SHALL distinguish recorded ADR status, human approval, integration and
historical validation, and SHALL identify retrospective rationale as such.

#### Scenario: Implementation is merged while the ADR is still proposed

- **WHEN** an implementation pull request is merged without explicit ADR ratification
- **THEN** the register preserves the recorded ADR status and links the merge separately
- **AND** it identifies the pending ratification without attributing a new human approval.

#### Scenario: Evidence belongs to an open pull request

- **WHEN** a decision or validation exists only in an open pull request
- **THEN** the register links a dated commit and marks the evidence as not integrated.
