# JUP-056 — Operational analysis

## Existing contracts and scope

`GET /billing/summary` v2 reads normalized stored cost, keeps currencies separate and returns decimal strings. The executive dashboard and budget evaluator already use it. The operational page must use this layer instead of the static fixtures. An account is a subscription ID; project uses the existing typed project / normalized tag fallback. No Azure subscription API or external provider is called from the page.

## Additive filter contract

Optional request fields: `subscription_id`, `service_name`, `project`, `filter_tag_key`, `filter_tag_value`. All supplied predicates combine with AND. Values match exactly and case-sensitively; empty, whitespace-only and control-character selections are rejected. Meaningful leading/trailing spaces remain literal. Tag key normalization reuses the current canonicalization (`env` → `environment`, `CostCenter` → `cost_center`). The tag pair is independent of grouping `tag_key`, and both fields are required together.

Filtering happens before aggregation and missing-dimension counts. SQL values are parameters, never interpolated expressions. Source-overlap detection covers the authorized tenant and period before applying filters, so filtering cannot hide ambiguous data. The existing tenant-wide undated count and ingestion indicators retain their meanings and are explained in the UI/documentation.

Filtered responses echo a `filters` object containing the requested fields (canonical tag key). Unfiltered v2 responses preserve their previous shape. The frontend rejects a filtered response without matching metadata, so an older backend cannot silently supply global totals for a filtered request.

## Interaction and precision

A draft filter form has Apply and Clear actions; changing a field does not fetch immediately. Applied scope remains visible alongside results. Dates use UTC half-open ranges consistent with v2, with user-facing date labels explaining the exclusive end. All query identity includes tenant, session generation, dates, grouping and every filter. Old results/export are hidden during invalid selections, refetch/error and tenant changes. Existing HTTP/session handling and abort signal are reused.

Totals and detail retain decimal strings. There is no mixed-currency total, invented usage ratio, hourly chart or unsupported multi-cloud data. Export contains only current filtered detail. Labels, focus indicators, responsive control grids and scrollable table reuse existing design tokens; shared shell mobile behavior remains outside this change.

## Verification and limits

Tests cover simultaneous predicates, canonical tags, literal values/SQL parameters, foreign tenant isolation, no matches, credits/zero/multicurrency precision, overlap errors and backward compatibility. Frontend tests cover request/response metadata, stale state and filter actions. Browser screenshots distinguish deterministic API doubles from real database evidence. Human pairing, `Revision JUP-056`, `Validacion JUP-056`, production integration and acceptance are never inferred from automated checks.
