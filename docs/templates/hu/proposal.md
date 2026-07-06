# HU Proposal

Use this as the PM/product handoff artifact. Create it at:

```txt
openspec/changes/hu-NNN-slug/proposal.md
```

Do not add `## Human Approval` while the HU only has this proposal. Pre-code approval should be added after the technical owner generates and reviews `specs`, `design.md`, and `tasks.md`.

```md
## Why

<Explain the user/business problem, who is affected, current pain, and why this should be done now.>

Example:
Operators need <capability> because today <problem>. This causes <impact> and blocks <outcome>.

## User / Actor

- Primary actor: <user, operator, admin, system, worker, etc.>
- Secondary actors: <other users/systems affected or "none">
- Tenant/context: <tenant, role, plan, environment, or "not tenant-scoped">

## Goal

This HU is successful when:

- <observable outcome 1>
- <observable outcome 2>
- <observable outcome 3>

## What Changes

- <expected behavior/product change 1>
- <expected behavior/product change 2>
- <expected behavior/product change 3>

## Out of Scope

- <explicitly excluded behavior 1>
- <explicitly excluded behavior 2>
- <candidate follow-up HU if already known>

## Acceptance Criteria

- **WHEN** <actor/system action or condition>
  **THEN** <observable expected result>

- **WHEN** <edge case, permission case, empty state, failure, etc.>
  **THEN** <observable expected result>

- **WHEN** <another important scenario>
  **THEN** <observable expected result>

## Architectural Impact

- Frontend: <yes/no/likely downstream; explain expected UI/client impact>
- Backend: <yes/no; explain expected API/business logic impact>
- Processor: <yes/no; explain expected worker/pipeline impact>
- Infra/DB: <yes/no/limited; explain expected database, queue, pgvector, config, or migration impact>

## Data / Inputs

- Required data: <fields, entities, payloads, files, params, or "none">
- Optional data: <optional fields or "none">
- Source: <frontend, backend, processor, RabbitMQ, external API, user input, etc.>
- Constraints: <format, limits, validation, tenant rules, or "unknown">

## UX / API Expectations

- UI expectation: <screen/action/state/message or "not applicable">
- API expectation: <endpoint/contract if known or "technical owner to define">
- Error/empty states: <expected user/system behavior>

## Capabilities

### New Capabilities

- `<suggested-capability-name>`: <new observable behavior this HU introduces>

### Modified Capabilities

- `<existing-capability-name>`: <existing behavior this HU changes>
- None.

## Impact

- Product area: <frontend/backend/processor/infra/docs>
- Users affected: <who sees or depends on this>
- Permissions/security impact: <none or detail>
- Multi-tenant impact: <none or detail>
- AI/cost impact: <none or detail>
- Backward compatibility: <compatible/no compatible/unknown>

## Risks / Unknowns

- <risk, dependency, ambiguity, or technical question 1>
- <risk, dependency, ambiguity, or technical question 2>

## Priority / Delivery Notes

- Priority: <low/medium/high/critical>
- Suggested carril: light | standard | hotfix
- Deadline or dependency: <date/dependency or "none">
- Related issue/design/customer request: <link/reference or "none">
```
