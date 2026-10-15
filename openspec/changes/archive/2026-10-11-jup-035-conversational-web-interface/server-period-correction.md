# Server-owned response period

Paris approved server ownership of scope.period and requested local implementation
on 2026-10-11. This correction is isolated from the active JUP-035 checkout.

The public FinOpsResponse 1.0 schema remains unchanged. The chat provider schema
omits scope.period. Processor assembly injects the period frozen by the backend
before applying the full public validator. Model-supplied periods are rejected.

The backend derives response_period only from successful server billing
verification records. A single distinct UTC interval is retained. No verified
interval or multiple distinct intervals produces null, without inventing a union.
Browser selection, dialogue, retrieved text and provider output cannot set it.
Invalid verified intervals fail closed. The backend checks the assembled response
against its frozen period before persisting the final public response.

Prompt resource fingerprints include the provider-schema projection and server
period policy so old/new backend and processor bundles do not silently mix.
No changes to financial query filters, historical data, ingestion or model aliases.
Unauthorized response evidence is a separate finding, outside this correction.

Verification: Red/Green checks for provider-schema omission, preserved public
schema, null and verified-period assembly, rejected model injection, backend
derivation and final consistency; affected existing chat suites and real E5 replay.
