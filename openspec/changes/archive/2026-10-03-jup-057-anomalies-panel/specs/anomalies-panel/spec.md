## ADDED Requirements

### Requirement: Explicit demonstration scope
The panel SHALL label its records and charts as test data with a fixed sample
period and SHALL NOT claim real-time detection or tenant-specific findings.

#### Scenario: Open the sample panel
- **WHEN** a user visits `/anomalies`
- **THEN** the panel identifies the data as demonstration data for 18–19 April 2026
- **AND** no sample is presented as a finding from the active tenant

### Requirement: Consistent summary
The panel SHALL derive open count, high-severity open count, open estimated EUR
impact and resolved count from the same records, clearly identifying summary scope.

#### Scenario: Initial fixture summary
- **WHEN** the five supplied sample records are displayed
- **THEN** the summary reports three open anomalies, two high-severity open anomalies,
  estimated open impact of EUR 30700 and two resolved anomalies
- **AND** the summary is identified as referring to the complete sample

### Requirement: Prioritized open anomalies
The panel SHALL initially show only Pending and Investigating records, with
severity and impact visible, ordered by severity descending then impact descending.

#### Scenario: Initial review queue
- **WHEN** the user opens the panel
- **THEN** resolved records are excluded from the initial list
- **AND** high-severity examples precede lower-severity examples
- **AND** the higher-impact record appears first within each severity

### Requirement: Combined filters and empty state
The user SHALL be able to combine status and severity filters and restore the
initial view when no records match. Controls SHALL be labelled and keyboard accessible.

#### Scenario: Combined filters
- **WHEN** the user selects resolved status and medium severity
- **THEN** only records matching both filters appear

#### Scenario: No matching records
- **WHEN** a filter combination matches no sample record
- **THEN** an explicit empty state and reset action appear
- **AND** resetting restores the initial open view and all severities

### Requirement: Matching export and responsive presentation
Exported data SHALL match filtered ordered rows and identify its demo provenance.
The panel SHALL remain usable on desktop and mobile, with local table scrolling
when necessary and textual severity labels independent of color.

#### Scenario: Filtered export
- **WHEN** the user exports a filtered list
- **THEN** the export contains only its current records in the same order
- **AND** identifies the output as demo data

#### Scenario: Empty export
- **WHEN** no rows match the current filters
- **THEN** exporting an empty report is unavailable

#### Scenario: Mobile review
- **WHEN** the panel is viewed at a 390 pixel viewport width
- **THEN** filters remain operable and any wide table scrolls within its own region
- **AND** severity is communicated by readable text
