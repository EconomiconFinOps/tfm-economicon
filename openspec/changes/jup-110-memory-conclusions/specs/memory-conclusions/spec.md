## ADDED Requirements

### Requirement: Evidence-bounded conclusions

The section i proposal SHALL tie conclusions to dated, versioned evidence and
SHALL distinguish measured outcomes from hypotheses and unverified outcomes.

#### Scenario: Template baseline is available

- **WHEN** a reported run uses template answers and real embeddings
- **THEN** the proposal identifies both conditions and does not describe the run as final generative quality

#### Scenario: Business benefits are unmeasured

- **WHEN** only a proposed protocol or synthetic example supports a benefit
- **THEN** the proposal treats that benefit as unmeasured and does not claim realized savings

### Requirement: Acceptance work and future evolution

The proposal SHALL separate work required to accept the current MVP from
possible evolution after acceptance, without changing the operational backlog.

#### Scenario: Integrated validation is pending

- **WHEN** the integrated generative route or deployed candidate lacks acceptance evidence
- **THEN** the proposal records the pending check without presenting it as an optional enhancement

### Requirement: Governed section-only delivery

Section i SHALL follow project-memory-governance: human review before
publication, external canonical source, no memory copy in Git and no edits to
other sections. The proposal SHALL include coverage of all three brief parts.

#### Scenario: Proposal is ready but not personally reviewed

- **WHEN** the assistant has prepared the proposal and its evidence
- **THEN** it delivers the concrete proposal for human review and leaves canonical publication pending

#### Scenario: Another section would provide context

- **WHEN** reading or editing that section is not authorized
- **THEN** the assistant uses technical evidence and requests only the permitted fragment needed for incorporation

#### Scenario: Whole-document pagination is unavailable

- **WHEN** only the section proposal has been inspected
- **THEN** the global page-limit check remains pending until an authorized export is verified

### Requirement: Verifiable acceptance record

The deliverable SHALL record review and validation against a dated external
export and its SHA-256, independently from the documentation pull request.

#### Scenario: Documentation checks pass

- **WHEN** repository validation passes but the canonical section has not been incorporated
- **THEN** neither the card nor the content acceptance is reported as complete
