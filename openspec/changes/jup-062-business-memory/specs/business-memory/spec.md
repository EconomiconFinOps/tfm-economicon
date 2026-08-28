## Purpose

Define the content, traceability and review contract for the business section of
the Economicon Jupiter project memory.

## ADDED Requirements

### Requirement: Single editable source of truth

The project SHALL identify exactly one collaborative document as the editable
source of truth and SHALL preserve dated PDF and Markdown snapshots for every
formal review checkpoint.

#### Scenario: A reviewer evaluates a checkpoint

- **WHEN** a memory version is submitted for formal review
- **THEN** its source URL, export date, PDF page count and file hashes are recorded

### Requirement: Complete business-case coverage

The business section SHALL cover opportunity, target users, current
alternatives, market evidence, value proposition, differentiation, viability,
expected impact, costs and risks.

#### Scenario: A required topic is missing

- **WHEN** the content audit finds no supported statement for a required topic
- **THEN** the section remains in progress and the missing topic is listed as a task

### Requirement: Evidence and hypothesis discipline

Every external numerical or market claim SHALL cite a traceable source, and
unvalidated segment, demand or impact claims SHALL be labeled as hypotheses or
expected outcomes.

#### Scenario: A market statement lacks evidence

- **WHEN** a reviewer cannot trace a claim to a named source
- **THEN** the claim is removed, cited or rewritten as an explicit hypothesis

### Requirement: Page-budget compliance

The complete memory SHALL NOT exceed 20 PDF pages, and the introduction plus
business case SHOULD remain within a four-page working budget.

#### Scenario: A review export exceeds a limit

- **WHEN** the complete export exceeds 20 pages
- **THEN** the memory cannot pass review until the content is reduced

#### Scenario: The business working budget is exceeded

- **WHEN** the introduction and business case exceed four pages
- **THEN** the team documents the page trade-off before accepting the version

### Requirement: MVP-coherent business claims

Business claims SHALL reflect only capabilities demonstrated by the current
Azure public-dataset MVP and its reproducible evidence.

#### Scenario: The memory implies an unimplemented capability

- **WHEN** a claim implies live tenant integration, production readiness,
  automated savings or forecasting without evidence
- **THEN** the wording is narrowed or the claim remains explicitly future work

### Requirement: Attributable team review

The change SHALL record leadership, pairing/coauthoring, content review and
validation evidence using the four rotating roles assigned in Trello.

#### Scenario: Content is complete but a role lacks evidence

- **WHEN** one of the four required roles has no attributable contribution
- **THEN** JUP-062 remains in review and is not marked complete
