# anomalies-panel Specification

## Purpose
Define the `/anomalies` panel that shows the active tenant's stored cost-anomaly episodes: a summary of open impact per currency, a prioritized queue with combined filters, detection on demand with an inline result, an episode detail with status actions, a warning when the data is synthetic and a safe CSV/PDF export. The panel only reads and changes what the backend returns and never invents a cause.
## Requirements
### Requirement: Combined filters and empty state
The user SHALL be able to combine severity (all, Alta (P1), Media (P2), Baja (P3)), status (open by default, Nueva, Investigando, Resuelta, Falso positivo, all) and observation (all, still observed, no longer observed) filters and restore the initial view when no episode matches. Controls SHALL be labelled and keyboard accessible. The panel SHALL distinguish: a tenant where detection never ran (a message and a prominent detection button, without zero summary figures), a tenant with no open episodes (a message with the last evaluated day), loading (a skeleton without figures), a load error (a message with retry and no stale figures) and filters without matches (the existing message and reset action). Changing the active tenant SHALL clear the panel before the new tenant's data load.

#### Scenario: Combined filters
- **WHEN** the user selects status Resuelta and severity Media (P2)
- **THEN** only episodes matching both filters appear

#### Scenario: No matching records
- **WHEN** a filter combination matches no episode
- **THEN** an explicit empty state and reset action appear
- **AND** resetting restores the initial open view, all severities and all observations

#### Scenario: Never detected
- **WHEN** the tenant has no last evaluated day
- **THEN** the panel says anomalies were never searched for this tenant, shows the detection button and shows no summary figures

#### Scenario: Detected without open episodes
- **WHEN** the tenant has a last evaluated day and no open episode
- **THEN** the panel says there are no open anomalies and shows the last evaluated day

#### Scenario: Load error
- **WHEN** listing episodes fails
- **THEN** the panel shows an error message with a retry action and no figures from a previous load

#### Scenario: Tenant switch
- **WHEN** the active tenant changes
- **THEN** no episode of the previous tenant is visible at any moment while the new list loads

### Requirement: Matching export and responsive presentation
Exported CSV and PDF data SHALL match the filtered ordered rows. Each row SHALL contain the tenant, the data origin ("Sintéticos" when the tenant data include synthetic data, otherwise "Ingesta de costes"), the severity label, service, currency, accumulated impact as a number, counted days, start day, last seen day, observation, status, closing reason, last evaluated day, rules version and the text "Candidata: causa no establecida". Amounts SHALL never be summed across currencies. The file name SHALL include the tenant and the last evaluated day. The panel SHALL remain usable at 390 pixels wide, with local table scrolling, a full-screen detail on small screens and textual labels independent of color.

#### Scenario: Filtered export
- **WHEN** the user exports a filtered list
- **THEN** the export contains only its current rows in the same order with the columns above

#### Scenario: Empty export
- **WHEN** no rows match the current filters
- **THEN** exporting is unavailable

#### Scenario: Mobile review
- **WHEN** the panel is viewed at a 390 pixel viewport width
- **THEN** filters and the detection button remain operable, the table scrolls within its own region and the detail covers the screen

### Requirement: Detection on demand with an inline result
The panel SHALL offer a "Detectar ahora" action that calls the detection run for the active tenant, is disabled and labelled "Detectando…" while it runs, and then reports the outcome in an inline status message that remains visible until the next action and is announced to assistive technology. A completed run SHALL show the last evaluated day, the number of evaluated days and the opened, continued and no-longer-observed counts in the main line, any unsupported currency as a warning in the main line and the evaluated and skipped days with their reasons in a collapsed detail. The panel SHALL show distinct messages for up to date, insufficient data, ambiguous cost source and a concurrent detection. After a run the list and summary SHALL reload and newly opened episodes SHALL be highlighted. The panel SHALL always show the last evaluated day of the tenant ("Revisado hasta …") when there is one.

#### Scenario: Completed run with the demonstration data
- **WHEN** the user presses the action on the demonstration tenant for the first time
- **THEN** the message reports detection up to 2026-09-20 with 3 new anomalies, and the list shows them

#### Scenario: Double press
- **WHEN** the user presses the action twice quickly
- **THEN** only one request is sent while the first is running

#### Scenario: Up to date
- **WHEN** the action is pressed again without new cost data
- **THEN** the message says the tenant was already up to date to its last evaluated day and the list does not change

#### Scenario: Error outcomes
- **WHEN** the run answers insufficient data, 409 ambiguous_cost_source or 409 detection_conflict
- **THEN** the message explains each case in its own words and states that nothing was stored for the two conflicts

### Requirement: Episode detail with status actions
Each episode SHALL open a detail view showing severity, status, observation, reference daily cost, opening day and observed cost, accumulated impact with counted days and last included day, start and last seen days, previous episode when any, rules version, the statement that it is a candidate without established cause, its limitations and its traceability (who and when changed the status, first review and closing time and reason). From the detail the user SHALL be able to mark a new episode as investigating and to close a new or investigating episode as resolved or false positive. Closing SHALL require a reason, SHALL warn that it cannot be undone and SHALL require an explicit confirmation. Errors from the backend (invalid reason, invalid transition, concurrency conflict, not found) SHALL be shown in the detail without changing the displayed status. After a change the list and summary SHALL reload.

#### Scenario: Investigate then close
- **WHEN** the user marks Compute as investigating and later closes it as false positive with a reason
- **THEN** the detail shows the new status, who changed it and when, and the closing reason
- **AND** the list and summary reflect the change

#### Scenario: Closing requires reason and confirmation
- **WHEN** the user tries to close without a reason or cancels the confirmation
- **THEN** no request is sent and the status does not change

#### Scenario: Closed episode
- **WHEN** a resolved or false positive episode is opened
- **THEN** no status action is offered

#### Scenario: Conflict from the backend
- **WHEN** the backend answers 409 status_change_conflict or invalid_status_transition
- **THEN** the detail explains it and offers to reload the episode

### Requirement: Synthetic data warning
When the backend reports that the active tenant's cost data include synthetic data, the panel SHALL show a fixed warning "Datos sintéticos de demostración: no son facturas reales" above the summary. Otherwise it SHALL show no provenance warning and SHALL NOT call the data real.

#### Scenario: Demonstration tenant
- **WHEN** the demonstration dataset is loaded in the active tenant
- **THEN** the warning is visible above the summary

#### Scenario: Ingested data
- **WHEN** the tenant data come only from cost ingestion without the synthetic mark
- **THEN** no provenance warning is shown and no text calls the data real

### Requirement: Open-episode summary
The panel SHALL derive its summary from all stored episodes of the active tenant, independently of the filters, and SHALL state that scope. The summary SHALL show the accumulated impact of open episodes (status new or investigating) as one line per currency, using the exact totals returned by the backend and never summing amounts in the browser or across currencies; the number of open episodes; the number of open episodes with severity P1; and the number of open episodes that are no longer observed. Selecting the no-longer-observed figure SHALL filter the table to those episodes. Closed episodes SHALL NOT appear in the summary.

#### Scenario: Summary of the demonstration data
- **WHEN** the demonstration dataset has been detected and no status was changed
- **THEN** the summary shows 3619.43 EUR of open accumulated impact, 3 open episodes, 1 open P1 episode and 1 open episode no longer observed

#### Scenario: Several currencies
- **WHEN** a tenant has open EUR and USD episodes
- **THEN** the impact figure shows one line per currency and no combined total

#### Scenario: Summary ignores filters
- **WHEN** the user filters the table by severity Baja (P3)
- **THEN** the summary figures do not change

#### Scenario: No-longer-observed shortcut
- **WHEN** the user selects the no-longer-observed figure
- **THEN** the table shows only open episodes that are no longer observed and the observation filter reflects it

### Requirement: Prioritized episode queue
The panel SHALL initially show only open episodes, ordered as the backend returns them (severity P1 to P3, then accumulated impact descending, then most recent start). Each row SHALL show severity as text "Alta (P1)", "Media (P2)" or "Baja (P3)", the service with the excess of its opening day over its reference, the accumulated impact in its currency with the number of counted days, the period from start to last seen day with whether it is still observed, the status as "Nueva", "Investigando", "Resuelta" or "Falso positivo", and an action to open its detail. The panel SHALL NOT show invented types, descriptions or causes. A legend next to the severity filter SHALL state the thresholds: more than 2000, from 500 to 2000, and less than 500 of accumulated impact.

#### Scenario: Initial review queue with the demonstration data
- **WHEN** the user opens the panel after detecting the demonstration dataset
- **THEN** the rows are Compute "Alta (P1)" 2807.71 EUR in 12 days, Database "Media (P2)" 642.86 EUR in 5 days and Analytics "Baja (P3)" 168.86 EUR in 4 days, in that order
- **AND** Analytics shows that it is no longer observed since 2026-09-14

#### Scenario: Severity legend
- **WHEN** the severity filter is shown
- **THEN** its legend states the accumulated-impact threshold of each level

#### Scenario: No invented explanation
- **WHEN** any row is rendered
- **THEN** it contains no type, description or cause text that the backend did not return
