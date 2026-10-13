## MODIFIED Requirements

### Requirement: Self-contained synthetic anomaly dataset tool

The synthetic anomaly dataset SHALL be loaded, inspected and removed through the single entry point `scripts/demo_data.py` of the demo data capability, with the commands `apply`, `status` and `remove`, and SHALL NOT be loaded by a separate script that writes rows into the database. The dataset SHALL be loaded into the tenant `tenant-core` by default, every row SHALL belong to a subscription with the reserved prefix `synthetic-` listed in the demo manifest, and the tool SHALL state in its output that the rows are synthetic. `remove` SHALL also delete the stored anomaly episodes and the anomaly detection state of each tenant that held this dataset's rows and is left without other cost rows, because they are derived from its synthetic rows; for a tenant that still holds other cost rows it SHALL keep them and say so.

#### Scenario: Load is idempotent
- **WHEN** `apply` runs twice on an empty tenant
- **THEN** the first call loads the ingestion runs and records through the ingestion CLI and reports `loaded`
- **AND** the second call writes nothing and reports `already-present`

#### Scenario: Refuses a tenant with other cost data
- **WHEN** the target tenant already holds cost rows of a subscription that is not in the manifest, including rows of the public dataset
- **THEN** `apply` loads nothing and exits with status 2 stating the reason
- **AND** a partial or other-tenant state also refuses with its state named

#### Scenario: Removal touches only its own rows
- **WHEN** `remove` runs on `tenant-core` after a detection, while the cost dataset is loaded in `tenant-growth` and `tenant-growth` has its own episodes and detection state
- **THEN** the records and runs of the anomaly subscription, and the episodes and detection state of `tenant-core`, are deleted
- **AND** every row of `tenant-growth` and every episode and detection state of `tenant-growth` remain
- **AND** repeating `remove` deletes nothing and succeeds

#### Scenario: Episodes are kept when other cost data remain
- **WHEN** cost rows that are not this dataset's were added to `tenant-core` after loading, and `remove` runs
- **THEN** only this dataset's rows are deleted, the episodes and detection state of `tenant-core` are kept, and the output says why

#### Scenario: Reload after removal is detected again
- **WHEN** the dataset is loaded, detected, removed, loaded again and detected again
- **THEN** the second detection evaluates the whole history and opens the same episodes as the first

#### Scenario: Each tool ignores the other
- **WHEN** `status` reports the anomaly dataset on `tenant-growth`, where the cost dataset is loaded, and the cost dataset on `tenant-core`, where the anomaly dataset is loaded
- **THEN** each report counts only the rows of its own subscriptions as its own and shows the other dataset's rows as foreign
- **AND** removing one dataset never deletes rows of the other

### Requirement: Dataset designed for every branch of the evaluation

The dataset SHALL contain, in currency `EUR` and one synthetic subscription, one record per service and day from 2026-09-01 to 2026-10-30, every record carrying a service name, except Networking, which has no record before 2026-09-14. The figures of the days from 2026-09-01 to 2026-09-21 SHALL be exactly those of the previous version, so the totals of the baseline period `[2026-09-01, 2026-09-08)` and the current period `[2026-09-08, 2026-09-15)` stay: Compute 1000.00 baseline and 2400.00 current; Analytics 2200.00 and 2300.00; Storage 800.00 and 820.00; Database 1500.00 and 1200.00; Tools 10.00 and 40.00; Backup a recorded zero total of 0.00 in the baseline and 300.00 current; Networking no baseline record and 600.00 current. With the reference date 2026-09-22, one detection run on an empty detection state SHALL open exactly: Compute from 2026-09-09, still observed, P1 with 2807.71 of accumulated impact over 12 days; Database from 2026-09-16, still observed, P2 with 642.86 over 5 days; Analytics from 2026-09-10, no longer observed since 2026-09-14, P3 with 168.86 over 4 days; and no episode for Storage, Tools, Backup or Networking. The days from 2026-09-22 to 2026-10-30 SHALL be designed so that a detection that reaches 2026-10-30 opens at least two further episodes, each with figures fixed in the expected file, and so that no figure of the days before 2026-09-22 changes.

#### Scenario: Reference rules produce exactly two alerts
- **WHEN** the anomaly evaluation runs for the current period grouped by service in `EUR` with absolute threshold 2000.00, deviation 50.00 percent and minimum absolute increase 100.00, with the reference date 2026-09-22 or later
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
- **WHEN** a detection runs once on the loaded dataset with an empty detection state and the reference date 2026-09-22
- **THEN** exactly the three episodes above are stored with those figures
- **AND** the last evaluated day is 2026-09-21

#### Scenario: Reaching the end of the dataset opens the further episodes
- **WHEN** a detection runs on an empty detection state with the reference date 2026-10-31
- **THEN** the three episodes above are stored with the same start days and the figures that the expected file gives for 2026-10-30, and at least two further episodes appear with the figures of the expected file
- **AND** the last evaluated day is 2026-10-30

#### Scenario: Limitations are visible in the data
- **WHEN** the daily figures of Tools, Backup and Networking are evaluated
- **THEN** Tools never exceeds 100.00 over its reference, Backup rises from a zero reference and Networking appears without previous spend, so none opens an episode

### Requirement: Expected values verified independently

The repository SHALL contain `docs/demo/JUP-107/esperados-anomalias.json` with the reference rules, both periods, the per-service totals and record counts, each group's expected statuses and reasons, the two expected alerts, and the expected episodes after one detection at the reference date 2026-09-22 and after one detection at 2026-10-31, with their start, last seen day, observation, reference daily cost, accumulated impact, counted days and severity. A test that needs no database SHALL recompute every figure with exact `Decimal` arithmetic from the dataset rows, implementing the period sums and the daily rule independently, without using the backend services, and compare it with the file.

#### Scenario: Altered amount fails naming the figure
- **WHEN** one amount of the dataset or one figure of the expected file is changed
- **THEN** the test fails and names the service, the period or episode and the figure that differs

#### Scenario: Dataset and calendar stay consistent
- **WHEN** the test runs
- **THEN** every record date lies between 2026-09-01 and 2026-10-30, the two evaluation periods are consecutive and of equal length, and the last record date is 2026-10-30, failing with a clear message otherwise
- **AND** the test does not depend on the date of the day it runs

#### Scenario: Identifiers are not frozen offline
- **WHEN** the expected file is read
- **THEN** it contains no alert `id`, `evidence_id` nor episode `id`, which are checked against the real endpoints when the demonstration is validated

## REMOVED Requirements

### Requirement: No interference with other work

**Reason**: It described the boundaries of the change that introduced the dataset (no edits under `apps/`, to `scripts/synthetic_costs.py`, to the JUP-106 dataset or documents, to `docs/demo/JUP-065/` or to the public dataset). This change unifies the load path of both datasets and adds the reference date to the application, so the requirement would forbid the work it asks for. The protection that still matters is kept by the single-path capability: the original public fixtures stay byte-identical and the earlier figures of both datasets do not change.

**Migration**: None. The remaining requirements of this capability and the requirements of `demo-cost-data-single-path` cover the guarantees that stay.
