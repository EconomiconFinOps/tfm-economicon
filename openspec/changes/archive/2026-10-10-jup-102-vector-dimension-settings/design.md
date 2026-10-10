## Context

JUP-102 resolves RF-021-001 after JUP-021. Both API and worker already construct
PgVectorStore with the dimension resolved by Settings. Re-reading environment
variables in migration 001 creates a second, inconsistent source of configuration.

## Decisions

1. MigrationRunner accepts optional keyword arguments keyed by migration version.
   Existing relational migrations and vector migration 002 retain upgrade(connection).
2. PgVectorStore supplies its dimension to 001 as a required keyword argument.
   The migration imports neither Settings nor os and cannot silently fall back to 8.
   Settings retains explicit constructor > environment > selected env file > default.
3. Applied versions remain skipped. There is no new migration, ALTER COLUMN, data
   conversion or vector deletion. The existing StartupError and dimension checks remain.
4. Real tests allocate and remove only UUID databases on an explicitly selected,
   empty disposable pgvector instance. They compare persisted schema, indexes, ledger
   and rows across matching restarts and incompatible startup attempts.

## Limits and rollout

The guard remains after the existing migration runner. This patch does not change
the historical application of pending migration 002 to an old 001-only database.
Existing fully migrated volumes retain schema and data. Operators still back up
and serialize migration processes as documented by JUP-021.

Databases already created with vector(8) by the defect are not repaired in place.
Restore compatible Settings or explicitly provision and reingest into another database.
Review, independent validation and merge remain human steps under CONTRIBUTING.md.
