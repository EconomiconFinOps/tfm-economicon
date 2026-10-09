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

### Requirement: Tools prepare a draft proposal for their section instead of writing it

A tool or assistant that has both read access to the shared document and the express authorization to read the affected section SHALL, when asked to help with that section, prepare a proposed draft of it, SHALL attach to each figure its source, SHALL mark as pending what has no source, and SHALL hand the draft to the person, who reviews and incorporates it. Having access without the authorization SHALL be treated as having no access. A tool without access or authorization SHALL request the authorization where it is missing, SHALL read nothing, SHALL work only from the text the person gives it and SHALL NOT look for the document elsewhere. Reading another section for context SHALL require the authorization of that section, and text the person pastes SHALL be used only for that request. The location of the shared document SHALL be looked up on the Trello card named in the governance document, not in the repository.

#### Scenario: A tool with access and authorization is asked for a section

- **WHEN** a tool with read access and authorization to read a section is asked to help with it
- **THEN** it returns a draft proposal for that section with each figure and its source
- **AND** it does not write the draft into the document

#### Scenario: A tool with access but without authorization is asked for a section

- **WHEN** a tool with read access but without authorization to read the section is asked to help with it
- **THEN** it requests the authorization from the person who leads that section's card, reads nothing and works only from the text the person provides

#### Scenario: A tool without access is asked for a section

- **WHEN** a tool without read access is asked to help with a section
- **THEN** it works only from the text the person provides and does not look for the document elsewhere

#### Scenario: A draft needs context from another section

- **WHEN** a tool drafting one section needs to read a different section for context
- **THEN** it needs the authorization of that other section as well
- **AND** text that the person pastes from another section is used only for that request and is not edited

#### Scenario: A tool needs the location of the document

- **WHEN** a tool needs to know where the shared document is
- **THEN** it takes the location from the Trello card named in the governance document and not from the repository

### Requirement: The official project brief is the correction reference

The governance document SHALL declare the official project brief as the reference against which every section is written and corrected, SHALL say where its reference copy is kept, and SHALL NOT copy it into the repository. A section and a tool's draft for it SHALL be contrasted with three parts of the brief: the description of that section in the list of memory deliverables, the technical and functional requirements of the brief that affect that section, and the evaluation breakdown in which it falls. A tool's draft SHALL include a coverage list that names each requirement that affects the section and the paragraph that covers it, or marks it as pending. A tool without access to the brief SHALL ask the person for it and SHALL NOT replace it with assumptions. Reading the brief SHALL NOT require the authorization needed to read the memory.

#### Scenario: An author prepares a section

- **WHEN** an author or a tool prepares a section
- **THEN** it is contrasted with the description of that section in the official brief

#### Scenario: A requirement lives outside the section description

- **WHEN** the brief states a requirement that affects a section in a part other than that section's description, such as impact, viability and differentiation for the business case
- **THEN** the draft for that section is also contrasted with that requirement

#### Scenario: A draft shows its coverage

- **WHEN** a tool hands over a draft for a section
- **THEN** the draft lists each affected requirement with the paragraph that covers it or a pending mark

#### Scenario: A tool cannot reach the brief

- **WHEN** a tool without access to the brief prepares a draft
- **THEN** it asks the person for the brief and does not guess its content

#### Scenario: Someone looks for the brief

- **WHEN** a contributor reads the governance document
- **THEN** it says where the reference copy of the brief is kept
- **AND** the repository does not contain the brief

### Requirement: The repository guidelines point to the memory governance document

`AGENTS.md` SHALL contain one reference to the memory governance document under its source-of-truth rules, in neutral wording that names no specific tool, so that every contributor and tool that reads the guidelines is directed to it.

#### Scenario: A tool reads the guidelines

- **WHEN** a tool reads `AGENTS.md`
- **THEN** it finds the reference to the memory governance document
- **AND** the link resolves to an existing file
