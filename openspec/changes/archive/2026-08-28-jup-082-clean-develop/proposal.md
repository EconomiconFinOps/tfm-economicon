JUP: JUP-082
Trello: https://trello.com/c/QiZTzj7D

## Why

The shared `develop` branch contains valid application and documentation changes mixed with personal assistant configuration, an unrelated Windows executable and a second task namespace. This makes collaboration harder, duplicates Trello and prevents strict OpenSpec validation.

## What Changes

- Remove personal assistant skills, agent-specific generated commands, vendor memory tooling and checked-in executable binaries.
- Remove the duplicate task namespace and replace its tooling with Trello-aligned `JUP-XXX` traceability checks.
- Preserve OpenSpec, existing implemented capability specifications, architecture documentation and the technical content of the frontend migration spike.
- Update obsolete workflow references in the frontend migration spike without changing its migration findings or technical recommendations.
- Keep backend health improvements, demo authentication normalization and all other application code unchanged.
- Add reproducible repository-hygiene checks and document the common Trello/OpenSpec/GitHub workflow.

## Capabilities

### New Capabilities

- `repository-jup-hygiene`: The repository enforces a tool-neutral, Trello-aligned OpenSpec workflow and rejects unrelated tracked assets.

### Modified Capabilities

- None. Existing application capabilities are preserved without functional changes.

## Impact

- Affected areas: root repository guidance, package scripts, OpenSpec configuration, ADR documentation and repository maintenance tools.
- No product code, runtime behavior, infrastructure or deployment configuration is changed.
- Existing branches created from the current `develop` may require rebasing after this cleanup is merged.
