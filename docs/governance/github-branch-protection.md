# GitHub branch governance for JUP-079

- Trello: https://trello.com/c/10RWrMCS
- Canonical repository: `EconomiconFinOps/tfm-economicon`.
- Initial audit date: 2026-08-25; access recheck: 2026-08-26 (JUP-048).
- Versioned rulesets: `.github/rulesets/develop.json` and
  `.github/rulesets/main.json`.

## Confirmed remote state

The connected GitHub account is `Iber1to` (Alejandro). The repository is
public, defaults to `main`, has an established `develop` integration branch and
grants Alejandro repository administration permission.

The initial generic collaborator listing returned only `Iber1to`, but this did
not include organization-inherited permissions. JUP-048 subsequently verified
`Iber1to`, `ParisArcos` and `Victorh1397` individually as repository
administrators. Lucia's GitHub username and effective permission remain
unconfirmed. Required review approvals only count when they come from eligible
contributors, so administrator continuity remains available until that final
identity is incorporated.

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

Use these stable job names, the first seven from `.github/workflows/ci.yml` and the last one from `.github/workflows/pr-reviews.yml`. `tools/repository-governance.test.mjs` checks that this list matches the versioned rulesets:

- `JUP policy`
- `OpenSpec`
- `Python tests (azure-cost-api)`
- `Python tests (backend)`
- `Python tests (processor)`
- `Frontend build`
- `Frontend type check`
- `JUP reviews`

JUP-087 runs frontend lint and real journey tests before bundling in the required
`Frontend build` job. A lint error or failed test fails that required check; no
additional ruleset context is needed. The former 49 `react/prop-types` failures
are addressed by typing the existing components under ADR-0003, while JSX keeps
its prop validation rule. The separate `Frontend type check` also checks the
test project without adding Node globals to the browser source.

All seven contexts, including `Frontend type check`, were confirmed active in
the remote `develop` rules on 2026-09-08. Applying future changes to live
rulesets remains an administrator action; versioning JSON alone does not enable
them (see "Administrator activation checklist" below).

JUP-095 ported the frontend to `react-router` and originally added an eighth
check ("Frontend tests") that duplicated the journey-test run already covered
by `Frontend build`. Reconciling the port with `develop` (2026-09-19) removed
that duplicate job and its ruleset entries, restoring the seven confirmed
checks above as the full set; the port's own 39 test cases now run inside
`Frontend build` alongside JUP-087's regression suite, discovered from both
`src/**/*.test.tsx` and `tests/**/*.test.tsx`.

JUP-100 adds an eighth required context, `JUP reviews`, to both rulesets. It comes from its own workflow, `.github/workflows/pr-reviews.yml`, not from `ci.yml`: it also runs when a review is submitted, edited or dismissed, and review events inside `ci.yml` would rerun or cancel the other jobs and report skipped jobs as passing. The check reads the pull request and its reviews through the GitHub API with a read-only token and fails while the titled `Revision JUP-XXX` or `Validacion JUP-XXX` review is missing, a review comes only from the author, a request for changes is pending, or the same person published both without the exception line; the rules are in [CONTRIBUTING.md](../../CONTRIBUTING.md#review-and-validation-flow). Until an administrator applies the updated rulesets, the check runs but is not required. Once it is required, open pull requests without both titled reviews cannot be merged.

## Administrator exception and teammate onboarding

Each ruleset permits only the built-in repository-admin role (`actor_id: 5`) to
bypass review requirements, and only with `bypass_mode: pull_request`. GitHub
still requires a real pull request and records the administrator action; direct
pushes, deletion and force pushes cannot use this exception.

This continuity mechanism remains useful when an assigned reviewer is not yet
eligible. Confirm Lucia's GitHub username and permission, then use normal peer
approvals. Do not invent usernames, publish an incomplete `CODEOWNERS` file, or
claim approval that GitHub does not record.

## Administrator activation checklist

1. Confirm `EconomiconFinOps/tfm-economicon`, `develop` and administrator
   permissions through the GitHub API.
2. Open the JUP-079 pull request and wait for all required checks to complete.
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

Rulesets that already exist are updated, not created again: `POST` would add a second ruleset. To activate a later change such as the `JUP reviews` check of JUP-100, merge its pull request first so that the workflow exists in `develop`, then update each ruleset by its identifier and verify the branch rules:

```sh
gh api repos/EconomiconFinOps/tfm-economicon/rulesets --jq '.[] | "\(.id) \(.name)"'
gh api repos/EconomiconFinOps/tfm-economicon/rulesets/<develop-id> \
  --method PUT --input .github/rulesets/develop.json
gh api repos/EconomiconFinOps/tfm-economicon/rulesets/<main-id> \
  --method PUT --input .github/rulesets/main.json
gh api repos/EconomiconFinOps/tfm-economicon/rules/branches/develop
gh api repos/EconomiconFinOps/tfm-economicon/rules/branches/main
```

CODEOWNERS remains deferred until all four GitHub identities and effective
permissions are verified.

## References

- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository
- https://docs.github.com/en/actions/reference/security/secure-use
