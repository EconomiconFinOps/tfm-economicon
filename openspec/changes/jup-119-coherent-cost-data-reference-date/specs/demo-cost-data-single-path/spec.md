## ADDED Requirements

### Requirement: Demo data enters only through the simulated API and the ingestion CLI

The repository SHALL provide one demo dataset in the Azure cost export CSV format, served by the simulated Azure Cost API through its configured dataset path and loaded into a tenant only by the ingestion CLI of the processor. No script, test helper used for the demonstration or loader SHALL write rows into `azure_cost_records` or `azure_cost_ingestion_runs` for the demonstration other than through that CLI. The single entry point `scripts/demo_data.py` SHALL offer `generate`, `apply`, `status` and `remove`; `apply` SHALL run the ingestion CLI for each tenant and subscription pair named in the dataset manifest and SHALL NOT insert rows by itself.

#### Scenario: Loaded rows come from the CLI
- **WHEN** `apply` loads the demo dataset on empty tenants
- **THEN** every stored run was written by the ingestion CLI with a definition file stored in the repository
- **AND** the normalised columns (service, resource group, project, tags) of the stored rows equal what the normaliser produces from the CSV rows

#### Scenario: Both former loaders are replaced
- **WHEN** the repository is searched for code that inserts into `azure_cost_records` outside the processor repository, its migrations and the tests of those
- **THEN** `scripts/synthetic_costs.py` and `scripts/synthetic_anomalies.py` no longer exist or only forward to `scripts/demo_data.py`
- **AND** no demo guide documents a direct-insert command

#### Scenario: Generation is reproducible
- **WHEN** `generate` runs twice, on different machines and days
- **THEN** both CSV files and the manifest are byte-identical, no value depends on the clock or on a random seed that is not fixed in the file, and the checksum in the manifest matches

### Requirement: Every demo row states where it comes from

Every row of the demo CSV SHALL carry, in its tags, `dataset_origin` with exactly one of `public-shifted` or `synthetic`, and the ingestion SHALL preserve it as a stored tag. Rows of the public origin SHALL keep the original public values of every column except the date columns, which SHALL be shifted by one fixed number of days recorded in the manifest. Synthetic rows SHALL use subscription identifiers with the reserved prefix `synthetic-` and SHALL NOT reuse a public subscription identifier. The documentation SHALL state that the dates of the public rows are shifted, that no row is an invoice of 2026 and that synthetic rows are not Azure invoices.

#### Scenario: Public rows only change in their dates
- **WHEN** the shifted file is compared row by row with `EA-Cost-Actual.sample.csv`
- **THEN** all 50 rows are present, every column other than `Date`, `BillingPeriodStartDate` and `BillingPeriodEndDate` is byte-identical, and each date equals the original plus the shift recorded in the manifest
- **AND** the shift moves 2024-06-01 to 2026-09-01

#### Scenario: Original fixture untouched
- **WHEN** the change is applied
- **THEN** `fixtures/azure-cost/EA-Cost-Actual.sample.csv`, its manifest entry and the other original fixtures are byte-identical to the base

#### Scenario: Origin survives ingestion
- **WHEN** the demo dataset has been loaded
- **THEN** every stored record carries the tag `dataset_origin` and a query by that tag returns the public-shifted and the synthetic rows separately, with counts equal to the manifest

#### Scenario: No row passes for real 2026 billing
- **WHEN** the demo guide and the manifest are read from the top
- **THEN** the statement about shifted and synthetic data appears before the first figure

### Requirement: Continuous coverage until 2026-10-30

For each tenant that has cost data in the demo, the dataset SHALL contain at least one record on every calendar day from 2026-09-01 to 2026-10-30 inclusive, except the days that the dataset documents as intentionally empty for a stated reason, and no record after 2026-10-30. The check SHALL be a test that recomputes the coverage from the CSV and fails naming the tenant, the subscription and the first uncovered day.

#### Scenario: No gap
- **WHEN** the coverage test runs
- **THEN** every demo tenant has a record on each day from 2026-09-01 to 2026-10-30, apart from the documented empty days

#### Scenario: A removed day fails the test
- **WHEN** all rows of one day are removed from the CSV
- **THEN** the test fails and names the tenant, the subscription and that day

#### Scenario: Nothing beyond the end
- **WHEN** the CSV contains a record dated 2026-10-31
- **THEN** the test fails

### Requirement: Safe, idempotent load and removal for the whole dataset

`apply` SHALL be idempotent: a second call on loaded tenants writes nothing and reports `already-present`. It SHALL refuse, writing nothing, when a target tenant already holds cost rows that do not belong to this dataset (identified by the reserved `synthetic-` subscription prefix or the `dataset_origin` tag) and SHALL name the tenant and the reason. `status` SHALL report per tenant `absent`, `present`, `partial` or `other-data`. `remove` SHALL delete only the runs and records of this dataset, and the anomaly episodes and detection state of a tenant left with no other cost data; it SHALL be repeatable and SHALL leave other tenants untouched. A load interrupted before the end SHALL leave a `partial` state that `apply` refuses to complete silently.

#### Scenario: Second apply writes nothing
- **WHEN** `apply` runs twice
- **THEN** the second run reports `already-present` and the counts of runs and records are the same as after the first

#### Scenario: Tenant with other cost data is protected
- **WHEN** a target tenant holds a run whose subscription does not carry the reserved prefix or the origin tag
- **THEN** `apply` exits with status 2, loads nothing for any tenant and names the tenant

#### Scenario: Removal is exact and repeatable
- **WHEN** `remove` runs twice after a load and a detection
- **THEN** the first call deletes the dataset's runs, records, episodes and detection state, the second deletes nothing and succeeds
- **AND** rows of a tenant that is not in the dataset are unchanged

#### Scenario: Interrupted load
- **WHEN** the CLI fails on the third pair of tenant and subscription
- **THEN** `status` reports `partial` for the affected tenant, `apply` refuses and tells the user to run `remove` first

### Requirement: The single path is shown to work end to end

An automated test with the real database engine SHALL generate the dataset, serve it through the simulated API process, run the ingestion CLI for every pair, and compare the stored totals per tenant, month, currency and `dataset_origin` with expected values recomputed from the CSV with exact decimal arithmetic. The same test SHALL check that a second `apply` writes nothing, that `remove` returns the tables to their previous state and that the billing summary and the daily detection read the loaded data with the reference date set to 2026-09-21 and to 2026-10-30.

#### Scenario: Stored totals equal the file
- **WHEN** the test compares the stored totals with the totals recomputed from the CSV
- **THEN** they are equal for every tenant, month, currency and origin, without using the backend aggregation to compute the expected value

#### Scenario: Altered amount fails naming the figure
- **WHEN** one amount of the CSV is changed
- **THEN** the test fails and names the tenant, month and currency whose total differs
