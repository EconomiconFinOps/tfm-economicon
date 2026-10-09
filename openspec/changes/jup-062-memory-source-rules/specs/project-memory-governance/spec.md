## Purpose

Declares where the final project memory lives, who edits which section, how its review is recorded and how tools that read the repository must treat it, so that every contributor and tool follows the same rules.

## ADDED Requirements

### Requirement: The memory has one editable source outside Git

The repository SHALL declare that the final project memory is written in one shared document outside Git, and SHALL name that document and point to the Trello card that links it. The repository SHALL NOT contain a second canonical copy of the memory, whether as Markdown, PDF or any other format.

#### Scenario: A contributor looks for the memory

- **WHEN** a contributor reads the memory governance document
- **THEN** it names the shared document and the Trello card that holds its link
- **AND** it states that the memory is not stored in the repository

#### Scenario: Someone proposes keeping a copy in the repository

- **WHEN** a change adds a copy of the memory, in full or by section, to the repository
- **THEN** it contradicts the declared source and is not accepted as the canonical version

### Requirement: Dated exports are immutable and stay outside Git

Every export of the memory, in both PDF and Markdown, SHALL be dated, SHALL be stored outside Git next to the other final deliverables, and SHALL have its SHA-256 recorded in a manifest. An export SHALL NOT be edited after it is recorded.

#### Scenario: An export is stored

- **WHEN** a PDF and a Markdown export of the memory are stored
- **THEN** the manifest lists a date and a SHA-256 for each of the two files

#### Scenario: The repository is inspected for exports

- **WHEN** the repository tree is inspected
- **THEN** it contains no PDF or Markdown export of the memory

### Requirement: Each memory section maps to a Trello card without copying assignments

The governance document SHALL list every memory section, from the introduction to the conclusions, with the Trello card that owns it, or SHALL state explicitly that the section has no card of its own. It SHALL NOT copy assignees, rotating roles or delivery dates, which Trello owns, and SHALL refer to the card for the person responsible.

#### Scenario: A section has a card

- **WHEN** a contributor looks up a section such as the business case
- **THEN** the document gives the card identifier that owns it

#### Scenario: A section has no card

- **WHEN** a contributor looks up the evaluation or conclusions sections
- **THEN** the document states that they have no documentation card of their own instead of leaving them blank

#### Scenario: The map names no person and no date

- **WHEN** the section map is read
- **THEN** it contains no assignee name and no delivery date

### Requirement: Editing follows the document style guide and traceable sources

Every figure in the memory, including those in tables and in the executive summary, SHALL be traceable to a data point or a cited source. A figure or statement whose source does not yet exist SHALL be marked as pending and SHALL NOT be invented. The memory SHALL NOT exceed 20 pages across all sections. Each section SHALL be written by the person its card assigns, and any change to another person's section SHALL be proposed as a suggestion or a comment, not as a direct edit.

#### Scenario: A figure has no source yet

- **WHEN** an author needs a figure whose source is not available
- **THEN** the figure is marked as pending
- **AND** no value or source is invented

#### Scenario: A figure appears only in a table

- **WHEN** a figure appears in a table and not in the running text
- **THEN** it is traceable to its source in the same way

#### Scenario: Someone wants to change another person's section

- **WHEN** a contributor wants a change in a section assigned to someone else
- **THEN** the change is proposed as a suggestion or a comment

### Requirement: Review and validation of the deliverable are recorded outside GitHub reviews

Because the memory has no diff in the repository, its review and validation SHALL be recorded as comments in the shared document and as a comment on the Trello card, and each record SHALL name the exported version that was reviewed by its date and SHA-256. The `JUP reviews` check SHALL remain applicable only to pull requests. Versioned evidence SHALL live under `docs/evidence/`, and a change about the memory SHALL be closed with a documentation pull request.

#### Scenario: A reviewer records a review

- **WHEN** a reviewer finishes reading an exported version
- **THEN** the record names that version by date and SHA-256 in the document and on the card

#### Scenario: A memory change is ready to close

- **WHEN** the reviewed version is exported and recorded
- **THEN** the change is archived through a documentation pull request

### Requirement: Tools and assistants never search, regenerate or edit the memory unprompted

A tool or assistant that reads the repository SHALL NOT search the repository for the memory, SHALL NOT regenerate it from the repository, and SHALL NOT store a copy or an export of it in the repository. It SHALL NOT read or modify the shared document, or any export of it, without the express authorization of the person who leads the Trello card of the affected section, and that authorization SHALL be given separately for reading and for modifying. Authorization for one section SHALL NOT extend to another. No text SHALL be published to the document before a person reviews it.

#### Scenario: A tool has no authorization

- **WHEN** a tool is asked to work on a section of the memory without express authorization from the person who leads that section's card
- **THEN** it asks for that authorization and does not read or modify the document

#### Scenario: Authorization to read does not allow editing

- **WHEN** a tool has authorization to read the document
- **THEN** it does not modify the document until it also receives authorization to modify it

#### Scenario: Authorization covers one section only

- **WHEN** a tool has authorization to read one section
- **THEN** it does not read or modify any other section, so reading the business case does not allow modifying the architecture section

#### Scenario: A tool reads an export

- **WHEN** a tool is asked to read an export of the memory outside the repository
- **THEN** it needs the same authorization as for the shared document

#### Scenario: A tool drafts text for the memory

- **WHEN** a tool prepares text for the memory
- **THEN** a person reviews it before it is published to the document

### Requirement: The repository guidelines point to the memory governance document

`AGENTS.md` SHALL contain one reference to the memory governance document under its source-of-truth rules, in neutral wording that names no specific tool, so that every contributor and tool that reads the guidelines is directed to it.

#### Scenario: A tool reads the guidelines

- **WHEN** a tool reads `AGENTS.md`
- **THEN** it finds the reference to the memory governance document
- **AND** the link resolves to an existing file
