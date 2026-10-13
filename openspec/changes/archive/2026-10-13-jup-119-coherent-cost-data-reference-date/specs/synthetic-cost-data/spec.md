## MODIFIED Requirements

### Requirement: Deterministic documented dataset

The synthetic dataset SHALL be versioned, deterministic and identical on every generation, SHALL be part of the demo CSV of the single load path, and SHALL span the common window from 2026-07-01 to 2026-10-30, continuous in EUR. It SHALL include, at least: in USD, a month with a recorded cost of exactly zero, a month with no record at all and months with costs, so that a gap and a recorded zero stay distinguishable; a negative cost (credit); two currencies whose costs fall in different months; an amount whose integer value exceeds `Number.MAX_SAFE_INTEGER` and has no cents, in a month outside the main route; and records without a service or without the project tag. Every record SHALL have a usage date and SHALL carry no more fields than the service and the project tag. Every day of the window SHALL be covered as the single-path capability requires. The cases that the query API cannot deliver are listed in the requirement on automated tests and SHALL NOT be part of the demo CSV. A reference document SHALL list the expected totals per month and currency and the expected totals for each supported grouping, derived independently of the loader.

#### Scenario: Same data on every load
- **WHEN** the dataset is generated twice, or loaded twice on clean databases
- **THEN** both outputs contain identical rows, including identifiers, dates, amounts and currencies
- **AND** no value depends on the clock, randomness or the machine

#### Scenario: Required cases are present and documented
- **WHEN** the dataset is inspected against the reference document
- **THEN** every case listed above is present at least once, in the month the document states
- **AND** each case is described in the document together with the feature behaviour it exercises
- **AND** the document lists the cases of JUP-106 that are not in the demo CSV and where each one is tested instead

#### Scenario: Reference totals match an independent computation
- **WHEN** the monthly and per-currency totals are computed from the dataset records with exact decimal arithmetic
- **THEN** they equal the totals printed in the reference document, for the months from July to October 2026
- **AND** no total is produced by the loader's own aggregation code

#### Scenario: Window replaces the old months
- **WHEN** the dataset is read
- **THEN** it has no record before 2026-07-01 and the reference document states that the months of the former JUP-106 dataset were rebased into the window

### Requirement: Explicit synthetic provenance and isolation

Every synthetic row SHALL belong to a subscription with the reserved prefix `synthetic-` listed in the demo manifest, and the dataset SHALL NOT modify, replace or extend the original versioned public Azure dataset fixtures or the simulator code. The documentation SHALL state that the data are synthetic, are not Azure invoices and do not come from the public dataset.

#### Scenario: Synthetic marking
- **WHEN** the synthetic runs and records exist in the database
- **THEN** their subscription identifiers carry the reserved synthetic prefix and are in the manifest with the origin `synthetic`
- **AND** no non-synthetic row uses that prefix

#### Scenario: Public dataset untouched
- **WHEN** the change is applied
- **THEN** the original files of the public dataset and their manifest remain byte-identical and the simulator code is unchanged
- **AND** the schema and migrations are unchanged

### Requirement: Safe, idempotent load and removal

The load, status and removal of the synthetic cost dataset SHALL be done by the single entry point of the demo data capability, SHALL be idempotent, and removal SHALL delete only rows of the manifest's synthetic subscriptions. The load SHALL refuse a tenant that already has cost records of a subscription that is not in the manifest.

#### Scenario: Idempotent load
- **WHEN** the dataset is loaded and then loaded again
- **THEN** the second load changes nothing and reports the dataset as already present
- **AND** the number of synthetic runs and records equals the dataset's counts

#### Scenario: Removal restores the previous state
- **WHEN** the dataset is loaded and then removed
- **THEN** no synthetic run or record remains and every non-synthetic row is unchanged
- **AND** removal on a database without synthetic rows reports nothing to remove and succeeds

#### Scenario: Tenant with real data is protected
- **WHEN** the target tenant already holds cost records of a subscription that is not in the manifest
- **THEN** the load refuses, writes nothing and explains why
- **AND** removal in that tenant still deletes only the synthetic rows

#### Scenario: Partial or foreign state
- **WHEN** only part of the synthetic rows exist, or synthetic rows belong to another tenant
- **THEN** the status report shows the mismatch and loading does not silently complete or duplicate rows
- **AND** the tool tells the user to remove the dataset first

## ADDED Requirements

### Requirement: Edge cases the API cannot deliver are covered by automated tests

The cases of JUP-106 that the simulated query API cannot transport SHALL be covered by automated tests that build the rows directly and read them through billing with the real database engine: a record without a usage date, an amount above `Number.MAX_SAFE_INTEGER` with cents, records whose resource group differs only in letter case, records with a resource group, a cost center and other tags, and records with missing resource group, service and tags. These tests SHALL NOT load rows into any tenant of the demonstration. The reference document SHALL list each case with the test that covers it.

#### Scenario: Undated record
- **WHEN** a tenant has a record without a usage date and the summary is requested for a period
- **THEN** the amount is not in any period total and the response reports one excluded undated record

#### Scenario: Very large amount with cents
- **WHEN** a record of 9007199254740993.01 is read through the summary
- **THEN** the amount is returned as the decimal string "9007199254740993.01" without loss

#### Scenario: Resource group differing only in case
- **WHEN** records with resource groups `Web` and `web` exist and the summary is grouped by resource group
- **THEN** they are one group, as the billing rule for case-insensitive identifiers states

#### Scenario: Cases are listed with their tests
- **WHEN** the reference document is read
- **THEN** every case above names the test that covers it and the test exists

#### Scenario: Tests do not touch the demo tenants
- **WHEN** these tests run against a database that also holds the demo dataset
- **THEN** they use their own tenant and leave the demo rows unchanged
