JUP: JUP-100

## Context

- `.github/workflows/ci.yml` is the only workflow. It runs on `pull_request` (opened, synchronize, reopened, edited, ready_for_review) with `concurrency: cancel-in-progress` per ref, `permissions: contents: read`, actions pinned by commit and `persist-credentials: false`. Its job `pr-policy` ("JUP policy") runs `tools/pr-policy.mjs --event "$GITHUB_EVENT_PATH"`, which parses the PR title, body, head and base from the event.
- `tools/ci-workflow.test.mjs` asserts the seven required check contexts and that both `.github/rulesets/develop.json` and `main.json` require exactly the same checks. `develop` requires 1 approval and `main` 2; both dismiss stale approvals on push, require the last push to be approved by someone else and require review threads to be resolved.
- `tools/repository-governance.test.mjs` already asserts phrases in `CONTRIBUTING.md` and `docs/governance/repository-and-branch-strategy.md`; those assertions must keep passing.
- Release PRs (`develop` → `main`) also carry a JUP identifier and the four roles; "JUP policy" only relaxes the branch-name rule for them.
- `pull_request_review` runs in the same context as `pull_request` (`refs/pull/N/merge`) with activity types `submitted`, `edited` and `dismissed`, so a check it produces is attached to the PR like "JUP policy".
- The capability `repository-governance` belongs to the still-active change `jup-079-branch-protection` and is not in `openspec/specs/`; this change introduces its own capability instead of depending on it.

## Goals / Non-Goals

**Goals:**
- One place (`CONTRIBUTING.md`) with the full definition of roles and flow, plus the minimum copied into `AGENTS.md` and the PR template so that tooling that only reads those still applies it.
- Enforce what is mechanically checkable without changing the number of required approvals.

**Non-Goals:**
- Verifying that the person who reviews is the one named in the PR description (in 8 recent merged PRs only 2 approvals came from the declared reviewer; the check would block normal reassignments).
- Interpreting the free text of Comment reviews; humans judge it.

## Decisions

### D1. Separate workflow `pr-reviews.yml`, reusing `tools/pr-policy.mjs`
The check needs the `pull_request_review` trigger. Adding it to `ci.yml` would rerun every job on each review, let `cancel-in-progress` cancel running tests, and, if the other jobs were skipped for review events, GitHub would report those required checks as passing (skipped counts as success), which could mask a real failure. A separate workflow with a single job avoids all three. Alternative considered: a new standalone script; rejected because `pr-policy.mjs` already parses the JUP identifier, roles and base branch and has its own test suite.

### D2. Read reviews from the API, not from the event
The job fetches the PR and its reviews with `GITHUB_TOKEN` (`pull-requests: read`) at run time. `gh run rerun` replays the original event payload, so a check that trusted the payload kept failing after the PR was fixed (seen with "JUP policy"). The pure evaluation (reviews + PR metadata → errors) stays a function testable without network; only the fetch is I/O. An API failure is an error, never a pass.

### D3. Semantics of the check
- Titled review: body starts with `Revision`/`Revisión` or `Validacion`/`Validación` followed by the PR's `JUP-XXX`, case-insensitive; the author's reviews and draft (PENDING) reviews are ignored; dismissed reviews and reviews on earlier commits still count (freshness of approvals is already enforced by GitHub's stale-approval dismissal).
- Pending changes: for each reviewer (login compared without case), the latest review with state APPROVED, CHANGES_REQUESTED or DISMISSED decides; if any is CHANGES_REQUESTED, the check fails. A dismissal leaves the reviewer without a current decision, so an approval dismissed by a push does not revive an older request (adversarial review ADV-1). Later Comment reviews do not clear a request; CONTRIBUTING tells the requester to approve, or the request to be dismissed, once addressed (ADV-2).
- Same person: if the two titled reviews come from the same login, the PR description must contain the declaration line fixed in `CONTRIBUTING.md` (`- Excepcion: revision y validacion por la misma persona, acordado en Trello`). Only text GitHub renders as plain Markdown counts: HTML comments (closed or not), fenced blocks (``` or ~~~, indented up to three spaces, closed or not) and indented code are ignored, and the whole line must match, with an optional final period (pass 1 ADV-4, pass 2 ADV-3, pass 3 ADV-1). The declaration is required whenever some login published both titled reviews, even if a third person also published one (pass 3 ADV-3).
- Every failure message links to the flow with an absolute URL, clickable from the Actions log (ADV-5), and a missing titled review explains that the first line must be the plain title (ADV-3).
- Applies to `develop` and `main`. The Comment-then-Approve convention is documented, not enforced: on `main` both must approve, and the approval count is already enforced by the rulesets.

### D4. Required on both rulesets
`JUP reviews` is added to `required_status_checks` in both rulesets, and `tools/ci-workflow.test.mjs` is updated from seven to eight contexts while still asserting both rulesets are identical. Activation in GitHub remains an administrator step documented in `docs/governance/github-branch-protection.md`.

### D5. Propagation to local tooling in layers
1. The check's failure message names the missing piece and links to the CONTRIBUTING section.
2. `AGENTS.md` gets a short vendor-neutral section with the non-checkable rules, because some tools read only `AGENTS.md`.
3. The PR template carries the checklist into every PR.
4. `CONTRIBUTING.md` (English) holds the full text; the spec keeps the verifiable scenarios.
5. A `Process version: YYYY-MM (JUP-100)` line identical in `AGENTS.md` and `CONTRIBUTING.md`, asserted by `tools/repository-governance.test.mjs`.

### D5b. `JUP policy` accepts the declared exception
The same person in PR review and validation is allowed only with the exception line, and must then be reflected honestly in the Participacion section. `checkPullRequest` therefore accepts three different people instead of four when review and validation share a name and the exception line is present (same parser as `JUP reviews`: full line, outside HTML comments and code blocks); leadership and pairing must still be different from each other and from that person. The exception line with different names in review and validation is rejected as incoherent, and role names are compared without accents or a leading `@` (pass 3 ADV-2, ADV-4). Alternative rejected: keeping the official Trello names in Participacion and declaring the exception only in a separate line, which would make the pull request record contradict who did the work. Lucia chose this option on 2026-09-30.

### D6. No ADR
This is a team process decision, versioned in `CONTRIBUTING.md`, `docs/governance/` and this spec, following the precedent of `jup-079-branch-protection`, which documented branch protection in `docs/governance/` without an ADR.

## Risks / Trade-offs

- [The check blocks existing open PRs once activated, since none has titled reviews] → Activation is a separate administrator step after merge; announce it in Discord and list the open PRs that will need the two reviews.
- [A review event from a fork gets a read-only token] → Only read access is needed; the repository does not use forks.
- [Titles are free text and can be spoofed] → The check supports the process, it is not a security control; stated in CONTRIBUTING.
- [The same-person declaration can be added without real agreement] → The rule asks for agreement in Trello; the check only verifies it is explicit.
- [Local tooling ignores `AGENTS.md`] → The required check still blocks the merge and explains what is missing.

## Migration Plan

1. Merge the documentation, workflow, script, tests and ruleset files.
2. An administrator applies the updated rulesets following `docs/governance/github-branch-protection.md`.
3. Announce in Discord: process version, the new check, and that open PRs need both titled reviews; each person updates their local tooling.
Rollback: remove `JUP reviews` from the rulesets (administrator) and revert the PR.
