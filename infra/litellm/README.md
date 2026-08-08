# LiteLLM proposal for JUP-078

`config.example.yaml` is a reviewable proposal, not a production deployment. It contains no credentials and is deliberately not connected to the root Compose file.

Required runtime secrets:

- `OPENROUTER_API_KEY`: upstream key, visible only to LiteLLM.
- `LITELLM_MASTER_KEY`: internal gateway key; do not reuse the upstream key.

Before using this configuration:

1. pin and review a LiteLLM image version;
2. validate the current LiteLLM schema against that version;
3. verify from request traces that `zdr` and `data_collection: deny` reach OpenRouter;
4. create a virtual key capped at the budget approved in ADR-0002;
5. bind the service to an internal Docker network, not a public interface;
6. confirm that prompt/response logging is disabled;
7. run the benchmark before selecting the chat alias.

The existing container named `litellm` on `dockerserver` is outside this change. It must not be modified or reused until ownership, version, ports and isolation are confirmed.
