# JUP-078 validation evidence

- Date: 2026-08-25
- Branch: `docs/JUP-078-litellm-openrouter-adr`
- Base: official `EconomiconFinOps/tfm-economicon` `develop` after JUP-077.
- Trello: https://trello.com/c/M4zqDGlW

## Delivered

- ADR-0002 in `Proposed` state with gateway boundary, selected models, scoring rubric and provisional budget.
- Model correction requested by Alejandro: GLM-5.2 is the primary chat alias and DeepSeek V4 Pro is the explicit second chat alias; the previous draft selection was removed.
- OpenSpec change linked to JUP-078 and Trello.
- Processor startup validation for modes, aliases, gateway key, URL, limits and embedding dimension.
- LiteLLM example configuration with one upstream per alias and OpenRouter privacy routing.
- Correct proxy master-key location and explicit OpenRouter fallback denial.
- Optional high-effort reasoning disabled explicitly after authenticated
  testing exposed incomplete answers and request timeouts.
- Public synthetic benchmark cases and a metrics-only runner that rejects
  invalid cases, unsafe URLs, redirects and missing gateway credentials, with
  each benchmark response capped at 256 tokens.
- An isolated, digest-pinned LiteLLM 1.82.6 instance running on the loopback
  interface of `dockerserver`, without modifying the existing gateway.
- Real chat and embedding calls through LiteLLM and OpenRouter.

## Official public model-catalog verification

Public OpenRouter model lookups returned HTTP 200 on 2026-08-25:

| Model | Canonical ID | Context | Input USD / 1M | Output USD / 1M |
|---|---|---:|---:|---:|
| GLM-5.2 | `z-ai/glm-5.2` | 1,048,576 | 1.19 | 3.74 |
| DeepSeek V4 Pro | `deepseek/deepseek-v4-pro` | 1,048,576 | 0.572808 | 1.145616 |
| Embeddings | `openai/text-embedding-3-small` | 8,192 | 0.02 | N/A |

This read-only verification consumed no API credits and did not require
credentials. It confirms model availability and published pricing only; it is
was followed by the authenticated quality benchmark recorded below.

## Authenticated gateway and model verification

- Dedicated container: `economicon-jup-078-litellm`.
- Listener: `127.0.0.1:4100`; the existing `litellm` service remains on
  `127.0.0.1:4000` and was not modified.
- LiteLLM version: `1.82.6`.
- Pinned image digest:
  `sha256:7c311546c25e7bb6e8cafede9fcd3d0d622ac636b5c9418befaa32e85dfb0186`.
- Upstream and gateway keys are isolated outside Git in a server-side file
  readable only by its owner (`0600`).
- The upstream OpenRouter key has an existing 25 USD monthly cap. The proposed
  10 USD/month product budget and scoped LiteLLM virtual key still require
  team approval and implementation.
- Gateway health returned HTTP 200 and listed all three approved aliases.
- A real `economicon-embedding` request returned 1536 dimensions in 450.39 ms
  with 6 input tokens.

## Real benchmark results

Five public synthetic FinOps cases were sent to each chat alias with optional
reasoning disabled, a 256-token completion limit and a 30-second timeout:

| Model | Successful cases | Keyword score | p95 latency | Input tokens | Output tokens | Successful-response cost |
|---|---:|---:|---:|---:|---:|---:|
| GLM-5.2 | 5/5 | 90% | 11,728.50 ms | 216 | 293 | 0.0005395524 USD |
| DeepSeek V4 Pro | 4/5 | 75% | 10,875.63 ms | 158 | 126 | 0.0003567 USD |

Machine-readable, metrics-only evidence:
[`JUP-078-benchmark-results.json`](JUP-078-benchmark-results.json).

The DeepSeek `finops-actions` case timed out after 30,054.73 ms. The benchmark
therefore correctly returned a non-zero exit code: this is an observed model
availability issue, not a green benchmark. Both models exceeded the proposed
10-second p95 target; DeepSeek also missed the 90% keyword-score threshold.
Keyword matching is only a heuristic and requires human quality review.

The initial run, before disabling optional reasoning, completed only 3/5 cases
for each model. Explicitly disabling reasoning made GLM-5.2 complete 5/5;
limiting benchmark responses to 256 tokens reduced its successful-response
cost from 0.0016360818 USD to 0.0005395524 USD.

The authenticated OpenRouter key endpoint reported total accumulated usage of
0.011825531 USD after three benchmark runs, timed-out requests and the real
embedding check. This full-account delta is intentionally larger than the
0.0008962524 USD attributed to successful responses in the final benchmark.

## Automated validation

| Check | Result |
|---|---|
| Processor tests | 126 passed, including 32 AI configuration cases |
| Backend tests | 10 passed; 2 pre-existing short-test-key warnings |
| Azure fake API tests | 58 passed; 1 dependency deprecation warning |
| Shared contract and benchmark tests | 32 passed, including 11 benchmark safety cases |
| Gateway configuration tests | 6 passed: aliases, secrets, privacy, fallback, reasoning and limits |
| JUP checker and hygiene tests | 12 passed; existing team tooling preserved |
| Assistant corpus tests | 8 passed |
| `jup:check` | passed |
| Strict OpenSpec validation | 13 passed, 0 failed |
| Frontend production build | passed |
| Docker Compose rendering | Processor defaults remain mock; production Compose remains unchanged |
| Benchmark without credentials | refused as designed |
| Authenticated embedding | 1536 dimensions; 6 tokens; 450.39 ms |
| Authenticated chat benchmark | GLM-5.2 5/5; DeepSeek 4/5; one real timeout |

The proposed ADR intentionally keeps the OpenSpec approval task incomplete:
the real credential-backed benchmark has now been executed and attached, but
approval from all four team members is still outstanding.

## Dockerserver observation

The existing `litellm` container was inspected without reading environment
variables, logs or configuration contents. It uses the floating image
`docker.litellm.ai/berriai/litellm:main-latest`, runs with `/app/config.yaml`,
and binds port 4000 only to `127.0.0.1`.

It was not modified or reused. The Economicon benchmark uses its own named
container, dedicated loopback port and image pinned to an explicit digest.

## Pending human/external evidence

- Approve or adjust the 10 USD/month development cap.
- Review the real GLM-5.2 versus DeepSeek V4 Pro findings, including the
  DeepSeek timeout and p95 values above the proposed threshold.
- Provision a scoped, revocable LiteLLM virtual key capped at the team's
  approved product budget before connecting application services.
- Record approval from Lucia, Paris, Victor and Alejandro.
- Obtain review on the PR targeting the now-confirmed official `develop` branch.
