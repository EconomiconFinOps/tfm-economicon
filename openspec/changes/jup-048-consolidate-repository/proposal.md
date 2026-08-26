JUP: JUP-048
Trello: https://trello.com/c/l7mloFNe

## Why

Repository migration, selective OpenSpec reconciliation and protected branches
were completed across JUP-082 and JUP-079, but JUP-048 still describes them as
pending. The project needs one approved branch strategy, an auditable legacy
branch inventory and repository-level merge settings that match the documented
short-lived branch workflow.

## What Changes

- Confirm the canonical organization repository and permanent branches.
- Close the historical review of `setup/open-spec` without restoring HU tasks,
  personal agent configuration or platform-specific binaries.
- Version repository merge settings and test them against both rulesets.
- Disable merge commits and automatically remove merged pull-request branches.
- Record the exact legacy branches already contained in develop and preserve
  the unmerged `setup/sdd` branch pending a separate decision.
- Correct access evidence by verifying known GitHub accounts individually.

## Capabilities

### New Capabilities

- repository-lifecycle: canonical repository, branch lifecycle, merge policy
  and legacy branch audit.

### Modified Capabilities

- None.

## Out of Scope

- Deleting historical remote branches without team coordination.
- Integrating or discarding `setup/sdd`.
- Guessing Lucia's GitHub username or changing organization owners without
  organization-administrator authority.
- Replacing the protection checks delivered by JUP-079.

## Impact

Adds one definitive strategy, versioned repository settings, an automated
governance consistency test, updated OpenSpec evidence and a non-destructive
legacy branch inventory. Remote repository settings are activated only after
the protected pull request checks pass.
