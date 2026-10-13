# demo-reference-date Specification

## Purpose
TBD - created by archiving change jup-119-coherent-cost-data-reference-date. Update Purpose after archive.
## Requirements
### Requirement: One configurable reference date decides what "today" is

The backend SHALL resolve a single reference date from the setting `COST_REFERENCE_DATE`. When the setting is absent or empty the reference date SHALL be the current UTC date; when it holds a calendar date `YYYY-MM-DD` it SHALL be that date; any other value (a datetime, a date with spaces, a non-existent day such as `2026-02-30`, a two-digit year, or a date earlier than 1900-01-02 or later than 9998-12-29, whose neighbouring days the date type cannot represent) SHALL stop the backend at startup with a message that names the setting and does not print the value of any other setting. The reference date SHALL be read through one service, and no billing, anomaly or ownership code SHALL read the system clock to decide which days are visible.

#### Scenario: Default is the real UTC day
- **WHEN** the setting is absent and the clock reads 2026-10-13T23:59:59Z
- **THEN** the reference date is 2026-10-13
- **AND** one second later it is 2026-10-14 without restarting the backend

#### Scenario: Fixed date
- **WHEN** the setting is `2026-09-21`
- **THEN** the reference date is 2026-09-21 whatever the clock says, and it is not flagged as the real day

#### Scenario: Invalid value is rejected at startup
- **WHEN** the setting is `2026-09-21T00:00:00Z`, ` 2026-09-21`, `2026-02-30` or `26-09-21`
- **THEN** the backend does not start and the message names the setting (`cost_reference_date`)
- **AND** no cost, episode or conversation row has been read or written

#### Scenario: Dates at the edge of the date type are rejected
- **WHEN** the setting is `9999-12-31`, `9999-12-30`, `0001-01-01` or `1900-01-01`
- **THEN** the backend does not start and the message names the setting (`cost_reference_date`)
- **AND** `1900-01-02` and `9998-12-29` are accepted and every read works with them

#### Scenario: No other code decides the visible day
- **WHEN** the code of the billing routes, the anomaly services, the ownership question service and the anomaly request schema is searched for `datetime.now`, `date.today` and `utcnow`
- **THEN** none appears in the paths that choose a period, a "today" or a last complete day, and a test fails if one is added

### Requirement: Costs after the reference date are never read

Every read of stored costs for a tenant (billing summary, tag coverage, budget evaluation, the anomaly test query, the daily series of the detection and the ownership question) SHALL exclude records whose usage date is later than the reference date, and the effective end of any requested period SHALL be the earlier of its end and the day after the reference date. Records without a usage date SHALL keep their present treatment (counted and reported as excluded undated), because they are not later than any day. A request whose whole period lies after the reference date SHALL answer as a period with no data, not with an error and not with a hint of the hidden amounts.

#### Scenario: Summary stops at the reference date
- **WHEN** records exist for every day of September and October 2026, the reference date is 2026-10-15 and the summary is requested for 2026-10-01 to 2026-11-01
- **THEN** the totals contain only 2026-10-01 to 2026-10-15 inclusive
- **AND** the reported last usage date is 2026-10-15 and the observed days are 15

#### Scenario: Period entirely in the future
- **WHEN** the reference date is 2026-09-21 and the summary is requested for 2026-10-01 to 2026-11-01
- **THEN** the response is the no-data response of an empty period
- **AND** no amount, count or date of October appears in the body, in a log line or in an error

#### Scenario: Reference day is included, the next day is not
- **WHEN** records exist on 2026-09-21 and 2026-09-22 and the reference date is 2026-09-21
- **THEN** the day 2026-09-21 is counted and 2026-09-22 is not

#### Scenario: Every cost read obeys the limit
- **WHEN** the same data and reference date are used to call the summary, the tag coverage, the budget evaluation, the anomaly test query, the detection and the ownership question over a period that reaches beyond the reference date
- **THEN** none of the seven results includes a record later than the reference date

#### Scenario: Undated records keep their treatment
- **WHEN** a tenant has one record without a usage date and the reference date is any date
- **THEN** the summary still reports one excluded undated record and does not count its amount in a period

#### Scenario: Ambiguous source rule still applies
- **WHEN** two completed ingestions overlap on a day not later than the reference date
- **THEN** the request is refused with the existing `ambiguous_cost_source` conflict
- **AND** two ingestions that overlap only on days later than the reference date do not refuse the request

### Requirement: Default periods and anomaly validity follow the reference date

When a request names no period, the default period SHALL be the calendar month that contains the reference date, ending (exclusive) at the first day of the next month, with the data cut at the reference date. The anomaly test query SHALL accept only closed days up to the reference date: an end date after the reference date SHALL be rejected with the existing validation error. The daily detection SHALL treat the reference date as its "today", so the last complete day is the day before the earlier of the reference date and the latest day with visible data (ADR-0020), and it SHALL NOT evaluate days that are not complete at that point.

#### Scenario: Default month
- **WHEN** the reference date is 2026-10-15 and the summary is requested without a period
- **THEN** the period is 2026-10-01 to 2026-11-01 with data up to 2026-10-15
- **AND** with the reference date 2026-09-21 the period is 2026-09-01 to 2026-10-01

#### Scenario: Test query rejects a future end
- **WHEN** the reference date is 2026-09-21 and the test query ends on 2026-09-22
- **THEN** it answers the existing validation error for "closed UTC days", because the reference day is not closed
- **AND** an end on 2026-09-21 (exclusive end, last day 2026-09-20) is accepted

#### Scenario: Detection at the original reference date reproduces JUP-107
- **WHEN** the demo dataset is loaded with data until 2026-10-30 and one detection runs on an empty detection state with the reference date 2026-09-21
- **THEN** exactly the three episodes of the JUP-107 expected file are stored with the same figures and the last evaluated day is 2026-09-20

#### Scenario: Advancing the date brings new days
- **WHEN** a detection ran with the reference date 2026-09-21 and the reference date is then set to 2026-10-15 and the detection runs again
- **THEN** the days from 2026-09-21 to 2026-10-14 are evaluated and the episodes of the extension appear with their documented figures
- **AND** the episodes opened before are the same ones, not duplicated

### Requirement: Stored episodes obey the reference date

The list and the detail of stored anomaly episodes SHALL NOT expose an episode whose opening day, or any day of its accumulated impact, is later than the reference date as it is at the time of the request. An episode SHALL be visible only when the last day of its accumulated impact (`impact_through_date`) and, if it ended, the day it stopped being observed (`no_longer_observed_on`) are both earlier than the reference date; otherwise it SHALL be hidden, never reported as it would have been, so it never shows impact for days that have not happened yet. The last evaluated day shown with the list SHALL NOT be later than the day before the reference date. The status change of a hidden episode SHALL answer the same not-found response as an unknown identifier.

#### Scenario: Moving the date backwards hides the future
- **WHEN** an episode opened on 2026-10-10 exists and the reference date is changed to 2026-09-21
- **THEN** the list does not contain it and reading it answers 404 with the same body as an unknown identifier
- **AND** with the reference date back at 2026-10-15 it is listed again unchanged

#### Scenario: Episode that spans the reference date
- **WHEN** an episode opened on 2026-09-09 and was last seen on 2026-10-05, and the reference date is 2026-09-30
- **THEN** the episode is hidden, because its impact reaches days after the reference date
- **AND** the day on which the reference date is one day after the last day of its impact makes it visible again

### Requirement: The frontend reads the reference date from the backend

The backend SHALL expose the reference date to the authenticated frontend as `{ "reference_date": "YYYY-MM-DD", "simulated": boolean }`, where `simulated` is true exactly when `COST_REFERENCE_DATE` is set. The endpoint SHALL answer with the same tenant-independent value for every authenticated user and SHALL NOT expose any other setting. The frontend SHALL compute the default period of the executive dashboard (the six complete months before the month that contains the reference date, as before this change), the reference month shown by the assistant composer and every "today" it computes from that value instead of the browser clock, and SHALL show the visible label "Fecha simulada" with the date in the page header when `simulated` is true and no label when it is false. If the endpoint fails, the frontend SHALL show an explicit error state for the period selection and SHALL NOT silently fall back to the browser clock.

#### Scenario: Simulated date is visible
- **WHEN** `COST_REFERENCE_DATE` is `2026-10-15` and a user opens the dashboard
- **THEN** the header shows "Fecha simulada: 15/10/2026" and the dashboard opens on the six complete months before October 2026, from April to September 2026

#### Scenario: Real date shows no label
- **WHEN** the setting is absent
- **THEN** the endpoint answers `simulated: false` and the header shows no simulated-date label

#### Scenario: Browser clock is not used
- **WHEN** the browser clock says 2030-01-01 and the reference date is 2026-10-15
- **THEN** the dashboard period (April to September 2026), the composer reference month (October 2026) and the header date are those of 2026-10-15

#### Scenario: Endpoint failure is explicit
- **WHEN** the reference date endpoint answers an error
- **THEN** the period selection shows an error state and no request for costs is sent with a period computed from the browser clock

#### Scenario: Unauthenticated access
- **WHEN** the endpoint is called without a session
- **THEN** it answers the existing authentication error and returns no date

### Requirement: The assistant answers only about visible days

The cost answers of the assistant that read stored costs (the ownership question and any tool of the finops contract that reads billing) SHALL use the reference date for their default period and SHALL include in the answer the period and the reference date they used. An answer SHALL NOT quote an amount, a day or an anomaly later than the reference date, and the retrieval corpus SHALL be unchanged by this requirement.

#### Scenario: Ownership answer at an early date
- **WHEN** the reference date is 2026-09-21 and the ownership question runs without a period
- **THEN** the answer covers 2026-09-01 to 2026-09-21 inclusive and states the reference date
- **AND** it contains no amount from October

#### Scenario: Question about a future month
- **WHEN** the reference date is 2026-09-21 and the question asks for October 2026
- **THEN** the answer reports no data for the period and does not say that data exist later

