# JUP-102 — Effective vector dimension

Trello: https://trello.com/c/4OJ1OK53
Verification date: 2026-10-10. Base: `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
Technical implementation evidence; not a `Validacion JUP-102` human review.
Delivery: [PR #108 (draft)](https://github.com/EconomiconFinOps/tfm-economicon/pull/108),
implementation commit `bfffbea4be94ad9e8a01a687fc3cd28e58fdd606`. The draft preserves
the assigned leader's handoff and the need for independent human decisions.

## Reproduction before the correction

The original three production modules (runner, store and initial migration) were
loaded from the base commit into a separate Python process. On a new, dedicated
PostgreSQL database, only the selected env file contained the dimension:

```text
Settings.embedding_dimension: 16
EMBEDDING_DIMENSION in process environment: false
chunk_embeddings.embedding atttypmod: 8
vector_schema_migrations: 001, 002
StartupError: Configured embedding dimension differs from the stored vector schema;
restore the matching configuration or reindex into a new database.
```

The regression suite against those original modules also fails four cases:
env-file dimension, explicit Settings override, environment change after Settings
resolution, and a missing explicit migration argument. Three unchanged cases pass.

## Scope and criterion evidence

| Card criterion | Evidence / current result |
| --- | --- |
| Reproduce PostgreSQL/pgvector with dimension 16 only in the file | Reproduced above on the original base; no duplicate export. |
| New schema matches Settings and starts | Real `test_new_schema_settings_sources_and_real_retrieval[dotenv-16]` checks vector(16), ledger 001/002 and successful initialization. |
| Default, environment, file and precedence | Offline and real parameterized tests cover 8 default, 16 environment/file, environment 24 over file 16, and explicit Settings 32 over both. Offline test also changes the environment to 64 after resolving Settings 16. |
| Existing volume accepts matching settings and rejects mismatches without loss | Snapshot comparison includes column OIDs/types/dimensions, indexes, ledger timestamps and every document/chunk/vector. Repeated initialization is identical; mismatches 16→8, 16→32 and legacy 8→16 raise actionable StartupError with unchanged snapshots. |
| Repeatable migrations, write/retrieval and tenant isolation | Real processor writer, MockEmbeddingProvider and actual backend PgVectorQueryStore exercise two synthetic tenants, exact cosine ranking, foreign nearest match exclusion and an empty tenant. Existing replacement/collision tests are run separately. |
| Update runbook and resolve RF-021-001 after verification | Runbook describes effective Settings and removes duplicate export for corrected code; finding records technical correction separately from human acceptance. |
| Archived OpenSpec, green CI, separate reviews, merge and evidence before Done | Technical specification is archived in this branch. CI, human review by Victor, separate validation assigned to Alejandro, pairing evidence from Paris and integration by Lucia are recorded as pending until actually observed. No claim of Done or approval. |

## Reproduction commands

Use an exclusive disposable instance from the pinned image in
`infra/vector/compose.yaml`, with an empty `postgres` database and loopback port
55432 (SSH tunnel when the Docker daemon is remote). No JUP-021 volume is used.
Set `JUP102_VECTOR_TEST_URL` and, for legacy fixtures, `JUP086_VECTOR_TEST_URL`
to that authenticated `postgresql+psycopg` URL. Do not print or commit credentials.
Run PostgreSQL suites serially; each fixture creates/drops only its UUID database.

```bash
# From apps/processor, after installing requirements-dev.txt
python -m pytest tests/test_vector_settings_migrations.py tests/test_vector_settings_pgvector.py -v
python -m pytest tests -q -ra
# From apps/backend, after installing requirements-dev.txt
python -m pytest tests/test_tenant_isolation_vector.py tests/test_retrieval_contract_pgvector.py -q -ra
# From repository root
corepack pnpm jup:check:all
corepack pnpm jup:cleanup:check
node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs tools/jup-check.test.mjs tools/jup-cleanup-check.test.mjs
corepack pnpm openspec:validate
git diff --check
```

On Windows, pytest used unique `--basetemp` directories under the isolated copy
because the sandbox cannot read the shared temporary directory. An interrupted
run left one synthetic UUID database; subsequent fixture guards correctly refused
it. That specific database was removed and the suites were rerun serially.
These preparation failures do not count as successful application checks.

## Environment and limitations

Results obtained on the corrected source:

- GitHub Linux CI on `037295524f3708ca04cd0e6fbb67e6c77c9b1b85`: **7/7 SUCCESS**,
  [run 38036880694](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38036880694).
  Backend, processor, Azure API, frontend build/types, OpenSpec and JUP policy pass.
  This later evidence update changes documentation only. JUP reviews remains
  blocked pending the two independent human decisions.

- Processor complete suite with both PostgreSQL opt-ins: **467 passed, 53 skipped**.
  This includes all eight new real scenarios and the existing four vector isolation tests.
  Skips require CockroachDB or the explicit LiteLLM Docker fixture and are not passes.
- Initial directed run before adding the legacy 8→16 parameter: **33 passed**.
- Backend real vector isolation/retrieval suites: **17 passed**.
- Backend full suite on Windows: **732 passed, 34 skipped, 166 failed**. The first
  failure was reproduced unchanged on an extracted `origin/develop` baseline:
  `test_health_provider_admission_jup047.py::test_uncertifiable_or_restart_state_never_sends[price_verified]`.
  Its socket guard blocks Windows asyncio's internal socketpair. Other failures
  involve health checks, DNS subprocesses and observation budgets; these were not
  individually reproduced on the baseline and are not claimed fixed here.
  No backend production file is changed. The separate 17 real vector tests pass.
- Governance tests: **95 passed**. JUP traceability and repository hygiene passed.
- OpenSpec before archive: **56 passed, 0 failed**; after archive: **55 passed, 0 failed**.
  Processor compileall and `git diff --check` passed.

- PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2), pgvector 0.8.6.
- Image `pgvector/pgvector:pg17@sha256:cf134a767f474095eeba57e0117be8e568e011a63f33fbf252f14c9b760f8e6f`.
- Windows Python 3.11.9, pytest 9.1.1, SQLAlchemy 2.0.54, psycopg 3.3.6,
  pydantic 2.14.0, pydantic-settings 2.15.0, python-dotenv 1.2.4.
- Node 24.14.1, pnpm 9.0.0, OpenSpec 1.8.0.
- Offline SQL recorder is an explicit test double. It proves configuration flow;
  only the opt-in PostgreSQL tests prove real storage/retrieval compatibility.
- No real model/provider, production data, CockroachDB service, RabbitMQ service,
  capacity benchmark, deployment, restore or HA verification is claimed.
- Existing 001-only databases retain the historical application of pending 002.
  This correction adds no migration and does not resize already created columns.
- The contribution is prepared on an isolated branch under the implementation
  dispatch. Trello role assignments are preserved, not proof of participation.
  Automated or agent checks are not independent human reviews.
