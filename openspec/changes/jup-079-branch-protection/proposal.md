JUP: JUP-079
Trello: https://trello.com/c/10RWrMCS

## Why

The remote repository currently exposes main without an agreed remote develop
branch. Direct pushes, missing review evidence and pull requests without a JUP
link would make the four-person workflow and the October delivery difficult to
audit.

## What Changes

- Define the branch flow tipo/JUP-XXX-description to develop to main.
- Add a pull request template with Trello, evidence and all rotating roles.
- Add a local and CI validator for title, branch, target and role traceability.
- Add CI checks for OpenSpec, Python services and the frontend build.
- Document exact branch rules for an administrator to activate.

## Capabilities

### New Capabilities

- repository-governance: versioned and testable pull-request and branch policy.

### Modified Capabilities

- None.

## Out of Scope

- Creating remote develop before the canonical repository is confirmed.
- Enabling GitHub rules without repository administration permission.
- Adding incomplete CODEOWNERS entries for unconfirmed GitHub usernames.
- Publishing this stacked local branch.

## Impact

Adds GitHub workflow files, pull-request metadata, policy tests and
administrator documentation. Remote protection remains a visible pending task,
not a claimed result.
