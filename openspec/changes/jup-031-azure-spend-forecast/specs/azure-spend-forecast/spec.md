## ADDED Requirements

### Requirement: Authenticated monthly Azure forecast
The backend SHALL return a read-only monthly spend forecast grouped by subscription,
service or project for the active authorized tenant, preserving original currency
and exact monetary strings. Selection SHALL contain 1–24 closed calendar months
and a forecast horizon of 1–3 months. Conflicting completed ingestions SHALL be rejected.

#### Scenario: Unauthorized tenant
- **WHEN** a caller requests a tenant outside their memberships
- **THEN** the request is rejected before the forecast cost reader runs

#### Scenario: Supported dimensions and currencies
- **WHEN** completed, nonconflicting history exists in EUR and USD for a service
- **THEN** the service forecasts remain separate by currency without conversion

#### Scenario: Invalid period or source
- **WHEN** selection includes a current partial month, more than 24 months or conflicting ingestions
- **THEN** the backend rejects invalid selection with 422 or ambiguous cost source with 409

### Requirement: Temporal evaluation against a reference
Each forecast SHALL require at least `8 + horizon` consecutive observed months.
The backend SHALL compare a last-month baseline with a linear trend using three
expanding temporal origins, at least six training months and the complete requested
horizon in every holdout. Trend SHALL be selected only for greater than 5 percent MAE improvement.

#### Scenario: Consistent increasing synthetic spend
- **WHEN** twelve monthly costs increase by 10 from 100 to 210 and horizon is three
- **THEN** the trend predicts 220, 230 and 240, with baseline 210 and baseline MAE 20

#### Scenario: Constant spend
- **WHEN** all observed monthly costs are equal
- **THEN** the simpler last-month reference is selected, including genuine observed zero

### Requirement: Explicit sufficiency and uncertainty
The response SHALL distinguish empty data, short history, missing months, missing
dimension and nonfinite amounts. Missing months SHALL NOT be filled as zero.
Forecasts SHALL include a per-step empirical error envelope, temporal origins and
both model MAEs, without a nominal coverage claim or real-data accuracy claim.

#### Scenario: Incomplete sample
- **WHEN** only the public June 2024 sample or a series with an internal gap exists
- **THEN** the response contains no forecast points for that series and gives the reason

#### Scenario: Limits of uncertainty
- **WHEN** a forecast is returned
- **THEN** its warnings disclose uncalibrated ranges, incomplete coverage knowledge,
  signed net costs and omitted seasonal, pricing and infrastructure changes
