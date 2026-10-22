## ADDED Requirements

### Requirement: Robustness indicators panel

The dashboard SHALL show the calculated robustness indicators of the latest JUP-071 run that has them in a table of their own, placed before the per-row robustness table in section A. The table SHALL list each indicator under the evaluation family it belongs to (core quality, retrieval, system performance, conversation and user), with a plain-language name, the value with its unit, its base (numerator and denominator when it is a proportion) and whether a person or a rule decides it, plus the date and the run type. It SHALL read the indicator groups of the run and SHALL NOT read the case counts of the per-row table. An indicator that was not measured SHALL read as not measured and never as zero. The per-row robustness table SHALL remain as the audit detail.

#### Scenario: A run with indicators
- **WHEN** the latest JUP-071 run has indicator rows
- **THEN** the panel lists them by family with their value, base and who decides them, and the run type states when the run has no verified model

#### Scenario: No run with indicators
- **WHEN** no JUP-071 run has indicator rows, as when only runs without indicator rows are loaded
- **THEN** the panel shows a no-data message that names JUP-071 and no zero or percentage

#### Scenario: Indicator without a measurement
- **WHEN** an indicator row is not measured
- **THEN** its value reads as not measured and its base keeps the denominator

#### Scenario: Audit detail kept
- **WHEN** the dashboard is read in section A
- **THEN** the per-row robustness table is still present after the indicators panel, with its columns and order unchanged
