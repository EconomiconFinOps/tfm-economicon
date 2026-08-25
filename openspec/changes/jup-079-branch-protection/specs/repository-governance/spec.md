## Purpose

Define and verify the active repository governance required by JUP-079 without
claiming collaborator access or peer approvals that GitHub does not confirm.

## ADDED Requirements

### Requirement: No direct work on protected branches
The repository SHALL require pull requests for main and develop and SHALL block
force pushes and deletion.

#### Scenario: Contributor pushes directly
- **WHEN** a contributor attempts to push a commit directly to main or develop
- **THEN** GitHub rejects the update without changing the protected branch

### Requirement: Controlled promotion
The repository SHALL accept ordinary JUP branches only into develop and SHALL
accept only develop as a pull-request source for main.

#### Scenario: Feature branch targets main
- **WHEN** a typed JUP feature branch opens a pull request toward main
- **THEN** the JUP policy check fails and explains that develop is required

### Requirement: JUP and Trello traceability
Every pull request SHALL contain the same JUP-XXX identifier in its title,
body and source branch, plus a direct Trello card URL.

#### Scenario: Mismatched identifier
- **WHEN** the pull-request title and branch contain different JUP identifiers
- **THEN** the required policy check fails before merge

### Requirement: Four rotating roles
Every pull request SHALL identify concrete people for leadership,
pairing/co-authorship, PR review, and validation/tests/documentation; the four
roles SHALL identify four different people.

#### Scenario: Role left pending
- **WHEN** a pull-request role is empty or contains a placeholder
- **THEN** the policy check fails and names the missing role

#### Scenario: Same teammate occupies multiple rotating roles
- **WHEN** the same person is assigned to two or more pull-request roles
- **THEN** the policy check rejects the missing four-person participation

### Requirement: Administrator continuity without direct pushes
Repository administrators SHALL bypass an unavailable peer approval only
through an auditable existing pull request; the bypass SHALL NOT permit direct
pushes to `main` or `develop`.

#### Scenario: Administrator tries to update a protected branch directly
- **WHEN** an administrator pushes directly to a protected branch
- **THEN** the PR-only bypass does not apply and GitHub rejects the update

### Requirement: Required automated checks
Pull requests to main and develop SHALL pass governance validation, all Python
service tests and the frontend production build before merge.

#### Scenario: Service regression
- **WHEN** any required service test fails
- **THEN** the branch ruleset prevents the pull request from merging

### Requirement: Honest remote state
Documentation SHALL distinguish versioned desired configuration from remotely
activated protection and SHALL require administrator evidence before JUP-079 is
closed.

#### Scenario: No administration permission
- **WHEN** the implementer lacks repository administration permission
- **THEN** local artifacts may be completed but remote activation remains open
