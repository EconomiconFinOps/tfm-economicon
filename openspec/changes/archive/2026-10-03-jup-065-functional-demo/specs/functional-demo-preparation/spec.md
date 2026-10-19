## ADDED Requirements

### Requirement: Reviewable demonstration plan

The project SHALL provide a timed demonstration route with explicit actions,
expected outcomes, prerequisites, failure handling and a blank rehearsal record.

#### Scenario: The integrated MVP is not ready

- **WHEN** a reviewer reads the preparation package
- **THEN** offline preparation is distinguishable from a completed runtime rehearsal
- **AND** the missing integrated checks remain pending

### Requirement: Fixed reproducible references

The package SHALL pin the dataset, corpus and question inputs to a Git commit,
preserve source hashes and licensing, and calculate a cost reference offline.

#### Scenario: A reviewer reproduces the preparation

- **WHEN** the fixed Git object is available and the verifier runs
- **THEN** all generated files match their committed bytes and inventory
- **AND** public sample costs remain distinct from synthetic prompt inputs

#### Scenario: A generated artifact is altered

- **WHEN** a generated file is modified, removed or added unexpectedly
- **THEN** the verifier exits unsuccessfully without accessing a service

### Requirement: Separate prompts and evaluation keys

Prepared prompts SHALL contain only the selected question IDs and their supplied
context and question, with required and forbidden behavior held separately.

#### Scenario: An operator prepares a chat demonstration

- **WHEN** a selected input is copied into a fresh conversation
- **THEN** the prompt does not include the answer rubric or expected behavior label
- **AND** the operator can evaluate answer, clarification and abstention cases

### Requirement: Bounded acceptance claims

Evidence SHALL distinguish offline integrity, human preparation validation and
integrated functional acceptance without closing the task prematurely.

#### Scenario: Automated offline checks pass

- **WHEN** CI verifies the package without running an assistant or database
- **THEN** runtime and LLM evidence remain not run
- **AND** review, rehearsal and human acceptance are not inferred from CI
