## ADDED Requirements

### Requirement: Explicit authorized summary request
The system SHALL accept an explicit savings selection in the assistant API or
the command `/ahorro YYYY-MM-DD YYYY-MM-DD`, using authenticated tenant and
conversation ownership before reading sources.

#### Scenario: Foreign conversation
- **WHEN** a user requests a summary for another user's conversation
- **THEN** the API returns 404 without calling the savings provider

#### Scenario: Invalid selection
- **WHEN** the period is reversed or client-supplied amounts or identity are present
- **THEN** the API returns 422 without writing messages or querying sources

### Requirement: Honest potential savings
The system SHALL label every summary as potential estimates, leave realized
savings unverified, separate currencies and preserve null estimates.

#### Scenario: Unknown impact
- **WHEN** a recommendation has no quantified impact
- **THEN** the recommendation remains visible as unquantified and is not treated as zero

#### Scenario: Overlapping benefits
- **WHEN** recommendations have duplicate or unknown independent cost bases
- **THEN** the summary does not present their sum as an additive savings total

#### Scenario: Independent known estimates
- **WHEN** quantified opportunities have certified distinct cost bases
- **THEN** per-currency totals use exact decimal arithmetic and supplied annual estimates

### Requirement: Durable traceable evidence
The system SHALL retain the full source snapshot, assumptions, limitations and
upstream reports even when top_n limits visible recommendations.

#### Scenario: Reload a bounded summary
- **WHEN** the user reopens a conversation whose summary was limited to top_n
- **THEN** the complete original evidence remains available with its snapshot hash

#### Scenario: Invalid cross-tenant source
- **WHEN** a provider returns foreign tenant or mismatched period evidence
- **THEN** the API returns a generic 502 before persisting messages

### Requirement: Explicit upstream availability
The system SHALL distinguish missing providers from empty data and SHALL NOT
use synthetic rows as a runtime fallback.

#### Scenario: Dependency absent
- **WHEN** the recommendations and impact provider is not configured
- **THEN** a savings request returns 503 without embeddings, generation or persisted messages

#### Scenario: Hypothetical impact input
- **WHEN** JUP-034 provides a caller-supplied scenario for a matched recommendation
- **THEN** the adapter preserves that basis, its amounts, sources and assumptions without asserting realized savings
