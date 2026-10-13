## ADDED Requirements

### Requirement: A date-shifted derivative sits beside the untouched original

The repository SHALL provide a derived fixture of `EA-Cost-Actual.sample.csv` whose date columns (`Date`, `BillingPeriodStartDate`, `BillingPeriodEndDate`) are shifted by one fixed number of days so that 2024-06-01 becomes 2026-09-01, and whose other columns keep the original public values. It SHALL live in its own path, SHALL be described by its own manifest in the same directory as a derivative, with the name of its source fixture, the shift in days and its own row count and checksum, and SHALL NOT replace or alter any original fixture or the original manifest. The original fixtures SHALL keep being the ones that the Microsoft source checksum describes, and no manifest SHALL describe the derivative as original public data.

#### Scenario: Derivative is reproducible
- **WHEN** the derivative is regenerated from the original fixture
- **THEN** it is byte-identical to the versioned file and its checksum matches the manifest

#### Scenario: Original and derivative are told apart
- **WHEN** the original manifest and the manifest of the derivative are read
- **THEN** the original manifest keeps its 11 entries unchanged and the manifest of the derivative is marked as derived, with its source and its shift

#### Scenario: Shift is applied to every date column and only to them
- **WHEN** the derivative is compared with the original row by row
- **THEN** the three date columns differ by exactly the shift and every other column is byte-identical, including identifiers, tags and costs
