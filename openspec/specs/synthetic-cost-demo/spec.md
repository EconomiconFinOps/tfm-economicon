# synthetic-cost-demo Specification

## Purpose

Provide a short, rehearsable and reproducible demo of the cost features on the synthetic cost data of JUP-106, so that the team can show several months, two currencies, gaps, zeros and credits to an evaluation panel and answer questions with facts, without presenting the data as real.

## Requirements

### Requirement: Visible synthetic provenance and honest limits

The demo SHALL state, before the first figure is shown, that every amount comes from synthetic datasets (JUP-106 for the cost route and JUP-107 for the anomalies step) and not from Azure or from the public dataset. The guide and the supporting material SHALL carry the same statement. The demo SHALL name which application screens do not read these data (the screens fed by fixed frontend data) and SHALL NOT use them to illustrate any step. The anomalies panel SHALL only be used in the anomalies step, with the JUP-107 anomaly dataset loaded in `tenant-core`, and its synthetic data warning SHALL be visible.

#### Scenario: Declaration precedes the figures
- **WHEN** the guide is read from its first step
- **THEN** the first step that shows an amount comes after a step whose spoken text says the data are synthetic
- **AND** the preparation guide and the question table repeat that statement

#### Scenario: Screens that do not read the data are not used
- **WHEN** the steps of the guide are listed with the screen each one uses
- **THEN** every step that shows a cost figure uses the screen fed by the billing summary, except the anomalies step, which uses the panel fed by stored episodes
- **AND** the screens fed by fixed frontend data appear only in the statement of limits, never as evidence of a result

#### Scenario: Anomalies step shows its provenance
- **WHEN** the anomalies step is followed
- **THEN** the panel shows the synthetic data warning and the Compute episode "Alta (P1)" first

### Requirement: Timed route with expected result per step

The guide SHALL define a route of identified steps with the action, the text to say, the expected result and a duration in seconds. The main route SHALL include, right after the isolation step, an anomalies step that switches to `tenant-core`, presses the detection action, shows the last evaluated day and the first episode and opens its detail. The tag breakdown step SHALL be optional. The total of the main steps SHALL be declared, SHALL be 180 seconds, and with every optional step SHALL NOT exceed four minutes. Each step SHALL have a stable identifier that the question table can reference.

#### Scenario: Complete steps
- **WHEN** the machine-readable list of steps is read
- **THEN** every step has an identifier, an action, a spoken text, an expected result and a duration
- **AND** identifiers are unique

#### Scenario: Declared total matches the steps
- **WHEN** the durations of the main steps are added
- **THEN** the sum equals the total stated in the guide, 180 seconds
- **AND** the sum plus the durations of every optional step does not exceed 240 seconds

#### Scenario: Anomalies step follows isolation
- **WHEN** the steps are read in order
- **THEN** the anomalies step comes immediately after the isolation step and the tag breakdown step is marked optional

### Requirement: Period that keeps the figures readable

The main route SHALL use periods that end before the month whose amount exceeds the safe integer range of JavaScript numbers, so that the chart of the other months stays legible. The case of the very large amount SHALL be a separate optional step that states what it demonstrates and is shown in the exact-value table.

#### Scenario: Main route excludes the very large month
- **WHEN** the periods of the main steps are read
- **THEN** none of them includes the month with the very large amount
- **AND** the optional step is identified as optional and names that month

### Requirement: Expected values verified independently

Every figure in the route (monthly totals per currency, the month with no data, the recorded zero, the credit, the comparisons between months, the grouped totals and the excluded undated record) SHALL be listed in a machine-readable file and SHALL equal an exact decimal computation over the records of the synthetic dataset. No expected value SHALL be produced by the loader's own aggregation code or by the application.

#### Scenario: Values match an exact computation
- **WHEN** the expected values are compared with the sums computed from the dataset records using exact decimal arithmetic
- **THEN** every expected value equals the computed value
- **AND** a changed amount, month or currency in the dataset makes the comparison fail

#### Scenario: Comparisons follow the documented rule
- **WHEN** the comparison for a currency is computed from its first and last months with a non-zero cost inside the period
- **THEN** the difference and the percentage equal the figures in the file and in the guide of JUP-106
- **AND** a month with a recorded zero is not used as an endpoint

#### Scenario: A drifted guide is detected
- **WHEN** a figure in the expected-values file is altered
- **THEN** the verification fails and names the figure

### Requirement: Preparation and return to the initial state

The preparation guide SHALL start from an isolated stack with its own volumes where the demo tenants have no cost data, SHALL load the JUP-106 data in `tenant-growth` with the JUP-106 tool and the JUP-107 anomaly data in `tenant-core` with its tool, SHALL confirm the loaded state and the expected summary before the route, SHALL NOT run a detection before the route, and SHALL end with the removal of both synthetic datasets and the confirmation that both tenants are empty again, without episodes or detection state. It SHALL NOT use the stack of another task and SHALL state that the JUP-065 demo requires the same tenant to be empty.

#### Scenario: Preparation confirms the loaded state
- **WHEN** the preparation steps are followed on a fresh isolated stack
- **THEN** both tools report their datasets present and the billing summary for the main period equals the expected values
- **AND** the anomalies panel of `tenant-core` shows the never-detected state
- **AND** the loading is refused by the tools, not worked around, if a tenant already has data that are not synthetic

#### Scenario: Return to the initial state
- **WHEN** the final steps are followed
- **THEN** each removal reports its synthetic rows removed and a second removal reports nothing to remove
- **AND** the billing summaries of both tenants are empty and `tenant-core` has no episodes

### Requirement: Question table covers the route

The guide SHALL include a table of questions that an evaluation panel can ask (several currencies, a gap compared with a recorded zero, a credit, very large amounts, isolation between clients, tags, how anomalies are detected and prioritised, why a rise does not open an anomaly, and whether an anomaly states its cause) and, for each, the identifier of the step that answers it and the one-line answer.

#### Scenario: Every question points to a real step
- **WHEN** the question table is read
- **THEN** every question names an existing step identifier
- **AND** no question is answered with a screen that does not read the data

#### Scenario: Anomaly questions
- **WHEN** the anomaly questions are read
- **THEN** they point to the anomalies step and answer with the daily rule, the severity from accumulated impact and the candidate status without established cause

### Requirement: Rehearsal record without unearned claims

The package SHALL include a rehearsal record template with the person, the commit, the mode (automated browser run or human rehearsal), the result of each step (pass, fail, blocked or not run), the duration and the observations. The package SHALL NOT state that a human rehearsal took place unless a record of it exists, and an automated run SHALL be recorded as such.

#### Scenario: Automated run is labelled
- **WHEN** the evidence of an automated browser run is read
- **THEN** it states the commit, the date, that it was automated and which steps it checked
- **AND** it makes no claim about timing with a human presenter

#### Scenario: No rehearsal claimed without a record
- **WHEN** the package and its evidence are read
- **THEN** every statement that someone rehearsed the demo points to a filled record

### Requirement: No secrets, binaries or interference with other work

The package SHALL NOT contain secrets, credentials, captures, recordings or other binaries, and the browser recipe SHALL run outside the repository, SHALL NOT intercept or fake requests, and SHALL fail on a page error, a cross-origin error or a step that does not hold. The change SHALL leave the JUP-106 tool, the public dataset, the application code and the JUP-065 demo package byte-identical.

#### Scenario: Repository hygiene
- **WHEN** the repository hygiene check runs on the change
- **THEN** it passes and the change contains no image, video or executable binary

#### Scenario: Existing work untouched
- **WHEN** the files of the JUP-106 tool, the public dataset, `apps/` and the JUP-065 package are compared with the base
- **THEN** they are identical
