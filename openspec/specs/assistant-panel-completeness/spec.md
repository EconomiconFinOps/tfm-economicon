# assistant-panel-completeness Specification

## Purpose
TBD - created by archiving change jup-065-panel-actions-citations. Update Purpose after archive.
## Requirements
### Requirement: Visible next actions
The panel and history SHALL display valid persisted next_actions without executing them.

#### Scenario: Clarification after reload
- **WHEN** a persisted response requests a period and authorized source in next_actions
- **THEN** those requests remain visible after reloading the conversation

### Requirement: Open frozen documentary fragment
The UI SHALL open the selected authorized fragment as inert text and distinguish it from the full document.

#### Scenario: Current citation
- **WHEN** the user opens a source with persisted content
- **THEN** a keyboard-accessible dialog displays that content and available page/section
- **AND** no model-provided URL or HTML is executed

#### Scenario: Historical citation
- **WHEN** a citation only has an excerpt
- **THEN** the viewer displays it with an explicit incomplete-source notice

### Requirement: Reject dangling narrative slots
The renderer SHALL reject detected trailing continuation words without a typed quantity or prose continuation, including at stream completion.

#### Scenario: Documentary quote in a numeric slot
- **WHEN** an inference ends in "el gasto es de" followed by a documentary citation or answer end
- **THEN** the answer is rejected instead of confirmed as complete

#### Scenario: Grounded calculation
- **WHEN** the continuation is an authorized typed calculation
- **THEN** its value and provenance are preserved without browser reconstruction

#### Scenario: Sentence boundary from rehearsal
- **WHEN** adjacent prose ends in sentence punctuation and begins with an uppercase letter without whitespace
- **THEN** render and stream insert one space, preserving existing whitespace and literal citations
- **AND** original concatenation validation and final length limits remain enforced

#### Scenario: Incomplete transition before a citation
- **WHEN** prose ends in comma, semicolon or colon before a citation or answer end
- **THEN** the incomplete candidate is rejected
- **AND** prose or authorized typed continuations remain allowed

