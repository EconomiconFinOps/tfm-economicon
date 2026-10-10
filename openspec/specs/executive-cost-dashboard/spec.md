# executive-cost-dashboard Specification

## Purpose
Present stored Azure costs in the executive dashboard for an inclusive monthly interval, preserving exact per-currency amounts, monthly evolution and comparison of the first and last observed non-zero costs. Reuse the existing frontend style and billing summary contract.
## Requirements
### Requirement: Inclusive monthly selection for stored costs

The executive dashboard SHALL select an inclusive start and end month, default
to the last six complete UTC months, and support any valid monthly interval
within years 0001 through 9998 without a six-month cap. It SHALL consume existing
stored billing v2 data, not claim live Azure completeness.

#### Scenario: Default across a calendar boundary
- **WHEN** the UTC clock is January 2027
- **THEN** the initial selection is July through December 2026
- **AND** local timezone does not change the selected months

#### Scenario: Arbitrary ranges and API boundaries
- **WHEN** February through August 2026 is selected
- **THEN** the total query covers 2026-02-01 inclusive through 2026-09-01 exclusive and the series has seven ordered monthly positions
- **AND** March through June has four positions, not six

#### Scenario: Single month and calendar validation
- **WHEN** one valid month is selected
- **THEN** that month is accepted, the total response is reused for its point and comparison uses the explicit one-or-no-eligible-month state
- **AND** blank, invalid, reversed or out-of-domain month selections cause no billing request and explain the correction

#### Scenario: Early years and months in progress
- **WHEN** an early year such as 0099, a current month or a future month is selected
- **THEN** UTC boundaries retain the selected year and all months in the interval
- **AND** current/future labels imply no forecast or certification of complete charges

### Requirement: Whole-interval totals and existing breakdowns

The dashboard SHALL display authoritative whole-interval totals and groups from
one aggregate request, separately by currency. It SHALL support subscription,
resource_group, service, project and tag using their existing contract semantics,
and SHALL NOT reconstruct the total from rounded monthly or group amounts.

#### Scenario: Rounded components differ from the total
- **WHEN** stored sub-cent records produce monthly or grouped rounded amounts whose sum differs from the whole-interval rounded total
- **THEN** the dashboard retains the aggregate total and original components
- **AND** explains independent rounding without redistributing the residual

#### Scenario: Multiple currencies and missing dimensions
- **WHEN** EUR and USD totals coexist with missing group labels or subscription scope
- **THEN** totals and rows retain their currencies without conversion or summation across currencies
- **AND** null dimensions/scopes have explicit missing labels without invented service or organisational names

#### Scenario: Tag canonicalization
- **WHEN** tag grouping sends a valid key whose spelling the backend canonicalizes
- **THEN** all requests use the same selected key and responses use the aggregate response's canonical key
- **AND** changing away from tag omits the inactive key without changing backend normalization

### Requirement: Exact signed comparison of non-zero observed endpoints

For each selected currency the dashboard SHALL use the first and last
chronological months within the selected interval with a successfully recorded
non-zero cost. Missing currency totals and recorded zero costs SHALL be excluded
only from comparison endpoint selection. Negative costs and exact amounts
outside the safe plotting range SHALL remain eligible.
Absolute difference SHALL be last eligible cost minus first eligible cost and
percentage SHALL divide that difference by the first eligible non-zero cost
times 100, with exact money and signed two-decimal percentage presentation.
The dashboard SHALL identify both effective months and currency, separately
from the selected interval, without filtering totals, breakdown or series.

#### Scenario: Whole year with costs only in interior months
- **WHEN** January through December is selected and successful EUR results contain non-zero costs only from March through August
- **THEN** the comparison uses August against March and labels those effective months in EUR
- **AND** the series/table retains all twelve selected positions, absence stays a gap and totals/breakdown cover the whole year

#### Scenario: Zero and missing months at the interval edges
- **WHEN** the first selected month has recorded zero and a following month has 40.00 EUR, with a last eligible month at -50.00 EUR and successful zero or absent months after it
- **THEN** comparison uses the 40.00 and -50.00 months, giving -90.00 EUR and -225.00 percent
- **AND** zeros remain plotted zeros and missing months remain labelled gaps without connecting them

#### Scenario: One or no eligible month
- **WHEN** all monthly outcomes are successfully known and only one month has non-zero cost in the selected currency
- **THEN** comparison has no numeric difference or percentage and explains "Solo hay un mes con coste para comparar"
- **AND** when no month has non-zero cost it instead explains "No hay meses con coste en este periodo", including a range containing only recorded zeros

#### Scenario: Negative base and large exact amounts remain eligible
- **WHEN** first eligible cost is -100.00 and last eligible cost is -50.00 in one currency
- **THEN** absolute difference is +50.00 and percentage -50.00 with the negative base identified
- **AND** non-zero money above Number.MAX_SAFE_INTEGER remains eligible from its exact cost even when its plotted value is null, with no negative zero percentage

#### Scenario: Each currency chooses its own months
- **WHEN** EUR and USD coexist but have non-zero costs in different months
- **THEN** switching currency selects the first and last eligible months of that currency only
- **AND** other-currency-only months do not supply an endpoint, total currencies stay separate and all selected monthly positions are retained

#### Scenario: Errors inside two established eligible endpoints
- **WHEN** two eligible months exist, all earlier and later months have successful outcomes, and one intervening month fails or has incompatible metadata
- **THEN** the comparison may show those observed endpoints and exact arithmetic with an explicit interior-error limitation
- **AND** the failed month stays an error/gap with its cause, never an empty or zero month

#### Scenario: Errors prevent determining the endpoints or eligible count
- **WHEN** a failed or metadata-incompatible month occurs before the first or after the last observed non-zero month, or errors coexist with fewer than two eligible months
- **THEN** numeric comparison is unavailable and explains that the months with cost cannot be determined because of those errors, identifying the affected month/cause
- **AND** the dashboard does not replace that uncertainty with either definitive one-month or no-cost messages, while valid aggregate/series results remain available

#### Scenario: Zero aggregate with non-zero months
- **WHEN** successful months contain 20.00 and -20.00 EUR and the authoritative interval total is 0.00 EUR
- **THEN** both months remain eligible and comparison is -40.00 EUR and -200.00 percent
- **AND** eligibility is not inferred from the aggregate total or from rounded group sums

#### Scenario: Partial successful data
- **WHEN** successful monthly data includes partial metadata and at least two eligible months can be determined
- **THEN** those recorded costs can be compared as observed partial results with the effective months identified
- **AND** partial notices and stored-query limitations remain visible without claiming full Azure coverage

### Requirement: Honest monthly series and partial outcomes

The dashboard SHALL include one monthly position per selected month, expose
absence and errors as gaps rather than zero, and provide an exact accessible
table. It SHALL disclose partial metadata, query failures and representation
limits without inventing metrics.

#### Scenario: Missing month versus zero month
- **WHEN** a monthly currency total is absent and another month has recorded 0.00
- **THEN** the absent month is a labelled gap and the recorded zero is a plotted zero
- **AND** graph lines do not connect gaps and the table distinguishes both states

#### Scenario: Monthly error with successful aggregate
- **WHEN** the whole-interval request succeeds and an interior monthly request fails
- **THEN** whole-interval totals/groups remain available with a monthly failure notice
- **AND** the failed month is a gap, while two non-zero eligible amounts can still produce an observed comparison only when failed months lie strictly between the established endpoints, with an explicit limitation

#### Scenario: Aggregate failure or ambiguous cost source
- **WHEN** the whole-interval request fails, including 409 ambiguous_cost_source
- **THEN** no successful monthly sum or demonstration data is substituted as a total or valid dashboard result
- **AND** a specific overlap warning appears for 409 with no replacement, confirmation or ingestion write action

#### Scenario: Partial metadata and repeated undated counts
- **WHEN** responses indicate partial, missing dimensions or excluded undated records
- **THEN** the dashboard exposes those limitations and identifies calculations as observed partial data
- **AND** repeated tenant-wide undated counts are not summed into an invented interval count

#### Scenario: Plotting cannot safely represent an amount
- **WHEN** a monthly amount's integer cents exceed the safe Number range
- **THEN** the graph omits that point with a representation notice and a gap
- **AND** the exact value remains in the accessible table and other safe points remain usable

#### Scenario: Unsupported executive metrics
- **WHEN** the executive dashboard renders from billing v2
- **THEN** its previous demo trend, inventory and demo export are absent and savings remains unavailable
- **AND** no forecast, budget, live Azure assurance or invented subscription/account filter appears

### Requirement: Query cohorts respect session scope and cancellation

The dashboard SHALL identify each query cohort by contract version, tenant,
session generation, period, grouping and effective requested tag. It SHALL
limit concurrent requests to three, cancel obsolete work, validate response
selection metadata and never mix data from different executions.

#### Scenario: Scope changes during a request
- **WHEN** tenant, session, period, grouping or effective tag changes before the previous requests finish
- **THEN** prior amounts are hidden, obsolete initiated requests are aborted and pending obsolete requests do not start
- **AND** late old responses do not alter the new dashboard

#### Scenario: Many selected months and explicit retry
- **WHEN** a long interval is loading or the user retries a partially failed cohort
- **THEN** no more than three requests are simultaneous and all selected months are retained
- **AND** retry loads a fresh complete cohort without mixing prior successes into its gaps or automatically repeating 409/422 failures

#### Scenario: Cached values during refetch
- **WHEN** the current cohort is refetched with cached data
- **THEN** controls remain usable but previous amounts/comparisons are hidden under an announced loading state
- **AND** after refetch only the new cohort outcomes are displayed

#### Scenario: Response metadata or session is invalid
- **WHEN** a response has the wrong dates, timezone, grouping or incompatible canonical tag, or the session expires
- **THEN** mismatched responses are errors rather than accepted amounts, and expired-session behavior follows existing invalidation
- **AND** without a valid token and tenant no billing requests are initiated

### Requirement: Existing visual language and accessible responsive behavior

The executive dashboard SHALL reuse the existing application shell, cards,
compatible controls, chart theme and semantic color tokens. It SHALL preserve
the application's visual language without introducing a palette or dependency
and provide labelled keyboard controls, announced states and a table alternative.

#### Scenario: Desktop and mobile presentation
- **WHEN** normal, loading, empty, error and partial states are viewed at 1440×900 and 390×844
- **THEN** cards, typography, spacing, borders, icons and navigation match the established application style
- **AND** the page has no horizontal overflow, while wide tables may scroll in their own container

#### Scenario: Focus and currency selection
- **WHEN** a keyboard user changes months, grouping, tag or currency
- **THEN** labels and focus remain visible and the selected currency scopes the graph/comparison
- **AND** all exact monthly values and states can be understood through the table and text without relying on color

#### Scenario: Unchanged neighboring capabilities
- **WHEN** the change is exercised alongside /overview-legacy and the other dashboard routes
- **THEN** legacy billing, authentication, tenant isolation and unrelated demonstration screens retain their existing behavior
- **AND** documentation identifies the executive route's new behavior without claiming other screens were connected

### Requirement: Breakdown adjacent to its grouping control

For a successful executive cost result with recorded totals, the dashboard SHALL
place the existing whole-period breakdown as the first result block after the
month/grouping selection and applicable status notices, before totals,
comparison and monthly trend. Visual order and accessible reading order SHALL
agree. Grouping SHALL change the breakdown dimension only, without filtering
the monetary scope of totals, comparison or trend.

#### Scenario: Breakdown follows selection
- **WHEN** a valid stored-cost result is displayed after choosing months and grouping
- **THEN** the grouping control precedes the whole-period breakdown and the breakdown precedes totals, comparison and monthly trend in visual and accessible reading order
- **AND** applicable status notices remain understandable, the breakdown is displayed only once and loading or aggregate error exposes no previous breakdown values

#### Scenario: Grouping preserves financial scope
- **WHEN** the same tenant, period and currency contain multiple subscriptions, services and projects and the user changes grouping from service to project
- **THEN** the breakdown labels and grouped amounts reflect the requested dimension near the control
- **AND** whole-period totals, ordered monthly costs and first-to-last non-zero comparison retain the same amounts once each query cohort settles, without currency conversion or filtering
