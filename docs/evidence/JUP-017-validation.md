# JUP-017: positive-cost tag coverage — author evidence

Verified 2026-10-03. Trello: https://trello.com/c/3wiy5PJS.
Branch: `feat/JUP-017-tagged-cost-coverage`, based on develop `d6fc408`.
This records the author's checks, not independent `Validacion JUP-017`.

## Approved scope and limits

The user explicitly approved the five-tag proposal and authorized continuation
without waiting for Paris. No approval is attributed to Paris. JUP-015 remains
the organizational taxonomy follow-up; it does not block this version-1 metric.
Required canonical tags: owner, environment, application, cost_center, project.
Four identifiers use the documented nonempty portable-ID format; environment
uses the explicit development/test/staging/production vocabulary. This checks
metadata rules, not membership of a corporate catalog or accounting accuracy.

GET /billing/tag-coverage uses the existing authenticated active-tenant guard.
Both ISO date boundaries or neither; omitted selects current UTC month.
Only completed matching-tenant/subscription records contribute. Undated records
are counted and excluded; multiple completed runs per subscription/date return
409 with no amounts. Never sum currencies or alternative dataset exports.

P is positive observed pretax cost; T complies with every rule; U=P-T.
Coverage is T/P, not a count of tagged rows or division by net spend.
Signed negative adjustments and net costs are shown separately.
No positive charges means null/N-D. Percentage complement totals 100.00.
Amounts are independently rounded to two decimals; raw aggregates reconcile,
displayed subtotals may differ through rounding. Source metadata omitted by
aggregated ingestion cannot be reconstructed by this endpoint.

## Acceptance evidence

| Criterion | Evidence |
| --- | --- |
| Five minimum tags, partial and invalid values | Real SQL with complete versus three-tag controls; null, blank, whitespace, placeholders, non-string, invalid identifiers/environment |
| Positive-cost weighting and credits | 80 compliant + 20 partial - 30 adjustment -> 80/20, net 70 |
| Total net zero | 0.006 compliant + 0.004 partial - 0.01 -> 60/40 despite displayed net zero; browser uses 60+40-100 |
| Zero, negative-only, empty | JPY zero and GBP -20 -> null with separate reasons; empty -> no currency entries |
| Currency and exact amounts | EUR/USD/GBP/JPY separate; 9007199254740993.005 USD -> exact decimal string 9007199254740993.01 |
| Tenant/period/run scope | Foreign tenant, mismatched runs/subscriptions, unfinished/failed runs, outside interval and undated records cannot enter sums |
| Auth and dates | 401/403/400 and malformed/reversed/incomplete dates before the cost query |
| Duplicate sources | Completed overlapping run -> 409 ambiguous_cost_source without monetary fields |
| Dashboard states and selection | Component tests: loading, N/D, empty, error, exact amounts, period race and tenant switch; terminal 409 not retried |
| Existing billing compatibility | All 15 existing billing tests pass with seven actual CockroachDB cases |

Controls are explicit synthetic data in
`apps/backend/tests/fixtures/tag_coverage.json`. Public Microsoft CSVs and
the simulator's allowed-tag mapping are unchanged. In the previously audited
Actual source, 0/135253 rows have all five required tags; any-tag coverage was
49.11% of positive cost. That is a historical local-source audit (2026-10-02),
not a fresh deployment metric.

## Executed checks

- Windows Python 3.14, isolated CockroachDB v24.1.11:
  `python -m pytest tests/test_tag_coverage.py tests/test_billing_summary.py -q`
  from apps/backend: **44 passed** (28 real SQL cases, 16 SQLite route cases).
- Final normalized-marker regression plus positive-weighting/invalid-value cases:
  **20 passed** on real CockroachDB after reserving None/True/False as invalid.
- Linux Python 3.12 (same major/minor as CI), dedicated ephemeral container:
  backend **337 passed, 38 skipped**; processor **414 passed, 55 skipped**;
  simulator **59 passed**. Integration tests without their explicit isolated
  services skip in this broad run; the 28 billing/coverage SQL cases above ran.
- Frontend full suite with
  `corepack pnpm --filter @finops/frontend exec vitest run --maxWorkers=2 --minWorkers=1`:
  **442 passed** before the additional tenant-switch coverage case; the final
  five coverage component cases are verified separately.
- Frontend build, lint and all three TypeScript configurations: pass.
  Existing Vite bundle-size warning remains; no bundle splitting in this scope.
- OpenSpec strict validation, JUP traceability/hygiene, PR policy tests, CI
  workflow tests, repository governance tests and git diff whitespace: pass.

The first broad Windows Python 3.14 run had platform/runtime failures in existing
DNS resolver and recursive-JSON tests. They pass in the Linux/Python 3.12 run.
The first highly parallel frontend run had four timeout failures; the full suite
passes with two workers. Turbo's root commands selected a conflicting bundled
pnpm version and failed before checks; equivalent per-service commands above ran
instead. No product or test changes were made to hide these environment failures.

## Browser checks

Playwright Chromium exercised the actual Vite application at 1440px and 390px
using explicitly intercepted synthetic API responses. SQL correctness and auth
are evidenced separately above; this is not an end-to-end deployed backend test.
Confirmed: net-zero retains 60/40 coverage, signed adjustments, tenant request
header, mobile panel has no horizontal overflow, negative-only N/D, 409 hides
previous amounts, no page errors. Desktop and mobile screenshots were inspected.

Screenshots and reproducible local audit live outside Git under the workspace
`materiales/07-evidencias/JUP-017-etiquetado-2026-10-02/`.
The browser script is temporary, not a new application dependency.

## Reproduction

Install requirements-dev.txt separately in each Python service and run
`python -m pytest tests -q`. To exercise SQL, create an exclusively owned
CockroachDB 24.1.11 test node, set
`cluster.organization = 'processor-integration-tests'`, and supply
`JUP086_COCKROACH_TEST_URL` with localhost, a nondefault port, root/defaultdb
and sslmode=disable. The fixture checks ownership and creates/drops only its
unique test database. Never point this at shared or production data.

Run frontend test/typecheck/lint/build with corepack pnpm. In the executive
dashboard, select the period and expand “Cobertura de etiquetas FinOps”.
Datasets ingested without required tags should show noncompliance, not inferred
owners/application. No ingestion mutation or automatic tag repair is exposed.

## Pending independent delivery work

Lucia's assigned pairing/co-authorship has not been evidenced by this automation.
Paris's assigned PR review and Victor's validation remain human/team work.
No merge, task closure or completion of JUP-015 is claimed.
