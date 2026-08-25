# Repository Guidelines

## Project Structure

This pnpm/Turborepo monorepo contains the frontend, Python backend and processor in `apps/`, reusable configuration in `packages/`, project documentation in `docs/`, and technical specifications in `openspec/`.

## Source Of Truth And Identifiers

- Trello owns scope, priorities, assignees, rotating responsibilities, delivery dates and task status.
- OpenSpec stores versioned requirements, implementation design, technical tasks and acceptance scenarios.
- GitHub stores code, documentation, pull requests and technical review history.
- Reuse the same Trello identifier everywhere: `JUP-082`, `openspec/changes/jup-082-clean-develop/` and `chore/JUP-082-clean-develop`.
- Do not create a second numbering system or duplicate the operational backlog inside the repository.

## Build And Validation Commands

- `corepack pnpm install --frozen-lockfile`: install the workspace dependencies.
- `corepack pnpm build`, `corepack pnpm lint` and `corepack pnpm test`: run workspace validations.
- `corepack pnpm openspec:list`: inspect active OpenSpec changes.
- `corepack pnpm openspec:validate`: validate all specifications and changes strictly.
- `corepack pnpm jup:check -- --change jup-082-clean-develop`: verify Trello/OpenSpec traceability.
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
