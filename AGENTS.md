# Repository Guidelines

## Project Structure

This pnpm/Turborepo monorepo contains the frontend, Python backend and processor in `apps/`, reusable configuration in `packages/`, project documentation in `docs/`, and technical specifications in `openspec/`.

## Project Continuity

Read `docs/continuidad/README.md` and the relevant topic at the start of project
work; update both after meaningful milestones.

## Source Of Truth And Identifiers

- Trello owns scope, priorities, assignees, rotating responsibilities, delivery dates and task status.
- OpenSpec stores versioned requirements, implementation design, technical tasks and acceptance scenarios.
- GitHub stores code, documentation, pull requests and technical review history.
- The project memory (the final TFM deliverable) is written in a shared document outside Git; see `docs/memoria/README.md` for its location, section map and editing rules, and do not copy it into the repository.
- Reuse the same Trello identifier everywhere: `JUP-085`, `openspec/changes/jup-085-auth-session-contract/` and `feat/JUP-085-auth-session-contract`.
- Do not create a second numbering system or duplicate the operational backlog inside the repository.

## Build And Validation Commands

- `corepack pnpm install --frozen-lockfile`: install the workspace dependencies.
- `corepack pnpm build`, `corepack pnpm lint` and `corepack pnpm test`: run workspace validations.
- `corepack pnpm openspec:list`: inspect active OpenSpec changes.
- `corepack pnpm openspec:validate`: validate all specifications and changes strictly.
- `corepack pnpm jup:check -- --change jup-085-auth-session-contract`: verify Trello/OpenSpec traceability.
- `corepack pnpm jup:check:test`: test the JUP traceability checker.
- `corepack pnpm jup:cleanup:check`: reject personal agent configuration, unrelated binaries and parallel task namespaces.
- `corepack pnpm jup:cleanup:test`: test the repository hygiene checker.
- `docker compose up --build`: run the local development environment.

## Branches, Reviews And Tooling

- Never work directly on `main` or `develop`; create a short-lived branch containing its Trello `JUP-XXX` identifier.
- Open pull requests against `develop` and share implementation, pairing, review and validation among all four team members.
- Keep repository instructions independent of any specific assistant, IDE or vendor.
- Do not commit personal agent skills, local memory tools, generated environments or platform-specific executable binaries.
- Record durable architectural decisions in `docs/adr/` and link them to their Trello card and OpenSpec change.

## Pull Request Review And Validation

Process version: 2026-10-18 (JUP-126, PR135-only authorization)

The full rules and the definition of the four roles are in `CONTRIBUTING.md#review-and-validation-flow`. The required check `JUP reviews` only verifies that both titled reviews count under the latest-title rule, that neither comes from the author, that no request for changes is pending and, when the same person supplies both counting titles, that the pull request description contains the visible exception line; the rest of these rules depend on you:

- For each person and review kind, only their latest published title for this card counts; if dismissed, it supplies no role and does not revive an older title. Keep the complete history when resolving requests for changes. This does not verify assigned identities, current-SHA acceptance or review contents.
- Publish review and validation as two separate reviews titled `Revision JUP-XXX` and `Validacion JUP-XXX`. Towards `develop`, the first one published is a Comment and only the second one approves, when both are satisfied; towards `main`, both approve.
- A validation records evidence for each acceptance criterion of the Trello card and lists what was not validated and why. Never report as validated something that was not tested.
- A Comment does not lift a Request changes: once the changes are addressed, whoever requested them approves (or the request is dismissed with a reason).
- Reviewers and validators never push commits to the pull request branch ("Commit suggestion" counts as a push; "Update branch" does not); out-of-scope findings are requested from the leader.
- Before addressing changes or merging, read every review, the conversation comments and the inline comments on the diff, not only the latest review.
- Merge only when both reviews exist and nothing is pending; if "Update branch" brings changes to files or behaviour the pull request depends on (not just rows added to shared registries), request a revalidation first.
- Anyone using local tools, prompts or scripts to review, validate or merge pull requests aligns them with `CONTRIBUTING.md` whenever the process version changes.


### One-off authorization for PR135

Only PR #135 / JUP-126 in this repository has the human-authorized exception of
2026-10-18: Alejandro leads, Lucia pairs and reviews, Paris validates. It requires
the exact visible declaration documented in CONTRIBUTING, authoritative PR number,
repository/author/branch/base and exact roles. It does not change any other PR.
Only Lucia's latest eligible Revision and Paris's latest eligible Validacion can
supply the titles in this case; all published history still resolves changes.
No author/draft/dismissed title supplies a role; Comment does not lift changes.
This records the real pairing rather than crediting Paris with coimplementation.
Both independent titled verdicts and affected-delta revalidation remain required;
this exception grants no merge approval or power to dismiss a historical review.

### One-off authorization for PR161

On 2026-10-24 the user authorized two independent agents to perform the review
and validation of PR161 / JUP-131 instead of the assigned human verdicts. Scope,
candidate SHA, attribution and evidence are recorded in
`docs/evidence/JUP-131-pr161-agent-exception.md`. This is specific to PR161; it
does not authorize deployment, merge, fabricated human reviews or weakening
the general repository policy.

For the 2026-10-25 reconciliation, `JUP reviews` recognizes this case through
the exact visible declaration and two integrity-checked agent reports specified
in CONTRIBUTING. The reviewed commit must be an ancestor of the live PR head;
only the explicitly listed publication documents may change afterwards. Any
code delta requires both agents to revalidate. Outstanding GitHub change requests
still block; no GitHub approval or human identity is fabricated.
