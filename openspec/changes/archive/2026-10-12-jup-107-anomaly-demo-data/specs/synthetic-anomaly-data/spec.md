## ADDED Requirements

### Requirement: Self-contained synthetic anomaly dataset tool

The repository SHALL provide `scripts/synthetic_anomalies.py`, a single ASCII-only file runnable through standard input in the processor container, with the commands `apply`, `status` and `remove`. It SHALL load the dataset into the tenant `tenant-core` by default, mark every ingestion run and every record with the identifier prefix `synthetic-jup107-` and with a boolean synthetic flag on the run, and SHALL state in its output that the rows are synthetic.

#### Scenario: Load is idempotent
- **WHEN** `apply` runs twice on an empty tenant
- **THEN** the first call loads one ingestion run and its records and reports `loaded`
- **AND** the second call writes nothing and reports `already-present`

#### Scenario: Refuses a tenant with other cost data
- **WHEN** the target tenant already holds cost rows that do not carry the prefix and the synthetic flag of this tool, including rows of the JUP-106 dataset or of the public dataset
- **THEN** `apply` loads nothing and exits with status 2 stating the reason
- **AND** a partial or other-tenant state also refuses with its state named

#### Scenario: Removal touches only its own rows
- **WHEN** `remove` runs while the JUP-106 dataset is loaded in `tenant-growth`
- **THEN** only the records and runs with this tool's prefix and flag are deleted
- **AND** every JUP-106 row and every real row remains
- **AND** repeating `remove` deletes nothing and succeeds

#### Scenario: Each tool ignores the other
- **WHEN** `synthetic_costs.py status` runs on `tenant-core` with this dataset loaded, and this tool's `status` runs on `tenant-growth` with the JUP-106 dataset loaded
- **THEN** each reports the foreign rows as real data of the tenant, never as its own

### Requirement: Dataset designed for every branch of the evaluation

The dataset SHALL contain, in currency `EUR` and one synthetic subscription, records dated in a baseline period `[2026-09-01, 2026-09-08)` and a current period `[2026-09-08, 2026-09-15)`, every record carrying a service name and no record dated outside those periods, with these totals per service: Compute 1000.00 baseline and 2400.00 current; Analytics 2200.00 and 2300.00; Storage 800.00 and 820.00; Database 1500.00 and 1200.00; Tools 10.00 and 40.00; Backup a recorded zero amount of 0.00 in the baseline and 300.00 current; Networking no baseline record and 600.00 current.

#### Scenario: Reference rules produce exactly two alerts
- **WHEN** the anomaly evaluation runs for the current period grouped by service in `EUR` with absolute threshold 2000.00, deviation 50.00 percent and minimum absolute increase 100.00
- **THEN** exactly two alerts are returned: Compute with both `absolute_threshold` and `period_increase`, and Analytics with `absolute_threshold` only
- **AND** the evaluation reports seven groups, the data quality of both periods as `available` with zero records missing a dimension, and each alert with `cause_status` `not_established`

#### Scenario: Each non-alerting group exercises a different branch
- **WHEN** the same evaluation is read for the five groups without alert
- **THEN** Storage and Database are `below` on both rules, with Database showing a delta of -300.00 and -20.00 percent
- **AND** Tools shows delta 30.00 and 300.00 percent but deviation `below` because 30.00 is under the minimum increase of 100.00
- **AND** Backup shows deviation `baseline_nonpositive` with its recorded zero baseline
- **AND** Networking shows deviation `baseline_missing`

#### Scenario: Percentage is exact for the boundary group
- **WHEN** Analytics is evaluated with a deviation threshold of 4.55 percent and minimum increase 100.00
- **THEN** its delta of 100.00 over a baseline of 2200.00 does not reach 4.55 percent before rounding, because the comparison is made by cross-multiplication
- **AND** the expected file states 4.55 percent only as the rounded display value

### Requirement: Expected values verified independently

The repository SHALL contain `docs/demo/JUP-107/esperados-anomalias.json` with the reference rules, both periods, the per-service totals and record counts, each group's expected statuses and reasons, and the two expected alerts. A test that needs no database SHALL recompute every figure with exact `Decimal` sums from the dataset rows, without using the anomaly evaluation service, and compare it with the file.

#### Scenario: Altered amount fails naming the figure
- **WHEN** one amount of the dataset or one figure of the expected file is changed
- **THEN** the test fails and names the service, the period and the figure that differs

#### Scenario: Dataset and calendar stay consistent
- **WHEN** the test runs
- **THEN** every record date lies inside one of the two periods, the two periods are consecutive and of equal length, and the current end date is not later than the UTC date of the day, failing with a clear message otherwise

#### Scenario: Identifiers are not frozen offline
- **WHEN** the expected file is read
- **THEN** it contains no alert `id` nor `evidence_id`, which are checked against the real endpoint when the demonstration is validated

### Requirement: Demonstration through the endpoint with honest limits

`docs/demo/JUP-107/anomalias.md` SHALL describe how to show the alerts by calling `POST /billing/anomalies/evaluate` with the reference request, the expected alerts and non-alerts with their reasons, and SHALL state before the first figure that every amount is synthetic, not from Azure or the public dataset. It SHALL state that the `/anomalies` panel shows fixed demonstration data and does not read this endpoint, and that the figures illustrate the rules and do not demonstrate detection quality or causes. Any script it includes SHALL read the demo password from the container environment and SHALL NOT print it.

#### Scenario: Declaration precedes figures
- **WHEN** `anomalias.md` is read from the top
- **THEN** the synthetic declaration appears before the first amount

#### Scenario: Panel limitation is explicit
- **WHEN** the limits section is read
- **THEN** it names the `/anomalies` panel and says it does not show these alerts

#### Scenario: No credential is printed
- **WHEN** the included script runs
- **THEN** its output contains no password and no bearer token

### Requirement: Preparation and return to the initial state

The guide SHALL describe, in order: an isolated stack with new volumes, checking that `tenant-core` has no cost rows, `apply`, `status`, the request and its comparison with the expected file, `remove` repeated, the tenant empty again and the stack and volumes deleted, with a warning that the synthetic dataset and the JUP-065 demo must not share a tenant at the same time.

#### Scenario: State after removal
- **WHEN** the guide is followed to the end
- **THEN** `tenant-core` has no cost rows, `tenant-growth` is unchanged and no container or volume of the isolated project remains

### Requirement: No interference with other work

The change SHALL NOT modify `apps/`, `scripts/synthetic_costs.py`, the JUP-106 dataset or documents, `docs/demo/JUP-065/`, the first part of `docs/demo/JUP-107/` or the public dataset, and SHALL include no secret and no binary.

#### Scenario: Protected files are unchanged
- **WHEN** the final diff against `develop` is read
- **THEN** it contains no path under `apps/` and none of the protected files, and CI runs the new test through a named step

#### Scenario: Removing the CI step breaks the check
- **WHEN** the CI workflow test is run after removing the new step
- **THEN** it fails
