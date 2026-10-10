## ADDED Requirements

### Requirement: Configured model generation
The chat SHALL generate answers through the configured gateway when CHAT_PROVIDER is litellm, preserving tenant-scoped retrieval and existing authorization.

#### Scenario: Supported document answer
- **WHEN** the authorized user asks a question with relevant retrieved evidence
- **THEN** the gateway receives a system instruction and bounded untrusted data
- **AND** the validated generated reply is persisted with source citations and claim metadata

#### Scenario: Mock environment
- **WHEN** mock generation is configured
- **THEN** the interface labels its template replies as non-generative

### Requirement: Grounded claims and abstention
Each generated factual statement SHALL reference evidence supplied by the server and provide a matching literal quote; invalid references, new numeric tokens and malformed output SHALL be rejected.

#### Scenario: Missing evidence
- **WHEN** retrieval returns no context
- **THEN** the chat abstains without a model request or invented citations

#### Scenario: Fabricated source
- **WHEN** a model response cites a source outside the current retrieval or a nonexistent quote
- **THEN** no assistant message is saved and the user receives a controlled error

### Requirement: Existing cost tool integration
Structured cost questions SHALL use the existing tenant-scoped read adapter and retain its cost evidence independently from generated prose.

#### Scenario: Explicit ownership selection
- **WHEN** an authorized user submits an ownership query with generation enabled
- **THEN** the SQL adapter runs for the authorized tenant and its evidence is supplied to the model
- **AND** its full provenance, period, currencies and limitations remain in the persisted reply

### Requirement: Usable failure and history states
The interface SHALL expose loading, empty, insufficient-data and provider-error states, preserve the draft on failure, and allow accessible navigation of cited evidence.

#### Scenario: Provider timeout
- **WHEN** the gateway times out
- **THEN** the user receives a sanitized error and no invented assistant response
- **AND** the draft remains available for an explicit retry

#### Scenario: Persist and reopen
- **WHEN** a generated exchange is reopened from CockroachDB
- **THEN** both messages and citation metadata remain readable
- **AND** another tenant requesting that conversation receives 404
