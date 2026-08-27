## Purpose

Provide reproducible and controlled access to the project collaboration systems
without exposing credentials or granting implicit write authority.

## ADDED Requirements

### Requirement: Controlled credentials
The bridge SHALL load Discord and Trello credentials at runtime and SHALL NOT
store credentials or snapshots in the repository.

#### Scenario: Repository is cloned without operator secrets
- **WHEN** a contributor runs the bridge without a configured environment
- **THEN** it fails with the missing variable names and does not contact either provider

### Requirement: Bounded rate-limit recovery
The bridge SHALL retry HTTP 429 using JSON `retry_after` or the `Retry-After`
header with bounded attempts and delay.

#### Scenario: Discord limits a paginated request
- **WHEN** a page returns HTTP 429 and a retry interval
- **THEN** the bridge waits for that interval and retries the same page without losing prior pages

#### Scenario: Discord remains rate limited
- **WHEN** the retry budget is exhausted
- **THEN** synchronization fails explicitly instead of waiting indefinitely

### Requirement: Explicit non-destructive writes
The bridge SHALL require both a server write switch and per-command confirmation
and SHALL expose no delete operation.

#### Scenario: A write lacks one authorization gate
- **WHEN** the server switch or command confirmation is absent
- **THEN** the bridge rejects the write before contacting the provider

### Requirement: Reproducible snapshots
The bridge SHALL generate local JSON and Markdown snapshots from the configured
Discord channel and Trello board.

#### Scenario: A full synchronization succeeds
- **WHEN** valid read credentials are configured
- **THEN** latest and timestamped snapshots are written only to the ignored data directory
