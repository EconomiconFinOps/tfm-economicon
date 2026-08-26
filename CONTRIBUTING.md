# Contributing to Economicon

All work starts from a Trello card with a JUP-XXX identifier. Do not work
directly on main or develop.

## Branches

Use:

    tipo/JUP-XXX-short-description

Allowed types are feat, fix, docs, test, chore, refactor, ci and build.
Ordinary pull requests target develop. Only develop may target main.
Task branches are short-lived. Prefer squash merge for ordinary work and delete
the remote task branch after integration; GitHub performs that deletion
automatically. Rebase merge remains available when preserving a small,
intentional commit series adds review value. Merge commits are disabled.

## Pull requests

Use the repository template and provide:

- the same JUP-XXX used by the branch, title and body;
- a direct link to the Trello card;
- a concise scope and validation evidence;
- four distinct people for leadership, pairing/co-authorship, PR review, and
  validation/tests/documentation.

Run the applicable local checks before requesting review:

    corepack pnpm jup:check:all
    corepack pnpm pr:check:test
    corepack pnpm ci:check:test
    corepack pnpm repository:governance:test
    corepack pnpm openspec:validate
    corepack pnpm test
    corepack pnpm build

Never commit credentials, tokens or generated environment files. A task is not
complete until its reviewed pull request is merged and its evidence is linked
from Trello.

The desired GitHub rules and their administrator activation procedure are in
docs/governance/github-branch-protection.md.
The approved repository lifecycle, legacy-branch audit and release flow are in
docs/governance/repository-and-branch-strategy.md.

The repository-admin continuity exception applies only to an existing pull
request and never authorizes direct pushes to `main` or `develop`.
