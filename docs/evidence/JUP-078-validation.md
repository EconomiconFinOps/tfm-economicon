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
- Public synthetic benchmark cases and a metrics-only runner that rejects
  invalid cases, unsafe URLs, redirects and missing gateway credentials.

## Official public model-catalog verification

Public OpenRouter model lookups returned HTTP 200 on 2026-08-25:

| Model | Canonical ID | Context | Input USD / 1M | Output USD / 1M |
|---|---|---:|---:|---:|
| GLM-5.2 | `z-ai/glm-5.2` | 1,048,576 | 1.19 | 3.74 |
| DeepSeek V4 Pro | `deepseek/deepseek-v4-pro` | 1,048,576 | 0.572808 | 1.145616 |
| Embeddings | `openai/text-embedding-3-small` | 8,192 | 0.02 | N/A |

This read-only verification consumed no API credits and did not require
credentials. It confirms model availability and published pricing only; it is
not a substitute for the required authenticated quality benchmark.

## Automated validation

| Check | Result |
|---|---|
| Processor tests | 126 passed, including 32 AI configuration cases |
| Backend tests | 10 passed; 2 pre-existing short-test-key warnings |
| Azure fake API tests | 58 passed; 1 dependency deprecation warning |
| Shared contract and benchmark tests | 32 passed, including 11 benchmark safety cases |
| Gateway configuration tests | 5 passed: aliases, secrets, privacy, fallback and limits |
| JUP checker and hygiene tests | 12 passed; existing team tooling preserved |
| Assistant corpus tests | 8 passed |
| `jup:check` | passed |
| Strict OpenSpec validation | 13 passed, 0 failed |
| Frontend production build | passed |
| Docker Compose rendering | Processor defaults remain mock; no gateway is deployed |
| Benchmark without credentials | refused as designed |

The proposed ADR intentionally keeps two OpenSpec tasks incomplete: a real
credential-backed benchmark and approval from all four team members.

## Dockerserver observation

The existing `litellm` container was inspected without reading environment variables, logs or configuration contents. It uses the floating image `docker.litellm.ai/berriai/litellm:main-latest`, runs with `/app/config.yaml`, and binds port 4000 only to `127.0.0.1`.

It was not modified. Reuse is blocked until ownership and configuration are confirmed and the image is pinned to a reviewed version.

## Pending human/external evidence

- Approve or adjust the 10 USD/month development cap.
- Provision temporary OpenRouter and LiteLLM keys outside Git.
- Run the real GLM-5.2 versus DeepSeek V4 Pro benchmark and review answer quality.
- Record approval from Lucia, Paris, Victor and Alejandro.
- Obtain review on the PR targeting the now-confirmed official `develop` branch.
