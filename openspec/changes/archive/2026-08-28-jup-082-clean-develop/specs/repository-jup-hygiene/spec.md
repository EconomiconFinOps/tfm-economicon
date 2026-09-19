## ADDED Requirements

### Requirement: Repository changes reuse the Trello task identifier

Every active OpenSpec change SHALL reuse the `JUP-XXX` identifier of its Trello task in its directory name, proposal and technical design.

#### Scenario: Contributor prepares a traceable OpenSpec change

- **WHEN** a contributor starts work for a Trello task
- **THEN** the change directory uses the matching `jup-xxx-<description>` name and its proposal contains both the matching `JUP-XXX` identifier and a direct Trello card URL.

### Requirement: Repository guidance remains assistant-independent

The repository SHALL document a shared collaboration workflow without requiring personal agent skills, generated assistant commands or an assistant-specific memory service.

#### Scenario: Contributor clones the repository with any development environment

- **WHEN** a team member installs the documented workspace dependencies
- **THEN** the project workflow and OpenSpec validations are available without checked-in personal assistant configuration.

### Requirement: Unrelated executable assets are not tracked

The repository SHALL reject unrelated vendor tools and platform-specific executable binaries from its tracked project files.

#### Scenario: Repository hygiene check encounters a Windows executable

- **WHEN** a platform-specific executable or vendored memory tool is present in non-ignored tracked files
- **THEN** the repository-hygiene command fails and reports the offending path.

### Requirement: Trello remains the sole operational task inventory

The repository SHALL NOT maintain a second active or archived task namespace that duplicates the Trello task inventory.

#### Scenario: Repository hygiene check encounters a duplicate task proposal

- **WHEN** an OpenSpec proposal belongs to a task namespace other than the team-agreed `JUP-XXX` convention
- **THEN** the repository-hygiene command rejects the duplicate proposal.

### Requirement: Existing valid project work survives repository cleanup

Repository cleanup SHALL preserve application behavior, implemented capability specifications, architecture guidance and valid frontend migration research.

#### Scenario: Contributor reviews the cleanup pull request

- **WHEN** the cleanup branch is compared with the existing `develop` branch
- **THEN** product source files remain unchanged, useful OpenSpec capability specifications remain present and the frontend migration spike retains its technical findings while obsolete workflow references are updated.
