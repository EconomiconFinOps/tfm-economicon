## ADDED Requirements

### Requirement: Versioned robustness cases anchored to the reference bank

The robustness suite SHALL contain at least sixteen meaningful incomplete or ambiguous variants anchored to existing JUP-069 cases, and SHALL include each referenced original baseline exactly once. Each variant SHALL identify its expected behavior, context, question, category, perturbation group, source references and rubric. The evaluator SHALL validate the suite version, unique identifiers, base-case references, reference-bank digest, methodology digest and source digests before collection or scoring. The original JUP-069 bank SHALL remain unchanged.

#### Scenario: Several variants share one baseline
- **WHEN** two robustness cases refer to the same original question
- **THEN** both variants remain distinct and the expanded execution contains that original baseline once

#### Scenario: Reference evidence changed
- **WHEN** a base-case identifier is missing, an identifier repeats or a pinned bank, methodology or source digest no longer matches
- **THEN** evaluation stops with an actionable validation error instead of silently changing the reference

#### Scenario: The reference bank is updated upstream
- **WHEN** the reference bank, its methodology or its corpus sources change in the integration branch
- **THEN** the suite references are updated only after confirming that the questions and the rules its variants rely on are unchanged
- **AND** the suite keeps its own version and the report records the suite digest, which covers the pinned digests of the bank, the methodology and the sources

### Requirement: Strict suite validation with controlled errors

The evaluator SHALL validate the structure of the suite before use: the schema version SHALL be the integer one and not a boolean, the suite version SHALL have the form major.minor.patch, every case SHALL be an object whose identifier, base identifier, behavior, risk, question, context, category and perturbation are text and whose required points, forbidden behaviors, sources and expected numbers are lists, and the baseline, methodology and sources reference blocks SHALL be present and well formed. Case identifiers SHALL have the form JUP-071 followed by three digits, the behavior SHALL be one of answer, clarify or abstain and the risk one of critical or standard, and all three behaviors SHALL be present. Cases with expected figures SHALL be declared critical. Each expected figure SHALL be an object whose value and tolerance are finite JSON numbers, so booleans and integers too large to represent are refused, and any aliases it declares SHALL be non-empty and unique after normalization. Any violation SHALL stop evaluation with an error that names the case or block. Hostile input, such as numbers too large for a float or documents nested far beyond the usual depth, SHALL end in the same controlled error and SHALL NOT produce an unhandled exception or traceback.

#### Scenario: Malformed case
- **WHEN** a case is not an object, a text field holds a list, a required list is missing or an expected figure is not an object
- **THEN** validation fails with an error naming the case and the field

#### Scenario: Standard-risk case with expected figures
- **WHEN** a case with expected figures is declared with a risk other than critical
- **THEN** validation fails, so a single reviewer cannot be enough for a case that carries figures

#### Scenario: Number or document beyond representable limits
- **WHEN** an expected figure, a declared temperature, a retrieved distance or a duration is an integer too large for a float, or a document is nested thousands of levels deep
- **THEN** the command ends with a controlled error and exit code two, and writes nothing

#### Scenario: Alias that normalizes to nothing
- **WHEN** a declared alias is empty after normalization, for example only emphasis marks, or repeats another alias after normalization
- **THEN** validation fails, because an empty alias would match any sentence

### Requirement: Explicit incomplete-data and ambiguity coverage

The suite SHALL cover absent or conflicting tags, shared costs without sufficient allocation evidence, incomplete data coverage and ambiguous scope, period or units. Its rubrics SHALL distinguish a supported partial answer, a request for missing information and abstention from an unsupported claim. Baselines with sufficient evidence SHALL remain available to detect indiscriminate abstention.

#### Scenario: Shared cost without an approved allocation basis
- **WHEN** a case provides a shared cost but no sufficient approved allocation basis
- **THEN** its rubric requires preserving that uncertainty and seeking the missing basis
- **AND** it forbids presenting an invented allocation as approved

#### Scenario: Missing records do not prove zero cost
- **WHEN** a case has incomplete ingestion and an empty cost result
- **THEN** its rubric distinguishes missing evidence from a measured zero

### Requirement: Prompt fidelity and faithful HTTP collection

The adapter SHALL prepare prompts from only the context and question and SHALL reuse the relevant collection functions of JUP-070. HTTP collection SHALL send the prepared prompt exactly, use a new conversation for every case and record the response, citations, retrieved context, HTTP status and total duration. It SHALL NOT transmit expected behavior, rubric or answer keys, SHALL NOT retry failed cases and SHALL classify infrastructure errors as blocked. Credentials SHALL be read from the environment and SHALL NOT be printed or stored in the run artifacts. A prepare command SHALL write the prepared prompts, and only them, to a file outside the repository, and SHALL refuse a path inside it even if the path has the name of a generated report. The run description supplied for a collection SHALL contain the six declared fields and no others and SHALL be validated before the first request is sent. Its generation object SHALL carry only a model alias and a temperature, and its corpus and retrieval descriptions SHALL each be a short text or a flat object of at most sixteen short scalar values whose keys are plain lowercase names that do not look like credentials. An unexpected or oversized field SHALL be refused naming the field and not its value, because the description is stored with the raw collection.

#### Scenario: Rubric stays outside the request
- **WHEN** a case is prepared and sent to the chat
- **THEN** the request contains its exact prepared context and question and no evaluation rubric or expected behavior

#### Scenario: Infrastructure failure is retained
- **WHEN** a case encounters a timeout or a server failure
- **THEN** it is recorded once with its failure category and a blocked outcome
- **AND** it is excluded from the pass/fail denominator without disappearing from the report

#### Scenario: Invalid run description
- **WHEN** the run description names an invalid commit, provider, alias or generation, carries a field outside the six declared ones, or nests an unexpected field or a large or credential-like value inside generation, corpus or retrieval
- **THEN** collection stops before any request is made and nothing is written
- **AND** the offending field is named in the error without echoing its value

### Requirement: Offline template execution is labelled as such

The offline execution SHALL call the application's real template service with an explicitly declared retrieval double and SHALL require no network, embeddings service or database. It SHALL refuse to run when the service file differs from the reviewed version. Its artifacts SHALL identify this execution mode and SHALL NOT present it as a full HTTP integration, retrieval relevance measurement or model-generated answer evaluation. A manually supplied model alias or real embedding provider SHALL NOT constitute verification of generation by a model.

#### Scenario: Offline service result is collected
- **WHEN** the local template is evaluated with fixed retrieved fragments
- **THEN** the artifact identifies the template service and the retrieval double
- **AND** its conclusions are limited to that execution

#### Scenario: Service changed since the review
- **WHEN** the application's template service no longer matches the reviewed version
- **THEN** the offline execution stops before importing it

#### Scenario: Current HTTP endpoint does not prove generation
- **WHEN** a runtime response contains answer text and citations but no verified evidence of the generation path
- **THEN** the report leaves real-model evaluation unverified even if the run metadata names a model

### Requirement: Human semantic review and reused numerical checks

The evaluator SHALL provide a review sheet containing each case's rubric, original response, citations and retrieved fragments. Human judgments SHALL cover behavior, required points and prohibited behaviors. Numerical expectations SHALL be checked through JUP-070's numerical evaluator with their labels, aliases, units and absolute tolerances; the aliases of a figure are the ones declared by the suite for it, then the ones of the reference rules, then its label, and the rival labels of a figure SHALL be the aliases of the other expected figures of the same case. Cases declared critical, including the original baselines and cases with expected figures, SHALL require two distinct human reviewers for each semantic judgment unless explicitly scored provisionally with one. Missing judgments SHALL result in not_run when no failure is already established. A failing numerical check or received human judgment SHALL preserve fail even while other judgments are pending; missing judgments SHALL remain visible and assessment completeness SHALL remain false. Disagreement or a failing check SHALL prevent pass. Synthetic judgments used to test the evaluator SHALL NOT be presented as real human review.

#### Scenario: Correct number with unsupported meaning
- **WHEN** a response contains a correct expected number but human review finds that its behavior or a prohibition fails
- **THEN** the case does not pass

#### Scenario: Figure under another figure's label
- **WHEN** a response gives the value of one expected figure under a label that belongs to another figure of the same case
- **THEN** the numerical check of the mislabelled figure fails

#### Scenario: Paraphrased correct figure
- **WHEN** a response states an expected figure with its declared alias instead of its exact label
- **THEN** the numerical check passes in the variant exactly as it does in the baseline it derives from

#### Scenario: Critical review is incomplete
- **WHEN** a critical case has only one distinct reviewer, no check has established a failure and provisional mode is disabled
- **THEN** it is reported as not_run with the reason

#### Scenario: No judgments have been supplied
- **WHEN** responses have been collected but their required semantic judgments are absent
- **THEN** cases without any established failure remain not_run and cases with a failed numerical check retain fail
- **AND** both kinds retain their missing semantic checks and incomplete assessment status without synthesizing a reviewer or inferring an approval

#### Scenario: A known failure does not imply complete review
- **WHEN** a numerical check or one received judgment fails while other judgments are missing
- **THEN** the case outcome is fail and the pending checks remain visible
- **AND** the report does not count that case as a completed human assessment

#### Scenario: Provisional review is explicit
- **WHEN** a critical case is scored provisionally with one reviewer
- **THEN** the case is marked with reduced reviewer coverage in the machine-readable and the human-readable report
- **AND** assessment completeness is false while any case has reduced coverage

### Requirement: Judgments bound to one validated collection

A raw collection SHALL be validated before it is reviewed or scored: every prompt SHALL equal the prepared prompt of its versioned case, case identifiers SHALL be known and unique, the configuration digest SHALL match its content, failure categories SHALL belong to a closed list, citations and retrieved fragments SHALL have the expected shape, distances and durations SHALL be finite and durations non-negative, and the collection time SHALL be a calendar-valid UTC timestamp. Human judgments SHALL carry the digest of the exact collection they judge and SHALL be refused for any other, SHALL refer only to known cases and judgment points, and SHALL have at most two distinct reviewers per point. Reviewer identities SHALL be compared after normalization, which is not an authentication of identity.

#### Scenario: Judgments for another collection
- **WHEN** a judgments file declares the digest of a different raw collection
- **THEN** scoring is refused and no report is written

#### Scenario: Altered collection
- **WHEN** a prompt differs from its versioned case, a case repeats or a configuration digest no longer matches
- **THEN** the collection is refused with an error that names the case

### Requirement: Complete grouped reports and private raw material

The report SHALL retain one outcome per planned case from pass, fail, blocked and not_run. It SHALL show the planned total and all four counts, group baselines separately from variants, and break down results by perturbation type, by category and by expected behavior. The category breakdown SHALL aggregate the variants that share a category, in addition to the per-perturbation breakdown whose groups hold a single case each, and SHALL state the number of cases of every group so that a rate over a very small group is not read as a general result. Reported success rates SHALL distinguish pass divided by the planned total from pass divided by pass plus fail, and SHALL expose unavailable denominators rather than replace them with zero or success. The report SHALL state that known failures with pending judgments can belong to the pass/fail denominator, which SHALL NOT be described as completed human review coverage, and SHALL state the number of cases with reduced reviewer coverage and whether the assessment is complete. Versionable results SHALL exclude question, answer and retrieved-fragment text, reviewer names and private judgment notes; raw responses and review material SHALL be written outside the repository.

#### Scenario: Most cases lack review
- **WHEN** one case passes and the remaining cases are not_run
- **THEN** the report shows the single evaluated case alongside the full planned population and not_run count
- **AND** it does not describe the entire suite as passed

#### Scenario: No evaluated cases in a group
- **WHEN** a group's cases are all blocked or not_run
- **THEN** that group's success rate is unavailable and its non-evaluated counts remain visible

#### Scenario: Missing responses
- **WHEN** a response is absent for some planned cases
- **THEN** those cases stay in the planned total as not_run with the reason, in every breakdown

### Requirement: Controlled output locations

Raw collections, review sheets and judgment templates SHALL be written outside the repository. Inside the repository only the generated JUP-071 report files of the evidence folder MAY be written. The evaluator SHALL refuse any output that would overwrite an input, a versioned reference, the suite, the baseline, the service, the evaluator code or another output, and SHALL refuse destinations whose parent directory does not exist. Paths SHALL be compared after normalization: extended-length prefixes, trailing dots and spaces in a component and case differences SHALL NOT hide a repository location, and on Windows network share paths, including administrative shares that resolve to a local drive, SHALL NOT be accepted. A refusal SHALL occur before any file is written.

#### Scenario: Output inside the repository
- **WHEN** an output path is inside the repository and is not a generated JUP-071 report of the evidence folder
- **THEN** the command fails and no file is written

#### Scenario: Location disguised by path syntax
- **WHEN** a path uses an extended-length prefix, a network share form, a trailing dot or space, or parent references to reach a repository location
- **THEN** it is treated as that repository location and refused

#### Scenario: Output would replace evidence
- **WHEN** an output path equals the raw data, the judgments, a reference or another output of the same command
- **THEN** the command fails before writing

### Requirement: Declared run metadata is restricted and never certifies a model

Provider, alias and generation identifiers written by the operator SHALL be lowercase identifiers of up to sixty-four characters made of letters, digits, dots, slashes and hyphens, and SHALL NOT contain credential-shaped parts or unbroken alphanumeric runs of twenty-four characters or more. A declared commit SHALL be seven to forty lowercase hexadecimal characters. A declared temperature SHALL be absent or a finite number, not a boolean and not an integer too large for a float. Only these validated fields SHALL reach the versionable report; other configuration fields SHALL NOT be copied. This validation is a heuristic against accidental disclosure and SHALL NOT be described as a guarantee that no secret can be written. No declared field, and no all-pass set of judgments, SHALL set model verification or generative robustness acceptance to true.

#### Scenario: Credential-shaped or descriptive value
- **WHEN** a declared provider, alias or generation identifier is a URL, has uppercase letters, spaces or underscores, starts with a credential prefix or exceeds the length limit, as the descriptive markers of the collector guide do
- **THEN** the report is not produced and the error names the field

#### Scenario: Plain words that look like placeholders
- **WHEN** a declared identifier satisfies the pattern but is a word such as to-be-defined or unknown
- **THEN** it is accepted, because the validation checks shape and not meaning, and declaring real values remains the operator's responsibility

#### Scenario: Extra configuration fields
- **WHEN** the operator configuration holds fields such as an API key or collector hashes
- **THEN** the versionable report contains none of them

### Requirement: Report identity aligned with the JUP-070 run header

Each versionable report SHALL carry a unique run identifier derived from the raw collection and a `run` object with the same field names as the JUP-070 report header (`commit`, `date`, `provider`, `alias`, `suite_version`, `suite_sha256`, `generation`), so a later consumer can compare runs of different suites without suite-specific knowledge. For an offline template run, `provider` and `alias` SHALL state that no model was involved instead of being omitted or left empty. For a live run, `generation` MAY be given as an object with a model alias and a temperature, or as a single identifier string which is recorded as the model alias without temperature. The existing top-level fields SHALL be kept. Adding the header SHALL NOT change any outcome, count or denominator, and the report SHALL NOT claim compatibility with the JUP-067 metric catalogue.

#### Scenario: Two runs of the same suite on the same day
- **WHEN** two reports are produced from the same suite version on the same date
- **THEN** their run identifiers differ
- **AND** each report names its provider and alias, or states that none applies

#### Scenario: Run description from the chat collector
- **WHEN** a live run is described with a short declared commit and `generation` as a single identifier string, as the JUP-123 chat collector writes it
- **THEN** the report records that string as the model alias with no temperature
- **AND** provider, alias and the identifier remain subject to the restricted pattern, so a descriptive placeholder or a credential-shaped value is rejected

#### Scenario: Header added without changing results
- **WHEN** a report is regenerated from the same raw material and judgments with the header present
- **THEN** every outcome, count and denominator equals the previous report's

### Requirement: Evidence without a measured distance is kept as unmeasured

The raw collection format SHALL accept a retrieved fragment whose `distance` is explicitly null, meaning the server reported no distance, and SHALL still reject a fragment whose distance is missing, textual, boolean or not finite. A case MAY carry a `public_evidence` list of objects with textual `id` and `kind` and a null or finite `distance`; the review sheet SHALL show it with the citations and fragments. A null distance SHALL NOT be converted to a number and SHALL NOT affect any outcome. The tool SHALL expose `ACCEPTS_UNMEASURED_DISTANCE` as true so a collector can detect that it may export such evidence instead of blocking the row.

#### Scenario: Fragment with a null distance
- **WHEN** a raw collection contains a retrieved fragment with `distance: null`
- **THEN** it validates, is scored like any other case and appears in the review sheet with `"distance": null`

#### Scenario: Missing or invalid distance
- **WHEN** a fragment omits `distance` or gives it as a string, a boolean or a non-finite number
- **THEN** the collection is rejected with a controlled error

#### Scenario: Malformed public evidence
- **WHEN** `public_evidence` is not a list of objects with textual `id` and `kind`, or carries an invalid distance
- **THEN** the collection is rejected

### Requirement: Dashboard rows without text or names

The tool SHALL provide a `rows` command that writes a score report as the `rows-v1` contract of the evaluation dashboard (JUP-121): a run identity taken from the report (identifier, date, commit, suite and its hash, model alias, and a synthetic flag that is true for template runs) and result rows for the case states in total, by baseline or variant and behavior, and by category, for both pass rates, for reduced coverage and for numeric checks. Case-state rows SHALL carry a count and a denominator and no value. A rate with no evaluated cases SHALL be not measured with a null value, never zero. The rows SHALL NOT contain answer text, reviewer names or notes. Fields no report records (corpus, retrieval and prompt hashes) SHALL be null. Output paths SHALL follow the same limits as the other outputs, with generated `JUP-071-*-rows.json` files allowed in `docs/evidence`.

#### Scenario: Rows from a report
- **WHEN** `rows` converts a valid score report
- **THEN** the run identity matches the report and the case-state rows add up to the total of cases
- **AND** the rows contain no answer text, reviewer name or judgment note

#### Scenario: Rate without evaluated cases
- **WHEN** the report has no evaluated cases
- **THEN** the evaluated rate is not measured, with a null value and a zero denominator

#### Scenario: Unsafe input or output
- **WHEN** the report is malformed or missing, or the output would overwrite the input or sits inside the repository outside the generated names
- **THEN** the command fails with a controlled error and writes nothing

### Requirement: Reproducible evidence with a real-model verification boundary

Evidence SHALL identify the execution date, application commit, suite version and digest, relevant source versions, runtime configuration and evidence level. Final evaluation of a generative system SHALL require three independent collections with the same suite and configuration and the required human judgments; all repetitions SHALL be preserved, and a repeated export of the same collection SHALL NOT count as an independent execution. Evidence SHALL distinguish technical instrument checks, template or mock results and verified model runs. When JUP-035 generation is not verified, the generative evaluation SHALL remain explicitly pending.

#### Scenario: Only template evidence exists
- **WHEN** the available run uses the template service or a mocked response producer
- **THEN** the report may describe observed limitations of that run
- **AND** it leaves robustness of a generative model pending

#### Scenario: Repeated model evaluation
- **WHEN** a verified generative runtime is evaluated for the final measurement
- **THEN** all three runs use the same suite and configuration and are published separately
- **AND** the best run is not substituted for the others

#### Scenario: Mixed or repeated collections
- **WHEN** three reports are compared and they differ in suite, configuration, code or provisional status, or two of them share the same raw collection
- **THEN** the comparison is refused
- **AND** a summary that lacks the expected fields is refused with a controlled error
