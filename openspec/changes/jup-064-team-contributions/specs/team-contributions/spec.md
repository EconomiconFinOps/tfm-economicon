## ADDED Requirements

### Requirement: Contribution evidence stays distinct from assignments
The inventory SHALL show all four members for every open JUP card, its direct
Trello link, current assigned roles, and observed original GitHub action links.
Assignments alone SHALL NOT be presented as completed contributions.

#### Scenario: A member has no imported action
- **WHEN** a card assigns a member but no matching action was collected
- **THEN** the member remains visible with an explicit missing or not imported marker

### Requirement: Evidence preserves provenance and limits
The inventory SHALL link commits, declared coauthors, PR, reviews, test and
documentation artifacts and CI checks with review state and HEAD context. It
SHALL also retain original discussion-comment URLs, public authors and dates
without inferring formal review or validation from comment existence.
Shared checks and file existence SHALL NOT be attributed as individual validation.
Old reviews, role differences and outstanding requests SHALL remain visible.

#### Scenario: A validation review references an older commit
- **WHEN** a titled validation review references a SHA other than the current PR HEAD
- **THEN** its original link is retained with a stale SHA marker and it does not satisfy current-role evidence

#### Scenario: A comment follows requested changes
- **WHEN** a reviewer requests changes and later publishes a comment
- **THEN** the inventory still marks requested changes as pending until approval or dismissal

#### Scenario: Historical participation is recorded in a PR comment
- **WHEN** a team member published a contribution note in the PR discussion
- **THEN** the inventory links the note under its original author and date but does not treat it as a titled validation review

### Requirement: Collection is reproducible and constrained
Trello reads SHALL use only the deployed Economicon integration on DockerServer.
The collector SHALL be read-only, paginate GitHub collections, fail on source
errors, and produce a dated reduced snapshot and deterministic offline report.
It SHALL NOT persist credentials, emails, conversations or review bodies.

#### Scenario: Offline report refresh
- **WHEN** the report is rendered from an unchanged snapshot without live access
- **THEN** its content matches the originally rendered report

### Requirement: Human evidence remains necessary
The guide SHALL describe role reassignment, manual original evidence links,
coverage limits and team contrast before closing stories or the final memory.
The collector SHALL NOT certify acceptance criteria or authorize merging.

#### Scenario: Pairing is recorded outside GitHub
- **WHEN** pairing only exists in a Trello note
- **THEN** the guide allows an original manual link with action, date, person and contrast status without inventing a commit
