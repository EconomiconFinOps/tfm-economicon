# LiteLLM proposal for JUP-078

`config.example.yaml` is a reviewable proposal, not a production deployment. It contains no credentials and is deliberately not connected to the root Compose file.

Required runtime secrets:

- `OPENROUTER_API_KEY`: upstream key, visible only to LiteLLM.
- `LITELLM_MASTER_KEY`: internal gateway key; do not reuse the upstream key.
- `LITELLM_API_KEY`: scoped virtual key delivered to the processor; it must be
  different from both the OpenRouter credential and the gateway master key.

The reviewed alias map is:

| Product alias | LiteLLM provider model |
| --- | --- |
| `economicon-chat` | `openrouter/z-ai/glm-5.2` |
| `economicon-chat-deepseek` | `openrouter/deepseek/deepseek-v4-pro` |
| `economicon-embedding` | `openrouter/openai/text-embedding-3-small` |

The proxy master key belongs under `general_settings`, not
`litellm_settings`. Every upstream request explicitly sets `zdr: true`,
`data_collection: deny` and `allow_fallbacks: false`; OpenRouter otherwise
enables provider fallbacks by default.

Both chat models enable high-effort reasoning by default at OpenRouter. The
gateway explicitly disables optional reasoning for the baseline FinOps
evaluation: reasoning tokens count toward the 800-token output cap and can
otherwise exhaust the response or exceed the 30-second request timeout. Any
future reasoning-enabled mode must be selected deliberately and benchmarked
separately.

Before using this configuration:

1. pin and review a LiteLLM image version;
2. validate the current LiteLLM schema against that version;
3. verify that `zdr`, `data_collection: deny` and `allow_fallbacks: false`
   reach OpenRouter without storing request prompts or response bodies;
4. create a virtual key capped at the budget approved in ADR-0002;
5. bind the service to an internal Docker network, not a public interface;
6. confirm that prompt/response logging is disabled;
7. run the benchmark before selecting the chat alias.

The existing container named `litellm` on `dockerserver` is outside this change. It must not be modified or reused until ownership, version, ports and isolation are confirmed.

JUP-053 keeps these credentials external and the example fields empty.
Python services load dotenv only through an explicit `ECONOMICON_ENV_FILE`;
environment variables win. A shared dotenv file may contain gateway keys, but
they are not application settings and Compose does not pass them to the apps.
Never deliver upstream/master keys through build ARG, image ENV or VITE variables.
Mock providers need no gateway key; selecting LiteLLM retains all existing
conditional validators and does not demonstrate a deployed real provider.

For a future approved deployment, rotate keys in their owning gateway/provider
first, coordinate consumer updates and restarts, verify the scoped virtual key
with a non-sensitive request, then revoke the old key. An environment edit alone
does not rotate a server-side key. On failure use an operator-approved valid,
uncompromised key, never an old insecure default. No gateway is deployed or
modified by this change.
