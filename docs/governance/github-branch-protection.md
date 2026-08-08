# GitHub branch governance for JUP-079

- Trello: https://trello.com/c/10RWrMCS
- Repository observed: ParisArcos/tfm-economicon
- Audit date: 2026-08-08
- Status: desired configuration; not applied remotely

## Confirmed remote state

The connected GitHub account is Iber1to (Alejandro). The repository is public,
its default branch is main, and the integration reports pull access but no push
or administration access.

Observed branches:

- main
- chore/migrate-frontend
- setup/open-spec
- setup/sdd

There is no remote develop branch. Branch rules cannot be activated until the
team confirms this repository and Paris, as its administrator, creates the
agreed base or grants the required permission.

Required reviews only count from people with write permission. Before requiring
two approvals, Paris must add Alejandro, Lucia and Victor as collaborators with
the agreed access and confirm the GitHub usernames of Lucia and Victor.

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
8. Do not allow bypass except a documented emergency administrator action.

## Required rules for main

Configure a branch ruleset matching refs/heads/main:

1. Require a pull request before merging.
2. Require at least two approving reviews.
3. Apply the same stale-review, last-push, conversation, status, force-push and
   deletion rules as develop.
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

## Administrator activation checklist

1. Confirm that ParisArcos/tfm-economicon is canonical.
2. Add all four members as collaborators; verify their effective permission.
3. Integrate the prepared JUP stack into a reviewed remote branch.
4. Create develop from the commit agreed by the team.
5. Open a test pull request so every CI check runs at least once.
6. Create the develop ruleset with the exact check names above.
7. Create the stricter main ruleset.
8. Attempt a direct push to each protected branch using a disposable commit and
   verify GitHub rejects it; do not rewrite shared history.
9. Capture screenshots or API output and link them from JUP-079.

CODEOWNERS is deliberately deferred because only the GitHub usernames
ParisArcos and Iber1to are confirmed. Adding incomplete ownership would exclude
Lucia or Victor and would not prove participation by all four members.

## References

- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository
- https://docs.github.com/en/actions/reference/security/secure-use
