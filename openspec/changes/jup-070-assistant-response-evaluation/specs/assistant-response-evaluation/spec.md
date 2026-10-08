## Purpose

Measure the answers of the assistant chat against the reference of the JUP-069 question bank, deciding by rule what can be checked objectively and by people what needs judgement, and turn the result into the results file of JUP-067 and an acceptance verdict, so that the team can state with evidence how well the chat answers and whether it invents.

## ADDED Requirements

### Requirement: Faithful collection of the chat answers

The collection step SHALL send, for each case of the bank, exactly the prompt produced by the JUP-069 preparation step, in a new conversation, to the chat API of a stack that is already running, and SHALL record per case the text of the answer, its citations, the retrieved fragments with their distances, the HTTP status and the total duration. It SHALL NOT send the expected answers, the rubric or any hint, SHALL read the demo password only from the environment and SHALL NOT print or store it. A case that cannot be answered because of an infrastructure error SHALL be recorded as blocked with the failure category, never as an incorrect answer.

#### Scenario: Exact prompt in a new conversation
- **WHEN** the collection runs against a stack
- **THEN** every case uses its own new conversation and the message sent equals the prepared prompt byte for byte
- **AND** nothing from the `expected` section of the bank is sent

#### Scenario: Infrastructure failure is not a wrong answer
- **WHEN** the chat answers a case with a server error, a timeout or no connection
- **THEN** the case is recorded with its failure category and is blocked in the results
- **AND** it is not counted as a pass or as a fail

#### Scenario: No secrets in the raw file
- **WHEN** the raw run file is read
- **THEN** it holds no password, token or authorization header

### Requirement: Objective figures decided by rule

For every expected figure of a case, the evaluation SHALL decide by rule whether the answer contains a figure equal to the expected value within the stated absolute tolerance, with the stated unit and associated with the expected label or one of its declared aliases in the same sentence. A figure that appears without the unit, with another unit, far from its label, or outside the tolerance SHALL NOT satisfy the check. The parsing SHALL accept both decimal conventions (`1.000,50` and `1,000.50`), the percent sign and the word forms of the unit, and SHALL NOT accept a number that is part of a longer number.

#### Scenario: Correct figure with the right label and unit
- **WHEN** the answer states the expected total with its unit next to its label
- **THEN** the figure check passes

#### Scenario: Tolerance and units are respected
- **WHEN** an answer gives 10,1 % where 10 % with an absolute tolerance of 0,01 points is expected, or the right number with a different currency
- **THEN** the figure check fails

#### Scenario: Number inside another number
- **WHEN** the expected value is 90 and the answer contains 190 or 90,5
- **THEN** the figure check fails

#### Scenario: Right number, wrong label
- **WHEN** the expected number appears only next to an unrelated label
- **THEN** the figure check fails

### Requirement: Prohibited behaviours decided by rule

Every prohibited behaviour of a case SHALL have an explicit detection rule in the versioned rules file: a pattern over the normalized text of the answer, a prohibited figure, or the presence of an amount that does not appear in the prompt. A case SHALL fail the corresponding check when its rule matches and pass when it does not. The rules file SHALL cover every prohibited behaviour of the bank, and the evaluation SHALL refuse to run if one is missing.

#### Scenario: Rule matches a prohibited behaviour
- **WHEN** the answer presents the synthetic amounts as a real Azure invoice
- **THEN** the corresponding check fails

#### Scenario: Invented amount in an abstain case
- **WHEN** the answer to a case that must abstain states an amount that is not in the prompt
- **THEN** the check that forbids inventing amounts fails

#### Scenario: Missing rule
- **WHEN** a prohibited behaviour of the bank has no rule in the rules file
- **THEN** the evaluation stops with an error that names the case and the item

### Requirement: Human judgement of the required points

The required points SHALL be judged by people. The evaluation SHALL generate a review sheet with, per case, the expected behaviour, the required and prohibited points, the original answer, the citations and the retrieved fragments, and SHALL read a judgements file with a pass or fail per required point and the reviewer. For the critical cases, the ones with expected figures, two different reviewers SHALL be required, unless the run is explicitly declared provisional, in which case one reviewer is accepted, the measurement is marked provisional and those cases are listed. A prohibited behaviour that a reviewer observes and the rule missed SHALL be recorded as a failing required point with a note. A case with a missing judgement SHALL NOT be scored.

#### Scenario: Critical cases need two reviewers
- **WHEN** a critical case has a judgement from only one reviewer or from the same reviewer twice and the run is not declared provisional
- **THEN** the case is reported as not run with the reason and is not counted as a pass or a fail

#### Scenario: Provisional measurement with one reviewer
- **WHEN** the run is declared provisional and a critical case has one reviewer
- **THEN** the case is scored, the measurement is marked provisional and the case is listed as having a single decider

#### Scenario: Disagreement is not hidden
- **WHEN** two reviewers disagree on a required point
- **THEN** the point counts as failed and the case is listed in the report as a disagreement for resolution

#### Scenario: Missing judgement
- **WHEN** a case has required points without any judgement
- **THEN** it is not scored and is counted as not run

### Requirement: Case outcome and traceability of figures

A case SHALL pass only if every objective check passed and every required point was judged as passed. The evaluation SHALL classify every figure that the answer states as traceable to the question, to the context of the prompt, to a retrieved fragment, or as untraceable. In a critical case an untraceable figure SHALL prevent a pass. The behaviour expected of the case (answer, clarify or abstain) SHALL be reported with each result so that the groups are measured separately.

#### Scenario: Untraceable figure in a critical case
- **WHEN** a critical case states an amount that is in neither the prompt nor the retrieved fragments
- **THEN** the case cannot pass, whatever the other checks say

#### Scenario: Pass requires every criterion
- **WHEN** one required point fails or one figure check fails
- **THEN** the case does not pass

### Requirement: Results in the format of the metrics

The evaluation SHALL write a results file in the version of the format accepted by the reference calculator of JUP-067, without modifying it, containing the run header (commit, date, bank version and hash, corpus, provider, generation settings and availability) and one entry per case. The file SHALL NOT contain the text of any question, answer or fragment, nor credentials. The calculator SHALL accept the file and produce its report.

#### Scenario: Calculator accepts the file
- **WHEN** the results file is given to the reference calculator
- **THEN** it validates and computes the report with no change to the calculator

#### Scenario: No text and no secrets in the results
- **WHEN** the results file is inspected
- **THEN** it holds no answer text, question text, fragment text, password or token

### Requirement: Acceptance verdict with explicit thresholds

The evaluation SHALL compare the measured run with the thresholds of the versioned rules file and SHALL report an acceptance verdict with the reason of each unmet threshold. The thresholds SHALL start from the provisional targets of ADR-0002 (objective checks at 90 %, no untraceable figure in the critical cases, 95 % of answers that comply with the schema and a 95th percentile of the total latency of 10 seconds in development) and SHALL be reported together with the confidence interval and the sample size. A required threshold that cannot be computed SHALL be reported as not available, never as met, and SHALL prevent an accepted verdict; a threshold that is declared not required for the kind of chat measured SHALL be reported as not applicable.

#### Scenario: Unmet threshold
- **WHEN** fewer than 90 % of the objective checks pass
- **THEN** the verdict is not accepted and names that threshold

#### Scenario: Not computable is not met
- **WHEN** the run has too few observations for a required threshold
- **THEN** that threshold is reported as not available and the verdict cannot be accepted

#### Scenario: Not applicable threshold
- **WHEN** the chat measured returns no structured output and the schema threshold is declared not required
- **THEN** that threshold is reported as not applicable and does not prevent an accepted verdict

### Requirement: Determinism and repetition

With the same raw run, judgements, rules and timestamp, the evaluation SHALL produce the same results bytes. The methodology SHALL require repeated runs for a final measurement, each recorded separately with the same inputs and settings, and the report SHALL show the variation between them and SHALL NOT replace a failing run by a better one.

#### Scenario: Same inputs, same bytes
- **WHEN** the scoring runs twice with identical inputs and timestamp
- **THEN** both results files are byte-identical

### Requirement: Baseline of the current chat

The repository SHALL contain the measurement of the chat as it is at the time of the change, with the results file and the report, and no answer text, so that later measurements can be compared with it. The evidence SHALL state that the chat measured was the template-based chat that does not call a model, and SHALL NOT present those results as the quality of a generative system.

#### Scenario: Baseline is labelled
- **WHEN** the baseline evidence is read
- **THEN** it identifies the commit, the date, the provider and the fact that no model generated the answers
- **AND** it makes no claim about the quality of a model-generated chat
