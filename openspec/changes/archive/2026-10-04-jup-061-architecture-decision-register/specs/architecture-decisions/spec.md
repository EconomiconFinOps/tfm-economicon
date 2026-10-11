## ADDED Requirements

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
