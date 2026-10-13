## MODIFIED Requirements

### Requirement: Detection run on demand is bounded and idempotent

An authenticated member of the active tenant SHALL be able to request a detection run. Identity, tenant selector and membership SHALL be checked before rejecting a request body. A run SHALL evaluate, in ascending date order, every day after the tenant's last evaluated day up to the last complete day; on the first run, every day from the earliest observed tenant day up to the last complete day. Days are bounded by the stored cost history, not by a fixed count. After a successful run the last evaluated day SHALL be the last complete day. A run SHALL be atomic: on any failure, including an ambiguous cost source, nothing SHALL be stored. Repeating a run with no new complete day SHALL change nothing and report up_to_date. Concurrent runs for the same tenant SHALL NOT duplicate episodes; a run that loses the race SHALL return a conflict and store nothing. The run SHALL only read cost data and never use rules supplied in the request.

#### Scenario: First run
- **WHEN** the first run happens on a tenant whose cost history starts on 2026-09-01 and whose last complete day is 2026-09-20
- **THEN** every day from 2026-09-01 to 2026-09-20 is considered in order, days without seven previous observed days are skipped as reference_incomplete, and the response lists evaluated and skipped days and the opened, continued and no-longer-observed counts

#### Scenario: Repeated press
- **WHEN** the run is requested twice without new cost data
- **THEN** the second response is up_to_date and stored episodes are identical

#### Scenario: Days missed between runs
- **WHEN** the previous run evaluated up to 2026-09-01 and the last complete day is now 2026-09-20
- **THEN** every day from 2026-09-02 to 2026-09-20 is evaluated and no day is left unevaluated

#### Scenario: Same result in one press or several
- **WHEN** the same cost history is evaluated with one run, or with one run per new complete day
- **THEN** the stored episodes, impacts, severities and observations are identical

#### Scenario: Ambiguous source
- **WHEN** billing detects overlapping cost sources in the read range
- **THEN** the run returns 409 with ambiguous_cost_source and stores neither episodes nor the last evaluated day

#### Scenario: Concurrent runs
- **WHEN** two runs for the same tenant are requested at the same time
- **THEN** stored episodes equal those of a single run and at most one run reports success

### Requirement: Episode read API and tenant isolation

Authenticated members SHALL list the active tenant's episodes, open ones (new or investigating) by default and all on request, ordered by severity P1 to P3, then accumulated impact descending, then start day descending, then id. Each episode SHALL expose id, currency, service, start day, last seen day, observation and the day it stopped being observed, anchored reference, opening observed cost, accumulated impact with its counted days and last included day, severity, status with its traceability fields, previous episode id, rules version with its thresholds, cause_status not_established, the word candidate in its kind, and its limitations. The list SHALL also return, independently of the requested scope, the tenant's last evaluated day (null when detection never ran), whether any completed cost ingestion of the tenant carries the synthetic mark, and the exact accumulated impact of open episodes per currency, rounded only for display and never summed across currencies. Every read and write SHALL be scoped to the active tenant; a foreign or nonexistent episode id SHALL return the same 404 after authentication and membership checks. Listing SHALL only read stored episodes and SHALL never run a detection.

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
- **THEN** each shows its impact in its own currency, and the open impact totals contain one entry per currency and no combined total

#### Scenario: Exact open totals
- **WHEN** three open EUR episodes have exact impacts whose rounded values would add up to a different cent
- **THEN** the EUR open total is the exact sum rounded once

#### Scenario: Never detected and synthetic mark
- **WHEN** a tenant has only synthetic-marked ingestions and no detection ran
- **THEN** the list returns no episodes, a null last evaluated day and the synthetic indicator set
- **AND** a tenant with only unmarked ingestions returns the indicator unset, and a tenant with both returns it set

#### Scenario: Synthetic indicator is tenant-scoped
- **WHEN** another tenant has synthetic-marked ingestions and the active tenant has none
- **THEN** the active tenant's indicator is unset
