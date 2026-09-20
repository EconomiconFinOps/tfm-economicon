## ADDED Requirements

### Requirement: Explicit normalized resource identity
The processor SHALL expose `resource_id` and `resource_name` as distinct
normalized fields when the Azure row provides them, following the same
promotion pattern as the existing typed dimensions.

#### Scenario: Query contains resource-level identifiers
- **WHEN** an Azure row contains `ResourceId` and `ResourceName`
- **THEN** the processor promotes them to typed fields and retains only
  unknown values in the additional dimensions object

#### Scenario: Query omits resource-level grouping
- **WHEN** Azure does not return resource-level dimensions for a row
- **THEN** `resource_id` and `resource_name` are null and the processor does
  not infer a value

### Requirement: Non-blocking detection of resource hierarchy inconsistency
Within a single normalization batch, the processor SHALL detect a
`resource_id` reported under more than one `resource_group`, comparing
values case-insensitively while preserving each row's original casing.
Detection SHALL NOT reject the row or the batch.

#### Scenario: A resource stays under one resource group
- **WHEN** all rows for a given `resource_id` in the batch share the same
  `resource_group`, regardless of casing differences
- **THEN** no inconsistency is recorded for that resource

#### Scenario: A resource appears under two resource groups in one batch
- **WHEN** rows for the same `resource_id` report different
  `resource_group` values in the same batch
- **THEN** every affected row is normalized and persisted as usual
- **AND** the inconsistency is recorded as a queryable signal, not as a
  normalization failure

#### Scenario: Case-only differences are not inconsistencies
- **WHEN** the same `resource_id` reports `resource_group` values that
  differ only in letter casing
- **THEN** no inconsistency is recorded, and each row keeps its original
  source casing
