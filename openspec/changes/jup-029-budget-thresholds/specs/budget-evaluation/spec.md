## ADDED Requirements

### Requirement: Explicit budget definition
The system SHALL accept a positive fixed-decimal budget, currency, explicit UTC
date interval and ordered percentage thresholds for the authenticated tenant.

#### Scenario: Invalid definition
- **WHEN** the amount is zero, dates are reversed, thresholds repeat or extra fields are supplied
- **THEN** evaluation returns 422 without reading cost data

### Requirement: Exact observed consumption and deviations
The system SHALL evaluate the selected currency's billing v2 total with decimal
arithmetic, preserving credits and comparing thresholds before display rounding.

#### Scenario: Exact threshold
- **WHEN** a 100.00 EUR budget has an observed total of 80.00 EUR
- **THEN** consumption is 80.00 percent, remaining is 20.00 and deviation is -20.00, and the 80.00 threshold is reached

#### Scenario: Rounded percentage is not a threshold crossing
- **WHEN** consumption rounds to a configured threshold but is mathematically below it
- **THEN** that threshold is not marked reached

### Requirement: Honest availability and protected costs
The system SHALL preserve tenant isolation, billing ambiguity errors and data
quality, without mixing currencies or interpreting absent data as observed zero.

#### Scenario: Missing currency
- **WHEN** no total exists for the budget currency
- **THEN** evaluation is unavailable and financial metrics and threshold results are null

#### Scenario: Partial observed data
- **WHEN** a matching total exists in a partial billing summary
- **THEN** metrics are provisional and omission counts remain visible

#### Scenario: Overlapping sources
- **WHEN** billing rejects ambiguous cost sources
- **THEN** evaluation returns 409 with ambiguous_cost_source and no amounts

#### Scenario: Unauthorized tenant
- **WHEN** a user requests evaluation for a tenant without membership
- **THEN** access is denied before reading billing costs
