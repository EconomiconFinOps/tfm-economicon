JUP: JUP-081

## Context

Dockerserver already stores valid Discord and Trello credentials in a mode-600
`.env` and runs the bridge through one-shot Docker Compose commands. A real
ten-page Discord synchronization reproduced HTTP 429 while a one-page snapshot
succeeded. The historical implementation exists only as untracked local files
and on the server.

## Decisions

### Keep the bridge on demand

The bridge remains an operator tool rather than a long-running application
service. One-shot containers reduce exposed runtime and use the same reviewed
code for checks, snapshots and authorized writes.

### Retry at the shared HTTP boundary

The standard-library transport handles HTTP 429 for both providers. It prefers
Discord's JSON `retry_after`, falls back to `Retry-After`, clamps each wait to
50 milliseconds through 60 seconds and permits four retries. Other HTTP errors
fail immediately.

### Preserve explicit write authority

Every write still requires the server switch and the command flag. Discord
messages disable mentions, and no delete operation is exposed.

### Keep credentials and collaboration data outside Git

Only `.env.example` is versioned. The root ignore file excludes the snapshot
directory. Documentation warns that snapshots can reproduce content already
exposed in the source channel and are not a secret-redaction mechanism.

## Risks and mitigations

- Repeated rate limits may stall an operator command: retries and waits are
  bounded, then the command fails with a concise diagnostic.
- Retrying writes could duplicate an operation: providers return 429 before
  accepting the rate-limited operation; writes also require explicit authority.
- Snapshots can contain sensitive messages: keep them server-local with
  restrictive permissions and rotate any credential exposed in its source.
- CI could change protected contexts: tests run inside the existing OpenSpec
  job, preserving the six required names.

## Rollback

Revert the JUP-081 commit and continue using the previous server-local bridge.
The server `.env` and snapshots are never part of the Git rollback.
