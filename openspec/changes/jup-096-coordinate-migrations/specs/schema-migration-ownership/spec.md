## Purpose

Guarantee that backend and processor can migrate the shared CockroachDB database concurrently from a cold start, by giving every shared table a single owning service.

## ADDED Requirements

### Requirement: Single owner for every shared table
Every table in the shared CockroachDB database that more than one service reads or writes SHALL be created and altered by exactly one owning service's migrations. The backend SHALL own `jobs`, `tenants`, `users`, `user_tenants`, `conversations` and `messages`. The processor SHALL own `azure_cost_ingestion_runs` and `azure_cost_records`. No processor migration SHALL create, alter or drop a backend-owned table, and no backend migration SHALL create, alter or drop a processor-owned table.

#### Scenario: Processor migrates a fresh database on its own
- **WHEN** the processor applies all its migrations to an empty database where the backend has not migrated
- **THEN** its own tables and version records exist
- **AND** none of the backend-owned tables, including `jobs`, exists

#### Scenario: Backend migrates a fresh database on its own
- **WHEN** the backend applies all its migrations to an empty database where the processor has not migrated
- **THEN** `jobs` and the other backend-owned tables exist
- **AND** none of the processor-owned tables exists

### Requirement: Concurrent cold-start migration
When backend and processor apply their migrations to the same empty database at the same time, both SHALL complete without a transaction conflict and each SHALL record its own migration versions exactly once.

#### Scenario: Both services migrate an empty database simultaneously
- **WHEN** backend and processor start their migrations against the same empty database at the same instant, repeated at least 5 times
- **THEN** both services complete every run without `SerializationFailure` or any other error
- **AND** the backend and processor version tables each list their own versions once, and `jobs` exists once with the backend definition

#### Scenario: Services migrate with a small start offset
- **WHEN** the processor starts its migrations 0.5 s after the backend against an empty database, repeated at least 5 times
- **THEN** both services complete every run without error

### Requirement: Existing databases keep their data and history
Databases migrated before this change SHALL keep their tables, rows and version records unchanged when either service starts after the change, and no migration SHALL be re-applied.

#### Scenario: Database previously migrated by both services
- **WHEN** a database where backend and processor already recorded all their versions, with rows in `jobs`, is started with the changed services
- **THEN** no new version is recorded, no migration is re-applied, and the `jobs` rows and every other table are unchanged

#### Scenario: Database previously migrated only by the processor
- **WHEN** a database where only the old processor migrated (so `jobs` exists, created by processor version `001`, possibly with rows) is then migrated by the backend
- **THEN** the backend completes its migrations without error, records its versions once, and the existing `jobs` rows are preserved
