## MODIFIED Requirements

### Requirement: Self-contained synthetic anomaly dataset tool

The repository SHALL provide `scripts/synthetic_anomalies.py`, a single ASCII-only file runnable through standard input in the processor container, with the commands `apply`, `status` and `remove`. It SHALL load the dataset into the tenant `tenant-core` by default, mark every ingestion run and every record with the identifier prefix `synthetic-jup107-` and with a boolean synthetic flag on the run, and SHALL state in its output that the rows are synthetic. `remove` SHALL also delete the stored anomaly episodes and the anomaly detection state of each tenant that held this tool's rows and is left without other cost rows, because they are derived from its synthetic rows; for a tenant that still holds other cost rows it SHALL keep them and say so.

#### Scenario: Load is idempotent
- **WHEN** `apply` runs twice on an empty tenant
- **THEN** the first call loads one ingestion run and its records and reports `loaded`
- **AND** the second call writes nothing and reports `already-present`

#### Scenario: Refuses a tenant with other cost data
- **WHEN** the target tenant already holds cost rows that do not carry the prefix and the synthetic flag of this tool, including rows of the JUP-106 dataset or of the public dataset
- **THEN** `apply` loads nothing and exits with status 2 stating the reason
- **AND** a partial or other-tenant state also refuses with its state named

#### Scenario: Removal touches only its own rows
- **WHEN** `remove` runs on `tenant-core` after a detection, while the JUP-106 dataset is loaded in `tenant-growth` and `tenant-growth` has its own episodes and detection state
- **THEN** the records and runs with this tool's prefix and flag, and the episodes and detection state of `tenant-core`, are deleted
- **AND** every JUP-106 row and every episode and detection state of `tenant-growth` remain
- **AND** repeating `remove` deletes nothing and succeeds

#### Scenario: Episodes are kept when other cost data remain
- **WHEN** cost rows that are not this tool's were added to `tenant-core` after loading, and `remove` runs
- **THEN** only this tool's rows are deleted, the episodes and detection state of `tenant-core` are kept, and the output says why

#### Scenario: Reload after removal is detected again
- **WHEN** the dataset is loaded, detected, removed, loaded again and detected again
- **THEN** the second detection evaluates the whole history and opens the same episodes as the first

#### Scenario: Each tool ignores the other
- **WHEN** `synthetic_costs.py status` runs on `tenant-core` with this dataset loaded, and this tool's `status` runs on `tenant-growth` with the JUP-106 dataset loaded
- **THEN** each reports the foreign rows as real data of the tenant, never as its own

### Requirement: Dataset designed for every branch of the evaluation

The dataset SHALL contain, in currency `EUR` and one synthetic subscription, one record per service and day from 2026-09-01 to 2026-09-21, every record carrying a service name, except Networking, which has no record before 2026-09-14. The totals of the baseline period `[2026-09-01, 2026-09-08)` and the current period `[2026-09-08, 2026-09-15)` SHALL stay: Compute 1000.00 baseline and 2400.00 current; Analytics 2200.00 and 2300.00; Storage 800.00 and 820.00; Database 1500.00 and 1200.00; Tools 10.00 and 40.00; Backup a recorded zero total of 0.00 in the baseline and 300.00 current; Networking no baseline record and 600.00 current. The week `[2026-09-15, 2026-09-22)` SHALL be designed so that one detection run on an empty detection state opens exactly: Compute from 2026-09-09, still observed, P1 with 2807.71 of accumulated impact over 12 days; Database from 2026-09-16, still observed, P2 with 642.86 over 5 days; Analytics from 2026-09-10, no longer observed since 2026-09-14, P3 with 168.86 over 4 days; and no episode for Storage, Tools, Backup or Networking.

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

#### Scenario: One detection shows every severity and both observations
- **WHEN** a detection runs once on the loaded dataset with an empty detection state
- **THEN** exactly the three episodes above are stored with those figures
- **AND** the last evaluated day is 2026-09-20

#### Scenario: Limitations are visible in the data
- **WHEN** the daily figures of Tools, Backup and Networking are evaluated
- **THEN** Tools never exceeds 100.00 over its reference, Backup rises from a zero reference and Networking appears without previous spend, so none opens an episode

### Requirement: Expected values verified independently

The repository SHALL contain `docs/demo/JUP-107/esperados-anomalias.json` with the reference rules, both periods, the per-service totals and record counts, each group's expected statuses and reasons, the two expected alerts, and the expected episodes after one detection with their start, last seen day, observation, reference daily cost, accumulated impact, counted days and severity. A test that needs no database SHALL recompute every figure with exact `Decimal` arithmetic from the dataset rows, implementing the period sums and the daily rule independently, without using the backend services, and compare it with the file.

#### Scenario: Altered amount fails naming the figure
- **WHEN** one amount of the dataset or one figure of the expected file is changed
- **THEN** the test fails and names the service, the period or episode and the figure that differs

#### Scenario: Dataset and calendar stay consistent
- **WHEN** the test runs
- **THEN** every record date lies between 2026-09-01 and 2026-09-21, the two evaluation periods are consecutive and of equal length, and the last record date is not later than the UTC date of the day, failing with a clear message otherwise

#### Scenario: Identifiers are not frozen offline
- **WHEN** the expected file is read
- **THEN** it contains no alert `id`, `evidence_id` nor episode `id`, which are checked against the real endpoints when the demonstration is validated

### Requirement: Demonstration through the endpoint with honest limits

`docs/demo/JUP-107/anomalias.md` SHALL describe how to show the alerts by calling `POST /billing/anomalies/evaluate` with the reference request, the expected alerts and non-alerts with their reasons, and how to show the stored episodes in the `/anomalies` panel with one detection, and SHALL state before the first figure that every amount is synthetic, not from Azure or the public dataset. It SHALL explain that the test query compares weekly totals with configurable rules while the panel applies the daily business rule, and that the figures illustrate the rules and do not demonstrate detection quality or causes. Any script it includes SHALL read the demo password from the container environment and SHALL NOT print it.

#### Scenario: Declaration precedes figures
- **WHEN** `anomalias.md` is read from the top
- **THEN** the synthetic declaration appears before the first amount

#### Scenario: Panel limitation is explicit
- **WHEN** the limits section is read
- **THEN** it states that Analytics alerts in the test query by its weekly total while in the panel it is a single-day spike already no longer observed, and that Tools, Backup and Networking open no episode and why

#### Scenario: No credential is printed
- **WHEN** the included script runs
- **THEN** its output contains no password and no bearer token

### Requirement: Preparation and return to the initial state

The guide SHALL describe, in order: an isolated stack with new volumes, checking that `tenant-core` has no cost rows, `apply`, `status`, the request and its comparison with the expected file, opening the panel and pressing the detection action with its comparison with the expected episodes, `remove` repeated, the tenant empty again with no episodes and no detection state, and the stack and volumes deleted, with a warning that the synthetic dataset and the JUP-065 demo must not share a tenant at the same time.

#### Scenario: State after removal
- **WHEN** the guide is followed to the end
- **THEN** `tenant-core` has no cost rows, no anomaly episode and no detection state, `tenant-growth` is unchanged and no container or volume of the isolated project remains
