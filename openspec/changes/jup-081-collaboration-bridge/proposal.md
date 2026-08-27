JUP: JUP-081
Trello: https://trello.com/c/g91V6TXp

## Why

The controlled Trello and Discord bridge is deployed on Dockerserver but was
never integrated into the canonical repository. Its Discord pagination also
fails with HTTP 429 because it ignores the provider retry interval. The bridge
must become reproducible, reviewable and resilient without publishing secrets
or enabling implicit writes.

## What Changes

- Version the existing bridge, container definition and safe example settings.
- Retry HTTP 429 responses using Discord `retry_after` or `Retry-After`.
- Bound retry count and delay so synchronization cannot wait indefinitely.
- Test pagination, retries, write guards, snapshots and non-destructive writes.
- Run the bridge tests within the existing OpenSpec CI context.
- Document the on-demand Dockerserver workflow and troubleshooting.

## Capabilities

### New Capabilities

- controlled-collaboration-bridge: authenticated, bounded access to the project
  Trello board and Discord channel.

### Modified Capabilities

- None.

## Out of Scope

- Turning the bridge into an Economicon production service.
- Storing credentials, snapshots or personal agent configuration in Git.
- Sending Discord messages without explicit authorization.
- Deleting Trello or Discord content.

## Impact

Adds a standard-library Python tool under `tools/collaboration`, an ignored data
directory, tests, CI coverage, OpenSpec and validation evidence. Existing
application services and their six branch-protection check contexts remain
unchanged.
