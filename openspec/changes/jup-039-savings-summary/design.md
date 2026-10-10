JUP: JUP-039

## Boundary and provenance

The client selects an explicit UTC interval [start, end), optional subscription
and top_n per currency; tenant is taken from the authenticated membership.
The command uses only dates and cannot encode a different tenant. No client
amounts or source rows are accepted. Conversation ownership is checked before
calling the internal provider.

`SavingsProvider.load_snapshot(tenant_id, selection)` returns the versioned
consumer contract `savings-input.v1`. Absence/failure returns 503 before writing
messages. Invalid snapshots return a generic 502. Default runtime contains no
sample provider. The JUP-033/034 adapter consumes server-side loaders; installing
those loaders is an explicit integration step, not an implemented upstream API.

## Calculation and presentation

Potential recommendations are proposed/accepted; dismissed, expired and
implemented recommendations do not establish realized savings and are excluded.
Annual estimates are supplied by the provider, never inferred by the summarizer.
Known zero remains zero; unknown estimates remain null. Currency groups are
independent. Exact addition is allowed only when a provider certifies distinct
independent_cost_basis values for all quantified opportunities in that currency.
Missing/repeated bases suppress totals. Partial coverage or unknown estimates
produce an explicitly partial subtotal when addition is otherwise valid.

JUP-033 has aggregated project candidates and no savings estimates. JUP-034
has caller-supplied scenarios, atomic cost scopes and totals calculated before
rounding. The adapter never invents atomic scopes from projects, never derives
savings from observed cost, and does not re-sum rounded JUP-034 amounts. Original
reports and their totals remain in evidence; the conservative presentation lists
individual estimates without an additive total until compatible scope provenance
is supplied. Scenario amounts remain hypothetical, not verified financial facts.

top_n affects presentation only. The complete validated snapshot, source
reports, assumptions, limitations, excluded states and SHA-256 survive in
message metadata.savings_evidence and conversation reload. These are distinct
from corpus citations. The hash detects snapshot changes; it is not a signature
or proof of authenticity.

## Integration and decisions

The documentary assistant path remains intact. The savings branch does not call
embeddings, retrieval or a language model. Existing database persistence and
authorization are reused. No shared architecture decision or ADR is necessary.
Do not mark the card complete without upstream runtime validation and the
assigned human reviews. See docs/api/savings-summary.md for adapter contracts.
