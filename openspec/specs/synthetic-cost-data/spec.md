# synthetic-cost-data Specification

## Purpose
Provide a reproducible synthetic cost dataset and a command-line tool to load, inspect and remove it in the local environment, so that cost features can be validated in the real interface across several months, currencies and edge cases that the public Azure dataset cannot cover.
## Requirements
### Requirement: Deterministic documented dataset

The synthetic dataset SHALL be versioned, deterministic and identical on every load. It SHALL span several consecutive calendar months of 2026 and include, at least: months with a recorded cost of exactly zero, months with no record at all, a negative cost (credit), two currencies whose costs fall in different months, an amount whose integer value exceeds `Number.MAX_SAFE_INTEGER`, records with missing resource group, service and tags, records whose resource group differs only in letter case, and one record without a usage date. A reference document SHALL list the expected totals per month and currency and the expected totals for each supported grouping, derived independently of the loader.

#### Scenario: Same data on every load
- **WHEN** the dataset is loaded twice on clean databases
- **THEN** both databases contain identical synthetic runs and records, including identifiers, dates, amounts and currencies
- **AND** no value depends on the clock, randomness or the machine

#### Scenario: Required cases are present and documented
- **WHEN** the dataset is inspected against the reference document
- **THEN** every case listed above is present at least once, in the month the document states
- **AND** each case is described in the document together with the feature behaviour it exercises

#### Scenario: Reference totals match an independent computation
- **WHEN** the monthly and per-currency totals are computed from the dataset records with exact decimal arithmetic
- **THEN** they equal the totals printed in the reference document
- **AND** no total is produced by the loader's own aggregation code

### Requirement: Explicit synthetic provenance and isolation

Every synthetic row SHALL be identifiable as synthetic by its identifiers and by the ingestion-run request metadata, and the dataset SHALL NOT modify, replace or extend the versioned public Azure dataset, the simulator or its fixtures. The documentation SHALL state that the data are synthetic, are not Azure invoices and do not come from the public dataset.

#### Scenario: Synthetic marking
- **WHEN** the synthetic runs and records exist in the database
- **THEN** their identifiers and subscription identifiers carry a reserved synthetic prefix and each run records that it is synthetic
- **AND** no non-synthetic row uses that prefix

#### Scenario: Public dataset untouched
- **WHEN** the change is applied
- **THEN** the files of the public dataset, its manifest and the simulator remain byte-identical
- **AND** the schema, migrations and ingestion code are unchanged

### Requirement: Safe, idempotent load and removal

The tool SHALL load the dataset into the local cost tables of the configured tenant, report its state and remove it. Loading SHALL be idempotent, removal SHALL delete only synthetic rows, and the tool SHALL refuse to load into a tenant that already has non-synthetic cost records.

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
- **THEN** the tool refuses to load, writes nothing and explains why
- **AND** removal in that tenant still deletes only the synthetic rows

#### Scenario: Partial or foreign state
- **WHEN** only part of the synthetic rows exist, or synthetic rows belong to another tenant
- **THEN** the status report shows the mismatch and loading does not silently complete or duplicate rows
- **AND** the tool tells the user to remove the dataset first

### Requirement: Observable through the cost summary

Once loaded, the existing billing summary for the target tenant SHALL expose the dataset without changes to the endpoint, so that the documented expected values can be compared with what the application returns and displays. Removal SHALL return the summary to its previous empty state.

#### Scenario: Summary matches the reference
- **WHEN** the dataset is loaded and the billing summary is requested for the months and groupings in the reference document
- **THEN** the returned totals, groups, currencies, missing-dimension count and excluded-undated count equal the expected values
- **AND** a month with no record is absent from the response and a month with a recorded zero is present with zero

#### Scenario: Summary after removal
- **WHEN** the dataset has been removed
- **THEN** the summary for the same period reports no data for the tenant
- **AND** other tenants' summaries are unchanged by loading and removal

