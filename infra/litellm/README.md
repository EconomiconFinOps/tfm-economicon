# Isolated LiteLLM runtime (JUP-023 / JUP-078)

This opt-in Compose project supplies the gateway and its own plain PostgreSQL
for revocable virtual keys and spend metadata. The same two services are
included by the root Compose under its optional `ai` profile; the root mock
defaults remain unchanged. Never reuse the shared DockerServer, its
containers, networks, volumes, product database or vector database.

For the complete root stack, use both `-f docker-compose.yml` and
`-f infra/litellm/compose.ai.yml` with `--profile ai`. The additional file
makes gateway health mandatory for backend and processor; the profile alone
does not gate their startup. Follow the [root startup instructions](../../README.md#perfil-opcional-de-ia-real)
for two scoped keys and a separate project when replacing eight-dimensional
mock embeddings with 1536-dimensional real embeddings. Preserve the mock
project volumes; changing the dimension does not migrate an existing table.

For the complete application stack, the root README is the canonical guide:

- [Mock startup without OpenRouter](../../README.md#modo-mock-stack-completo-sin-openrouter):
  explicit mock providers/dimension8, normal stack credentials, doctor, startup
  and smoke. No gateway or virtual key is required.
- [AI startup](../../README.md#perfil-opcional-de-ia-real): bootstrap, two scoped
  keys, `.env.ai`, separate1536-dimensional volumes and full stack command.
- [Return from AI to the original mock project](../../README.md#volver-de-ia-al-proyecto-mock-original):
  stop AI without deleting volumes, restore the original mock environment/project
  and restart. Keep shell overrides from selecting a different mode or project.

The isolated gateway commands below run only LiteLLM/PostgreSQL; they do not
start frontend, backend, processor or the other application infrastructure.

## Approved pins and pending runtime checks

Paris approved LiteLLM 1.103.2 on 2026-10-02:
`ghcr.io/berriai/litellm@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd`.
The dedicated database uses
`postgres:17-alpine@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24`
(registry index; amd64 annotation 17.11-alpine3.24).

The supplied image preflight reports all 17 official advisories inspected and
not applicable, LiteLLM version verified with networking disabled, and Prisma
0.11.0. The synthetic integration replay below checks runtime compatibility;
it does not establish compatibility with the real OpenRouter service.
Never run the vulnerable historical 1.82.6 image or `latest`. The version decision
is documented in [ADR-0016](../../docs/adr/ADR-0016-litellm-version-pin.md), whose
status remains Proposed; ADR-0002 was accepted on 2026-10-04 and real-use approvals are separate.

The fake-upstream runtime check requires a
synthetic upstream, a config mount override pointing every alias only to that
upstream, and an internal isolated Docker network preventing external egress.
Use only a temporary synthetic environment file, never the root `.env` or real
OpenRouter key. Verify virtual-key auth, aliases, privacy flags, no fallback,
zero gateway/router retries, no prompt echo in container/spend logs, retained
cost metadata and non-LLM health. This is not an OpenRouter smoke.

## Secrets and isolated startup

Keep secrets outside Git. Select an owner-controlled environment file by
absolute path on **every** Compose invocation, including validation. Do not read
or source the root `.env`. Inherited shell variables override the selected file;
the owner must prevent real credentials from replacing synthetic values.

| Variable | Recipient and constraint |
| --- | --- |
| `OPENROUTER_API_KEY` | Gateway only; synthetic for fake-upstream tests |
| `LITELLM_MASTER_KEY` | Gateway/admin only; must start with `sk-`, with at least 32 characters and strong random material |
| `LITELLM_DATABASE_PASSWORD` | Gateway DB and gateway connection only; unique strong URL-safe password, e.g. random hexadecimal; no default |
| `LITELLM_ADMIN_PORT` | Optional loopback port, default 44000; choose a free port |
| `LITELLM_API_KEY` | Processor only; separate scoped, revocable virtual key |
| `BACKEND_LITELLM_API_KEY` | Backend only in the root Compose; embedding alias only |

Only explicitly listed variables enter containers; no wholesale `env_file`
forwarding. PostgreSQL has no public port. Gateway administration binds only to
`127.0.0.1`. Networks and volumes belong to a unique Compose project with no
fixed global names or external resources.

From the repository root, after the applicable runtime gate, substitute a unique
owned project name and absolute environment-file path:

```text
docker compose --env-file <absolute-isolated-env-file> -p <owned-unique-project> -f infra/litellm/docker-compose.yml --profile ai config --quiet
docker compose --env-file <absolute-isolated-env-file> -p <owned-unique-project> -f infra/litellm/docker-compose.yml --profile ai up -d
```

For manual fake-upstream runs, append `-f <isolated-fake-override>`
before each subcommand. Do not start the base configuration against OpenRouter
during that phase. Never run full `docker compose config`, dump container
environments or retain unsanitized API output. `/health/liveliness` does not
invoke a model. Cleanup belongs to the owner and targets only that project.
The isolated fake override must make both `gateway` and `default` networks
internal: LiteLLM joins the root application's default network when included
there, but synthetic tests must not gain an external route.

## Synthetic integration replay

With the approved images already available in local Docker and the existing
processor test dependencies available, run from `apps/processor` in PowerShell:

```powershell
$env:JUP023_DOCKER_FAKE = '1'
$testTemp = Join-Path $env:TEMP ('jup023-privacy-' + [guid]::NewGuid())
python -B -m pytest -p no:cacheprovider tests/test_litellm_docker.py -q -s --tb=short --basetemp=$testTemp
```

The opt-in test creates a unique Compose project, temporary synthetic credentials
and config override, an internal network, and a fake upstream. It disables default
dotenv loading, removes inherited provider credentials from the Docker command
environment, uses `config --quiet` and `--pull never`, and cleans up its containers,
network and volume. `JUP023_RECEIPTS` identifies the temporary directory containing
sanitized results, including cleanup status. No real OpenRouter key is used.

The replay exercises FinOps chat, 1536-dimensional embeddings, virtual-key auth,
denied aliases, upstream privacy flags, exactly three attempts on 429/503, retained
spend records, and absence of prompt, response, credential and upstream-error
markers in container logs and spend records. On Windows Docker Desktop, an
internal-only network may not publish a reachable port: the fixture then uses a
loopback HTTP relay through `docker exec` to the real gateway, without adding
egress. This does not validate direct host port publication in that environment.
It also does not validate real upstream privacy enforcement, prices, budget
exhaustion, expired/revoked keys, or processor persistence in pgvector. Synthetic
success grants no real-spend, ADR acceptance or publication approval.

The [validation record](../../docs/evidence/JUP-023-validation.md) documents the
initial failure: console suppression alone left upstream error text in SpendLogs.
The approved correction uses the public callback described below, on the same
image pin. A passing replay must preserve all eight failure rows (three 429,
three 503, one denied alias and one invalid key), both success rows, identity,
timing and available numeric usage/cost metadata, with no private markers.
Failure rows with zero or missing spend do not prove zero upstream charges.
Real use remains gated separately; the linked evidence records delivery status.

## Processor configuration

| Setting | Explicit real-provider value |
| --- | --- |
| `LLM_PROVIDER` / `EMBEDDING_PROVIDER` | `litellm` / `litellm` |
| `AI_EXECUTION_MODE` | `evaluation` (rejects mocks) |
| `LITELLM_BASE_URL` | `http://litellm:4000/v1` on the owned network, or `http://127.0.0.1:<admin-port>/v1` from the host |
| `LITELLM_API_KEY` | Restricted virtual key, never master/upstream key |
| `LLM_MODEL` | `economicon-chat` |
| `EMBEDDING_MODEL` / `EMBEDDING_DIMENSION` | `economicon-embedding` / `1536` |
| `LLM_TIMEOUT_SECONDS` | At most 30 per attempt |
| `LLM_MAX_RETRIES` | At most 2, including zero; at most 3 total attempts |
| `LLM_MAX_OUTPUT_TOKENS` | At most 800 |

The existing database, queue and other required settings remain necessary; use
only the smoke owner's isolated services. Processor dotenv loading requires an
explicit `ECONOMICON_ENV_FILE`; environment variables win. Do not point it to the
root dotenv. Without explicit provider selection development retains mocks and
requires no gateway key. Real limits fail validation rather than being clamped.

Chat preserves `invoke(prompt, response_format=...)` and FinOpsResponse 1.0
guardrails. Embeddings preserve `embed(text)` and require exactly 1536 finite
numbers, rejecting booleans and strings before persistence. Gateway URLs with
or without `/v1` work; redirects never forward credentials.

Only transient connection/timeout failures, HTTP 429 and 5xx are retried, with
bounded backoff. Auth, other 4xx, redirects and invalid outputs are terminal.
Gateway and router retries are both zero. There is no automatic mock/model/
provider fallback. `ProviderError` marks ingestion `failed`/`ingestion_failed`
and causes worker nack without requeue; other error policies are unchanged.
The timeout is per attempt, not a whole-job deadline.

## Aliases, privacy and budgets

| Product alias | LiteLLM provider model |
| --- | --- |
| `economicon-chat` | `openrouter/z-ai/glm-5.2` |
| `economicon-chat-deepseek` | `openrouter/deepseek/deepseek-v4-pro` |
| `economicon-embedding` | `openrouter/openai/text-embedding-3-small` |

For the approved compatibility trial, only `economicon-chat` restricts OpenRouter
to `provider.only: [deepinfra/fp4]` with `require_parameters: true`. GLM-5.2,
the complete strict response schema, privacy flags, disabled reasoning, 30-second
timeout and 800-token output cap remain intact. That routing selection left the
secondary and embedding aliases unchanged; the approved embedding pricing
correction is described below. The real smoke passed within the limited scope documented
below. An incompatible route must still fail without fallback or relaxing the
contract; this remains an OpenRouter route, not a direct DeepInfra connection.

Select the secondary alias explicitly for evaluation, never as a fallback. Both
chat aliases disable optional reasoning within the 800-token cap. Every alias
sets `zdr: true`, `data_collection: deny` and `allow_fallbacks: false`;
incompatible routes must fail closed.

Only `economicon-embedding` declares `model_info.input_cost_per_token: 0.00000002`
USD/token and `output_cost_per_token: 0.0` USD/token. The input tariff is
USD 0.02 per million tokens, recorded on 2026-10-02 from the official
[OpenRouter embedding catalogue](https://openrouter.ai/api/v1/embeddings/models)
in the [validation record](../../docs/evidence/JUP-023-validation.md#successful-real-smoke-and-accounting).
`extra_body.provider.max_price.prompt: 0.02` uses USD per million input tokens,
not a key budget. Spend calculated from this tariff and token usage is derived
accounting, not an individual upstream invoice. Reverify the price before any
live call; a changed or unverifiable price, unknown cost, cap or margin requires
stopping, not raising limits. The upstream key cap remains USD 0.40 without
reset, including prior usage; the aggregate EUR 0.50 ceiling is unchanged.
Zero or missing spend with positive usage does not establish a free call.

Following the [LiteLLM logging contract](https://docs.litellm.ai/docs/proxy/logging),
`litellm_settings.turn_off_message_logging: true` suppresses message content and
`general_settings.store_prompts_in_spend_logs: false` excludes prompts/responses
from spend logs. `set_verbose: false` is additional protection, not the content
logging control. Spend tracking remains enabled for budgets. Do not enable
debug modes or prompt/response logging callbacks.

The gateway container also fixes `LITELLM_LOG=CRITICAL`. In the pinned 1.103.2
source, `proxy/common_request_processing.py::log_llm_api_exception` logs the
upstream exception text at ERROR even with message logging disabled.
`_logging.py::resolve_log_level` and `proxy/proxy_cli.py` apply the configured
level to the LiteLLM output handler and Uvicorn. CRITICAL suppresses those ERROR
records and their tracebacks without disabling database spend tracking. This
also suppresses gateway warning/error and ordinary access diagnostics; use the
processor's safe technical metadata and gateway spend records for this workflow.
It is a severity filter, not universal content redaction: verify the replay
again when changing the image or logging configuration, and do not lower the
level for requests containing private data. See the supported
[logging environment control](https://docs.litellm.ai/docs/proxy/debugging).

`safe_logging.py` is mounted read-only alongside the gateway config and its
`safe_error_logger` instance is the first configured callback in
`litellm_settings.callbacks`, after the built-in virtual-key budget limiter.
It implements the public `CustomLogger.async_post_call_failure_hook`, replacing
the shared exception's `message`, `args`, and existing `detail` and
`litellm_debug_info` fields with fixed content-free text. It does not replace the
exception, remove failure rows, or change status, class, model, IDs, timing,
usage or cost. No raw-error copy is retained by the callback. Returning a new
HTTPException alone would not sanitize the original object seen by later hooks.

In pinned 1.103.2, configured callbacks load before startup appends `_ProxyDBLogger`;
`proxy/utils.py` awaits failure hooks in that order. The DB callback reads the
sanitized exception message. `LITELLM_SUPPRESS_SPEND_LOG_TRACEBACKS=true`, with
`LITELLM_LOG=CRITICAL`, omits the previously captured traceback from spend
metadata, as confirmed by source inspection. The controls are complementary:
message replacement cannot change an already captured traceback string.
Reported validation did not detect removal of the traceback-suppression flag
in the tested HTTP paths; a direct check of `spend_log_error` at ERROR did
detect its removal. Both controls are retained, but their independent necessity
has not been demonstrated in those HTTP paths. `disable_error_logs` remains unset and
normal success/failure accounting stays enabled. Recheck ordering and persistence
when changing the image, callback configuration or log level.

The bind mount refuses to create a missing source path. A missing module,
import error or invalid registered instance fails config initialization before
the gateway serves model requests. Runtime hook failures have a different
contract: LiteLLM catches non-HTTP exceptions, reports them through its logger
and continues to later callbacks; CRITICAL can suppress that diagnostic. This
callback is not a circuit breaker. Any hook failure or failed privacy replay
blocks validation and real use; do not treat health alone as privacy evidence.

Processor logs allow alias, duration, HTTP status, failure category, validated
optional token/cost metadata and existing correlation context. Never log bodies,
prompts, credentials or raw upstream errors. Missing cost is unknown, not zero;
local telemetry is not budget enforcement.

An administrator must issue a virtual key through the gateway key management
API, restricted to approved aliases with expiry, maximum budget, budget duration,
rate and concurrency limits. Record sanitized effective limits and privately
deliver the returned secret to the processor. Verify denied aliases,
revoked/expired keys and exhausted budgets against the fake upstream. Rotate
server-side first, update the consumer, verify with synthetic input, then revoke
the previous key. Editing an environment variable alone does not rotate a key.

Real spend requires the ADR-0002/privacy/budget gates, verified upstream and
virtual-key caps, current prices and conservative USD/EUR conversion. Reserve
worst-case cost including retries and charged failures before each sequential
operation, reconcile deltas, and stop if cost or margin is unknown. The aggregate
real-validation ceiling is EUR 0.50, not account balance or a monthly budget.
Image approval and fake-upstream success do not authorize real spend.

## Runtime handoff

The processor smoke requires an isolated disposable pgvector fixture with schema for
1536 dimensions before processor persistence. The existing bootstrap creates
8-dimensional vectors: do not migrate production data, reinterpret existing
vectors or reuse the product vector database. That fixture is separate from this
gateway's PostgreSQL.

The [successful real smoke and accounting](../../docs/evidence/JUP-023-validation.md#successful-real-smoke-and-accounting)
records a limited PASS: primary chat passed the original full-schema
FinOpsResponse 1.0 guardrails, embeddings were finite with 1536 dimensions,
one vector persisted in real disposable pgvector, and the original ingestion
path completed a job in disposable SQLite. This was not a CockroachDB/RabbitMQ
end-to-end run. The earlier invalid output remains unexplained; one successful
smoke does not establish provider reliability.

F1 verification passed after the [embedding budget correction](../../docs/evidence/JUP-023-validation.md#embedding-budget-correction)
approved by Paris on 2026-10-02. Previously, embedding SpendLogs recorded zero
despite a positive upstream charge; that failure remains part of the history.
The synthetic replay passed one test and all 25 controls: two embedding calls
each added USD 0.000000240 to the actual virtual-key counter, reaching
USD 0.000000480 against a USD 0.000000360 cap. The third request returned HTTP 429
with structured type `budget_exceeded`, with no additional upstream call.
Counter updates are asynchronous, not atomic pre-reservations; this does not
guarantee that an individual call cannot overshoot the budget.

Exactly one real embedding call, without retries, returned HTTP 200, 12 tokens
and 1536 finite values. SpendLogs, the virtual-key counter increment and the
official aggregate usage delta each recorded USD 0.000000240, bringing total
usage to USD 0.002591548. This corroborates derived tariff-based accounting,
not an individual invoice. Price re-verification and stop rules above remain
mandatory; the USD 0.40 upstream cap without reset and EUR 0.50 aggregate ceiling
are unchanged. No new chat or persistence run, CockroachDB/RabbitMQ end-to-end
test, or real budget-denial request was performed for this correction.
Internal technical review and local QA passed; see the [review history](../../openspec/changes/archive/2026-10-04-jup-023-litellm-openrouter/review.md#final-local-qa-and-post-qa-gate).
PR [#65](https://github.com/EconomiconFinOps/tfm-economicon/pull/65) was reviewed, validated and merged into develop. This does not approve ADR-0002/0016 or remove the limits above.
