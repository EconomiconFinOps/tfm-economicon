## MODIFIED Requirements

### Requirement: Dated exports are immutable and stay outside Git

Every export of the memory, in both PDF and Markdown, SHALL be dated, SHALL be stored outside Git, and SHALL have its SHA-256 recorded in a manifest. An export SHALL NOT be edited after it is recorded.

#### Scenario: An export is stored

- **WHEN** a PDF and a Markdown export of the memory are stored
- **THEN** the manifest lists a date and a SHA-256 for each of the two files

#### Scenario: The repository is inspected for exports

- **WHEN** the repository tree is inspected
- **THEN** it contains no PDF or Markdown export of the memory
