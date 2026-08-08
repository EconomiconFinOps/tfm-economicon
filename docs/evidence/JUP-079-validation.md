# JUP-079 validation evidence

- Date: 2026-08-08
- Trello: https://trello.com/c/10RWrMCS
- Local branch: chore/JUP-079-branch-protection
- Stacked base: JUP-078 commit b8cf6b5
- Remote writes: none

## Remote audit

The GitHub integration observed ParisArcos/tfm-economicon as a public repository
whose default branch is main. The connected account Iber1to has read access but
no push or administration access.

Remote branches returned by GitHub:

- main
- chore/migrate-frontend
- setup/open-spec
- setup/sdd

No develop branch was returned. Remote protection, collaborator access and
rulesets were not changed.

## Delivered locally

- Pull-request template with JUP, Trello, validation and four rotating roles.
- Root contributor guide with the agreed branch and review flow.
- Metadata validator for branch type, target, matching JUP ID, Trello URL and
  filled roles.
- CI workflow with read-only contents permission and immutable action SHAs.
- Separate required jobs for policy, OpenSpec, each Python service and frontend
  production build.
- Administrator runbook for develop and main.
- Strict OpenSpec change for JUP-079.

## Validation

| Check | Result |
|---|---|
| PR policy tests | 8 passed |
| JUP checker tests | 5 passed |
| Active JUP checks | JUP-078 and JUP-079 passed |
| Strict OpenSpec validation | 2 changes passed |
| Processor tests | 42 passed |
| Backend tests | 7 passed; 2 inherited short-key warnings |
| Azure fake API tests | 34 passed; 1 dependency deprecation warning |
| Frontend production build | passed |
| Frontend lint baseline | 49 inherited errors; deliberately not required yet |
| Workflow YAML parse | passed |
| Aggregate local Turborepo build | environment policy rejected dependencies published less than 24 hours ago; component tests and frontend build passed |

The three GitHub-owned actions were verified against their official repositories
at the exact full commit SHAs used by the workflow.

The aggregate build interruption came from the local package supply-chain age
policy, not a compilation or test failure. GitHub CI still requires its first
remote run before the checks can be selected in a ruleset.

## Pending remote evidence

- Confirm that this is the canonical repository.
- Grant appropriate collaborator access to all four members.
- Confirm Lucia and Victor GitHub usernames.
- Create develop from the agreed integrated stack.
- Run the new workflow in GitHub and select its exact checks in both rulesets.
- Demonstrate that direct pushes to main and develop are rejected.
- Open and review the linked pull request.
