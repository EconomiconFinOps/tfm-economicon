## ADDED Requirements

### Requirement: Scoped AI memory contribution

The JUP-063 contribution SHALL cover only memory sections e and g and SHALL
preserve the external canonical source and the human review gate defined by
project-memory-governance.

#### Scenario: Draft before canonical incorporation
- **WHEN** an AI memory draft is prepared
- **THEN** it is kept outside Git and identified as a proposal, not a canonical export
- **AND** the repository records evidence and pending human acceptance without copying memory content

#### Scenario: Other sections cannot be read with scoped authorization
- **WHEN** the available tool would return the entire memory and authorization covers only e/g
- **THEN** the contributor requests the authorized fragments and does not read the whole body
- **AND** an independent proposal can advance from code and the official brief

### Requirement: Evidence distinguishes real capabilities

The contribution SHALL distinguish implemented paths, configuration, test doubles,
historical measurements and unverified integration, with a dated code reference.

#### Scenario: Retrieval exists but chat generation is absent
- **WHEN** the inspected chat retrieves embeddings and returns a template
- **THEN** the draft identifies the template and does not claim integrated generative RAG
- **AND** any separate ingestion generation path is described with its actual input and output limits

#### Scenario: Model and guardrail claims
- **WHEN** pretrained models or validation guards are described
- **THEN** model aliases and configured dimensions are traceable to the inspected revision
- **AND** structural validation, mock behavior and historical benchmarks are not treated as proof of truth or current model quality

### Requirement: Reviewable coverage and limitations

The proposal SHALL map relevant requirements from the memory section list,
technical/functional conditions and evaluation breakdown to paragraph identifiers
or explicit pending items.

#### Scenario: Document acceptance is incomplete
- **WHEN** the current section text, style reconciliation, reviewed export or pagination is unavailable
- **THEN** that check remains pending with a concrete next step
- **AND** successful local checks do not close the card or impersonate human review
