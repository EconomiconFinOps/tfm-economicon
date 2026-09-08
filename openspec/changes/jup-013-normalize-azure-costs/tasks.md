## 1. Contract and reconciliation

- [x] 1.1 JUP-013 audit the JUP-076/077 client, normalizer and persistence
- [x] 1.2 JUP-013 define explicit optional FinOps fields and provider aliases
- [x] 1.3 JUP-013 refine Trello scope, dependencies and rotating roles

## 2. Implementation

- [x] 2.1 JUP-013 promote dimensions, consumption and tags in the normalizer
- [x] 2.2 JUP-013 make canonical hashes independent of provider aliases
- [x] 2.3 JUP-013 add migration 003 with backfill and analysis indexes
- [x] 2.4 JUP-013 persist and fetch the explicit normalized columns
- [x] 2.5 JUP-013 use resource group and service in the default cost slice

## 3. Validation and publication

- [x] 3.1 JUP-013 add normalization, migration and repository tests
- [x] 3.2 JUP-013 run all service, governance and build validations
- [x] 3.3 JUP-013 validate the migration and ingestion on dockerserver
- [x] 3.4 JUP-013 publish a pull request toward develop and pass remote CI
- [ ] 3.5 JUP-013 obtain pairing, review and functional validation evidence

## 4. Validation after updating PR #14 from develop

- [x] 4.1 JUP-013 apply migrations 001 through 003 to an isolated fresh
  CockroachDB database and verify normalized record persistence and retrieval
- [x] 4.2 JUP-013 upgrade an isolated database containing migrations 001/002
  and representative legacy rows; verify backfill, indexes, unchanged record
  identities and costs, and equal totals per tenant, subscription and currency
- [x] 4.3 JUP-013 verify typed fields, tags, optional consumption, unknown
  dimensions, equivalent and conflicting aliases, zero and negative values,
  and invalid-input rejection without partial cost persistence
- [x] 4.4 JUP-013 repeat ingestion with the same tenant, subscription, query
  and input; verify stable run identity, row count, source hashes and cost totals
- [ ] 4.5 JUP-013 verify all seven existing CI checks on the updated PR #14:
  JUP policy, OpenSpec, Python tests (azure-cost-api), Python tests (backend),
  Python tests (processor), Frontend build and Frontend type check
- [x] 4.6 JUP-013 fix the existing-table migration 003 DDL visibility defect
  using a migration-local non-transactional opt-in in the processor runner;
  keep unmarked migrations transactional and record each version only after
  its upgrade succeeds
- [x] 4.7 JUP-013 verify fresh creation and the six-row 001/002 upgrade on
  isolated CockroachDB 24.1.11, then verify retry after committed DDL, backfill
  and partial index creation without data loss or false completion
- [x] 4.8 JUP-013 verify version-insert failure and subsequent retry, committed
  marker handling after lost acknowledgement, completed-version skipping,
  default transactional rollback, and isolation from 003's autocommit mode
- [x] 4.9 JUP-013 verify numeric legacy tags, complete mixed tag sources and
  retained typed values across interrupted backfill; complete partial consumption
  only when its retained component matches the source pair
