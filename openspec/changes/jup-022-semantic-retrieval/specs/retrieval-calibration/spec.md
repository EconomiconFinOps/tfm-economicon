## ADDED Requirements

### Requirement: Document-level retrieval measurement

A versioned script SHALL measure, for each of the 28 cases of the JUP-069 question bank, whether any of the `top_k` fragments retrieved for the question belongs to one of the documents declared in the `sources` of that case. It SHALL report the hit rate overall, by `category` and by `behavior`, and SHALL report the cases with `behavior` other than `answer` separately so they do not alter the hit rate of the answer cases.

#### Scenario: Hit and miss per case

- **WHEN** the retrieved fragments of a case include one from a declared source document
- **THEN** that case counts as a hit and otherwise as a miss, and the report lists the case identifier and the retrieved documents

#### Scenario: Cases that do not expect an answer

- **WHEN** a case has `behavior` equal to `clarify` or `abstain`
- **THEN** it appears in its own block of the report and is excluded from the answer hit rate

#### Scenario: Threshold not tuned against non-answer cases

- **WHEN** the maximum distance is selected from the sweep
- **THEN** the selection rule does not use the cases with `behavior` other than `answer`
- **AND** the report shows, for those cases, whether the retrieved fragments include their declared source documents, without choosing a value that empties them

#### Scenario: Case with several declared sources

- **WHEN** a case declares more than one source document
- **THEN** a fragment from any of them counts as a hit, and the report states how many of the declared documents were retrieved

### Requirement: Measurement independent of the database

The calibration SHALL split the corpus documents with the same function and parameters as the ingestion pipeline, embed the fragments and the questions with the configured provider and compute the cosine distance in the script itself. It SHALL NOT open any database connection and SHALL NOT write to any vector store.

#### Scenario: No database involved

- **WHEN** a calibration run executes with no database available
- **THEN** it completes normally and opens no database connection

#### Scenario: Same chunking as ingestion

- **WHEN** the ingestion chunk size or overlap changes
- **THEN** the calibration uses the new values and the report records them

#### Scenario: Same distance as the store

- **WHEN** the distance between a question and a fragment is computed by the script
- **THEN** it equals the cosine distance that the vector store reports for the same pair, within a stated numeric tolerance

### Requirement: Section-level labels outside the question bank

Section-level expectations SHALL be stored in a separate versioned file under `docs/validation/` that maps each case identifier to the headings expected in the source documents. The JUP-069 question bank file SHALL NOT be modified by this change. A validator SHALL reject a labels file in which a case identifier does not exist in the bank, a source is not declared by that case, a heading does not exist in the exact version of the document identified by its SHA-256, a case is labelled twice, or a label has no heading.

#### Scenario: Unknown case

- **WHEN** a label references a case identifier that the bank does not contain
- **THEN** validation fails and names the identifier

#### Scenario: Heading missing in the document version

- **WHEN** a label names a heading that does not exist in the document with the recorded SHA-256
- **THEN** validation fails and names the case, the document and the heading

#### Scenario: Document changed after labelling

- **WHEN** the SHA-256 of a source document differs from the one recorded in the labels
- **THEN** validation fails and indicates that the labels must be reviewed

#### Scenario: Bank untouched

- **WHEN** the labels file is added or changed
- **THEN** the JUP-069 question bank file is byte-for-byte unchanged

### Requirement: Reproducible calibration report

Each calibration run SHALL write a JSON result file and a human-readable report recording the model alias, the dimension, the corpus and bank versions with their hashes, the date, the `top_k` values and the maximum distances swept, the metrics per sweep point, the per-case results and the known limits of the measurement. Neither file SHALL contain a credential or the text of fragments beyond the headings already published in the corpus. The default `top_k` and maximum distance SHALL be set only to a sweep point that appears in a committed report, and the report SHALL state the selection rule used.

#### Scenario: Report is complete

- **WHEN** a calibration run finishes
- **THEN** the JSON file and the report contain every field above and list the limits, including the small corpus size

#### Scenario: Default without evidence

- **WHEN** a pull request changes the default maximum distance
- **THEN** a committed report that contains that value as a sweep point and the selection rule is referenced, or the change is rejected in review

#### Scenario: No secrets in the outputs

- **WHEN** a calibration run uses a real key
- **THEN** the key appears in neither output file nor in the console output

### Requirement: Bounded and opt-in real execution

A calibration run against the real provider SHALL be explicit and opt-in, SHALL refuse to start with a clear message when the key or the gateway URL is missing, and SHALL compute the number of embedding calls before the first one and stop without calling when that number exceeds a configured maximum. The continuous integration SHALL NOT run it.

#### Scenario: Missing key

- **WHEN** the run starts without the virtual key
- **THEN** it stops before any network call with a message that names the missing setting and prints no value

#### Scenario: Call budget exceeded

- **WHEN** the planned calls exceed the configured maximum
- **THEN** the run aborts before the first call and reports the planned and the allowed numbers

#### Scenario: Run in continuous integration

- **WHEN** the continuous integration executes the repository tests
- **THEN** the real-provider run is skipped and the validator of the labels file still runs
