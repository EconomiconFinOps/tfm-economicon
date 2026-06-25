## ADDED Requirements

### Requirement: Architecture decisions use ADRs

The project SHALL record durable, cross-cutting architecture decisions as ADR files under `docs/adr/`.

#### Scenario: Contributor records a durable architecture decision

- **WHEN** a HU introduces or changes a durable architecture decision
- **THEN** the contributor creates or updates an ADR and links it from the HU `design.md` or `review.md`.

### Requirement: ADRs remain tied to OpenSpec source of truth

The project SHALL keep accepted architecture decisions in Git/OpenSpec documentation, not only in Engram memory.

#### Scenario: Engram contains architecture context

- **WHEN** Engram contains context that affects an architecture decision
- **THEN** the contributor reflects the final decision in an ADR, OpenSpec artifact, or Git-tracked documentation.

### Requirement: ADRs are not required for local implementation details

The project SHALL keep ADR usage lightweight by requiring ADRs only for durable or cross-cutting architecture choices.

#### Scenario: Contributor makes a local implementation decision

- **WHEN** a decision is local to one HU and has no durable cross-HU architecture impact
- **THEN** the contributor may record it only in `design.md` and mark ADR as not applicable during review.
