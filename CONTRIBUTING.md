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

## Rotating roles

Process version: 2026-09-30 (JUP-100)

Every Trello card assigns four different people to four roles. The same names go in the Participacion section of the pull request.

If someone other than the assigned person takes over a role (for example, whoever opens the pull request assumes leadership), they reassign it explicitly: update the Participacion section of the pull request and the Trello card. A reviewer who notices an outdated Participacion section asks for it to be updated.

### Leadership

- **Does:** owns the card end to end: refines the acceptance criteria with the team, creates the branch, specifies and implements the change (OpenSpec propose and apply), keeps the evidence, opens the pull request from the template, requests review and validation, and addresses every requested change.
- **When:** from the start of the card until the pull request is merged and Trello is updated.
- **Delivers:** a pull request ready for review (CI green, evidence linked, change archived in the same branch), answers to each requested change, and out-of-scope findings registered in `openspec/findings/backlog.md` when reviewers ask for them.
- **Does not:** review or validate their own pull request.

### Pairing and co-authorship

- **Does:** designs and builds the change together with the leader, challenges the approach before code is written, and can take over if the leader is unavailable.
- **When:** during refinement and implementation, before the pull request is opened.
- **Delivers:** co-authored commits or a short note in Trello of what was paired.
- **Does not:** act as the reviewer or the validator of the same pull request.

### PR review

- **Does:** checks the code against the card and the spec: correctness, edge cases and error paths, the quality of the tests (they must fail if the behaviour is broken), and the consistency of the documentation with the code. Runs locally the tests CI does not run when the pull request touches them.
- **When:** once the pull request is ready, in parallel with the validation.
- **Delivers:** a GitHub review titled `Revision JUP-XXX` with what was verified and how, the changes requested, and what was not checked.
- **Does not:** push commits to the branch, validate the acceptance criteria, or merge without the validation.

### Validation, tests and documentation

- **Does:** runs the pull request branch following the README or the pull request instructions as written, checks each acceptance criterion of the Trello card and tries to break it with at least one edge or error case.
- **When:** once the pull request is ready, in parallel with the review.
- **Delivers:** a GitHub review titled `Validacion JUP-XXX` with a checklist of the card criteria, the evidence for each one (commands and output, steps, screenshots added from the browser), what was not validated and the limitations of the evidence.
- **Does not:** judge the code or the tests, push commits to the branch, or mark as validated anything that was not tested.

## Review and validation flow

1. Review and validation are two separate GitHub reviews on the pull request. The first line of each one is its title: `Revision JUP-XXX` or `Validacion JUP-XXX`, with the identifier of the pull request (case and accents do not matter).
2. They can happen in parallel. Towards `develop`, the first one published is a **Comment** when it finds no problem and says that the other one is still missing; the second one is an **Approve** only when both are satisfied and nothing blocking remains. Towards `main`, which requires two approvals, both are **Approve** when satisfied.
3. Any problem is a **Request changes**, whichever review goes first. A Request changes also copies what is still pending from the other review, so that reading only the latest review is enough. Once the changes are addressed, whoever requested changes approves to lift the request: a Comment does not lift a Request changes. Approving early does not open the merge, because `JUP reviews` still waits for the other titled review. Alternatively, the request is dismissed with a reason, only by whoever requested it or by someone who is not the author: the author never dismisses reviews on their own pull request. `JUP reviews` does not verify who dismissed a review; the dismissal and its reason stay visible in the pull request.
4. Review and validation are done by the different people assigned in Trello. If exceptionally the same person does both, it is agreed in Trello, that person still publishes two separate reviews, and the pull request description declares it with this line:

   ```
   - Excepcion: revision y validacion por la misma persona, acordado en Trello
   ```

5. Neither the reviewer nor the validator pushes commits to the branch: a push dismisses the existing approvals. Findings outside the scope of the pull request are requested from the leader in the review text.
6. Whoever addresses requested changes or decides to merge reads every source of feedback: all the reviews, the conversation comments and the inline comments on the diff, not only the latest review.
7. Anyone may merge once the pull request has both titled reviews and nothing pending. If "Update branch" brings changes that touch the same files or areas as the pull request, a revalidation of what is affected is requested before merging.
8. The required check `JUP reviews` blocks the merge until both titled reviews exist, neither from the author, without pending requests for changes, and with the exception line when the same person published both. It supports the process; it is not a security control, and it does not judge the content of the reviews. It runs the code of the pull request itself, so reviewers pay special attention to changes in `tools/pr-policy.mjs` and `.github/workflows/`, which can alter the checks.

A validation lists what was not validated instead of marking it as met. The Validacion section of the pull request template is the leader's own evidence; it does not replace the validation review.

The desired GitHub rules and their administrator activation procedure are in
docs/governance/github-branch-protection.md.
The approved repository lifecycle, legacy-branch audit and release flow are in
docs/governance/repository-and-branch-strategy.md.

The repository-admin continuity exception applies only to an existing pull
request and never authorizes direct pushes to `main` or `develop`.
