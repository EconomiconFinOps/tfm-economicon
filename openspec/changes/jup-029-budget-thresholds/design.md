JUP: JUP-029

## Contract

POST /billing/budget/evaluate accepts amount as a positive canonical decimal
string with exactly two fractional digits and at most 26 integer digits,
currency as three uppercase ASCII letters (not an ISO registry validation),
start_date/end_date as ISO dates, and thresholds_percent as 1–10 positive,
strictly increasing decimal strings <= 1000.00 (default ["80.00", "100.00"]).
Extra fields are rejected. Budget scope is the entire authenticated tenant and
the selected currency. Dates are explicit, inclusive start/exclusive end, UTC;
start must precede end. No recurrence or automatic period rollover.

The route obtains tenant identity through get_active_tenant and fetches billing
v2 with group_by=subscription. It never accepts client totals or tenant identity
in the body. Reuse existing completed-ingestion, currency, date and overlap
rules. An ambiguous source yields the same 409 code as /billing/summary.

Use the selected currency's already rounded v2 total as observed spend S and
budget B. Do not sum independently rounded groups or convert currencies.
consumption_percent = 100*S/B; remaining_amount = B-S;
deviation_amount = S-B; deviation_percent = 100*(S-B)/B.
Deviation is against the entire budget, not elapsed-time prorating or forecast.
Use Decimal with a local precision sufficient for input operands; round output
percentages once to two places, HALF_UP. Monetary subtraction is exact at cents.
Compare S*100 >= B*threshold before rounding percentages. Equality reaches the
threshold. Return every reached threshold in configured order and the highest
one (null if none). Credits are preserved, including negative consumption.

No selected-currency total => unavailable with null metrics, never invented
zero or a healthy status. An observed zero is evaluated. Partial summaries with
a matching total yield provisional metrics; retain data_status and omission
counts. Available means observed data exists, not certified complete coverage.
Duplicate currency totals or mismatched periods violate the internal contract
and fail rather than silently produce a result.

## Architecture

ADR: not applicable. This is a local stateless calculation over the established
JUP-026 billing boundary; no persistence, service boundary or shared architecture
change. Existing [ADR-0010](../../../docs/adr/ADR-0010-azure-cost-source-overlap.md)
continues to govern source ambiguity.

## Validation

Cover exact threshold equality, rounded-percent false positives, credits, zero,
missing currency, partial input, large amounts, invalid inputs, period forwarding,
tenant membership, authentication and 409 propagation. Reuse the real Cockroach
billing fixture for an opt-in acceptance case with date/tenant exclusions.
