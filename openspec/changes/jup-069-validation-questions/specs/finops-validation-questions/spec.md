## ADDED Requirements

### Requirement: Versioned representative questions

The repository SHALL provide at least 21 Spanish FinOps questions with stable
JUP-069 case IDs, explicit provenance, fixed context, source references and
expected behavior covering costs, allocation, tagging, budgets, anomalies,
recommendations and scope limitations.

#### Scenario: A reviewer prepares a repeatable validation

- **WHEN** the reviewer selects a suite version
- **THEN** each case contains all its synthetic inputs and an answer rubric
- **AND** the suite distinguishes representative questions from customer transcripts

### Requirement: Verifiable answer expectations

Each case SHALL state required and forbidden behavior. Numerical expectations
SHALL include value, unit and absolute tolerance. The suite SHALL cover requests
that can be answered, require clarification or require abstention.

#### Scenario: A baseline or denominator is missing or zero

- **WHEN** a case cannot support a valid numerical answer
- **THEN** its rubric requires acknowledging the limitation instead of inventing a result

#### Scenario: A threshold is exactly met

- **WHEN** a case uses equality at an internal anomaly or allocation threshold
- **THEN** its rubric preserves the documented strict or inclusive comparison

### Requirement: Offline integrity validation

The repository SHALL validate IDs, coverage, nonempty rubrics, source existence
and source content hashes offline, returning a failing exit code on invalid data.

#### Scenario: A reference document changes

- **WHEN** its normalized content hash differs from the stored reference
- **THEN** validation fails and asks for deliberate expectation and version review

### Requirement: Inputs without answer leakage

The preparation command SHALL produce deterministic case prompts containing only
the supplied context and question, with stable IDs and suite version/hash metadata.

#### Scenario: Inputs are prepared for model evaluation

- **WHEN** a valid battery is exported
- **THEN** expected answers, behavior labels and rubrics are absent from the prompts
- **AND** the documented protocol starts an independent conversation for every case

### Requirement: Honest validation evidence

Documentation SHALL separate battery integrity from assistant response quality
and hand off response evaluation to JUP-070 and robustness execution to JUP-071.

#### Scenario: Only offline checks have run

- **WHEN** the suite validator succeeds without invoking an assistant
- **THEN** evidence reports structural success without claiming functional answer quality
