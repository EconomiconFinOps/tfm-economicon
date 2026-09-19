# azure-public-cost-dataset Specification

## Purpose
TBD - created by archiving change jup-072-audit-azure-dataset. Update Purpose after archive.
## Requirements
### Requirement: Public Azure dataset provenance is pinned and reproducible

The repository SHALL document the official Microsoft FinOps Toolkit dataset release, original download URL, MIT license, archive size and SHA-256 checksum required to identify the exact public Azure cost dataset used for development.

#### Scenario: Contributor verifies the selected Microsoft source

- **WHEN** a contributor reads the dataset documentation and machine-readable audit
- **THEN** both identify Microsoft FinOps Toolkit release `v14`, the official `dataset-examples.zip` download and archive SHA-256 `d7769d9e759b5968a68affcb364235ad938a705168c546ab86cad5bbb27ff607`.

#### Scenario: Large source archive remains outside version control

- **WHEN** a contributor inspects tracked repository files
- **THEN** the original 109,532,323-byte ZIP archive is absent and repository ignore rules reject ZIP archives and raw-data directories.

### Requirement: Azure exports are inventoried and quality-audited

The repository SHALL provide a reproducible streaming audit covering all 11 CSV exports, their headers, row counts, malformed records, date ranges, currencies and cost statistics.

#### Scenario: Contributor checks the complete archive inventory

- **WHEN** the committed audit report is inspected
- **THEN** it identifies 11 CSV entries, 1,295,308 total records, no unsafe archive paths and no malformed rows.

#### Scenario: Negative and zero costs remain visible

- **WHEN** the actual Azure cost export is profiled
- **THEN** the report records negative, zero and positive cost values without removing or classifying them as invalid.

### Requirement: Small versioned fixtures retain original public values

The repository SHALL provide one deterministic CSV fixture per audited Microsoft export, capped at 50 rows, with original headers and original public values preserved without anonymization or pseudonymization.

#### Scenario: Fixture manifest matches the audited source

- **WHEN** the versioned fixture manifest is validated
- **THEN** it references all 11 CSV fixtures, records the exact source release and archive checksum, and lists the correct source entry and row count for every fixture.

#### Scenario: Repeated sampling produces identical rows

- **WHEN** the same archive is audited twice with the same sample size
- **THEN** the selected fixture headers, rows and source checksum are identical.

#### Scenario: Public identifiers remain unchanged

- **WHEN** a sampled Microsoft row contains public subscription identifiers, account fields or resource identifiers
- **THEN** its versioned fixture contains the original published values without redaction, hashing or substitution.

#### Scenario: Microsoft licensing notice accompanies fixtures

- **WHEN** the fixture directory is distributed or reviewed
- **THEN** it contains the Microsoft Corporation MIT copyright notice.

### Requirement: Canonical fixture supports the future Azure fake API

The repository SHALL identify `EA-Cost-Actual.sample.csv` as the default public dataset for the simulated Azure Cost Management API while keeping amortized, FOCUS, pricing and reservation exports separate.

#### Scenario: Downstream contributor loads the default dataset

- **WHEN** a contributor implements the Azure fake API or cost ingestion client
- **THEN** the documented default fixture supplies actual Azure costs and retains at least one negative amount, one zero amount and one positive amount.

#### Scenario: Downstream work does not require a real Azure tenant

- **WHEN** a contributor runs fixture validation or builds local Azure API tests
- **THEN** the versioned dataset and tests operate without Azure credentials, a tenant connection or the complete downloaded archive.
