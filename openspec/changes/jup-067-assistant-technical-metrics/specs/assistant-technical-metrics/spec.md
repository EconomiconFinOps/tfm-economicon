## ADDED Requirements

### Requirement: Metric catalogue with stable definitions

The project SHALL publish a catalogue of technical metrics for the assistant. Each metric SHALL have a stable identifier, a name, a formula expressed as a numerator and a denominator, the population it is computed over, the source of each datum, the unit and the family it belongs to. The families SHALL be accuracy, context relevance, grounding, latency, structured-output robustness and availability. A metric SHALL NOT change its meaning without a new version of the catalogue.

#### Scenario: Every metric is fully defined

- **WHEN** the catalogue is validated
- **THEN** each metric has identifier, formula with numerator and denominator, population, source, unit and family
- **AND** no two metrics share an identifier

#### Scenario: A definition changes

- **WHEN** the formula or population of a metric is edited
- **THEN** the catalogue version changes and a report that states an older version is not accepted as current

### Requirement: Case outcomes and populations

Each evaluated case SHALL have exactly one outcome among `pass`, `fail`, `blocked` and `not_run`. A rate SHALL be computed over the cases that are `pass` or `fail` of the declared population only; `blocked` and `not_run` cases SHALL be excluded from every denominator and SHALL be reported as counts. Cases whose expected behavior is `clarify` or `abstain` SHALL be reported separately from `answer` cases and SHALL NOT enter the answer-case rates. Every published rate SHALL show its numerator, its denominator and a 95 % Wilson interval.

#### Scenario: Blocked cases do not lower a rate

- **WHEN** 28 cases are evaluated and 3 are `blocked`
- **THEN** the denominator of the rates is the number of `pass` plus `fail` cases
- **AND** the report lists 3 blocked cases

#### Scenario: Non-answer cases are separate

- **WHEN** the population contains `answer`, `clarify` and `abstain` cases
- **THEN** the answer-case rate ignores the other two groups
- **AND** each group has its own rate and counts

#### Scenario: Small samples show their uncertainty

- **WHEN** a rate is computed over 20 cases
- **THEN** the report shows the counts and the Wilson interval, not only the percentage

### Requirement: Accuracy from the question bank rubric

Accuracy SHALL be computed from the rubric of the JUP-069 question bank. A case SHALL be `pass` only if every point of `required` is satisfied, no `forbidden` conduct appears and every value of `numbers` is within its absolute tolerance, with the unit and the label checked and not only the presence of the number. The report SHALL distinguish objective checks (`numbers` and `forbidden`, decidable by rule) from judged checks (`required`, decided by a reviewer), SHALL record who decided each judged check, and SHALL compute an objective-check rate over the objective checks alone.

#### Scenario: Number within tolerance but wrong unit

- **WHEN** a response contains the expected value with a different unit
- **THEN** the numeric check fails and the case is not `pass`

#### Scenario: One required point missing

- **WHEN** all numbers are correct and no forbidden conduct appears but one required point is not satisfied
- **THEN** the case is `fail`

#### Scenario: Judged checks name their decider

- **WHEN** a `required` point is recorded as satisfied
- **THEN** the record states whether a person or a rule decided it

### Requirement: Context relevance from section-level labels

Context relevance SHALL be computed from the retrieval of each case with the labels of JUP-022: a document hit when any retrieved fragment belongs to a document declared by the case, a section hit when any retrieved fragment belongs to a labelled section, and an empty-result rate. Cases labelled with coverage `none` SHALL be excluded from the section hit rate and listed as corpus gaps. The metrics SHALL state the `top_k`, the maximum distance, the chunking and the embedding alias they were measured with.

#### Scenario: Corpus gap

- **WHEN** a case has coverage `none`
- **THEN** it is excluded from the section hit rate and appears in the list of gaps

#### Scenario: Measurement conditions are part of the result

- **WHEN** a relevance report is produced
- **THEN** it states `top_k`, maximum distance, chunk size, overlap and embedding alias

### Requirement: Retrieval confidence from similarity

Retrieval confidence SHALL be reported as the median and the quartiles of the similarity of the best retrieved fragment of each case, defined as one minus the cosine distance returned by the vector store, over the cases with at least one retrieved fragment. Cases with an empty result SHALL be excluded from it and counted in the empty-result rate. The value SHALL be published as computed, without clamping, and a report measured with the mock embedding provider SHALL state that the similarity has no semantic meaning.

#### Scenario: Similarity from distance

- **WHEN** the best fragment of a case has distance 0.35
- **THEN** its similarity is 0.65

#### Scenario: Empty results do not count as zero

- **WHEN** a case retrieves nothing because of the maximum distance
- **THEN** it is excluded from the confidence statistics and counted as an empty result

#### Scenario: Mock provider

- **WHEN** the run used the mock embedding provider
- **THEN** the report marks the confidence as not semantically meaningful

### Requirement: Grounding of citations and figures

Grounding SHALL be measured by three metrics: the share of citations that point to a fragment in the retrieved set of that question and tenant, the number of numeric claims in a response that cannot be traced to the retrieved context, the evidence of the response or the question itself, and the integrity of evidence references in structured responses (every metric and recommendation references an existing evidence identifier). A response with any untraceable figure in a case marked critical SHALL make that case `fail` for grounding.

#### Scenario: Invented citation

- **WHEN** a response cites a fragment that was not retrieved for the question
- **THEN** it counts against the valid-citation rate

#### Scenario: Figure without support in a critical case

- **WHEN** a critical case contains a number that appears in neither the context nor the question
- **THEN** the case fails for grounding

#### Scenario: Dangling evidence reference

- **WHEN** a metric of a structured response references an evidence identifier that does not exist
- **THEN** it counts against the evidence-integrity metric

### Requirement: Latency percentiles

Latency SHALL be reported per stage (embedding of the question, retrieval query, generation and total) with the median, the 95th percentile and the maximum, computed with the nearest-rank method over the milliseconds recorded for each call. Failed and timed-out calls SHALL be counted in a separate failure rate, and the percentiles SHALL state whether they cover successful calls only. A percentile SHALL NOT be reported when fewer than a documented minimum number of observations exists.

#### Scenario: Nearest-rank percentile

- **WHEN** ten observations are recorded
- **THEN** the 95th percentile is the tenth value of the sorted list

#### Scenario: Failures are visible

- **WHEN** some calls time out
- **THEN** the failure rate counts them and the percentiles are labelled as covering successful calls only

#### Scenario: Too few observations

- **WHEN** fewer observations than the documented minimum exist for a stage
- **THEN** the percentile is reported as not available

### Requirement: Structured-output robustness

The share of responses that parse against the response schema and the count of failures by category SHALL be reported, where the categories are exactly the fixed set of provider failure categories plus the schema-validation failure.

#### Scenario: Unknown category

- **WHEN** a result record carries a failure category outside the fixed set
- **THEN** the results file is rejected

### Requirement: Availability of the chat

Availability SHALL be reported as the share of chat requests of the run that did not end in a server error (status 500 to 599), over all chat requests, with its counts and Wilson interval. A run with no chat requests SHALL report availability as not available, not as 100 %.

#### Scenario: Server errors lower availability

- **WHEN** 200 chat requests are recorded and 3 end in a server error
- **THEN** availability is 197 of 200 with its interval

#### Scenario: Client errors do not count

- **WHEN** a request ends with status 404 or 422
- **THEN** it is not a server error

#### Scenario: No requests

- **WHEN** the run recorded no chat requests
- **THEN** availability is reported as not available

### Requirement: Versioned results format without sensitive content

Per-case results SHALL use a versioned format that records, for each case, its identifier, outcome, the individual checks, the stage latencies, the retrieved identifiers, the citations and the failure category, and, for the run, the commit, the question bank version and hash, the corpus hashes and size in documents and fragments, the provider and alias, the generation settings, the count of chat requests and of server errors, and the date. The format SHALL NOT contain the text of questions, responses or fragments, nor credentials, and a file that does would be rejected.

#### Scenario: Question text in a result file

- **WHEN** a results file contains a field named `question`, `prompt` or `response`
- **THEN** it is rejected

#### Scenario: Corpus size is reported with latency

- **WHEN** a report includes latency percentiles
- **THEN** it states the corpus size of the run beside them

#### Scenario: Results for another suite

- **WHEN** the question bank hash in the results differs from the bank in the repository
- **THEN** the calculation stops and names the mismatch

### Requirement: Reproducible reference calculator

A reference calculator SHALL validate a results file and compute every catalogue metric offline, with the standard library, deterministically (same input, same output) and without network or database access. It SHALL reject malformed input with a message that names the offending field and no value, and it SHALL write the report as JSON and as Markdown.

#### Scenario: Same input twice

- **WHEN** the calculator runs twice over the same results file
- **THEN** both reports are byte-identical apart from the generation timestamp, which is an explicit argument

#### Scenario: Unknown case

- **WHEN** the results file contains a case identifier absent from the question bank
- **THEN** the calculator stops naming the identifier

#### Scenario: No network

- **WHEN** the calculator runs with all network access blocked
- **THEN** it produces the report

### Requirement: Provisional targets next to measured values

The report SHALL show, beside each measured value, the provisional target it is compared with and its source, and SHALL state whether the value meets it, without treating the target as an acceptance gate. Targets taken from a proposed decision SHALL be marked provisional.

#### Scenario: Target comparison

- **WHEN** the 95th percentile of total latency is 12 s and the provisional target is 10 s
- **THEN** the report shows both values, the source of the target and that the target is not met
- **AND** the report does not declare the assistant rejected
