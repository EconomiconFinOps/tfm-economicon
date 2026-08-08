## Purpose

Define the testable repository governance required by JUP-079 without claiming
remote protection before an administrator enables it.

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
Every pull request SHALL contain a JUP-XXX identifier consistent with its
source branch and a direct Trello card URL.

#### Scenario: Mismatched identifier
- **WHEN** the pull-request title and branch contain different JUP identifiers
- **THEN** the required policy check fails before merge

### Requirement: Four rotating roles
Every pull request SHALL identify concrete people for leadership,
pairing/co-authorship, PR review, and validation/tests/documentation.

#### Scenario: Role left pending
- **WHEN** a pull-request role is empty or contains a placeholder
- **THEN** the policy check fails and names the missing role

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
