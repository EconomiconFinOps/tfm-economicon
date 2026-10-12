## Purpose

Persist tenant-scoped cost-anomaly candidate episodes detected with the JUP-019 daily business rule over observed daily costs per service, with an anchored reference, accumulated impact, severity, traceable status and an authenticated API, so that the anomalies panel and the assistant can list, prioritise and follow them without claiming causes.

## ADDED Requirements

### Requirement: Daily business rule over observed daily costs

The system SHALL evaluate, for the active tenant, each service and currency group on each evaluable day. A group is the pair (currency, service) over completed ingestions of the tenant, keeping a null service as its own group, with the billing v2 completed-ingestion, tenant and source-overlap protections. The observed cost of a group on a day SHALL be the exact sum of its records with that usage date; a group without records on an observed tenant day has an observed cost of 0.00. A day SHALL never be derived by dividing a period aggregate.

The expected cost of a group on day D SHALL be the anchored reference of its tracking episode when one exists, and otherwise the mean daily observed cost of the group over the seven days D-7 to D-1. The rule SHALL trigger only when expected > 0 AND observed - expected > 100.00 AND (observed - expected) * 100 > expected * 20, all compared with exact decimal arithmetic before any display rounding. Both thresholds SHALL be strict and both conditions SHALL be required. Thresholds SHALL be nominal amounts in the group currency and SHALL apply only to EUR and USD; groups in any other currency SHALL NOT be evaluated and the detection result SHALL list those currencies as unsupported.

#### Scenario: Both conditions exceeded
- **WHEN** a EUR service has observed 400.00 on each of the seven previous days and 550.00 on day D, with no tracking episode
- **THEN** the rule triggers on D with expected 400.00, absolute increase 150.00 and relative increase 37.50 %

#### Scenario: Exact absolute boundary
- **WHEN** expected is 400.00 and observed is 500.00
- **THEN** the rule does not trigger because the absolute increase equals 100.00

#### Scenario: Exact relative boundary
- **WHEN** expected is 1000.00 and observed is 1200.00
- **THEN** the rule does not trigger because the relative increase equals 20 %

#### Scenario: Only one condition exceeded
- **WHEN** expected is 100.00 and observed is 190.00, or expected is 5000.00 and observed is 5150.00
- **THEN** the rule does not trigger

#### Scenario: Zero or negative expected cost
- **WHEN** a service has no cost, or a nonpositive net cost, over the seven previous days and observes 150.00 on D
- **THEN** the rule does not trigger, the relative increase is not computed and no episode is opened

#### Scenario: Unsupported currency
- **WHEN** a tenant has GBP records that would exceed both conditions nominally
- **THEN** no GBP episode is opened and the detection result lists GBP as unsupported

#### Scenario: Large monetary values
- **WHEN** valid daily sums exceed exact IEEE-754 integer precision
- **THEN** comparisons, impact and stored amounts preserve cents as decimal strings

### Requirement: Evaluable days and coverage

An observed tenant day is a UTC date with at least one completed cost record of the tenant in any currency. The last complete day SHALL be the day before the latest observed tenant day, and never today or later in UTC. A day D SHALL be evaluable only when D and each of the seven days D-7 to D-1 are observed tenant days. Non-evaluable days SHALL be skipped and reported with their reason, and SHALL NOT open, extend, end or add impact to any episode.

#### Scenario: Latest day is not treated as complete
- **WHEN** the latest observed tenant day is 2026-09-14
- **THEN** the last complete day is 2026-09-13 and 2026-09-14 is not evaluated

#### Scenario: Gap in the reference window
- **WHEN** a tenant has no records on 2026-09-05
- **THEN** 2026-09-05 is skipped as not_observed and each day from 2026-09-06 to 2026-09-12 is skipped as reference_incomplete
- **AND** no episode opens, extends, ends or adds impact on those days

#### Scenario: Not enough history
- **WHEN** a tenant has fewer than eight consecutive observed days
- **THEN** detection reports insufficient_data and stores nothing

### Requirement: Detection run on demand is bounded and idempotent

An authenticated member of the active tenant SHALL be able to request a detection run. Identity, tenant selector and membership SHALL be checked before rejecting a request body. A run SHALL evaluate, in ascending date order, the days after the tenant's last evaluated day up to the last complete day, limited to the seven most recent of those days; on the first run, the seven days ending on the last complete day. After a successful run the last evaluated day SHALL be the last complete day. A run SHALL be atomic: on any failure, including an ambiguous cost source, nothing SHALL be stored. Repeating a run with no new complete day SHALL change nothing and report up_to_date. Concurrent runs for the same tenant SHALL NOT duplicate episodes; a run that loses the race SHALL return a conflict and store nothing. The run SHALL only read cost data and never use rules supplied in the request.

#### Scenario: First run
- **WHEN** the first run happens with a last complete day of 2026-09-13
- **THEN** days 2026-09-07 to 2026-09-13 are evaluated in order and the response lists evaluated and skipped days and the opened, continued and no-longer-observed counts

#### Scenario: Repeated press
- **WHEN** the run is requested twice without new cost data
- **THEN** the second response is up_to_date and stored episodes are identical

#### Scenario: Days missed between runs
- **WHEN** the previous run evaluated up to 2026-09-01 and the last complete day is now 2026-09-20
- **THEN** only 2026-09-14 to 2026-09-20 are evaluated and the response reports the unevaluated range 2026-09-02 to 2026-09-13

#### Scenario: Ambiguous source
- **WHEN** billing detects overlapping cost sources in the read range
- **THEN** the run returns 409 with ambiguous_cost_source and stores neither episodes nor the last evaluated day

#### Scenario: Concurrent runs
- **WHEN** two runs for the same tenant are requested at the same time
- **THEN** stored episodes equal those of a single run and at most one run reports success

### Requirement: Episodes with anchored reference and tolerance

A triggering group without a tracking episode SHALL open a new episode starting on that day, with status new, observation observed and an anchored reference equal to the expected cost of that day. A tracking episode is one with status new or investigating and observation observed; each tenant, currency and service SHALL have at most one. While an episode is tracking, a triggering day SHALL extend it by setting its last seen day. When an evaluated day is more than three days after its last seen day without triggering, the episode SHALL become no_longer_observed, recording that day. A no-longer-observed or closed episode SHALL never be reopened; a later trigger opens a new episode that references the most recent previous episode of the same group. Episode identifiers SHALL be opaque, deterministic for tenant, rules version, currency, service and start day, and SHALL never authorise access.

#### Scenario: Opening an episode
- **WHEN** Compute EUR triggers on 2026-09-08 with expected 1000.00 and no tracking episode
- **THEN** one episode is stored with start and last seen day 2026-09-08, reference 1000.00, status new and observation observed

#### Scenario: Anchored reference keeps a sustained rise visible
- **WHEN** Compute EUR stays at 2400.00 per day for fourteen days after its episode opened with reference 1000.00
- **THEN** every one of those days triggers against 1000.00 and extends the same episode, even though the seven-day mean has reached 2400.00

#### Scenario: Intermittent spikes within tolerance
- **WHEN** a tracking episode was last seen on day 5 and the group triggers again on day 8 without triggering on days 6 and 7
- **THEN** the same episode continues with last seen day 8

#### Scenario: Tolerance exceeded
- **WHEN** a tracking episode was last seen on day 5 and days 6 to 9 are evaluated without a trigger
- **THEN** the episode becomes no_longer_observed on day 9 and its status is unchanged

#### Scenario: Return after the episode ended
- **WHEN** a group whose episode is no_longer_observed or closed triggers again
- **THEN** a new episode is opened referencing the previous one and the previous one is unchanged

#### Scenario: Closed while still high
- **WHEN** a tracking episode is closed while its group stays above the anchored reference
- **THEN** later days use the seven-day mean again, which may no longer trigger, and this limitation is documented

### Requirement: Accumulated impact and severity

Each episode SHALL store its accumulated impact: the sum, over every evaluated day while it was tracking from its start day, of max(0, observed - reference), each day counted once, together with the number of counted days and the last day included. Impact SHALL stop accumulating once the episode is no longer tracking. Severity SHALL be derived from the exact accumulated impact, before display rounding, in the episode currency: P1 when greater than 2000.00, P2 from 500.00 to 2000.00 inclusive, and P3 below 500.00. Impact and severity SHALL be shown in the episode currency only and SHALL never be summed or compared across currencies.

#### Scenario: Severity from accumulated impact
- **WHEN** a EUR episode with reference 1000.00 observes 2400.00 on its first two days
- **THEN** its accumulated impact is 2800.00 over two days and its severity is P1

#### Scenario: Single-day spike
- **WHEN** a single day exceeds its reference of 400.00 by 150.00 and the episode later becomes no_longer_observed with no other positive excess
- **THEN** its accumulated impact is 150.00 and its severity is P3

#### Scenario: Severity boundaries
- **WHEN** accumulated impact is exactly 500.00 or exactly 2000.00
- **THEN** severity is P2

#### Scenario: Severity uses the exact impact
- **WHEN** the exact accumulated impact is 499.996
- **THEN** it is displayed as 500.00 and its severity is P3

#### Scenario: Days below the reference
- **WHEN** a tracking day observes less than the reference
- **THEN** it adds 0.00 and does not reduce the accumulated impact

### Requirement: Traceable status

Episode status SHALL be one of new, investigating, resolved and false_positive. Allowed changes SHALL be new to investigating, and new or investigating to resolved or false_positive. Closing as resolved or false_positive SHALL require a reason of 1 to 500 characters after trimming, without Unicode control, format, private-use, surrogate, unassigned, line-separator or paragraph-separator characters, and with at least one visible letter, number, punctuation mark or symbol other than blank fillers; the reason SHALL be rejected for investigating. Any member of the active tenant SHALL be able to change status. Each change SHALL record who made it and when; the episode SHALL keep who made the first change out of new and when, and the closing time. A change that loses a concurrent race SHALL be reported as a concurrency conflict, distinct from an invalid transition. A closed episode SHALL NOT change status again. Concurrent conflicting changes SHALL result in exactly one success.

#### Scenario: Investigate then resolve
- **WHEN** a member sets investigating and later resolved with reason "Escalado revertido"
- **THEN** the episode stores both actors and times, its first review time is the investigating time and its closing time and reason are those of the resolution

#### Scenario: Missing closing reason
- **WHEN** resolved or false_positive is requested with no reason or only whitespace
- **THEN** the request is rejected with 422 and nothing changes

#### Scenario: Invisible or control characters in the reason
- **WHEN** the reason contains U+0085, U+202E, U+2028, U+2029, a soft hyphen or only a zero-width space, or only blank fillers such as U+3164 or U+2800 or isolated combining marks
- **THEN** the request is rejected with 422 and nothing changes

#### Scenario: Closed episode
- **WHEN** any status change is requested for a resolved or false_positive episode
- **THEN** the request is rejected with 409 and nothing changes

#### Scenario: Invalid transition
- **WHEN** new is requested for an investigating episode
- **THEN** the request is rejected with 409

### Requirement: Episode read API and tenant isolation

Authenticated members SHALL list the active tenant's episodes, open ones (new or investigating) by default and all on request, ordered by severity P1 to P3, then accumulated impact descending, then start day descending, then id. Each episode SHALL expose id, currency, service, start day, last seen day, observation and the day it stopped being observed, anchored reference, opening observed cost, accumulated impact with its counted days and last included day, severity, status with its traceability fields, previous episode id, rules version with its thresholds, cause_status not_established, the word candidate in its kind, and its limitations. Every read and write SHALL be scoped to the active tenant; a foreign or nonexistent episode id SHALL return the same 404 after authentication and membership checks. Listing SHALL only read stored episodes and SHALL never run a detection.

#### Scenario: Other tenant
- **WHEN** a member of tenant-core requests or changes an episode of tenant-growth by id
- **THEN** the response is the same 404 as for a nonexistent id and nothing changes

#### Scenario: Non-member
- **WHEN** a user requests episodes or a run for a tenant they do not belong to
- **THEN** access is denied before any cost or episode read

#### Scenario: Listing does not detect
- **WHEN** episodes are listed after new cost data arrived
- **THEN** stored episodes are returned unchanged and no run happens

#### Scenario: Several currencies
- **WHEN** a tenant has open EUR and USD episodes
- **THEN** each shows its impact in its own currency and no total across currencies is returned

### Requirement: Versioned rules and honest limitations

Each episode SHALL store the rules version and thresholds that opened it; runs SHALL only use the current business rules. Episodes SHALL be presented as candidates: the system SHALL NOT claim a cause, savings, statistical confidence or completeness of the cost data. Documented limitations SHALL include: a day may be evaluated before late data arrives; days older than the seven-day catch-up window between runs are not evaluated; new spend from a zero reference is not detected; weekly cycles may produce false candidates; a recent spike raises the seven-day mean; currencies other than EUR and USD are not evaluated; only the service dimension is watched.

#### Scenario: Rules recorded on the episode
- **WHEN** an episode is opened
- **THEN** it stores the rules version together with 20 %, 100.00, seven reference days, three tolerance days and the severity tiers

#### Scenario: Limitations exposed
- **WHEN** any episode is read
- **THEN** the response includes cause_status not_established and the limitations list
