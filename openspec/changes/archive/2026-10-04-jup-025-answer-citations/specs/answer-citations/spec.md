## ADDED Requirements

### Requirement: Resolve used document evidence
The assistant SHALL preserve ordered evidence IDs and attach document identity,
title, source, stable reference and the excerpt actually used in each new reply.
Section and page SHALL be included when known and remain null otherwise.

#### Scenario: Only used evidence is cited
- **WHEN** four chunks are retrieved and three are quoted
- **THEN** the reply contains three ordered citations matching those excerpts
- **AND** the unused fourth chunk is not represented as supporting evidence

#### Scenario: Location is unavailable
- **WHEN** original text has no section or the chunk location is ambiguous
- **THEN** section remains null and the document/chunk reference remains available
- **AND** a page number is never invented from plain text

### Requirement: Validate citation authority
The application SHALL validate ownership before generating a response and SHALL
reject unknown or duplicate evidence IDs before saving an assistant message.

#### Scenario: Foreign evidence
- **WHEN** retrieval contains a record outside the active tenant
- **THEN** the assistant is not called and the API returns a sanitized error
- **AND** no assistant answer or foreign excerpt is persisted or returned

#### Scenario: Invalid references
- **WHEN** a reply references an unknown ID or duplicates an ID
- **THEN** the API returns the same sanitized error and saves no assistant reply

### Requirement: Inspect persisted citations
The conversation UI SHALL link cited passages to expandable source evidence and
SHALL retain the original evidence snapshot when a conversation is reopened.

#### Scenario: Reopen an authorized conversation
- **WHEN** the conversation owner reopens the conversation in its tenant
- **THEN** numbered links reveal document, source, available location and excerpt
- **AND** another tenant or conversation owner cannot read that evidence

#### Scenario: Legacy or invalid metadata
- **WHEN** metadata has only old IDs or a malformed or ambiguous citation set
- **THEN** the answer remains readable with an evidence-unavailable indication
- **AND** the UI does not create fabricated or external evidence links

### Requirement: Preserve JUP-024
The change SHALL preserve FinOpsResponse 1.0 and its evidence validation rules.

#### Scenario: Separate processor output
- **WHEN** a processor returns structured FinOps metrics or recommendations
- **THEN** existing evidence_ids and JUP-024 validation continue unchanged
- **AND** document citation rendering does not assert that chat runs this pipeline


### Requirement: Parse document locations efficiently and faithfully
Citation resolution SHALL ignore non-document headings, preserve title text and
reuse a single location index per retrieved document within a consistent snapshot.

#### Scenario: Empty or non-document headings
- **WHEN** a document contains empty headings, CRLF, code comments or YAML front matter
- **THEN** only nonempty document ATX headings supply titles and sections
- **AND** the API falls back to source when no title exists without returning 500
- **AND** a trailing hash in a title such as C# remains intact

#### Scenario: Repeated document retrieval
- **WHEN** four retrieved chunks belong to one document with a thousand headings
- **THEN** its full text is fetched once and a single linear-time location index is built
- **AND** both retrieval queries use the same tenant and consistent database snapshot

#### Scenario: Padded source label
- **WHEN** the source contains leading or trailing whitespace
- **THEN** its display in both the cited passage and citation uses the same trimmed value
