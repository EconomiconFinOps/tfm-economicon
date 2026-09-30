# Repository Guidelines

## Project Structure

This pnpm/Turborepo monorepo contains the frontend, Python backend and processor in `apps/`, reusable configuration in `packages/`, project documentation in `docs/`, and technical specifications in `openspec/`.

## Source Of Truth And Identifiers

- Trello owns scope, priorities, assignees, rotating responsibilities, delivery dates and task status.
- OpenSpec stores versioned requirements, implementation design, technical tasks and acceptance scenarios.
- GitHub stores code, documentation, pull requests and technical review history.
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

Process version: 2026-09-30 (JUP-100)

The full rules and the definition of the four roles are in `CONTRIBUTING.md#review-and-validation-flow`. The required check `JUP reviews` enforces the titled reviews; these rules are not checked automatically:

- Publish review and validation as two separate reviews titled `Revision JUP-XXX` and `Validacion JUP-XXX`. Towards `develop`, the first one published is a Comment and only the second one approves, when both are satisfied; towards `main`, both approve.
- A validation records evidence for each acceptance criterion of the Trello card and lists what was not validated and why. Never report as validated something that was not tested.
- Reviewers and validators never push commits to the pull request branch; out-of-scope findings are requested from the leader.
- Before addressing changes or merging, read every review, the conversation comments and the inline comments on the diff, not only the latest review.
- Merge only when both reviews exist and nothing is pending; if "Update branch" brings changes to the same files or areas, request a revalidation first.
- Anyone using local tools, prompts or scripts to review, validate or merge pull requests aligns them with `CONTRIBUTING.md` whenever the process version changes.
