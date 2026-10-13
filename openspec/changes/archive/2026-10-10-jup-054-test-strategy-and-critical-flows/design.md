JUP: JUP-054

## Baseline and decisions

Audit base: `origin/develop` at `c2995a1`. Trello checked through the official
DockerServer integration on 2026-10-10; scope unchanged from dispatch snapshot.

The repository already contains frontend route integration, backend security
and retrieval tests, processor ingestion and opt-in multi-service tests.
Preserve those suites and add assertions at currently disconnected seams.

- Use actual application components inside each new regression; document the
  remaining provider, persistence and transport doubles in the test and matrix.
- Extend the existing real-service journey rather than create a second stack.
- Invoke Vitest directly in its existing required CI job. Keep required context
  names and protections unchanged; pytest already bypasses Turbo in CI.
- Separate fresh execution, historical evidence and unexecuted opt-in checks.
  A skip never establishes acceptance of a real-service behavior.

## Dependencies and limits

JUP-087/085/086/096 provide the baseline runners and contracts. Tests using
CockroachDB, pgvector and RabbitMQ require isolated disposable services and
their existing guarded fixtures. Real Azure, production transport, paid LLMs,
cloud deployment and browser rendering remain outside offline test evidence.

## Delivery

The initial plan submitted the assigned validator's contribution for Lucía's
adoption. On 2026-10-10 the user explicitly authorized completion under an
exception because the MVP delivery was overdue. Implementation, validation
evidence and administrative PR closure are attributed to Alejandro with Codex
assistance; no human pairing or independent approval is inferred. The existing
PR-only administrator exception is used without changing branch protections.
Scope, commands, attribution and evidence are recorded in
`docs/testing/critical-flows.md` and `docs/evidence/JUP-054-validation.md`.
