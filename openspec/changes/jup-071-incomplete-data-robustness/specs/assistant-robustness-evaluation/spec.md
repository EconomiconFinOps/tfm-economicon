## ADDED Requirements

### Requirement: Versioned robustness cases anchored to the reference bank

The robustness suite SHALL contain at least sixteen meaningful incomplete or ambiguous variants anchored to existing JUP-069 cases, and SHALL include each referenced original baseline exactly once. Each variant SHALL identify its expected behavior, context, question, perturbation group, source references and rubric. The evaluator SHALL validate the suite version, unique identifiers, base-case references, reference-bank digest and source digests before collection or scoring. The original JUP-069 bank SHALL remain unchanged.

#### Scenario: Several variants share one baseline
- **WHEN** two robustness cases refer to the same original question
- **THEN** both variants remain distinct and the expanded execution contains that original baseline once

#### Scenario: Reference evidence changed
- **WHEN** a base-case identifier is missing, an identifier repeats or a pinned bank or source digest no longer matches
- **THEN** evaluation stops with an actionable validation error instead of silently changing the reference

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

The adapter SHALL prepare prompts from only the context and question and SHALL reuse the relevant collection functions of JUP-070. HTTP collection SHALL send the prepared prompt exactly, use a new conversation for every case and record the response, citations, retrieved context, HTTP status and total duration. It SHALL NOT transmit expected behavior, rubric or answer keys, SHALL NOT retry failed cases and SHALL classify infrastructure errors as blocked. Credentials SHALL be read from the environment and SHALL NOT be printed or stored in the run artifacts.

#### Scenario: Rubric stays outside the request
- **WHEN** a case is prepared and sent to the chat
- **THEN** the request contains its exact prepared context and question and no evaluation rubric or expected behavior

#### Scenario: Infrastructure failure is retained
- **WHEN** a case encounters a timeout or a server failure
- **THEN** it is recorded once with its failure category and a blocked outcome
- **AND** it is excluded from the pass/fail denominator without disappearing from the report

### Requirement: Offline template execution is labelled as such

The offline execution SHALL call the application's real template service with an explicitly declared retrieval double and SHALL require no network, embeddings service or database. Its artifacts SHALL identify this execution mode and SHALL NOT present it as a full HTTP integration, retrieval relevance measurement or model-generated answer evaluation. A manually supplied model alias or real embedding provider SHALL NOT constitute verification of generation by a model.

#### Scenario: Offline service result is collected
- **WHEN** the local template is evaluated with fixed retrieved fragments
- **THEN** the artifact identifies the template service and the retrieval double
- **AND** its conclusions are limited to that execution

#### Scenario: Current HTTP endpoint does not prove generation
- **WHEN** a runtime response contains answer text and citations but no verified evidence of the generation path
- **THEN** the report leaves real-model evaluation unverified even if the run metadata names a model

### Requirement: Human semantic review and reused numerical checks

The evaluator SHALL provide a review sheet containing each case's rubric, original response, citations and retrieved fragments. Human judgments SHALL cover behavior, required points and prohibited behaviors. Numerical expectations SHALL be checked through JUP-070's numerical evaluator with their labels, aliases, units and absolute tolerances. Cases declared critical, including the original baselines and cases with expected figures, SHALL require two distinct human reviewers for each semantic judgment unless explicitly scored provisionally with one. Missing judgments SHALL result in not_run when no failure is already established. A failing numerical check or received human judgment SHALL preserve fail even while other judgments are pending; missing judgments SHALL remain visible and assessment completeness SHALL remain false. Disagreement or a failing check SHALL prevent pass. Synthetic judgments used to test the evaluator SHALL NOT be presented as real human review.

#### Scenario: Correct number with unsupported meaning
- **WHEN** a response contains a correct expected number but human review finds that its behavior or a prohibition fails
- **THEN** the case does not pass

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
- **THEN** its provisional status and reduced reviewer coverage are visible in the report

### Requirement: Complete grouped reports and private raw material

The report SHALL retain one outcome per planned case from pass, fail, blocked and not_run. It SHALL show the planned total and all four counts, group baselines separately from variants, and break down results by perturbation group and expected behavior. Reported success rates SHALL distinguish pass divided by the planned total from pass divided by pass plus fail, and SHALL expose unavailable denominators rather than replace them with zero or success. The report SHALL state that known failures with pending judgments can belong to the pass/fail denominator, which SHALL NOT be described as completed human review coverage. Versionable results SHALL exclude question, answer and retrieved-fragment text and private judgment notes; raw responses and review material SHALL be written outside the repository.

#### Scenario: Most cases lack review
- **WHEN** one case passes and the remaining cases are not_run
- **THEN** the report shows the single evaluated case alongside the full planned population and not_run count
- **AND** it does not describe the entire suite as passed

#### Scenario: No evaluated cases in a group
- **WHEN** a group's cases are all blocked or not_run
- **THEN** that group's success rate is unavailable and its non-evaluated counts remain visible

### Requirement: Reproducible evidence with a real-model verification boundary

Evidence SHALL identify the execution date, application commit, suite version and digest, relevant source versions, runtime configuration and evidence level. Final evaluation of a generative system SHALL require three independent collections with the same suite and configuration and the required human judgments; all repetitions SHALL be preserved. Evidence SHALL distinguish technical instrument checks, template or mock results and verified model runs. When JUP-035 generation is not verified, the generative evaluation SHALL remain explicitly pending.

#### Scenario: Only template evidence exists
- **WHEN** the available run uses the template service or a mocked response producer
- **THEN** the report may describe observed limitations of that run
- **AND** it leaves robustness of a generative model pending

#### Scenario: Repeated model evaluation
- **WHEN** a verified generative runtime is evaluated for the final measurement
- **THEN** all three runs use the same suite and configuration and are published separately
- **AND** the best run is not substituted for the others
