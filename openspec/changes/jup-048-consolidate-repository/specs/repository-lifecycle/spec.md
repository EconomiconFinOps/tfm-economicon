## Purpose

Define the canonical repository and auditable lifecycle for permanent, task and
legacy branches after the repository migration.

## ADDED Requirements

### Requirement: Canonical repository and permanent branches
The project SHALL use `EconomiconFinOps/tfm-economicon` as its canonical
repository, `main` as its stable default branch and `develop` as its shared
integration branch.

#### Scenario: Contributor starts a task
- **WHEN** a contributor starts work for a Trello JUP card
- **THEN** the typed JUP branch is created from the current remote develop branch

### Requirement: Auditable promotion path
Task branches SHALL target develop and only develop SHALL target main.

#### Scenario: Task branch targets main
- **WHEN** a task branch opens a pull request directly toward main
- **THEN** repository policy rejects the pull request before merge

### Requirement: Short-lived task branches
The repository SHALL disable merge commits, retain squash and rebase merge, and
automatically delete merged pull-request branches.

#### Scenario: Task pull request is merged
- **WHEN** GitHub completes a squash or rebase merge from a task branch
- **THEN** the remote source branch is deleted automatically

### Requirement: Non-destructive legacy branch audit
Legacy branches SHALL be tested for ancestry against develop before deletion or
reuse, and non-ancestor branches SHALL remain unchanged until separately reviewed.

#### Scenario: Legacy branch is outside develop
- **WHEN** `git merge-base --is-ancestor` reports that a legacy branch is not in develop
- **THEN** the branch is preserved and a separate Trello decision is required

### Requirement: Effective access evidence
Contributor permissions SHALL be verified for the concrete GitHub username
before the project counts that person as an eligible reviewer or administrator.

#### Scenario: Teammate can view the public repository
- **WHEN** a teammate confirms only that the repository is visible
- **THEN** the project keeps write and review eligibility pending until GitHub's permission endpoint confirms it
