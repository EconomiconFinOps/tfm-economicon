JUP: JUP-079

## Confirmed facts

- `EconomiconFinOps/tfm-economicon` is the confirmed public repository and
  defaults to `main`; the integrated `develop` branch exists.
- On 2026-08-25 both branches reported `protected: false`, no GitHub Actions
  workflows or rulesets were configured, and `Iber1to` had admin access.
- The collaborator endpoint returned only `Iber1to`. The GitHub usernames and
  effective write permissions of the other three teammates are not verified.
- Requiring reviewer approvals without a PR-only admin exception would block
  every future merge until eligible teammates receive access.

## Desired flow

Feature, fix, documentation, test and maintenance branches target develop.
Only develop may target main. GitHub rulesets block deletion, force pushes and
merges without reviews, resolved conversations and required status checks.
`develop` requires one approval; `main` requires two and linear history.

The repository-admin bypass uses `bypass_mode: pull_request`: it can be used
only on an already-open pull request and does not permit direct pushes. This
preserves an auditable route while Alejandro remains the only collaborator.

The JUP policy check validates metadata that rulesets cannot express:

1. a JUP-XXX identifier in the title;
2. a direct Trello card URL;
3. a typed JUP branch targeting develop;
4. develop as the only source for main;
5. the same JUP identifier in the title, branch and pull-request body;
6. four concrete, distinct people for the rotating roles.

## CI boundary

Pull requests to main or develop run:

- metadata and branch policy validation;
- OpenSpec and local governance validators;
- independent Python test jobs for the three services;
- frontend production build.

Frontend lint is excluded from the required set because 49 existing
react/prop-types failures predate JUP-079. This debt must be resolved separately
before lint becomes a protected-branch requirement.

## Security

The workflow grants read-only contents permission. GitHub-owned actions are
pinned to verified immutable commit SHAs. It reruns when pull-request metadata
changes and does not consume repository secrets, execute deployment steps or
use `pull_request_target`. Existing corpus, cleanup, gateway and OpenSpec
validators remain enforced.

## Activation

An administrator first opens the JUP-079 pull request and waits for its six
required checks to run successfully. The exact rulesets in
`.github/rulesets/develop.json` and `.github/rulesets/main.json` can then be
activated through GitHub's repository-rules API. Effective API state verifies
matching branches, required reviews/checks, force-push/deletion restrictions
and PR-only administrator bypass.

Granting all four teammates access remains a separate prerequisite for normal
peer approvals and cannot be completed until their GitHub identities and the
organization's desired roles are confirmed.

Rollback removes or disables the ruleset through GitHub administration. The
versioned PR template and validators remain reviewable and do not grant access.
