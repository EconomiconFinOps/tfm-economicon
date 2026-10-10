# finops-business-metrics Specification

## Purpose
Define reproducible business-metric records and calculations for paired time savings, cost-weighted assignment coverage and evidence-based potential savings, preserving provenance and unavailable results without claiming observed product benefit.
## Requirements
### Requirement: Reproducible business evaluation record

The instrument SHALL require a versioned record with scope, period, currency,
cost basis, dataset version, commit, configuration, reviewer, provenance and evidence.
Unknown fields, malformed data and unsafe integer totals SHALL be rejected.

#### Scenario: Synthetic example remains visibly synthetic

- **WHEN** the example record is calculated
- **THEN** the report preserves synthetic provenance, metadata and a deterministic input hash
- **AND** it does not claim observed product benefit

### Requirement: Paired time savings

Time savings SHALL use only correct manual/assisted pairs with positive durations
and identical task context; failures, blocked and not-run attempts SHALL be counted
separately. Negative savings SHALL be preserved and zero denominators SHALL yield null.

#### Scenario: Fast incorrect output does not inflate savings

- **WHEN** an assisted answer fails the reference criteria
- **THEN** its duration is excluded from paired savings and its failure is counted

### Requirement: Cost weighted assignment coverage

Assigned coverage SHALL equal allocated cost over allocated plus shared plus
unallocated cost. Shared governed coverage SHALL be reported separately. Owners
and documented shared/exclusion rules SHALL be required; missing denominators SHALL yield null.

#### Scenario: Shared and excluded costs remain distinct

- **WHEN** costs are 700 allocated, 200 shared, 100 unallocated and 50 excluded
- **THEN** assigned coverage is 70 percent and governed coverage is 90 percent

### Requirement: Evidence based potential savings

Potential savings SHALL aggregate supported estimates with owner, risk and method
in the baseline period/currency. Overlapping resource estimates and amounts beyond
eligible resource cost SHALL be rejected. Candidates SHALL carry null savings;
realized savings SHALL remain unavailable.

#### Scenario: No supported estimate is available

- **WHEN** only unquantified candidates are recorded
- **THEN** potential savings is null and candidates remain counted

#### Scenario: Multiple alternatives overlap

- **WHEN** two estimates target the same resource
- **THEN** the record is rejected until consolidated with evidence
