## ADDED Requirements

### Requirement: HU changes use lightweight OpenSpec workflow

The project SHALL model each HU as an OpenSpec change and keep the workflow lightweight unless risk requires additional ceremony.

#### Scenario: Doc-only HU pilot

- **WHEN** the team validates the first documentation-only HU
- **THEN** the HU is represented by an OpenSpec change with proposal, design, specs, tasks, human approvals, review, and archive.

### Requirement: Human approval gates are recorded

The project SHALL record human approval before execution and after review for each HU.

#### Scenario: Approval before execution

- **WHEN** PRD, technical design, and tasks are ready
- **THEN** the change records a pre-code human approval before execution starts.

#### Scenario: Approval after review

- **WHEN** execution and review are complete
- **THEN** the change records a post-review human approval before archive.

### Requirement: Git and OpenSpec remain source of truth

The project SHALL keep final requirements, decisions, approvals, and review results in Git/OpenSpec documents, not only in Engram memory.

#### Scenario: Engram stores auxiliary context

- **WHEN** Engram captures useful session context
- **THEN** any final decision that affects the HU is also reflected in the OpenSpec change or project documentation.
