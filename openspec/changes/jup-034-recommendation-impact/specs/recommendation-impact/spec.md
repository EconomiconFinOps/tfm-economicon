## ADDED Requirements

### Requirement: Explicit monthly and annual potential
The system SHALL calculate gross monthly savings as max(monthly baseline minus
monthly target, zero), annualize the unrounded result by 12, and expose inputs,
evidence references, assumptions and caller-supplied provenance.

#### Scenario: Calculable recommendation
- **WHEN** the monthly baseline is 100 EUR and target is 60 EUR
- **THEN** monthly potential is 40.00 and annual potential is 480.00 EUR
- **AND** observed savings is null and unchanged-use/price assumptions are visible

#### Scenario: Missing cost scenario
- **WHEN** baseline and target are both missing
- **THEN** status is insufficient_data and both potential amounts are null
- **AND** a missing amount is never substituted with zero

### Requirement: Prevent duplicate potential in a portfolio
The system SHALL aggregate only disjoint declared atomic cost scopes, select
descending raw monthly savings with stable ID tie-breaking, explain exclusions,
separate currencies and reject duplicate recommendation IDs.

#### Scenario: Alternatives overlap
- **WHEN** two recommendations on the same atomic scope save 40 and 30 EUR monthly
- **THEN** the portfolio includes only 40 EUR and identifies the excluded alternative

#### Scenario: Independent currencies
- **WHEN** disjoint recommendations use EUR and USD
- **THEN** each currency has its own total and no converted grand total exists

#### Scenario: Scope identity normalization
- **WHEN** two scope keys differ only in case, exterior whitespace or trailing slash
- **THEN** the keys are treated as the same cost scope

### Requirement: Authenticated bounded scenario evaluation
The system SHALL require the existing bearer and tenant membership checks,
reject authority or observed-savings fields in the body, and validate bounded
nonnegative decimal strings, a complete baseline month and unique identifiers.

#### Scenario: Foreign tenant
- **WHEN** a caller selects a tenant they do not belong to
- **THEN** the endpoint responds with 403 without evaluating the scenario

#### Scenario: Invalid amount
- **WHEN** an amount is negative, numeric JSON, NaN, infinity or exponential text
- **THEN** the endpoint responds with 422
