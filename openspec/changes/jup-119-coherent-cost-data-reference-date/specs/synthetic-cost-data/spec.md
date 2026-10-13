## MODIFIED Requirements

### Requirement: Deterministic documented dataset

The synthetic dataset SHALL be versioned, deterministic and identical on every generation, SHALL be part of the demo CSV of the single load path, and SHALL span the consecutive calendar months from January 2026 to 2026-10-30. It SHALL include, at least: months with a recorded cost of exactly zero, months with no record at all, a negative cost (credit), two currencies whose costs fall in different months, an amount whose integer value exceeds `Number.MAX_SAFE_INTEGER`, records with missing resource group, service and tags, and records whose resource group differs only in letter case. The days from 2026-09-01 to 2026-10-30 SHALL be covered continuously as the single-path capability requires. The case of a record without a usage date cannot be served by the simulated API, which rejects a row without a date, so it SHALL NOT be part of the demo CSV and SHALL be covered by an automated test that builds that row directly. A reference document SHALL list the expected totals per month and currency and the expected totals for each supported grouping, derived independently of the loader.

#### Scenario: Same data on every load
- **WHEN** the dataset is generated twice, or loaded twice on clean databases
- **THEN** both outputs contain identical rows, including identifiers, dates, amounts and currencies
- **AND** no value depends on the clock, randomness or the machine

#### Scenario: Required cases are present and documented
- **WHEN** the dataset is inspected against the reference document
- **THEN** every case listed above is present at least once, in the month the document states
- **AND** each case is described in the document together with the feature behaviour it exercises
- **AND** the document states that the undated record is exercised by a test and why it is not in the demo CSV

#### Scenario: Reference totals match an independent computation
- **WHEN** the monthly and per-currency totals are computed from the dataset records with exact decimal arithmetic
- **THEN** they equal the totals printed in the reference document, for the months of 2026 up to October
- **AND** no total is produced by the loader's own aggregation code

#### Scenario: Months before September keep their figures
- **WHEN** the totals of January to July 2026 are compared with those of the JUP-106 reference document
- **THEN** they are equal, so the figures of the JUP-065 and JUP-106 demonstrations do not change

### Requirement: Explicit synthetic provenance and isolation

Every synthetic row SHALL be identifiable as synthetic by its identifiers, by a subscription identifier with the reserved prefix `synthetic-` and by the tag `dataset_origin` with the value `synthetic`, and the dataset SHALL NOT modify, replace or extend the original versioned public Azure dataset fixtures or the simulator code. The documentation SHALL state that the data are synthetic, are not Azure invoices and do not come from the public dataset.

#### Scenario: Synthetic marking
- **WHEN** the synthetic runs and records exist in the database
- **THEN** their subscription identifiers carry the reserved synthetic prefix and each record carries the tag `dataset_origin` with the value `synthetic`
- **AND** no non-synthetic row uses that prefix or that tag value

#### Scenario: Public dataset untouched
- **WHEN** the change is applied
- **THEN** the original files of the public dataset and their manifest remain byte-identical and the simulator code is unchanged
- **AND** the schema and migrations are unchanged

### Requirement: Safe, idempotent load and removal

The load, status and removal of the synthetic cost dataset SHALL be done by the single entry point of the demo data capability, SHALL be idempotent, and removal SHALL delete only rows that carry the reserved synthetic prefix. The load SHALL refuse a tenant that already has non-synthetic cost records.

#### Scenario: Idempotent load
- **WHEN** the dataset is loaded and then loaded again
- **THEN** the second load changes nothing and reports the dataset as already present
- **AND** the number of synthetic runs and records equals the dataset's counts

#### Scenario: Removal restores the previous state
- **WHEN** the dataset is loaded and then removed
- **THEN** no synthetic run or record remains and every non-synthetic row is unchanged
- **AND** removal on a database without synthetic rows reports nothing to remove and succeeds

#### Scenario: Tenant with real data is protected
- **WHEN** the target tenant already holds cost records that are not synthetic
- **THEN** the load refuses, writes nothing and explains why
- **AND** removal in that tenant still deletes only the synthetic rows

#### Scenario: Partial or foreign state
- **WHEN** only part of the synthetic rows exist, or synthetic rows belong to another tenant
- **THEN** the status report shows the mismatch and loading does not silently complete or duplicate rows
- **AND** the tool tells the user to remove the dataset first
