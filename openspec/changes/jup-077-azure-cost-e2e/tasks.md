## 1. Normalize And Persist Public Azure Costs

- [x] 1.1 Normalize finite positive, zero and negative costs, strict currency
  codes, optional usage dates and preserved Azure query dimensions.
- [x] 1.2 Add CockroachDB run/record migration, tenant indexes, safe statuses,
  foreign keys and the native SQLAlchemy Cockroach dialect.
- [x] 1.3 Generate deterministic tenant/query/row identities and atomically
  complete idempotent reruns without duplicated records.

## 2. Secure Operational Outcomes

- [x] 2.1 Reject unsafe tenant/subscription scopes before persistence and keep
  successful mutations restricted to their original scope.
- [x] 2.2 Mark client/normalization failures explicitly and transactionally
  remove stale records from failed reruns.
- [x] 2.3 Record safe page/retry/row metrics, preserve bearer secrecy and bind
  persistent development CockroachDB endpoints to loopback only.

## 3. Validate, Document And Integrate

- [x] 3.1 Verify processor, simulator, shared-contract, workspace, OpenSpec
  and repository traceability suites.
- [x] 3.2 Execute real Docker dataset-to-Cockroach ingestion, idempotent rerun,
  tenant isolation and controlled authentication failure on `dockerserver`.
- [x] 3.3 Publish `test/JUP-077-azure-cost-e2e` as a pull request targeting
  `develop` and link Trello, architectural decisions and validation evidence.
