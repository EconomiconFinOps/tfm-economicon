JUP: JUP-079

## Confirmed facts

- ParisArcos/tfm-economicon is public and defaults to main.
- Remote branches observed on 2026-08-08 are main, chore/migrate-frontend,
  setup/open-spec and setup/sdd.
- The connected account Iber1to has pull access but no push or admin access.
- No remote develop branch is visible.
- Requiring two approvals is not viable until the other members have write
  permission, because GitHub only counts required reviews from eligible users.

## Desired flow

Feature, fix, documentation, test and maintenance branches target develop.
Only develop may target main. GitHub rulesets block deletion, force pushes and
merges without reviews, resolved conversations and required status checks.

The JUP policy check validates metadata that rulesets cannot express:

1. a JUP-XXX identifier in the title;
2. a direct Trello card URL;
3. a typed JUP branch targeting develop;
4. develop as the only source for main;
5. concrete people for all four rotating roles.

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

The workflow grants read-only contents permission. Third-party GitHub actions
are pinned to immutable commit SHAs. It does not consume repository secrets,
execute deployment steps or use pull_request_target.

## Activation

An administrator must first confirm the repository, create develop from the
agreed integrated head, grant the four members the agreed access, run all checks
on a test pull request and then create the develop and main rulesets. Required check names are documented in
docs/governance/github-branch-protection.md.

Rollback removes or disables the ruleset through GitHub administration. The
versioned PR template and validators remain reviewable and do not grant access.
