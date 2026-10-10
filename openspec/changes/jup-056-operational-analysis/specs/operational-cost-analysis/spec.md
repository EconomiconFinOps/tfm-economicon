## ADDED Requirements

### Requirement: Conjunctive operational cost filters
The system SHALL allow an authenticated analyst to filter stored Azure costs by subscription ID, service, project and tag key/value simultaneously before aggregation, using the active authorized tenant and selected UTC period.

#### Scenario: Combined filters
- **WHEN** an analyst applies account, service, project and tag filters together
- **THEN** each returned cost record contributes only when all supplied filters match and the totals and grouped breakdown cover that same intersection

#### Scenario: Invalid tag pair
- **WHEN** only a tag key or only a tag value is supplied
- **THEN** the API rejects the selection with HTTP 422 and the page explains that both are required

#### Scenario: No matching data
- **WHEN** valid filters match no stored records
- **THEN** the page shows an empty result rather than demonstration data or a fabricated zero-cost total

### Requirement: Safe compatible billing query
The system SHALL retain unfiltered billing v2 behavior, parameterize all filter values, preserve exact monetary amounts per currency and echo applied filters for filtered requests.

#### Scenario: Existing consumers
- **WHEN** an executive or budget client requests costs without operational filters
- **THEN** its response fields and aggregation behavior remain compatible with the existing v2 contract

#### Scenario: Ambiguous sources
- **WHEN** the selected tenant and period contain overlapping cost sources even if a filter would hide one source
- **THEN** the query returns the existing ambiguity error rather than an apparently valid filtered amount

#### Scenario: Ignored filters
- **WHEN** the backend returns missing or different applied filter metadata for a filtered request
- **THEN** the operational page rejects the result instead of labelling global costs as filtered costs

#### Scenario: Multiple currencies and credits
- **WHEN** matching records contain multiple currencies, negative amounts or zero
- **THEN** the page preserves their exact decimal strings and currency labels without conversion or combining currencies

### Requirement: Scoped operational interaction
The operational page SHALL expose labelled period/filter controls, an explicit apply/reset flow, current applied scope, grouped detail and current-result export using existing session and style infrastructure.

#### Scenario: Pending or failed replacement
- **WHEN** a selected query is invalid, fetching, failed or belongs to a prior tenant/session
- **THEN** the page hides its previous data and export and provides the relevant invalid, loading or error state

#### Scenario: Apply and clear
- **WHEN** an analyst edits draft filters and applies them or clears them
- **THEN** the requested query and visible applied scope change together and results are obtained for that selection

#### Scenario: Partial data
- **WHEN** the contract reports partial data or undated records
- **THEN** the page shows the contract's limitation and does not imply the results are a complete invoice
