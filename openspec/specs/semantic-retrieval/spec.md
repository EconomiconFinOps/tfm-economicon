# semantic-retrieval Specification

## Purpose
Retrieval of context for the chat questions: query embedding with the ingestion model through the gateway, explicit retrieval parameters, deterministic ordering, empty results, tenant isolation, compatibility with the stored vectors, sanitized failures and traceability.

## Requirements
### Requirement: Query embedding with the ingestion model

The backend SHALL compute the embedding of each chat question with the same model alias and the same dimension that the ingestion pipeline used for the stored documents, through the LiteLLM gateway and with a virtual key that belongs to the backend and is different from the processor's. The embedding provider SHALL keep the existing interface: `embed(text)` returns a list of finite floats whose length equals the provider `dimension`, and the provider exposes `name`.

#### Scenario: Real provider embeds the question

- **WHEN** the provider is `litellm` and the alias is `economicon-embedding` with dimension 1536
- **THEN** the backend requests the embedding of the question from the gateway with that alias
- **AND** the vector used for the search has exactly 1536 finite values

#### Scenario: Mock provider outside development and test

- **WHEN** the backend starts with the `mock` provider and the runtime environment is not `development` or `test`
- **THEN** startup is rejected with a message that names the setting and no value

#### Scenario: Real provider without a key

- **WHEN** the provider is `litellm` and the virtual key is missing or blank
- **THEN** startup is rejected with a message that names the setting and prints no value

#### Scenario: Startup states which provider is active

- **WHEN** the backend starts with either provider
- **THEN** it logs one line with the provider, the model alias and the dimension
- **AND** the line never contains the key or any part of it

#### Scenario: Response with the wrong shape

- **WHEN** the gateway answers with a vector whose length differs from the provider dimension, or with a non-finite value, or with more than one vector
- **THEN** the question is not searched and the failure is reported as an invalid provider response

### Requirement: Backend gateway credentials

The backend SHALL read the gateway URL, the model alias and the virtual key from its own settings. The key SHALL be a secret value with no default that never appears in logs, in `repr`, in error messages, in responses, in images or in `.env.example` with a value. The transport SHALL use a bounded timeout and a bounded number of retries, retry only transient failures (timeout, connection, rate limit, upstream 5xx), never follow redirects, and classify failures into the same fixed categories as the processor client.

#### Scenario: Key never printed

- **WHEN** the backend logs, formats its settings or fails with any provider error
- **THEN** neither the key nor any substring of it appears in the output

#### Scenario: Redirect is not followed

- **WHEN** the gateway answers with a redirect
- **THEN** the backend does not send the key to the new location and reports the `redirect` category

#### Scenario: Retries are bounded and transient only

- **WHEN** the gateway answers 429 or 503 repeatedly, or answers 401 once
- **THEN** the 429 and 503 cases are retried at most the configured number of times and then fail
- **AND** the 401 case is not retried

### Requirement: Explicit retrieval parameters

The retrieval SHALL take `top_k` and an optional maximum cosine distance from backend settings. `top_k` SHALL be an integer within a documented inclusive range and values outside it SHALL be rejected at startup. The maximum distance, when defined, SHALL be a number greater than 0 and not greater than 2, and a value outside that range SHALL be rejected at startup. When the maximum distance is not defined no fragment SHALL be excluded by distance. When the setting is absent or blank, the backend SHALL use the default calibrated for its embedding provider (0.6 for `litellm`, none for `mock`, whose vectors carry no semantic distance); the words `none` and `off` SHALL disable the threshold explicitly for any provider, and a numeric value SHALL always override the default.

#### Scenario: top_k limits the results

- **WHEN** the tenant has more matching fragments than `top_k`
- **THEN** exactly `top_k` fragments are returned, the closest ones

#### Scenario: Maximum distance filters the results

- **WHEN** the maximum distance is defined and only some of the closest fragments are within it
- **THEN** only those fragments are returned, up to `top_k`

#### Scenario: Invalid parameters

- **WHEN** `top_k` is zero, negative, above the range or not an integer, or the maximum distance is zero, negative, above 2 or not finite
- **THEN** startup is rejected with a message that names the setting

#### Scenario: Default threshold by provider

- **WHEN** the maximum distance is absent or blank and the provider is `litellm`
- **THEN** the effective maximum distance is 0.6
- **AND** with the `mock` provider no distance filter applies

#### Scenario: Threshold disabled or overridden explicitly

- **WHEN** the maximum distance is `none` or `off`, or a number
- **THEN** `none` and `off` remove the filter for any provider and the number replaces the default

#### Scenario: top_k larger than the available fragments combined with a threshold

- **WHEN** `top_k` is larger than the number of fragments of the tenant and the maximum distance excludes some of them
- **THEN** the result contains only the fragments within the distance and no filler

### Requirement: Deterministic ordering

The returned fragments SHALL be ordered by ascending cosine distance and, when distances are equal, by ascending fragment identifier. The order SHALL be the same for two executions over the same data, including ties between fragments of the same document and of different documents.

#### Scenario: Ties are ordered by identifier

- **WHEN** two fragments have exactly the same distance to the question
- **THEN** the one with the smaller identifier comes first on every execution

#### Scenario: Ties across documents

- **WHEN** the tied fragments belong to different documents
- **THEN** the order still follows the fragment identifier and not the document

### Requirement: Empty result when nothing is relevant

When no fragment of the active tenant satisfies the retrieval parameters, the retrieval SHALL return an empty list and the assistant SHALL answer with the existing no-context state. The retrieval SHALL NOT fill the result with fragments that do not satisfy the parameters. The empty list SHALL be the same whether the tenant has no documents or has documents that are all beyond the maximum distance.

#### Scenario: Tenant without documents

- **WHEN** the active tenant has no stored fragments
- **THEN** the result is empty and the assistant gives the no-context answer

#### Scenario: All fragments beyond the threshold

- **WHEN** every fragment of the tenant is farther than the maximum distance
- **THEN** the result is empty and the assistant gives the no-context answer

### Requirement: Tenant isolation in retrieval

Every retrieval SHALL return only fragments of the active tenant, with or without a maximum distance and including ties and empty results. The tenant filter SHALL apply to the same read snapshot as the ranking.

#### Scenario: Closer fragment of another tenant

- **WHEN** another tenant has a fragment closer to the question than any fragment of the active tenant
- **THEN** that fragment is never returned and does not affect the order or the count

### Requirement: Compatibility between query and stored vectors

At startup the backend SHALL compare the dimension declared by the stored embedding column with the dimension of its embedding provider and SHALL refuse to start with a fixed message when they differ, indicating that the corpus must be re-indexed into a new collection. On every query the backend SHALL verify the dimension of the question vector before searching and SHALL consider only stored vectors whose `provider` equals the configured provider.

#### Scenario: Column dimension differs

- **WHEN** the stored column has 8 dimensions and the provider has 1536, or the reverse
- **THEN** startup fails with the fixed message and no query is executed

#### Scenario: Question vector of the wrong length

- **WHEN** the provider returns a vector whose length differs from the configured dimension
- **THEN** the search is not executed and an invalid provider response is reported

#### Scenario: Mixed providers in the index

- **WHEN** the index holds vectors of provider `mock` and of provider `litellm` with the same dimension
- **THEN** only the vectors of the configured provider take part in the ranking

#### Scenario: Model change with the same dimension

- **WHEN** the model alias changes and the dimension does not
- **THEN** the change is not detected by this requirement and the limit is documented in the design and the findings

### Requirement: Sanitized failures

Failures of the embedding provider and of the vector store SHALL be reported to the caller as a 503 response with a fixed body that contains no text from the upstream service, from the database or from the question, and no credential. Authentication and rate-limit failures of the provider SHALL also be reported as a 503 to the caller. The failure category SHALL be logged.

#### Scenario: Provider timeout

- **WHEN** the gateway does not answer within the timeout and the retries are exhausted
- **THEN** the caller receives the fixed 503 body and the log records the `timeout` category

#### Scenario: Provider rejects the key

- **WHEN** the gateway answers 401 or 403
- **THEN** the caller receives the same fixed 503 body and the log records the `authentication` category, not the key

#### Scenario: Vector store unavailable

- **WHEN** the database raises an error during the search
- **THEN** the caller receives the fixed 503 body and no database message, query or connection data is exposed

#### Scenario: Provider failure combined with an empty tenant

- **WHEN** the provider fails and the tenant has no fragments
- **THEN** the response is the fixed 503 and not the no-context answer

### Requirement: Retrieval traceability

Each retrieval SHALL emit one structured log event with the correlation identifier, tenant, the identifier of the stored user message, fragment and document identifiers, distances, `top_k`, maximum distance, number of results, duration, provider and alias. The event SHALL NOT include the text of the question or the content of any fragment. Counters for empty results and for failures by category SHALL use only the fixed set of categories as label values.

#### Scenario: Event without content

- **WHEN** a retrieval completes with results
- **THEN** the event lists the identifiers and distances and contains neither the question nor any fragment text

#### Scenario: Question located through the message identifier

- **WHEN** someone investigates a retrieval event
- **THEN** the identifier of the stored user message in the event is enough to find the question in the conversation, under the tenant and user access rules, without the question being copied into the log

#### Scenario: Bounded metric labels

- **WHEN** failures with different upstream messages occur
- **THEN** the failure counter only ever shows labels from the fixed category set

### Requirement: Parity between backend and processor

A test SHALL fail when the backend and the processor disagree on the embedding model alias, the embedding dimension or the set of provider failure categories.

#### Scenario: One service changes alone

- **WHEN** the alias, the dimension or a failure category changes in only one of the two services
- **THEN** the parity test fails and names the differing value

### Requirement: Contract tests without network

The retrieval contract SHALL be testable without network and without cost by a deterministic test provider that returns similar vectors for texts that share words. The continuous integration SHALL NOT call the real embedding provider.

#### Scenario: Shared words are closer

- **WHEN** two texts share most of their words and a third shares none
- **THEN** the test provider places the first two closer to each other than to the third, and gives the same vector for the same text on every call
