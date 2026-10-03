# JUP-023: validation in progress

- Date: 2026-10-02.
- Branch: `feat/JUP-023-litellm-openrouter`.
- Base/HEAD: `5a54ce2ed9001dfb9d4b9d8e06eae84cffe91124`; tests cover the
  uncommitted working-tree implementation, not an immutable delivery commit.
- [Trello](https://trello.com/c/O8elKkm9),
  [OpenSpec](../../openspec/changes/jup-023-litellm-openrouter/tasks.md),
  [version decision](../adr/ADR-0016-litellm-version-pin.md).
- Executor: automated local checks. These are not human review or validation.
- Overall result: **LOCAL TECHNICAL QA PASS**. Real smoke, budget correction and
  technical review passed; final human approval and human reviews remain pending.
  The final isolated run completed chat, embeddings and pgvector persistence.
  Earlier failures remain recorded below; success is not a reliability claim.
- Real-provider gateway requests: eight chats, three embeddings, zero retries.
  Latest official aggregate usage: USD 0.002591548, including prior attempts.
  The smoke used real LiteLLM/OpenRouter and pgvector with SQLite job state,
  not a full RabbitMQ/CockroachDB deployment. No PR or closure is implied.

## Scope and process

The processor uses stdlib HTTP adapters for chat and 1536-dimensional embeddings,
preserving FinOpsResponse 1.0, mocks and existing unrelated error handling.
Provider failures remain typed through ingestion and are rejected without
indefinite queue retries. No web chat, retrieval or cost tools are implemented.

Current CONTRIBUTING plus the user-adopted local process
`2026-09-30 (JUP-100)` apply; adoption is not evidence of remote enforcement.
Export assignments: Paris leadership, Victor pairing, Alejandro review, Lucia
validation. Actual participation and the separate `Revision JUP-023` and
`Validacion JUP-023` reviews remain pending. No PR, merge, archive or tracker
update was performed. The user's mandatory real-smoke-before-PR condition holds.

## Offline checks

The earlier processor test environment was reused without new dependencies.
The earlier 433/57 regression and gateway mutation replays used
host Python **3.10.11**, confirmed from the recorded executable. The previous
3.12 attribution was incorrect; these runs do not establish Python 3.12 parity.
The gateway container's interpreter is separate from the host test runner.
Commands below run from `apps/processor`, with service opt-ins unset and no
dotenv loaded by the tests:

```text
python -B -m pytest -p no:cacheprovider tests/test_ai_settings.py tests/test_agent_runtime.py tests/test_embedding_pipeline.py tests/test_ingest_task.py tests/test_worker_tracing.py tests/test_secret_boundaries.py tests/test_tenant_isolation_malformed_queue.py -q --tb=short
python -B -m pytest -p no:cacheprovider tests -q --tb=short
```

Initial baseline: 91 passed, 5 skipped in the focused selection. Test-first Red:
97 passed, 23 failed, 6 skipped; gateway configuration 6 passed, 1 failed.
After implementation and correcting a test-source-literal false positive in the
traceback privacy assertion: focused 120 passed, 6 skipped; full processor
433 passed, 56 skipped before adding the opt-in Docker test. These counts overlap
and must not be summed. Skipped real-service tests are not credited as passes.
After the Docker fixture and console-logging correction, the complete processor
suite was rerun with a unique temporary directory: **433 passed, 57 skipped**,
exit 0, 11.43 seconds. The additional skipped case is the explicit Docker opt-in;
its integration results are recorded separately below. After the callback
correction, the processor suite passed again: **433 passed, 57 skipped**,
exit 0, 11.61 seconds. These counts overlap the earlier runs, not additional cases.

An isolated, marked, in-memory CockroachDB node also ran `tests/test_ingest_task.py`:
12 passed, zero skipped. The new terminal-provider case was repeated for SQLite
and CockroachDB: 2 passed, 10 deselected. The node was removed after testing;
shared data and clocks were not changed. This is not an OpenRouter or pgvector
integration result.

Eight targeted in-memory mutations were detected: retry cap, authentication
retry, redirect following, boolean vector acceptance, output-guardrail error
classification, provider-error type preservation, queue requeue, and prompt/key
logging. The test executor reported 8/8 detected with no setup/collection errors.
Those mutation runs have transcript receipts, not a saved replay script; a
fully replayable mutation artifact is not claimed here.

Repository checks (root):

| Command | Result |
| --- | --- |
| `node --test tools/llm-gateway-config.test.mjs` | 7 passed |
| `node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs` | 24 passed |
| `node tools/jup-check.mjs --all` | Passed, 9 active changes |
| `node tools/jup-cleanup-check.mjs` | Passed at 727 files, including the focused review artifact |
| `corepack pnpm openspec:validate` | 37 passed, zero failed after the correction evidence was added |
| `git diff --check` | Passed |

No full frontend/backend regression or remote CI is claimed for this change.

## Reproducible simulated gateway

The single opt-in test is
[`test_litellm_docker.py`](../../apps/processor/tests/test_litellm_docker.py), with
[`litellm_fake_upstream.py`](../../apps/processor/tests/fixtures/litellm_fake_upstream.py).
It creates a unique Compose project, synthetic keys, an internal-only Docker
network, LiteLLM and its own plain PostgreSQL. It reads no root `.env` and
overrides all model upstream URLs to the simulated service. It cleans its own
containers, networks and volumes and retains sanitized receipts in TEMP.

Images:

- LiteLLM: `ghcr.io/berriai/litellm@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd`.
- PostgreSQL: `postgres:17-alpine@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24`.

PowerShell replay from `apps/processor` using the existing Python environment:

```powershell
$env:JUP023_DOCKER_FAKE = '1'
Remove-Item Env:PROCESSOR_COCKROACH_TEST_URL -ErrorAction SilentlyContinue
$testTemp = Join-Path ([IO.Path]::GetTempPath()) ('jup023-pytest-' + [guid]::NewGuid().ToString('N'))
python -B -m pytest -p no:cacheprovider tests/test_litellm_docker.py -q -s --tb=short --basetemp=$testTemp
```

Docker Desktop did not publish the gateway port on the internal-only network.
The fixture uses a loopback HTTP relay over `docker exec` to the real gateway;
it does not enable Internet access or replace gateway responses. Direct
host-to-published-port access is not demonstrated by this run.

## Initial defect and historical results

Initial run: 1 passed in 49.56 seconds, but the privacy assertion omitted
upstream error bodies. Replaying the expanded assertion against the recorded
logs revealed the defect; that initial green is **not** an overall privacy pass.

With the supported `LITELLM_LOG=CRITICAL` setting, the corrected test ran again:
**1 failed, zero skipped, 49.59 seconds**. A preceding attempt failed during
pytest temporary-directory setup and never started Docker; using a unique
`--basetemp` resolved that local test-environment issue.

| Acceptance check | Observed result |
| --- | --- |
| Internal network; health without model calls | Passed |
| Restricted virtual key creation | Passed |
| Chat through actual adapter and FinOpsResponse guardrails | Passed, simulated answer |
| Embeddings | Passed, 1536 finite numbers from simulated upstream |
| ZDR, data-collection denial and fallback denial | Observed on outgoing chat/embedding requests; upstream enforcement not tested |
| Strict response schema | Observed on outgoing chat request |
| Invalid key and disallowed secondary alias | Rejected without upstream calls |
| 429 and 503 retry bounds | Exactly 3 upstream requests per failing operation |
| Container-log content protection after CRITICAL | No checked prompt, response, error or key sentinel found |
| Spend tracking retained | 10 spend rows |
| Spend database content protection | **FAILED: upstream error sentinel retained** |
| Owned-resource cleanup | Passed; no containers, networks or volumes left |

Without the corrective callback, the content-logging flags do not prevent arbitrary upstream error text
from entering SpendLogs. Raising the console threshold fixes only the console
path and reduces gateway diagnostics. Processor sanitized technical logs and
spend tracking remain enabled. This is an in-scope integration blocker, not a
deferred exception. Its correction and bounded validation follow below.

Read-only inspection of the pinned image located the retained text at
`LiteLLM_SpendLogs.metadata.error_information.error_message`.
`litellm_settings.redact_messages_in_exceptions` removes appended request
messages but does not replace the arbitrary upstream `error_str` on this path.
The supported `general_settings.disable_error_logs` returns before storing
failure rows; it is not selective redaction. Successful spend tracking remains,
but recovered costs for some charged failures would not be written by that
hook. It has **not** been enabled or tested here. Changing version is not yet
shown necessary. Any proposal to omit these rows must explicitly account for
charged failures using authoritative upstream usage and limits; do not treat
missing gateway failure spend as zero or as a complete budget ledger.

Local diagnostic receipts: `jup023-docker-fake-qjkraz9z/receipt.json` and
`log-privacy-replay.json` for the initial run; corrected replay
`jup023-docker-fake-vktvlm5c/receipt.json`, all below the executor's TEMP directory.
These are local receipts, not shared repository artifacts or permanent links.

## Failed-call preservation correction

Paris approved retaining failure records while sanitizing arbitrary upstream
text. The public `async_post_call_failure_hook` replaces free-form exception
messages before the database callback reads the same object. The gateway retains
success/failure accounting; `disable_error_logs` is not enabled. The callback
does not modify known usage/cost fields, identities, status or timing.

The pinned-image loader probe observed the configured callback before
`_ProxyDBLogger`. A separate call to `proxy_server.initialize()` without the
module raised `ImportError` while the model router remained unset. These were
initializer probes with networking disabled, not HTTP startup-rejection tests;
their commands/results were captured in the local execution transcript.

| Check | Result and boundary |
| --- | --- |
| Stronger Red, before callback | 1 failed, 50.28 s; rows retained but private error markers persisted |
| Actual gateway with callback | 1 passed, 49.58 s; 2 success and 8 failure rows retained; no checked private markers in complete DB rows or console |
| Failure details retained | Three 429, three 503, one denied alias and one invalid key; unique IDs, model/class, timestamps and finite duration retained |
| Known usage retained | Chat tokens 5/10/15 and embedding tokens 5/0/5 |
| Callback removed in temporary config | Detected: 1 failed, 49.64 s, specifically SpendLogs privacy; all 10 rows retained |
| Traceback flag removed, HTTP replay | Survived: 1 passed, 49.16 s; this replay does not independently prove the flag necessary |
| Direct real `spend_log_error` helper at ERROR | Control exit 0; flag-removal mutant exit 1, detecting synthetic error/traceback leakage without discarding the log event |
| Direct callback metadata preservation | Synthetic cost 0.125, tokens 17/23/40, status 503, model, ID and duration unchanged; not evidence of real billing or DB cost recovery |
| Cleanup | All owned resources removed for the integration runs |

The two focused mutations are covered by complementary checks, not two successful
HTTP mutation detections. No new pytest cases were added for this correction.
The reproducible helper probe is
[`litellm_callback_probe.py`](../../apps/processor/tests/fixtures/litellm_callback_probe.py).
For the gateway mutation replay, set `JUP023_CALLBACK_MUTATION=no_callback`
or `tracebacks` before the existing Docker test command, and unset it afterward.
The probe runs without network or credentials:

```powershell
$repo = (Get-Location).Path
$image = 'ghcr.io/berriai/litellm@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd'
docker run --rm --network none --entrypoint python --mount "type=bind,source=$repo/infra/litellm/safe_logging.py,target=/fixture/safe_logging.py,readonly" --mount "type=bind,source=$repo/apps/processor/tests/fixtures/litellm_callback_probe.py,target=/fixture/probe.py,readonly" $image /fixture/probe.py
```

Run that command from the repository root. Append
`--without-traceback-suppression` for the expected failing mutation.
Local receipts under the executor's TEMP directory:
`jup023-docker-fake-9av6qf8y`, `jup023-docker-fake-q50fnu0n`,
`jup023-docker-fake-oervh_nf`, `jup023-docker-fake-zpszdr23` (each `receipt.json`),
and `jup023-traceback-helper-{baseline,mutant}-20261002.json`.
These local files are not durable shared links; the observations above and
versioned test/probe provide the portable evidence and replay instructions.

Source inspection supports traceback suppression before DB error metadata.
The direct helper test demonstrates logging suppression at ERROR, not that DB
path. The README now distinguishes these facts from the surviving HTTP mutant.
Runtime callback exceptions remain fail-open in LiteLLM; this correction is not
a circuit breaker. A failing callback/privacy check blocks real use. Zero or
missing gateway failure spend does not prove zero upstream charges.

The focused technical review found no blocking implementation defects; its
documentation clarification and pending delivery gates are recorded in
[review.md](../../openspec/changes/jup-023-litellm-openrouter/review.md).
Focused QA passed with the expressly approved documentation-recovery exception.
It checked evidence coherence and 16 local links, without changing product or
tests. Its nonblocking environment-attribution observation is corrected above.

## Python 3.12 and key-control continuation

On 2026-10-02 the existing suite ran in a separate temporary environment using
**CPython 3.12.13**: **433 passed, 57 skipped, 330 warnings, 28.68 s, exit 0**.
The warnings concern deprecated SQLite date/datetime adapters. No new pytest
cases or repository changes were required. An existing managed runtime and 61
dependencies from the offline cache were used; requirements came from the same
`requirements-dev.txt` as CI. This demonstrates the CI Python minor version,
not an identical environment: Windows/uv offline instead of Ubuntu/pip,
unlocked dependencies and third-party pytest plugin autoload disabled.
Only an OS environment allowlist was inherited; secrets, service opt-ins and
dotenv were excluded. Commands, from the repository root (temporary paths
stand for the operator-owned test environment and evidence directory):

```text
uv venv --offline --python <existing-python-3.12> <temporary-venv>
uv pip install --offline --python <temporary-venv-python> -r apps/processor/requirements-dev.txt
```

From `apps/processor` with `PYTHONDONTWRITEBYTECODE=1` and
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`:

```text
<temporary-venv-python> -m pytest tests -q -rs -p no:cacheprovider --junitxml=<temporary-evidence>/pytest.xml
```

Local receipt directory: `jup023-python312-validation` under TEMP, containing
runtime, installed versions, sanitized environment, exact command, log and XML.

The existing Docker fixture was then reused by a temporary key-control replay
under that environment. The final **live replay exited 0 with all 22 checks
true**, without adding repository tests. The three denied requests did not
reach the simulated upstream:

| Scenario | Preparation and observed result |
| --- | --- |
| Exhausted budget | Admin `POST /key/generate`, models `[economicon-chat]`, duration `10m`, max_budget `0.01`, synthetic spend `0.02`; chat returns 429 `budget_exceeded`, upstream 0 to 0 |
| Revocation | Generate key with duration `10m` and max_budget `1`; initial chat 200, upstream 0 to 1; `POST /key/delete` with that key; next chat 401 `token_not_found_in_db`, upstream remains 1 |
| Expiration | Generate key with duration `1s` and max_budget `1`; wait 2 seconds; chat returns 401 `expired_key`, upstream remains 1 |
| Privacy and cleanup | Original 10-row assertions passed; later DB snapshot had 13 rows with no checked sentinels or full keys; console privacy and owned-resource removal passed |

Every key and administration credential above was synthetic and scoped to the
disposable project. Budget spend was seeded administratively: this proves
denial for exhausted state, **not actual charge accumulation**. The later DB
query checks privacy, not complete accounting of every denied control request.
The replay polls initial asynchronous spend persistence for at most 10 seconds.
Its preceding live attempt exited 1 because a temporary assertion expected
`not found` rather than `token_not_found_in_db`; an offline receipt check alone
was not credited as a green live run. That assertion was corrected before the
successful repeat. The original receipt is retained as history.

Local artifacts: `jup023-virtual-key-controls.py` and
`jup023-virtual-key-controls-rerun-result.json` under TEMP; final Docker receipt
`jup023-docker-fake-2mfztq5u/receipt.json`; preceding failure
`jup023-docker-fake-9286g1y7/receipt.json`. Replay command was the temporary
Python 3.12 interpreter followed by `-B` and that replay file. These are local
operational artifacts, not a new versioned automated suite; the API sequence
above documents reproduction with the existing isolated gateway fixture.

## Real-use preflight, without model calls

Paris explicitly confirmed on 2026-10-02 that the team agreement on budget,
privacy and models is already reached. This records his attestation, not
invented individual GitHub reviews or an automatic change to ADR-0002 status.
The live `develop` ADR still says Proposed. PR #21 has Paris's approval and
documents Alejandro's decision; the queried PR #10/#21 discussions do not add
individual approval evidence for the other members.

Unauthenticated public catalogue queries confirmed the three configured IDs:

| Model | Public catalogue USD per million input/output tokens on 2026-10-02 |
| --- | --- |
| `z-ai/glm-5.2` | 0.41 / 3.99 |
| `deepseek/deepseek-v4-pro` | 0.2088 / 0.4176; no secondary invocation authorized by this check |
| `openai/text-embedding-3-small` | 0.02 / 0 |

Sources: [chat catalogue](https://openrouter.ai/api/v1/models),
[embedding catalogue](https://openrouter.ai/api/v1/embeddings/models).
These are catalogue prices, not a bound on routed charges: the public GLM
endpoint list had maximum input/output rates of 2.31/8.00 USD per million;
embedding endpoints both listed input at 0.02. Availability in the catalogue
does not establish compatibility with the required privacy policy at runtime.
Recheck effective pricing before the first paid request.

A read-only `GET https://openrouter.ai/api/v1/key` used the key from the ignored
root dotenv through a structured parser, sent only to that official endpoint
with redirects disabled. Only allowlisted numeric/status fields were displayed;
the key, its label/hash and other dotenv values were not printed or forwarded.
Observed twice: usage `0`, limit and remaining `10` USD, monthly reset. The key
is not a management key. This was metadata inspection, not a model invocation.

The requested test-only upstream cap is **0.40 USD total, no automatic reset**.
The [ECB reference](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml)
dated 2026-10-01 was 1 EUR = 1.1298 USD, so that cap leaves margin under EUR 0.50.
It is a cap, not planned spend or proof of real costs. The user was asked to
adjust the existing key through its management UI; the final metadata recheck
still returned the original monthly limit. No management key was requested,
no upstream setting changed by the executor, and no paid call was made.

## First real-provider smoke: failed

Paris reported that the requested key limit was set on 2026-10-02. Official
key metadata at 10:49 UTC confirmed limit USD 0.40, no reset, usage zero and
remaining USD 0.40. This resolved the earlier upstream-limit blocker.

The automated tester executed one isolated smoke on the same uncommitted
working tree, using CPython 3.12.13 and the approved LiteLLM/PostgreSQL pins.
The separate disposable vector service used
`pgvector/pgvector:pg17@sha256:cf134a767f474095eeba57e0117be8e568e011a63f33fbf252f14c9b760f8e6f`.
The existing migration initialized a new `vector(1536)` schema. Job state used
temporary SQLite with the existing repository and fixture helpers; this was
not a RabbitMQ/CockroachDB end-to-end test. No existing database was modified.

The temporary gateway configuration retained the configured models, schema,
privacy flags, callback and zero gateway retries. It restricted aliases to
the primary chat and embeddings and added price guards (USD per million:
chat input/output 2.31/8, embedding 0.02/0) and chat `require_parameters: true`.
These are test-only routing restrictions, not the unchanged repository config.
The virtual key had a verified USD 0.20 budget without reset, 10-minute expiry,
RPM 6, TPM 32768, concurrency 1 and only those two aliases.

This smoke explicitly used zero processor retries, 30 seconds and 800 output
tokens. The offline gateway transformation probe retained schema, messages,
provider settings and output limit; serialized input was 7585 bytes. A
conservative 20000-input-token allowance estimated USD 0.0526 for a single
chat at the maximum checked endpoint rates; USD 0.10 was reserved. This is a
conservative estimate, not a universal tokenizer bound. The remaining reserve
is not released on the assumption that missing failure cost means zero.

| Observation | Result |
| --- | --- |
| Execution | 2026-10-02 11:06:20 to 11:07:17 UTC; exit 1 |
| Primary chat | One gateway request; HTTP 400 after 10464.43 ms; local `ProviderError`, category `request` |
| Following operations | No retry, no embedding request, no completed pipeline or persisted real vector |
| Official accounting | Initial and final key usage zero; follow-up GET at 11:09:50 UTC still usage zero, remaining USD 0.40, reset null |
| Privacy | Checked container-log secrets/content markers absent; no raw error body retained |
| Cleanup | Virtual key revoked; temporary secret file removed; owned containers, networks and volumes removed; no test process left running |
| Boundaries | Tester and targeted diagnostic reviewer guards passed, zero repository edits |

Replay command (local temporary operational script, not a versioned suite):

```text
C:/Users/Trabajo/AppData/Local/Temp/jup023-python312-validation/venv/Scripts/python.exe -B C:/Users/Trabajo/AppData/Local/Temp/jup023-real-smoke-execution.py
```

Local receipts: `jup023-real-smoke-kfsgz3wr/receipt.json`,
`jup023-real-smoke-execution-result.json`,
`jup023-real-smoke-execution-guard.json` under TEMP. They are not shared durable
links; the observations and configuration above are the portable record.

The targeted read-only review did not establish the cause. HTTP 400 and elapsed
time alone cannot distinguish gateway validation from an upstream rejection.
The temporary routing restrictions are a candidate, not a proven defect.
The smoke runner asserted success before exporting SpendLogs, so failure
metadata was not retained before disposable-volume cleanup. This is a gap in
the temporary test procedure, not evidence that the product deletes failed
records. Original error text was sanitized and is not recoverable from the
retained artifacts. No provider class, code or parameter can be claimed.

Proposed follow-up: preserve allowlisted failure metadata before cleanup and
verify a temporary diagnostic classifier offline before another real request.
Emit fixed rejection categories, validated numeric status and allowlisted
exception class only; never raw exceptions, bodies, credentials or tracebacks.
Keep existing sanitization unconditional and models/privacy/schema unchanged.
This was the proposal after the first run; the authorized follow-up is below.

## Authorized single-call diagnosis

Paris explicitly authorized one additional diagnostic call on 2026-10-02,
within the same aggregate budget. A temporary classifier was checked in the
pinned image without network: two synthetic cases passed (recognized schema
error and unknown error), with private markers absent, exception unmodified
by classification and the existing sanitizer executed afterward in both cases.
No permanent tests or product changes were added.

The second isolated run used the same models, schema, privacy and temporary
price/routing restrictions as the first. Its only additional gateway callback
classified errors before the unconditional existing sanitizer. One chat was
attempted, zero retries and zero embeddings. It ran from 11:26:55 to 11:27:56 UTC
and exited 1: HTTP 400 after 2958.79 ms, `BadRequestError`.

The emitted category was `request_parameter`, matched rule
`parameter_validation_marker`, parameter/code `unknown`. That rule also
matches the generic `invalid_request_error` marker and does not retain which
alternative matched. Therefore the defensible conclusion is **HTTP 400 with a
broad request-error marker; cause unknown**, not a confirmed invalid parameter.
The OpenRouter provider label does not prove upstream contact or rejection
origin. No raw exception, body, header or traceback was retained.

The temporary runner now exports allowlisted failure metadata before cleanup:
one SpendLogs failure, `BadRequestError`, status 400, tokens 14/0/14, spend 0,
recorded duration 2798 ms. Privacy checks passed for the checked markers.
This addresses the previous missing failure-export observation for this run.
Those gateway token/spend fields are not proof of actual model execution or
final charges. Official usage was zero during bounded settling and remained
zero in the post-cleanup GET at 11:29:15 UTC: remaining USD 0.40, no reset.
Both USD 0.10 reservations remain conservatively accounted for (USD 0.20 total);
reservations are not recorded charges or additional spend authorization.

The virtual key was revoked, the secret file removed and all owned containers,
networks and volumes removed. No test process remains. Tester and targeted
read-only review guards passed without repository changes; the review confirmed
the classification limitation above. This is not final full-change QA.

Replay command: the same temporary Python interpreter and runner as above,
with `--diagnostic-single-call`. Local TEMP receipts:
`jup023-diagnostic-offline-receipt.json`,
`jup023-real-smoke-nnb4bg9i/receipt.json`,
`jup023-diagnostic-single-call-result.json`,
`jup023-diagnostic-single-call-settled-key.json` and
`jup023-diagnostic-single-call-guard.json`. No further model call is authorized
by the single-call approval. Do not repeat requests blindly or weaken
models/privacy/schema to obtain a green smoke.

## Repair investigation and diagnostic permission

Paris subsequently requested fixing the unresolved integration. A full isolated
gateway-to-synthetic-upstream replay passed ten wire checks with no external
credentials or model spend: model, complete schema, one user message, output
limit, privacy/routing/reasoning parameters and upstream-only credential were
preserved; no nested `extra_body` remained. The wire was 7602 bytes. This checks
serialization, not acceptance by OpenRouter or its model endpoints. Local
receipts: `jup023-wire-replay-result.json` and
`jup023-docker-fake-ggdclqnl/wire.synthetic.json` under TEMP.

A temporary nested-JSON diagnostic was checked on three synthetic cases and
used for one further bounded chat request. It extracted `invalid_request_error`
and an isolated `type` token, but no specific restriction or numeric limit.
That token does not identify the offending field. The request again returned
HTTP 400; zero retries or embeddings. Gateway request ID:
`9a0e5880-8418-4ca4-83f9-7a91417e8309`. No concrete cause or product fix is
established. Official usage remained zero, remaining USD 0.40 without reset;
aggregate conservative reservations are USD 0.30, not actual charges. The
virtual key, secret file and owned runtime were cleaned up, and the tester
guard passed. Local receipts: `jup023-real-smoke-92dmzt4q/receipt.json`,
`jup023-fix400-nested-live-result.json` and
`jup023-fix400-nested-live-guard.json` under TEMP.

Because fixed-category diagnostics still discard the technical explanation,
the executor explicitly requested permission to inspect a temporary technical
error message after removing secrets, credentials and request content, within
the same EUR 0.50 ceiling and without changing product logging. That permission
was subsequently granted by Paris ("autorizado"); the preparation below alone
did not authorize consumption. The resulting bounded run is recorded next.

The temporary sanitizer preparation passed six offline checks, exit 0, including
nested message extraction, known-secret/payload removal, rejection of partial
echoes and unconditional sanitizer invocation in a stub `finally` probe. This
does not establish integration of the new diagnostic with the real gateway.
Artifacts are `technical_message.py`, `receipt.json` and `handoff.json` in
TEMP `jup023-sanitized-message-prep`. No dotenv read, external call, repository
code/test edit or live process in this preparation; role guard passed.
These operational probes are not new permanent suites or successful validation.

## Technical cause captured with explicit permission

The authorized temporary technical-message capture ran on 2026-10-02 from
12:22:52 to 12:23:50 UTC. One chat request returned HTTP 400 after 981.53 ms;
zero retries and embeddings. The sanitized error identifies `ExportLimitError`:
depth-bounded grammar unrolling exceeded 262144 intermediate states on the GLM
server. This establishes the reported rejection mechanism, not which construct
caused it, an invalid JSON Schema, or a proven repair. Do not generalize this
explanation to the earlier failures whose technical messages were not retained.

The original production sanitizer and logs were unchanged. Checked private
markers were absent from SpendLogs and console; one failed-call row was retained
before cleanup (HTTP 400, gateway tokens 14/0/14, spend 0, duration 787 ms).
Those gateway fields are not evidence of model generation or final billing.
Official usage observations remained USD 0, remaining USD 0.40, no reset.
Four conservative USD 0.10 reservations now total USD 0.40; they are not charges
and have not been released. Reconcile accounting before further model calls;
do not raise caps or exceed the approved aggregate EUR 0.50 ceiling.

The virtual key was revoked, private inputs removed, and owned containers,
networks and volumes removed. No active test process remains. Tester guard and
targeted read-only reviewer guard passed with no repository changes. This is
not full-change review, final QA, successful real validation or human approval.
Local receipts: TEMP `jup023-real-smoke-rmodq40t/receipt.json`, its `handoff.json`,
`jup023-sanitized-message-live-result.json` (exit 1), and
`jup023-sanitized-message-live-guard.json`.

Proposed repair, not implemented or proven: simplify the provider-facing schema
while preserving FinOpsResponse 1.0 and all local validation. Explicitly enumerate
constraints enforced locally rather than by generation before seeking approval
for that adaptation. Do not disable structured output, substitute models or
weaken privacy/fallback policy based on the provider's suggested workaround.

## Contract-preserving follow-up

Paris asked whether schema decisions belong to JUP-023, then authorized seeking
compatibility before considering contract changes. No schema simplification is
approved. The archived [JUP-024 design](../../openspec/changes/archive/2026-09-09-jup-024-structured-response-guardrails/design.md)
explicitly assigns compatible-endpoint enforcement to JUP-023. The current
provider config fixes the model, not a specific OpenRouter serving endpoint.
Read-only spec-planner guard `contract-compatible-investigation` passed.

Public documentation/catalog inspection on 2026-10-02, without credentials or
inference, supports investigating explicit routing before rewriting the schema:

- [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
  describes endpoint-specific support; advertising support is not proof that
  this complete schema can be compiled or enforced.
- [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)
  supports `only`, `require_parameters`, ZDR, data-collection denial and disabled
  fallback. A single explicit endpoint can retain the same model and upstream.
- The [GLM-5.2 endpoint catalog](https://openrouter.ai/api/v1/models/z-ai/glm-5.2/endpoints)
  lists `deepinfra/fp4` with response_format/structured_outputs, status 0 and
  reported prices USD 0.5625 input / 1.8 output per million tokens. These are
  dated catalog values, not invoices or a cost authorization. Its precision is
  FP4; there is no retained identity/precision for the failed endpoint to compare.
- [DeepInfra documentation](https://docs.deepinfra.com/chat/structured-outputs)
  describes strict json_schema mode, but does not establish acceptance of this
  particular schema. No live compatibility claim is made.

Candidate test configuration, not applied: add `only: [deepinfra/fp4]` and
`require_parameters: true` for the primary chat alias, preserving all existing
privacy flags, schema, model, 30-second timeout, 800-token ceiling and disabled
gateway retries. Secondary chat and embeddings stay unchanged. If routing cannot
satisfy privacy, fail rather than relax it. Exact endpoint ZDR eligibility has
not been verified: the public model response has no such field; the documented
[ZDR preview](https://openrouter.ai/docs/api/api-reference/endpoints/preview-the-impact-of-zdr-on-the-available-endpoints)
requires authentication and documents a management-key restriction. No key was
read or new credential requested during this investigation.

Prefer this candidate evaluation to removing schema constraints. First agree
the endpoint selection and reconcile held reservations; then reuse focused
transport tests and the real smoke. No product edits, new tests, Docker runs,
paid model calls, release of reserves or final QA occurred in this follow-up.

## Approved DeepInfra evaluation

Paris approved `deepinfra/fp4` through OpenRouter. Only primary chat gained
`only` and `require_parameters`; model, complete schema, privacy, secondary and
embeddings are unchanged. Spec-planner and coder guards passed. Existing tests
were extended with zero new permanent cases for this amendment.

RED: `node --test tools/llm-gateway-config.test.mjs`, exit 1, 6 passed / 1 failed
for missing routing. GREEN: same command, exit 0, 7 passed. Existing Docker
test passed in 57.05 s, 19 checks true, complete schema preserved, 10/10 SpendLogs
rows and checked privacy retained. Its earlier RED run saw 8/10 rows at a fixed
three-second read; that additional failure did not recur, but timing versus
another cause is not established. No wait change or assertion weakening.
Removing `only` and, separately, `require_parameters` in temporary copied config
was detected by the existing Node test. Both mutants detected; baseline 7 passed.
Receipts under TEMP: `jup023-docker-fake-5h9uzm5f/receipt.json`,
`jup023-deepinfra-mutants-fK2wHi/receipt.json`,
`jup023-real-smoke-hcb1sycv/handoff.json` (exact replay commands).

Preflight authenticated GETs confirmed cap USD 0.40 without reset, zero usage,
exact endpoint and ZDR-list membership. Four old USD 0.10 reservations were
operationally reconciled against zero using four terminal 400s, no auxiliary
services, official usage zero 43-120 minutes later and the official
[zero-completion policy](https://openrouter.ai/docs/guides/features/zero-completion-insurance).
Not missing cost alone or per-generation final invoices. No cap increase.
Receipt: TEMP `jup023-deepinfra-preflight-qvk105k5/receipt.json`.

Three subsequent real attempts used the original prompt/schema, 30-second model
timeout, 800-token ceiling and zero retries. Each runner exited 1:

| TEMP receipt directory | Result | Official usage increment (USD) |
| --- | --- | --- |
| `jup023-real-smoke-hcb1sycv` | Chat 200 in 5594.37 ms; temporary accounting wait expired before local validation. Cost reconciled after stopping. | 0.000816187 |
| `jup023-real-smoke-y95aqk4a` | Chat 200 in 4111.98 ms; cost reconciled after 14.859 s; local validation rejected output. Exact rule not retained. | 0.000576547 |
| `jup023-real-smoke-jfoy9oe0` | Chat 200 in 6141.5 ms, full local validation passed; embedding 200 in 441.77 ms, 12 input tokens, both cost fields absent. Stopped before vector validation/persistence. | Chat 0.000599947; later 0.000000240 consistent with embedding, attribution inferred. |

The accounting wait was bounded at 90 seconds after the first stop; product
timeouts were unchanged. The last run recorded only safe local validation
metadata, no responses: types, known field locations, static-rule categories
and finish reason. Temporary offline probes: 7/7 before the call; 11/11 after
expanding static-rule mapping. One valid response does not explain the earlier
invalid one or demonstrate output reliability. No further model calls were made.

Exact commands/configuration/times in each directory's handoff and receipt;
runtime was the existing TEMP Python 3.12 with `-B`, running respectively
`jup023-deepinfra-real-smoke.py`, `jup023-deepinfra-settling-smoke.py`,
`jup023-local-validation-smoke.py`. Latest read-only usage reconciliation:
`jup023-real-smoke-jfoy9oe0/accounting-settled.json`, total USD 0.001992921.
Conservative USD 0.10 reservation held, not an additional charge. Both approved
ceilings remain unchanged. Virtual keys revoked, secrets/owned runtime removed,
no active test processes; privacy checks and tester guards passed.

Next: support verifiable official accounting when embedding cost fields are
absent in the temporary smoke, then demonstrate actual 1536-dimensional vector
persistence. Do not fabricate zero cost or weaken the budget gate. No product
schema change, response repair, fallback, publication or full-change QA.

## Successful real smoke and accounting

Paris authorized continuing the temporary accounting repair and bounded real
test. No product, prompt, schema, model or privacy changes were made. Temporary
offline probes passed 8/8, including delayed accounting and fail-closed missing,
zero and unmatched cost observations. Decimal reconciliation used USD 0.000000001
tolerance, smaller than the observed embedding charge. Existing suites were not
rerun merely for this temporary repair.

On 2026-10-02, 13:52:56-13:54:41 UTC, the existing Python 3.12.13 environment ran:

```text
python -B %TEMP%/jup023-embedding-accounting-smoke.py
```

Exit 0. Full command, sanitized configuration and receipts are retained locally
in TEMP `jup023-real-smoke-hiku3zy0/receipt.json` and `handoff.json`; offline
probe receipt is `jup023-micro-accounting-offline.json`. These temporary runners
are not portable versioned test suites. Tested working tree and base are the
header revision; no delivery commit was created.

| Criterion | Observed result |
| --- | --- |
| Real primary chat, original full strict schema | HTTP 200, 4464.28 ms, 539 input / 294 output tokens; original local guardrails passed, FinOpsResponse 1.0, `insufficient_data`, finish reason `stop` |
| Real embedding and dimensions | HTTP 200, 550.01 ms, 12 input tokens; original provider validated a finite 1536-dimensional vector |
| Processor persistence | Original runtime, pipeline and ingestion path completed; one vector in real disposable pgvector; job `completed` in disposable SQLite |
| Routing and limits | Same GLM-5.2 via `deepinfra/fp4`, same embedding model, ZDR/deny/no fallback; 30 s, 800 output tokens, zero retries; no secondary call |
| Privacy and cleanup | Two SpendLogs rows preserved and checked; logs/content private within tested assertions; virtual key revoked, secret inputs and all owned containers/networks/volumes removed; zero active test processes |

Real accounting was sequential and reconciled before releasing the response to
the original validators. Chat reported USD 0.0005981475; official key usage
increased USD 0.000598147 after 29.609 s. The observed chat generation ID returned
404 from metadata, so it was not used as invoice evidence. Embedding supplied
neither cost nor a generation ID; no ID was guessed. Official key usage increased
USD 0.000000240 after 14.938 s, matching 12 observed tokens at the freshly checked
USD 0.00000002/token price. This is **aggregate attribution inferred**, not a
per-generation invoice and not a cost estimate alone.

Attempt charge from official aggregate usage: USD 0.000598387. Previous aggregate
USD 0.001992921 plus this attempt equals **USD 0.002591308**. Three final official
observations agreed. Conservative reservations were reconciled against actual
usage, not treated as charges or released merely for absent cost fields. Upstream
cap remains USD 0.40 without reset; remaining USD 0.397408692. The EUR 0.50 approved
ceiling and disposable virtual-key USD 0.20 cap were not raised.

Accounting limitation: the gateway's embedding SpendLogs row recorded `spend: 0`
despite the positive official upstream increment. Therefore this smoke does not
prove that the virtual-key monetary budget accounts for embedding charges; the
upstream cap and sequential official reconciliation bounded this test. Do not
report missing gateway cost or its zero as free usage. This discrepancy must be
assessed in full technical review before declaring the delivery ready.

Tester boundary check `embedding-accounting-smoke` passed with zero repository
changes. No raw response or secrets are copied into this evidence. Earlier
invalid output and the non-reproduced 8/10-row observation are retained; one
successful full smoke does not establish provider reliability or explain them.

## Embedding budget correction

Paris explicitly approved the proposed correction on 2026-10-02 after confirming
that USD 0.02 per million input tokens is a price, not the key budget. Only the
embedding deployment adds `model_info` rates (USD 0.00000002 input/token, zero
output) and `provider.max_price.prompt: 0.02` USD/million. Same models, schema,
dimensions, privacy, image and budgets. README records pricing maintenance and
derived-cost limitations; no new SDK, billing service or permanent test cases.

Existing tests were extended rather than adding cases. RED: Node 5 passed / 2
failed; Docker 1 failed in 89.43 s, zero spend after two embeddings and a third
HTTP 200 reaching the upstream. Receipt: TEMP `jup023-docker-fake-utj18mdy`.
Configuration GREEN: `node --test tools/llm-gateway-config.test.mjs`, 7 passed.

First Docker replay after configuration: 24/25 checks, 1 failed in 74.06 s.
SpendLogs and the virtual counter were positive and the third call was rejected,
but the test searched the deliberately sanitized message for budget text.
Receipt: TEMP `jup023-docker-fake-5pq67rlk`. Source inspection of the pinned image
confirmed that auth conversion preserves structured `error.type=budget_exceeded`.
The existing test now requires that exact type, a denial status and no upstream
increment; it does not infer budget exhaustion from HTTP 429 alone. No raw error
body/message is retained and no privacy control was changed.

Final simulated replay (Python 3.12.13, same existing Docker opt-in command above):
**1 passed, zero skipped, 66.03 s; 25/25 checks**. From zero, two 12-token embeddings
each accrue USD 0.000000240; the actual key counter becomes USD 0.000000480 against
a USD 0.000000360 test cap. The third request returns HTTP 429 with structured
`budget_exceeded`; upstream count stays 2. No spend was seeded. Ten original
SpendLogs rows and two budget-test rows remain, with privacy checks passing.
Accounting is asynchronous and denial occurs after accrual; this does not prove
an atomic reservation or that a final/in-flight call cannot exceed a virtual cap.
Receipt: TEMP `jup023-docker-fake-gkkzge27/receipt.json`.

Two mutations of TEMP copied configuration were detected by the existing Node
suite: remove embedding rates; remove embedding price ceiling. Baseline 7/7,
each mutant exit 1, no mutation left in the product. Receipt and replay command:
TEMP `jup023-embedding-budget-mutants-zoC3vJ/receipt.json` and
`node %TEMP%/jup023-embedding-budget-mutants.mjs`. No broad mutation score claimed.

The approved real replay used:

```text
python -B %TEMP%/jup023-embedding-budget-smoke.py
```

On 2026-10-02 15:06:51-15:07:46 UTC it exited 0 with **exactly one embedding,
zero chats and zero retries**. HTTP 200, 720.66 ms, 12 input tokens; original
adapter validated a finite 1536-dimensional vector. SpendLogs, the actual virtual
counter increment (zero to USD 0.000000240), and the positive official key-usage
delta all agree. Official accounting settled after 18.453 s (9 observations).
No generation ID was supplied or guessed: this is configured derived pricing
corroborated by aggregate usage, not an individual invoice. Persistence/chat
were not rerun; their original successful smoke remains the applicable evidence.

Before this request, a TEMP child-settings preparation failed with zero model
calls and zero new usage; it was corrected and exercised with a synthetic client
before proceeding. That receipt is preserved at TEMP
`jup023-embedding-budget-live-q4wmi73s/receipt.json`. Successful receipt:
`jup023-embedding-budget-live-0j6d3yy1/receipt.json`; complete sanitized commands,
environment, guard and mutation references:
`jup023-embedding-budget-denial-handoff.json`. These TEMP runners are not a
portable versioned live-test suite.

Total official usage: **USD 0.002591548**, including previous USD 0.002591308
and new USD 0.000000240. Upstream cap remains USD 0.40 without reset, remaining
USD 0.397408452. Published embedding prices and ZDR were rechecked before calling.
The dated ECB check (2026-10-02, USD 1.1225/EUR) places the entire upstream cap at
about EUR 0.35635, below the EUR 0.50 validation ceiling. Virtual key remained
limited/expiring and was revoked. Private inputs and all owned runtime resources
were removed; privacy checks passed and zero test processes remain.

Role checks `embedding-budget-red`, `embedding-budget-green`,
`embedding-budget-verification`, `embedding-budget-denial-check` and README-only
`embedding-budget-readme-result` passed. Earlier failed checks are retained, not
relabelled as success. No additional paid calls beyond the approved single
embedding replay, general regression reruns, product Python changes, publication
or human review occurred in this correction.

## Remaining gates

The mandatory real smoke and its aggregate cost reconciliation now pass within
the stated SQLite/pgvector scope. The approved accounting correction now has
simulated accrual/denial and real accrual/official-use evidence. Full review plus
affected re-review returned REVIEW_PASS, closing F1/F2 with the stated limits.
Final local technical QA returned QA_PASS, with no unresolved technical blocker.
Current-status README/design wording was corrected separately. Required human
participation and separate reviews remain pending.
No PR, push, merge, archive or tracker action is authorized by this run.
Full frontend/backend regression, full CI parity and production deployment are
not claimed; no retrieval, cost tools or web-chat connection were added.

## Final local QA

2026-10-02: QA_PASS on the header working tree, no QA edits, guard
`embedding-budget-final-qa` PASS. Acceptance mapping checked contracts/error
handling, real pipeline, privacy/routing, actual embedding accrual, simulated
budget denial, mutation sensitivity and approval/review records. Prior behavior
runs were reused where unchanged; 433 passed / 57 skipped remain their original
counts, not a new regression run. No paid call or Docker replay by QA.

Current checks: strict OpenSpec 37 passed, traceability 9 changes passed, hygiene
727 files, whitespace exit 0, and 26 local file links resolved. Local DoD at
`-Stage qa` passed. F1/F2 closed; F3 wording corrected. These checks do not prove
remote CI, human participation, GitHub approval or delivery closure.

The post-QA edits only record this verdict and update status references; tested
behavior, configuration and tests are unchanged. Final human approval remains
pending, as do the separately authorized publication/integration/tracker actions.

## Develop reconciliation

2026-10-02: Paris authorized updating local develop and incorporating it into
`feat/JUP-023-litellm-openrouter`. `git fetch origin` retrieved one new base
commit, `11d63ea03e6f8a2d19a8cace45d11c34bb9676a9` (JUP-100, PR #56).
After verifying ancestry and that develop was not checked out elsewhere,
local develop advanced from `5a54ce2ed9001dfb9d4b9d8e06eae84cffe91124`;
`git merge --ff-only develop` then advanced the task branch. No conflict,
stash, new commit, push or PR was needed. HEAD, develop and origin/develop
now identify `11d63ea`; the JUP-023 implementation remains uncommitted.

Before/after SHA256 checks matched all 29 modified or untracked files exactly.
The incoming 21 paths concern governance, review policy, its tests and OpenSpec;
none overlaps those 29 paths. Subsequent reconciliation notes only affect this
evidence, proposal.md and review.md. No product, configuration, test, secret or
runtime changes were made; no Docker or paid calls were run. The previous
behavioral evidence, including Python 433 passed / 57 skipped and the real
smoke, is reused with its original limits, not reported as a new execution.

Current process source: CONTRIBUTING.md and AGENTS.md at `11d63ea`, Process
version `2026-09-30 (JUP-100)`, now merged rather than locally adopted from an
open PR. Remote rule activation and human reviews were not verified here.
The internal incremental reviewer returned REVIEW_PASS with no new findings;
guard `develop-reconciliation-review` passed without edits. Internal incremental
QA then returned QA_PASS, with these checks on the reconciled working tree:

| Command / check | Result (exit 0) |
| --- | --- |
| `node --test tools/pr-policy.test.mjs` | 57 passed |
| `node --test tools/ci-workflow.test.mjs` | 10 passed |
| `node --test tools/repository-governance.test.mjs` | 13 passed |
| `node node_modules/@fission-ai/openspec/bin/openspec.js validate --all --strict --no-interactive` | 38 valid items |
| `node tools/jup-check.mjs --all` | 9 active changes passed |
| `node tools/jup-cleanup-check.mjs` | 736 files passed |
| `git diff --check` | No whitespace errors |
| Local Markdown targets in the three updated documents | 16 links, including 6 anchors, resolved |

Environment: Windows 11 build 26200, PowerShell 7.6.5, Node 24.17.0 and installed
OpenSpec 1.8.0. The initial `corepack pnpm pr:check:test` failed with cache EPERM;
equivalent unchanged package.json script bodies were executed directly with Node.
OpenSpec initially failed reading ora under the sandbox, then passed outside it
with telemetry disabled. No installation or environment repair was performed.
These local results are not a remote CI run or a Node 22 CI-parity claim.

QA-stage local DoD passed; guard `develop-reconciliation-qa` passed with zero
changed paths and violations. This result record only updates evidence/review
text after QA. No delivery closure, final human approval or publication is claimed.

## PR 65 HTTP Timeout Correction

2026-10-02, automated local execution for Paris (leadership). Branch
`feat/JUP-023-litellm-openrouter`, HEAD `9fe836eb8ec1c3805cda9c340a7c6e9bbf247376`
plus the uncommitted correction and five test cases. Reviewed Git blobs:
client `4175f2edfaad90e327c3c69c6b117fac565b19fc`, tests
`84a1e7bf3f25ea22fa00276c44475b420d82274a`.
Process: CONTRIBUTING/AGENTS `2026-09-30 (JUP-100)`. Victor pairs; Alejandro
reviews and Lucia validates. Internal execution is not their participation.

All PR reviews, inline comments and conversation comments were read before
addressing feedback. Both human requests remain pending:
[Revision](https://github.com/EconomiconFinOps/tfm-economicon/pull/65#pullrequestreview-5396101137)
and [Validacion](https://github.com/EconomiconFinOps/tfm-economicon/pull/65#pullrequestreview-5396552390).
Their blocking issue is the attempt timeout not covering a trickling response.
Paris explicitly approved the local correction and tests; no paid calls or push.

From `apps/processor`, with cached Python 3.12.13 and `UV_OFFLINE=1`:

```powershell
$timeoutTestTemp = Join-Path $env:TEMP ('jup023-timeout-red-' + [guid]::NewGuid().ToString('N'))
uv run --no-project --python 3.12 --with-requirements requirements-dev.txt python -B -m pytest tests/test_agent_runtime.py -k attempt_deadline -q -rs -p no:cacheprovider --basetemp $timeoutTestTemp --durations=5 --tb=short
```

Exit 1: **4 failed, 1 passed, 32 deselected in 3.82 s**. HTTP loopback sends a
byte every 0.03 s with timeout 0.05 s. Body/header cases return success after
0.453-0.454 s, rather than timeout; even with two retries only one successful
request occurs. The normal complete-response control passes. Tests require
elapsed below attempt budgets plus existing backoff and 0.15 s scheduling
slack, timeout category, exact attempt count and peer-observed transport closure.
The coder independently reproduced the same Red (0.453-0.469 s).

Paris subsequently instructed: "limitate a lo que se ha pedido en las revisiones
de la pr por favor". Implementation stays in the shared HTTP client: one
monotonic deadline, remaining budget for socket connection/TLS and every raw
read, closure on error and unchanged bounded retries. No background readers,
DNS subprocesses, new dependencies or ADR. System DNS remains synchronous and
non-cancelable; no full DNS-inclusive guarantee or reviewer acceptance of this
limitation is claimed. This scope instruction supersedes the earlier pause.

| Check after correction | Observed result |
| --- | --- |
| Focused regression | Exit 0: 5 passed, 32 deselected; repeated before/after mutations in 2.88/3.05 s |
| Full processor suite | Exit 0: 438 passed, 57 skipped, 330 deprecation warnings |
| Targeted in-memory mutations | 3/3 killed: remove raw-read deadline (4 failures), wrong timeout category (4), omit retries (2) |
| Synthetic local HTTPS success | HTTP200 in 0.016 s, certificate and hostname verified |
| Independent reviewer probes | Trickle CONNECT headers / stalled TLS: timeout and peer closure in 0.094/0.093 s for 0.08 s budget |

Green used the same pytest command above without `--durations`/`--tb`, and
`uv run --no-project --python 3.12 --with-requirements requirements-dev.txt python -B -m pytest tests -q -rs -p no:cacheprovider --basetemp <fresh-temp>`
for the full suite. The 57 skips require opt-in CockroachDB/pgvector/Docker
integrations; they are not passes. No new permanent tests beyond the five cases.
Mutation variants `reader`, `category`, `retries`, then `baseline` ran through
temporary `jup023-timeout-mutation-20261002.py` in the same offline uv environment,
compiling source replacements only inside the Python process. Product files
were never mutated on disk. The reader mutant retained the post-read clock
check, proving it alone is insufficient. Score is targeted, not exhaustive.
HTTPS probes used synthetic temporary certificates without changing a trust store.

Other observed local checks (exit 0): strict OpenSpec 38/38; traceability 9 active
changes; hygiene 736 files; gateway configuration tests 7/7; policy/CI/governance
tests 80/80; `git diff --check`. Commands: `node --test tools/llm-gateway-config.test.mjs`,
`node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs`,
`node node_modules/@fission-ai/openspec/bin/openspec.js validate --all --strict --no-interactive`
with telemetry disabled, `node tools/jup-check.mjs --all`, and
`node tools/jup-cleanup-check.mjs`. Node 24.17.0; cache/read EPERM required
authorized execution outside the sandbox, without environment repair.
Internal incremental review: REVIEW_PASS, no actionable in-scope findings.
All completed role guards passed; reviewer and mutation tester changed no files.
Incremental QA returned QA_PASS: strict OpenSpec 38/38, traceability 9, hygiene
736, whitespace and relevant links passed. Read-only guard and local QA-stage
DoD passed; reviewed product/test blobs are unchanged. This note records the
observed verdict, not a new implementation. Final human approval remains pending.
No Docker, OpenRouter, billing or Linux/macOS
run was repeated. These results do not replace remote CI, the human reviews or
functional revalidation on the published fix; prior real-provider evidence
retains its original scope and the two Requests changes remain pending.

Remote refs refreshed: origin/develop `d6fc408b60e944b726605b242f3e7a64129282c7`
contains newer JUP-050/JUP-021 work; not incorporated by this narrow authorization.
No commit, push, review publication, merge, archive, tracker update or model use.

## Real Revalidation After Timeout Correction

Paris explicitly authorized one primary chat and one embedding on 2026-10-03,
with zero retries and unchanged budget/privacy. Automated execution for leadership,
not Alejandro's review or Lucia's validation. Same branch/HEAD and client/test
blobs as the timeout correction above; no product or test changes in this phase.
The full live PR discussion was reread: both human Requests changes remain.

Execution window: 2026-10-02 23:44:32-23:46:59 UTC (2026-10-03 local date).
Python 3.12.13, Docker Desktop `desktop-linux`, owned project
`jup023-real-0cacba48da`, approved pinned gateway/PostgreSQL images. Command:
`<TEMP>/jup023-python312-validation/venv/Scripts/python.exe -B <TEMP>/jup023-embedding-budget-smoke.py`.
The existing temporary runner was adapted for exactly two transport operations,
without persistence. It imported the current working-tree client, checked its
blob before both requests, and used a scoped virtual key rather than the master
or upstream key. No permanent test was added. Receipt and handoff:
`<TEMP>/jup023-timeout-live-6begpbcc/{receipt,handoff}.json` (sanitized).

Preflight verified current model prices and ZDR listings, upstream cap 0.40 USD
without reset, and official usage 0.002603143 USD (includes other users of the
key; historical own usage was 0.002591548 USD). ECB 2026-10-02 rate 1.1225 USD/EUR
places the entire cap at approximately 0.35635 EUR, below 0.50 EUR. Temporary
virtual key: budget 0.20 USD, ten-minute expiry, only primary chat/embedding,
RPM 6, TPM 32768, concurrency 1. No limits were raised. The runner reserved
0.10 USD conservatively; reservation is not actual spend. Gateway/router and
client retries were zero, output cap 800, timeout 30 seconds, no fallback.

| Operation | Observed result | Tokens (input/output) | Accounting |
| --- | --- | --- | --- |
| Primary chat | HTTP 200, 4.672 s; strict FinOpsResponse 1.0 guardrails passed, `insufficient_data` | 539 / 242 | Response cost 0.0007387875 USD; official aggregate delta 0.000738787 USD after 66.281 s, within 1e-9 tolerance |
| Embedding | HTTP 200, approximately 1 s; runner stopped before adapter vector validation | 12 / 0 | Gateway-derived cost 0.000000240 USD; official delta not reconciled at cleanup |

Exactly two paid requests started, no retries: **793 reported tokens** (551 input,
242 output). At cleanup, official usage was 0.003341930 USD, new aggregate delta
0.000738787 USD; embedding charge remained unresolved, not free. Aggregate key
usage is not an individual invoice. Chat generation-metadata lookup returned
404; no individual invoice was invented. The temporary accounting helper raised
`ValueError: cost_mismatch` before returning the embedding payload to the adapter.
Consequently this run does not establish 1536 finite dimensions or a complete
two-operation PASS. No extra model call was made to repair the evidence.

Processor child exit 1; tester result **BLOCKED / partial evidence**. This is not
proof of a timeout regression or a successful embedding validation. Prior real
embedding/persistence evidence remains historical, not a repeat of this fix.
SpendLogs and final virtual spend were not exported before the owned database
was removed. Safe log scan passed without emitting raw logs; virtual key revoked,
temporary secret env removed, owned containers/networks/volumes absent. Tester
guard `live-smoke-20261003` passed with zero repository changes.

Affected documentation checks: strict OpenSpec 38/38, traceability 9 active
changes and whitespace passed. OpenSpec required execution outside the sandbox
after local dependency-read EPERM; no dependency installation or repair.
Previous code review and local regression/mutation results are unchanged, but
the new real-provider check is partial. No publication, commit, merge, archive,
tracker update, shared DockerServer use or delivery closure.

### Accounting Follow-Up Without Further Model Calls

At 23:52:38 UTC, one read-only `GET https://openrouter.ai/api/v1/key` (0.266 s)
reported usage 0.003342170 USD, unchanged cap/reset and 0.396657830 USD remaining.
The additional 0.000000240 USD matches the embedding's twelve tokens and configured
tariff. Total new aggregate spend is therefore **0.000739027 USD**. This resolves
the aggregate accounting mismatch, not the missing vector validation or an
individual invoice. Shared-key attribution limitations still apply. Sanitized
record: `<TEMP>/jup023-timeout-live-6begpbcc/accounting-addendum.json`.

Offline inspection of the temporary helper excludes float rounding as the cause
(difference 3e-23 USD, tolerance 1e-9). `settle_usage` raised on a negative or
positive-mismatched intermediate aggregate delta; the failing observation was
not retained, so its exact branch and cause cannot be established. The absent
`accounting_wait` event is emitted only after success and does not prove no wait
occurred. The child had parsed the HTTP response but waited for accounting approval
before returning it to the product adapter. Cleanup sent STOP, so dimension and
finiteness validation never ran; the vector was not retained for offline recovery.
The helper failure is not evidence of an invalid returned vector or a defect in
the timeout correction. Do not silently convert the original partial result to
PASS. No further model calls, containers, helper edits or product changes occurred.

### Authorized Single Embedding Recheck

2026-10-03: Paris approved correcting only the temporary checker and repeating
one embedding. No product or permanent test changes; same HEAD and client/test
blobs as above. The temporary helper now retains sanitized intermediate usage
observations, waits within a fixed bound for accounting to settle, and records
adapter vector validation independently before accounting. Unknown cost still
fails the accounting gate. Offline check command:
`<TEMP>/jup023-python312-validation/venv/Scripts/python.exe -B <TEMP>/jup023-embedding-recheck-offline.py`
returned exit 0, 10/10 checks, zero model calls. This is not a new product suite,
Red or mutation result; prior code review/regression/mutation evidence is reused.

Live command: the same Python executable with `-B <TEMP>/jup023-embedding-budget-smoke.py`.
Window 00:41:59-00:45:23 UTC, owned project `jup023-real-7ecfc7c927` on local
Docker Desktop, same approved image pins and privacy. Current price, ZDR, caps,
remaining usage and currency margin were rechecked. Virtual key allowed only
`economicon-embedding`, ten-minute expiry, max 0.20 USD; upstream 0.40 USD without
reset and aggregate 0.50 EUR caps unchanged.

**PASS, exit 0:** exactly one embedding, zero chat/retries/fallback. HTTP 200 in
0.516 s; the actual product adapter returned **1536 finite values**. Usage:
12 input tokens, zero output tokens. SpendLogs, virtual counter and official
aggregate delta matched **0.000000240 USD** after 173.641 s of metadata-only
settling. Shared-key usage moved from 0.003342170 to 0.003342410 USD; remaining
0.396657590 USD. This corroborates the calculated charge, not an individual invoice.

Sanitized receipt/handoff: `<TEMP>/jup023-timeout-live-n8ko8c75/{receipt,handoff}.json`;
offline record: `<TEMP>/jup023-embedding-recheck-offline-results.json`. Key revoked,
private env removed, owned containers/networks/volumes absent, log/spend privacy
checks and tester guard `embedding-repeat-20261003` passed. No shared resources.
The earlier partial run remains historical; this new run supplies its missing
vector validation. Together with the earlier successful chat, real transport
revalidation is now complete within this narrow scope. Persistence, full E2E,
DNS cancellation and remote CI were not repeated. Both human Requests changes,
publication authorization and final human approval remain pending.

## Develop Reconciliation 2026-10-03

Paris authorized reconciling the task branch with current develop. Tested tree:
automatic merge of `d6fc408b60e944b726605b242f3e7a64129282c7` into
`59fcea24a08d8ff5f35e8ad306edf58bdf9420e5`, without conflicts. The 37 incoming
paths are unchanged from develop and incorporate JUP-050/PR #59 and JUP-021/PR #53.
JUP-023 product/test files and the isolated LiteLLM configuration remain byte-for-byte
unchanged, including the timeout correction. No new tests or dependencies were added.

Existing checks on this merged tree:

- Processor, CPython 3.12.13, from `apps/processor`:
  `python -m pytest -q -rs -p no:cacheprovider --basetemp=<unique-temp>/pytest`:
  **448 passed, 57 skipped, 330 deprecation warnings**, exit 0, 35.04 s.
  OS-only inherited environment, plugin autoload disabled, no dotenv,
  credentials or service opt-ins; existing temporary interpreter reused.
- `node --test tools/ci-workflow.test.mjs tools/llm-gateway-config.test.mjs tools/docker-topology.test.mjs tools/local-doctor.test.mjs tools/local-smoke.test.mjs tools/repository-governance.test.mjs`:
  **135 passed**, no failures or skips.
- `corepack pnpm openspec:validate`: **40 passed**; `node tools/jup-check.mjs --all`:
  **9 changes**; `node tools/jup-cleanup-check.mjs`: **763 files**; whitespace clean.

Initial sandbox attempts could not read the existing Corepack cache or launch
the temporary Python environment; the affected checks passed with local permission
escalation, without installing or repairing dependencies. Sanitized commands,
environment names and outputs: `<TEMP>/jup023-reconcile-tests-20261003-1145/`.

Read-only incremental review found no in-scope regression: configured/provider
dimension 1536 remains compatible with the new store checks; migration 002 only
adds the tenant index and never converts an existing eight-dimensional schema.
The inherited configuration caveat remains [RF-021-001](../../openspec/findings/backlog.md#rf-021-001--dimension-desde-fichero-de-entorno).

Limits: the 57 service-dependent/opt-in skips are not passes. No new Docker,
pgvector persistence, OpenRouter or paid calls, mutation runs or remote CI were
performed for this reconciliation. Prior live evidence remains historical, not
a claim of live testing on the merged tree. Alejandro's review and Lucia's
validation Requests changes remain for their authors to reassess. This local
reconciliation does not publish, merge PR #65, archive OpenSpec or update Trello.
