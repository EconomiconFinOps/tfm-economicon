# Compose chat: approved local deployment delta

Paris explicitly approved this design on 2026-10-11 in the autonomous delivery
chat. Implementation may proceed through separate Red, Green and focal mutation
checkpoints. Runtime deployment and paid inference remain separately authorized.
No migration, dependency, model, gateway replacement or public API change.

## Packaging and dependency integrity

Backend builds from the repository root to copy the authoritative chat/v2 and
whole summary directory (v2 and v3). Processor retains its service build context.
Both install requirements.lock and requirements-chat.lock in one hash-checked
resolver invocation, followed by pip check. Shared pins must agree; do not install
one lock over another or silently regenerate them. Check the existing requirements.txt
constraints too. Validate bundled resources during build and offline under the
non-root, read-only runtime. No tokenizer download during startup.

The first real build exposed that pip constraints cannot include declared extras
(`psycopg[binary]`). Keep both locks unchanged: after installing them and pip check,
use `pip install --dry-run --no-index -r requirements.txt` to resolve declarations
and extras against installed metadata, without installation or index access.

## Ownership and private transport

One Compose service invokes the existing backend `python -m app.migrate` and
must exit successfully before backend starts with BACKEND_SCHEMA_MODE=verify.
Processor continues to own its existing migrations and vector initialization;
its existing dependency on healthy backend is retained. No new migration runner.

Backend and processor additionally join a project-scoped internal chat network.
Processor binds a configurable concrete private IPv4, not a wildcard. A dedicated
network alias resolves that address. Port 8003 is never published. Both read the
same operator-provided HMAC file through their existing environment names.
No generated default key, real dotenv edit or shared runtime modification.

## Mock and AI

CHAT_ENABLED and SUMMARY_ENABLED enable the same public chat path in both modes.
Explicit mock selection reuses MockLLMProvider and a deterministic summary adapter
with literal, bounded quotes and explicit omissions. It is a transport/persistence
fixture, not a semantic summarizer. Originals and previous artifacts remain intact;
existing validators still govern installation. Mock is development/test only,
never evaluation/production and never a fallback from a failed real provider.

The AI overlay retains JUP-108 aliases, models, gateway and readiness dependencies.
It mounts a separate summary virtual key only in processor; upstream and master
keys remain gateway-only. Chat reserves 800 output tokens, summary 10000, both
context defaults 1048576. Mirror reduced context budgets across both services.
Do not modify the gateway's 800 default without evidence that it overrides the
summary request's explicit 10000. Use separate volumes for mock8 and real1536.

## Proportionate evidence

Focused Red tests cover Compose ordering/private network/assets and mock factories,
validated responses, source correspondence, cancellation/deadline and no fallback.
Green checks use existing cached test images offline, but those do not prove image
packaging. The project Dockerfiles must also build and load their resources with
network disabled and a read-only root, without mounting source/assets. Parent owns
live startup/SSE/persistence checks. Focal mutations must detect a missing migration
dependency, exposed private listener and accidental real-to-mock selection.
