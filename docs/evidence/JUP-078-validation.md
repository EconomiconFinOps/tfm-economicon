# JUP-078 validation evidence

- Date: 2026-08-08
- Branch: `docs/JUP-078-litellm-openrouter-adr`
- Base: local JUP-077 head `02d00fd`
- Trello: https://trello.com/c/M4zqDGlW

## Delivered

- ADR-0002 in `Proposed` state with gateway boundary, candidates, scoring rubric and provisional budget.
- OpenSpec change linked to JUP-078 and Trello.
- Processor startup validation for modes, aliases, gateway key, URL, limits and embedding dimension.
- LiteLLM example configuration with one upstream per alias and OpenRouter privacy routing.
- Public synthetic benchmark cases and a metrics-only runner that refuses to run without gateway credentials.

## Automated validation

| Check | Result |
|---|---|
| Processor tests | 42 passed |
| Backend tests | 7 passed; 2 pre-existing short-test-key warnings |
| Azure fake API tests | 34 passed; 1 dependency deprecation warning |
| JUP checker tests | 4 passed |
| `jup:check` | passed |
| Strict OpenSpec validation | 1 change passed |
| Frontend production build | passed |
| Docker Compose rendering | passed with `docker-compose config` |
| Benchmark without credentials | refused as designed |

The frontend lint still reports 49 existing `react/prop-types` errors in files untouched by JUP-078. This branch does not hide or modify that baseline debt.

## Dockerserver observation

The existing `litellm` container was inspected without reading environment variables, logs or configuration contents. It uses the floating image `docker.litellm.ai/berriai/litellm:main-latest`, runs with `/app/config.yaml`, and binds port 4000 only to `127.0.0.1`.

It was not modified. Reuse is blocked until ownership and configuration are confirmed and the image is pinned to a reviewed version.

## Pending human/external evidence

- Approve or adjust the 10 USD/month development cap.
- Provision temporary OpenRouter and LiteLLM keys outside Git.
- Run the real benchmark and review answer quality.
- Record approval from Lucia, Paris, Victor and Alejandro.
- Confirm the canonical GitHub repository and target `develop` branch before push/PR.
