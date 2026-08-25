# JUP-079 validation evidence

- Date: 2026-08-25
- Trello: https://trello.com/c/10RWrMCS
- Local branch: chore/JUP-079-branch-protection
- Integrated base: official `develop` after JUP-078 merge `5e33659`.
- Canonical repository: `EconomiconFinOps/tfm-economicon`.

## Remote audit

The official repository is public, defaults to `main` and already has an
integrated `develop` branch. The connected account `Iber1to` (Alejandro) has
repository administration permission.

Immediately before JUP-079 activation, GitHub reported both `main` and
`develop` as unprotected, no repository rulesets and no registered Actions
workflows. Its collaborator endpoint returned only `Iber1to`; no invitations
were pending. The effective GitHub access of Paris, Lucia and Victor therefore
remains unverified and must not be represented as complete.

## Delivered locally

- Pull-request template with JUP, Trello, validation and four rotating roles.
- Root contributor guide with the agreed branch and review flow.
- Metadata validator for branch type, target, matching JUP ID, Trello URL and
  four distinct, concretely assigned roles.
- CI workflow with read-only contents permission, immutable verified GitHub
  action SHAs and reruns when pull-request metadata changes.
- Separate required jobs for policy, OpenSpec, each Python service and frontend
  production build.
- Existing OpenSpec, cleanup, assistant corpus and LiteLLM validations retained.
- Versioned active rulesets for `develop` and `main`, with one and two required
  reviews respectively, six required checks, stale-review dismissal, protected
  discussions, force-push/deletion rejection and linear release history.
- Administrator continuity restricted to existing pull requests; direct pushes
  remain forbidden even for repository administrators.
- Administrator runbook for `develop` and `main`.
- Strict OpenSpec change for JUP-079.

## Validation

| Check | Result |
|---|---|
| PR policy tests | 11 passed, including matching body ID and four distinct participants |
| Workflow and ruleset tests | 7 passed, including six exact checks and PR-only admin bypass |
| JUP checker tests | 7 passed |
| All active JUP changes | 11 changes passed |
| Strict OpenSpec validation | 14 changes/specifications passed |
| Processor tests | 126 passed |
| Backend tests | 10 passed; 2 inherited short-test-key warnings |
| Azure fake API tests | 58 passed; 1 inherited dependency warning |
| Shared contract and benchmark tests | 32 passed |
| Repository hygiene tests | 6 passed; current tracked files accepted |
| Assistant corpus tests | 8 passed; manifest validated |
| LiteLLM gateway configuration | 6 passed |
| Frontend production build | passed |
| Frontend lint baseline | 49 inherited errors; deliberately not required yet |
| Workflow YAML parse | passed |
| Aggregate local Turborepo build and test | Both passed across all workspace packages |

The three GitHub-owned actions were verified against their official release
tags and signed commits:

- `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (`v7.0.1`).
- `actions/setup-node@820762786026740c76f36085b0efc47a31fe5020` (`v7.0.0`).
- `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7.0.0`).

The administrator bypass uses repository role `5` and
`bypass_mode: pull_request`, never `always` or `exempt`. This preserves an
auditable pull-request route until additional collaborators gain access.

## Pending remote evidence

- Run the newly published workflow on the JUP-079 pull request.
- Activate and verify both repository rulesets through GitHub's API.
- Confirm GitHub identities and grant agreed access to Paris, Lucia and Victor;
  this dependency cannot be completed by guessing accounts.
- Obtain real peer approvals once all four contributors have effective access.
