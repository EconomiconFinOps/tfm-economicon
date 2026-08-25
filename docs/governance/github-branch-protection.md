# GitHub branch governance for JUP-079

- Trello: https://trello.com/c/10RWrMCS
- Canonical repository: `EconomiconFinOps/tfm-economicon`.
- Audit date: 2026-08-25.
- Versioned rulesets: `.github/rulesets/develop.json` and
  `.github/rulesets/main.json`.

## Confirmed remote state

The connected GitHub account is `Iber1to` (Alejandro). The repository is
public, defaults to `main`, has an established `develop` integration branch and
grants Alejandro repository administration permission.

The collaborator API currently lists only `Iber1to`; the other three team
members' effective GitHub access is not confirmed. Required review approvals
only count when they come from eligible contributors, so administrator
continuity must be possible until the missing accounts are incorporated.

## Branch and pull-request flow

    tipo/JUP-XXX-descripcion -> develop -> main

- Never commit directly to main or develop.
- Product, test and documentation branches target develop.
- Only develop may open a pull request toward main.
- Allowed prefixes are feat, fix, docs, test, chore, refactor, ci and build.
- Every pull request contains the same JUP-XXX in its title and source branch,
  plus a direct Trello card URL.
- Every pull request identifies leadership, pairing/co-authorship, PR review,
  and validation/tests/documentation.

## Required rules for develop

Configure a branch ruleset matching refs/heads/develop:

1. Require a pull request before merging.
2. Require at least one approving review.
3. Dismiss stale approvals when new commits are pushed.
4. Require approval of the most recent reviewable push by someone other than
   the author.
5. Require all conversations to be resolved.
6. Require the status checks listed below and require the branch to be current.
7. Block force pushes and deletion.
8. Allow repository administrators to bypass only through an existing pull
   request (`bypass_mode: pull_request`); never grant direct-push bypass.

## Required rules for main

Configure a branch ruleset matching refs/heads/main:

1. Require a pull request before merging.
2. Require at least two approving reviews.
3. Apply the same stale-review, last-push, conversation, status, force-push,
   deletion and PR-only administrator bypass rules as develop.
4. Require linear history.
5. Accept pull requests only from develop; the JUP policy check enforces this
   relation.

## Required status checks

Use these stable job names from .github/workflows/ci.yml:

- JUP policy
- OpenSpec
- Python tests (azure-cost-api)
- Python tests (backend)
- Python tests (processor)
- Frontend build

The frontend lint is not a required check yet because the inherited baseline
contains 49 react/prop-types failures. Track and fix that debt in its own JUP
card before making lint mandatory; builds remain required now.

## Administrator exception and teammate onboarding

Each ruleset permits only the built-in repository-admin role (`actor_id: 5`) to
bypass review requirements, and only with `bypass_mode: pull_request`. GitHub
still requires a real pull request and records the administrator action; direct
pushes, deletion and force pushes cannot use this exception.

This temporary continuity mechanism is necessary while `Iber1to` is the only
confirmed collaborator. Confirm the GitHub usernames for Paris, Lucia and
Victor, grant the agreed repository or organization access, and then use normal
peer approvals. Do not invent usernames, publish an incomplete `CODEOWNERS`
file, or claim approval that GitHub does not record.

## Administrator activation checklist

1. Confirm `EconomiconFinOps/tfm-economicon`, `develop` and administrator
   permissions through the GitHub API.
2. Open the JUP-079 pull request and wait for all six checks to complete.
3. Create the `develop` ruleset from `.github/rulesets/develop.json`.
4. Create the stricter `main` ruleset from `.github/rulesets/main.json`.
5. Query both rulesets and both branches; verify active enforcement, the exact
   required checks, review counts and PR-only administrator bypass.
6. Merge only through the JUP-079 pull request. If peers are not yet eligible,
   a repository administrator may use the documented PR-only exception.
7. Confirm the remaining teammates' accounts and grant the agreed access before
   treating four-person reviews as available.

Activation uses authenticated GitHub CLI calls with the versioned JSON files:

```sh
gh api repos/EconomiconFinOps/tfm-economicon/rulesets \
  --method POST --input .github/rulesets/develop.json
gh api repos/EconomiconFinOps/tfm-economicon/rulesets \
  --method POST --input .github/rulesets/main.json
gh api repos/EconomiconFinOps/tfm-economicon/rules/branches/develop
gh api repos/EconomiconFinOps/tfm-economicon/rules/branches/main
```

CODEOWNERS remains deferred until all four GitHub identities and effective
permissions are verified.

## References

- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository
- https://docs.github.com/en/actions/reference/security/secure-use
