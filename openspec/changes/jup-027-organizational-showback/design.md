JUP: JUP-027

## Decisions

Use the normalized azure_cost_records ledger, with the same completed-run, tenant/subscription join and overlap boundary as billing summary (ADR-0010). The SQL returns aggregates by the selected value and currency in one serializable transaction. No monetary values are derived from the existing rounded summary.

Each selected row contributes 100% once. Owner and application are different canonical tags; organization is not an alias for owner. Project uses its normalized typed column, falling back to its canonical tag only for null/blank columns, as in billing v2. cost_center is available as a fourth view. Views are alternative partitions and must not be added together. Shared costs have no invented split: a valid explicit unit receives the full amount; missing/invalid labels remain unassigned.

The isolated classifier follows JUP-015 economicon-minimum-v1: trim, case-sensitive portable identifiers up to 128 characters, case-insensitive placeholder rejection. Only the selected dimension determines assignment. Non-string JSON values become an invalid sentinel before grouping. No approved catalog is loaded: catalog_status=not_provided, organizationally_valid=null and a provisional adapter version are visible in the response. Direct owner attribution is not evidence of corporate team membership. Catalog mapping and temporal validity require later integration with JUP-015, not an invented catalog.

SUM uses the ledger's DECIMAL precision; Python Decimal uses a context sized from inputs and group count. The response retains up to 12 fractional digits, with a minimum of two for readability. Rounding would break reconciliation, so no display rounding is applied. Credits and zero amounts stay in their bucket; currencies are never combined or converted. Each currency exposes total, assigned, unassigned, counts and an exact zero reconciliation difference. Missing and invalid are distinct buckets even when both amounts are zero.

## Failure and data boundaries

An authenticated active tenant is mandatory. Invalid periods/dimensions return 422 before querying costs. The period is [start,end) in UTC; omitting both dates uses the current UTC month. More than one completed ingestion for a subscription/day returns 409 without money or source IDs. Undated records are excluded from the amount and counted for the tenant across all completed data because their period cannot be established. Partial indicates unassigned records or undated exclusions, not an estimate of ingestion completeness. Empty and observed zero are distinct.

## Verification

Independent expected fixtures cover exact arithmetic, cancellation, precision beyond 28 significant digits, invalid labels, separate currencies, HTTP scope enforcement, completed source selection, date boundaries, project fallback and overlap rejection. Real SQL is tested only on a disposable marked CockroachDB node; synthetic ledger data is not production evidence.
