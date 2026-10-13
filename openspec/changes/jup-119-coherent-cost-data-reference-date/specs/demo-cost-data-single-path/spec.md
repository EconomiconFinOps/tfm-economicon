## ADDED Requirements

### Requirement: Demo data enters only through the simulated API and the ingestion CLI

The repository SHALL provide one demo dataset in the Azure cost export CSV format, served by the simulated Azure Cost API through its configured dataset path and loaded into a tenant only by the ingestion CLI of the processor. No script or loader used for the demonstration SHALL write rows into `azure_cost_records` or `azure_cost_ingestion_runs` other than through that CLI. The single entry point `scripts/demo_data.py` SHALL offer `generate`, `apply`, `status` and `remove`; `apply` SHALL run the ingestion CLI for each tenant and subscription pair named in the dataset manifest and SHALL NOT insert rows by itself.

#### Scenario: Loaded rows come from the CLI
- **WHEN** `apply` loads the demo dataset on empty tenants
- **THEN** every stored run was written by the ingestion CLI with a definition file stored in the repository
- **AND** the stored columns (service, project, tags, usage date, amount, currency) of the rows equal what the normaliser produces from the API response for the CSV rows

#### Scenario: Both former loaders are replaced
- **WHEN** the repository is searched for code that inserts into `azure_cost_records` outside the processor repository, its migrations and automated tests
- **THEN** `scripts/synthetic_costs.py` and `scripts/synthetic_anomalies.py` no longer exist or only forward to `scripts/demo_data.py`
- **AND** no demo guide documents a direct-insert command

#### Scenario: Generation is reproducible
- **WHEN** `generate` runs twice, on different machines and days
- **THEN** both CSV files and the manifest are byte-identical, no value depends on the clock or on a random seed that is not fixed in the file, and the checksum in the manifest matches

### Requirement: Demo data uses only what the query API can deliver

Every row of the demo CSV SHALL carry a valid usage date. Each ingestion definition of the demo SHALL group by exactly two fields, the dimension `ServiceName` and the tag `Project`, because the simulated API accepts at most two groupings and a second definition over the same subscription would overlap the first. Amounts SHALL be integers or decimals that the API returns without loss: an amount SHALL be exact through the API, and an amount above 2^53 SHALL be an integer without cents. The dataset SHALL NOT contain a row without a usage date, an amount above 2^53 with cents, or a field that only exists in a different grouping. The manifest SHALL list the fields that are absent in the loaded rows (resource group, cost center, owner, application, environment) so that the guides and screens can state them.

#### Scenario: Rows without a date are not generated
- **WHEN** the generated CSV is validated
- **THEN** every row has a date in the format the API reads and a test fails otherwise

#### Scenario: Amounts survive the API
- **WHEN** the demo dataset is loaded and each stored amount is compared with the amount of its CSV rows summed with exact decimal arithmetic by tenant, subscription, day, service, project and currency
- **THEN** all amounts are equal and none differs by a rounding

#### Scenario: A second grouping is not used
- **WHEN** the definition files of the demo are read
- **THEN** each has exactly the two groupings above, and the dataset manifest names one definition per subscription

#### Scenario: Absent fields are declared
- **WHEN** the manifest and the demo guide are read
- **THEN** both list the fields that the loaded rows do not carry and say that the screens show them as absent

### Requirement: Origin is identified by the subscription

Every row of the demo CSV SHALL belong to a subscription listed in the dataset manifest with its origin, `public-shifted` or `synthetic`. Synthetic subscriptions SHALL use the reserved prefix `synthetic-` and SHALL NOT reuse a public subscription identifier. Rows of the public origin SHALL keep the original public values of every column except the date columns, which SHALL be shifted by one fixed number of days recorded in the manifest. The documentation SHALL state that the dates of the public rows are shifted, that no row is an invoice of 2026 and that synthetic rows are not Azure invoices.

#### Scenario: Public rows only change in their dates
- **WHEN** the shifted file is compared row by row with `EA-Cost-Actual.sample.csv`
- **THEN** all 50 rows are present, every column other than `Date`, `BillingPeriodStartDate` and `BillingPeriodEndDate` is byte-identical, and each date equals the original plus the shift recorded in the manifest
- **AND** the shift moves 2024-06-01 to 2026-09-01

#### Scenario: Original fixture untouched
- **WHEN** the change is applied
- **THEN** `fixtures/azure-cost/EA-Cost-Actual.sample.csv`, its manifest entry and the other original fixtures are byte-identical to the base

#### Scenario: Every subscription has a declared origin
- **WHEN** the demo CSV is read
- **THEN** every subscription identifier is in the manifest with its origin, and synthetic ones carry the prefix

#### Scenario: No row passes for real 2026 billing
- **WHEN** the demo guide and the manifest are read from the top
- **THEN** the statement about shifted and synthetic data appears before the first figure

### Requirement: One common continuous window from 2026-07-01 to 2026-10-30

For each tenant that has cost data in the demo, the dataset SHALL contain at least one record on every calendar day from 2026-07-01 to 2026-10-30 inclusive, except the days that the dataset documents as intentionally empty for a stated reason, and no record before 2026-07-01 or after 2026-10-30. The window is common to every demo tenant; a currency or a subscription inside a tenant MAY have gaps or recorded zeros that the dataset documents, as long as the tenant has a record on each day. The date-shifted public subscription is a documented complement with days without data and is not required to be continuous. The check SHALL be a test that recomputes the coverage from the CSV and fails naming the tenant, the subscription and the first uncovered day.

#### Scenario: No gap
- **WHEN** the coverage test runs
- **THEN** every demo tenant has a record on each day from 2026-07-01 to 2026-10-30, apart from the documented empty days

#### Scenario: A removed day fails the test
- **WHEN** all rows of one day are removed from the CSV
- **THEN** the test fails and names the tenant, the subscription and that day

#### Scenario: Nothing outside the window
- **WHEN** the CSV contains a record dated 2026-06-30 or 2026-10-31
- **THEN** the test fails

#### Scenario: Gap and recorded zero stay distinguishable
- **WHEN** the USD series of the cost tenant is read
- **THEN** it has recorded zero costs in one month, no record at all in another month and costs in the others, while the tenant still has a record on every day through its EUR series

### Requirement: Safe, idempotent load and removal for the whole dataset

`apply` SHALL be idempotent: a second call on loaded tenants writes nothing and reports `already-present`. It SHALL refuse, writing nothing, when a target tenant already holds cost rows whose subscription is not in the manifest and SHALL name the tenant and the reason. `status` SHALL report per tenant `absent`, `present`, `partial` or `other-data`. `remove` SHALL delete only the runs and records of the manifest's subscriptions, and the anomaly episodes and detection state of a tenant left with no other cost data; it SHALL be repeatable and SHALL leave other tenants untouched. A load interrupted before the end SHALL leave a `partial` state that `apply` refuses to complete silently. The documentation SHALL state the measured time of a complete load.

#### Scenario: Second apply writes nothing
- **WHEN** `apply` runs twice
- **THEN** the second run reports `already-present` and the counts of runs and records are the same as after the first

#### Scenario: Tenant with other cost data is protected
- **WHEN** a target tenant holds a run whose subscription is not in the manifest
- **THEN** `apply` exits with status 2, loads nothing for any tenant and names the tenant

#### Scenario: Removal is exact and repeatable
- **WHEN** `remove` runs twice after a load and a detection
- **THEN** the first call deletes the dataset's runs, records, episodes and detection state, the second deletes nothing and succeeds
- **AND** rows of a tenant that is not in the dataset are unchanged

#### Scenario: Interrupted load
- **WHEN** the CLI fails on the third pair of tenant and subscription
- **THEN** `status` reports `partial` for the affected tenant, `apply` refuses and tells the user to run `remove` first

### Requirement: The single path is shown to work end to end

An automated test with the real database engine SHALL generate the dataset, serve it through the simulated API process, run the ingestion CLI for every pair, and compare the stored totals per tenant, month, currency, service and project with expected values recomputed from the CSV with exact decimal arithmetic. The same test SHALL check that a second `apply` writes nothing, that `remove` returns the tables to their previous state and that the billing summary and the daily detection read the loaded data with the reference date set to 2026-09-21 and to 2026-10-30.

#### Scenario: Stored totals equal the file
- **WHEN** the test compares the stored totals with the totals recomputed from the CSV
- **THEN** they are equal for every tenant, month, currency, service and project, without using the backend aggregation to compute the expected value

#### Scenario: Altered amount fails naming the figure
- **WHEN** one amount of the CSV is changed
- **THEN** the test fails and names the tenant, month and currency whose total differs

### Requirement: Screens with absent fields show them as absent

With the demo data loaded, the screens and answers that depend on fields the demo does not carry SHALL show them as absent and SHALL NOT fail: the tag coverage SHALL report the tags `owner`, `environment`, `application` and `cost_center` as not covered in every record and `project` as covered where present; the ownership question by cost center, owner or application SHALL answer that the dimension has not been observed; the dashboard breakdown by resource group SHALL show the records as not applicable. A test or a recorded check on the real stack SHALL cover each of the three.

#### Scenario: Tag coverage with only the project tag
- **WHEN** the demo data are loaded and the tag coverage is requested for a period with records
- **THEN** the response lists the five required tags, reports four of them missing in every record, and `project` covered in the records that carry it, with HTTP 200

#### Scenario: Ownership by an absent dimension
- **WHEN** the ownership question is asked by cost center on the demo data
- **THEN** the answer has status `insufficient_data` with reason `dimension_unobserved` and contains no amount attributed to a cost center

#### Scenario: Breakdown by resource group
- **WHEN** the dashboard asks for the breakdown by resource group on the demo data
- **THEN** the response is successful and the records appear as not applicable, and the page shows no error

### Requirement: Loading is opt-in and never part of the default startup

The default `docker compose up` SHALL NOT load demo data. The repository SHALL provide a Compose profile `demo` whose one-shot service waits for the simulated API, the database and the processor to be healthy and then runs `scripts/demo_data.py apply`; the same profile SHALL start a second instance of the simulated API that serves the generated demo CSV, and the default instance SHALL keep serving the public sample. The profile SHALL refuse to run when `RUNTIME_ENVIRONMENT` is `production`. The generated CSV and the manifest SHALL be versioned, and a test SHALL regenerate them and fail if they differ.

#### Scenario: Default startup loads nothing
- **WHEN** `docker compose up` runs without the profile on empty tenants
- **THEN** no cost run or record exists afterwards and the simulated API still serves the public sample

#### Scenario: Profile loads once and is repeatable
- **WHEN** the stack starts with the profile `demo` and starts again
- **THEN** the first start loads the dataset and the second reports `already-present` without writing

#### Scenario: Production is refused
- **WHEN** the profile `demo` starts with `RUNTIME_ENVIRONMENT=production`
- **THEN** the one-shot service exits with an error stating the reason and loads nothing

#### Scenario: Versioned files stay reproducible
- **WHEN** the generator runs in CI
- **THEN** its output is byte-identical to the versioned CSV and manifest
