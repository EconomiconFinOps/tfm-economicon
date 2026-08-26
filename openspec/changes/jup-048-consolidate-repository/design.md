JUP: JUP-048

## Context

The official repository now lives in `EconomiconFinOps`, has a shared develop
branch and enforces pull requests through active rulesets. Earlier JUP-048 work
reviewed `setup/open-spec` from the original main commit, while later JUP-082
performed the actual selective cleanup and JUP-079 activated branch protection.
JUP-048 must consolidate those outcomes rather than replaying an obsolete branch.

## Decisions

### Treat main and develop as the only permanent branches

Typed JUP branches start from develop and target develop. Only develop targets
main. Hotfixes also pass through develop before promotion so the permanent
branches retain one auditable path.

### Prefer squash and prohibit merge commits

Ordinary task branches use squash. Rebase remains available for a small,
intentional commit sequence. Merge commits are disabled at repository level and
excluded from both rulesets. GitHub automatically removes merged remote task
branches, reducing stale branch accumulation without deleting historical
branches during this change.

### Audit ancestry before cleanup

Every remote branch is tested with `git merge-base --is-ancestor` against
origin/develop. Merged branches become cleanup candidates; a non-ancestor is
preserved and routed through a separate review. `setup/sdd` is deliberately
preserved because it is the only audited legacy branch outside develop.

### Verify access per identity

Public read access and the generic collaborator listing are insufficient for
organization-inherited permissions. Known usernames are checked through the
repository permission endpoint. Unknown identities remain pending. Organization
owner changes require `admin:org` and are not attempted by this task.

### Keep settings and effective state distinct

The JSON settings and tests define the desired reproducible policy. GitHub API
responses prove activation. The pull request and Trello evidence record both;
neither local files nor Discord statements alone prove effective governance.

## Risks and mitigations

- Existing contributors may still use old branches: do not delete them in this
  change and enable automatic deletion only for future merged PRs.
- Disabling merge commits changes team habits: document squash as the default
  and retain rebase as an explicit alternative.
- Unknown Lucia account blocks formal review: publish the PR and leave review
  evidence pending rather than using a guessed identity.

## Rollback

Repository settings can re-enable merge commits or disable automatic branch
deletion through the GitHub API. The ruleset JSON and test change must be
reverted in the same protected pull-request workflow to keep desired and
effective configuration aligned.
