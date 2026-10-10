## ADDED Requirements

### Requirement: Scoped organizational attribution

The backend SHALL provide authenticated showback for the active tenant by owner, project, application or cost_center from normalized completed cost records in a half-open UTC period. It SHALL refuse overlapping completed ingestions for the same subscription and usage day.

#### Scenario: Select a tenant and dimension
- **WHEN** an authorized user requests showback for a valid period and dimension
- **THEN** only records joined to a completed run of the same tenant and subscription are attributed once to that selected dimension

#### Scenario: Reject foreign tenant access
- **WHEN** a user selects a tenant to which they do not belong
- **THEN** the API responds 403 without reading cost aggregates

#### Scenario: Overlapping completed sources
- **WHEN** multiple completed ingestion IDs supply the same subscription and day in the period
- **THEN** the API responds 409 ambiguous_cost_source without amounts or source identifiers

### Requirement: Explicit allocation policy and unassigned costs

The report SHALL expose its policy version and absence of catalog verification, retain missing and invalid labels as unassigned, and apply the minimum taxonomy syntax only to the selected dimension. It SHALL NOT infer ownership or shared-cost splits.

#### Scenario: Missing or invalid classification
- **WHEN** the selected label is blank, absent, non-string, a placeholder or syntactically invalid
- **THEN** its full signed amount and record count remain in the corresponding unassigned bucket

#### Scenario: No implicit organization mapping
- **WHEN** a record has organization but no owner and owner is selected
- **THEN** the record remains unassigned and no team is inferred

#### Scenario: Project typed-field fallback
- **WHEN** the project column is present or blank
- **THEN** the report uses the nonblank column or falls back to the canonical project tag respectively

### Requirement: Exact reconciliation by currency

The report SHALL preserve the normalized ledger precision as decimal strings and reconcile groups plus unassigned to total independently for each currency. Credits and observed zero SHALL remain distinct from absent data.

#### Scenario: Fractions and signed adjustments
- **WHEN** costs include sub-cent fractions, large amounts, credits and zero
- **THEN** no rounding or float conversion changes their amounts and reconciliation_difference is exactly zero per currency

#### Scenario: Undated and empty records
- **WHEN** completed records have no usage date or the period contains no dated records
- **THEN** undated records are counted as exclusions and never included in period amounts, while no records is distinguishable from an observed zero
