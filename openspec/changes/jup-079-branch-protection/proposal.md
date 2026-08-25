JUP: JUP-079
Trello: https://trello.com/c/10RWrMCS

## Why

The canonical repository is `EconomiconFinOps/tfm-economicon`, `develop` now
exists and Alejandro has repository administration access. However, both
integration branches remain unprotected, no CI workflows are registered and
Alejandro is the only currently visible collaborator. Direct pushes, missing
review evidence and untraceable pull requests threaten the October delivery.

## What Changes

- Define the branch flow tipo/JUP-XXX-description to develop to main.
- Add a pull request template with Trello, evidence and all rotating roles.
- Add a local and CI validator for title, branch, target and role traceability.
- Add CI checks for OpenSpec, Python services and the frontend build.
- Version and activate exact GitHub branch rules for `develop` and `main`.
- Allow administrators to bypass missing approvals only through an auditable
  pull request; direct pushes remain blocked for administrators too.
- Keep missing teammate access visible instead of fabricating GitHub accounts
  or counting unavailable approvals.

## Capabilities

### New Capabilities

- repository-governance: versioned and testable pull-request and branch policy.

### Modified Capabilities

- None.

## Out of Scope

- Guessing GitHub usernames or silently granting access to unrelated accounts.
- Adding incomplete CODEOWNERS entries for unconfirmed team identities.
- Claiming review approval or collaborator participation that GitHub does not
  record.

## Impact

Adds GitHub workflow files, versioned rulesets, pull-request metadata, policy
tests and administrator documentation. Remote activation is verified using the
GitHub API; outstanding teammate access remains a separate visible dependency.
