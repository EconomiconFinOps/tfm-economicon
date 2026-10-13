## ADDED Requirements

### Requirement: Corpus describes cost anomalies as episodes consistent with the product

The assistant document corpus SHALL describe cost anomalies as the product treats them today (ADR-0020): one candidate episode per tenant, currency and service, with an expected value, a severity computed on accumulated impact, and the statuses `new`, `investigating`, `resolved` and `false_positive`. The corpus SHALL NOT state that severity is measured in EUR per month, and SHALL NOT list `acknowledged` as a status.

#### Scenario: Severity is defined on accumulated impact

- **WHEN** a contributor reads the anomaly section of the business-rules document
- **THEN** it defines P1 (above 2,000), P2 (500 to 2,000) and P3 (below 500) over the accumulated impact of the episode in its own currency, with nominal thresholds in EUR and USD and no conversion
- **AND** it does not define them as EUR per month.

#### Scenario: Statuses match the product

- **WHEN** a contributor reads the list of anomaly statuses in the corpus
- **THEN** it contains `new`, `investigating`, `resolved` and `false_positive`
- **AND** it does not contain `acknowledged`
- **AND** it says that closing an episode requires a reason and is final.

#### Scenario: Expected value and tracking are defined

- **WHEN** a contributor reads how an episode is detected and followed
- **THEN** the corpus states that the expected value is the mean daily cost of the previous 7 days, or the anchored reference of the episode while it is followed
- **AND** that the last day with data is treated as incomplete
- **AND** that an episode that stops triggering for 3 days is shown as no longer observed and is not closed automatically.

#### Scenario: A service with no previous spend is not asserted to meet the rule

- **WHEN** the corpus describes a service that has no spend before a given day
- **THEN** it states that the first day does not open an episode
- **AND** that from the second day the reference includes the first day, so stable new spend above the threshold can open one
- **AND** it does not state that a new resource meets or fails the double condition without data.

#### Scenario: An anomaly is a candidate, not a cause

- **WHEN** the corpus describes the outcome of the rule or of an episode
- **THEN** it presents it as a candidate to investigate
- **AND** it does not assert a root cause, a saving or statistical confidence
- **AND** it states that the panel does not act on resources.

### Requirement: Daily rule keeps its text and strict limits

The corpus SHALL keep the daily rule `relative_delta > 20 % AND absolute_delta > 100 EUR/day` unchanged and SHALL state, next to the rule and before any new anomaly content, that both limits are strict: a relative delta of exactly 20 % and an absolute delta of exactly 100 EUR/day each fail to trigger the rule.

#### Scenario: Strict relative limit

- **WHEN** a contributor reads the anomaly section
- **THEN** it says that an increase of exactly 20 % does not trigger the rule.

#### Scenario: Strict absolute limit

- **WHEN** a contributor reads the anomaly section
- **THEN** it says that an increase of exactly 100 EUR/day does not trigger the rule.

#### Scenario: Rule and strictness stay inside the first chunk of the section

- **WHEN** the anomaly section of the business-rules document is split by the ingestion chunker
- **THEN** the heading `Anomalias`, the rule and the statement of strict limits appear in the first fragment of that section.

### Requirement: Corpus guides the anomaly panel in the product's wording

The product-architecture document SHALL include a user guide of the anomaly panel written with the wording shown on screen, covering how to detect anomalies, what the review date means, the criticality labels, the observation labels, the status actions and the synthetic-data notice. It SHALL NOT expose implementation details such as endpoints, tables, queues or deployment, and SHALL NOT describe features that are not integrated in `develop` at the time the change is closed.

#### Scenario: Guide uses the on-screen wording

- **WHEN** a contributor reads the guide
- **THEN** it uses «Detectar ahora», «Revisado hasta…», Alta (P1), Media (P2), Baja (P3), «Se sigue observando» and «Ya no se observa» with the meaning the panel gives them.

#### Scenario: Guide exposes no internals

- **WHEN** corpus validation or review scans the guide
- **THEN** it contains no endpoint paths, header names, table names or service names.

#### Scenario: Guide covers only integrated features

- **WHEN** the reference date or the link to explain an anomaly in the assistant is not integrated in `develop`
- **THEN** the guide does not mention it
- **AND** the follow-up is recorded in the change review.

### Requirement: Corpus changes keep the evaluation pins consistent

When a document pinned by the JUP-069 question bank changes, the change SHALL update the pinned `sha256` of every modified source in that bank and in the JUP-022 retrieval labels, SHALL increment the `suite_version` of the bank, and SHALL keep every case identifier, question and expected point of the bank unchanged. Section labels SHALL name headings that exist in the modified documents.

#### Scenario: Pins match the modified documents

- **WHEN** the corpus validation, the question-bank validation and the retrieval-labels validation run after the change
- **THEN** all three pass
- **AND** the hashes recorded for the modified sources equal the hashes of the files in the repository.

#### Scenario: Bank content is not altered

- **WHEN** the bank before and after the change is compared ignoring `sources` and `suite_version`
- **THEN** the cases are identical.

#### Scenario: Labels name existing headings

- **WHEN** the retrieval labels are validated against the modified documents
- **THEN** every labelled heading exists in its source document.

#### Scenario: Earlier evaluation reports are kept as history

- **WHEN** the change is closed
- **THEN** the JUP-070 run reports are unchanged
- **AND** the change records that their corpus and bank hashes no longer match the repository.

#### Scenario: Retrieval calibration is repeated or declared not run

- **WHEN** the retrieval calibration cannot be run with the real embedding provider
- **THEN** the change records it as not run and does not publish simulated results as measurements of retrieval quality.

### Requirement: Corpus does not state the figures of a specific anomaly

The corpus SHALL explain how anomalies work in general and SHALL NOT state the figures of any specific anomaly (opening day, observed cost, reference, accumulated impact or status of a given episode). It SHALL use the same words as the panel and as the explanation of a stored episode (JUP-038): «Candidata: causa no establecida», the statuses «Nueva», «Investigando», «Resuelta» and «Falso positivo», and the criticality labels Alta (P1), Media (P2) and Baja (P3).

#### Scenario: Specific figures are not in the corpus

- **WHEN** a contributor reads the anomaly content of the corpus
- **THEN** it contains no amount, date or identifier of a particular episode
- **AND** it tells the user to open the detail of the anomaly in the panel to see those figures.

#### Scenario: Vocabulary matches the panel and the explanation

- **WHEN** a contributor compares the anomaly wording of the corpus with the panel and with the explanation of a stored episode
- **THEN** statuses, criticality labels and the sentence «Candidata: causa no establecida» are written the same way.

#### Scenario: The route to an explanation is mentioned only once it exists

- **WHEN** the link «Explicar en el asistente» is not integrated in `develop` at the time the change is closed
- **THEN** the corpus does not mention it
- **AND** the follow-up is recorded in the change review.
