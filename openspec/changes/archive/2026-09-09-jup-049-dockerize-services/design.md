JUP: JUP-049

## Context

`develop` already contains Docker coverage for backend, frontend, processor and
the simulated Azure Cost API, plus CockroachDB, RabbitMQ and Postgres/pgvector.
JUP-049 reconciles that inherited foundation instead of rewriting it. The first
clean remote audit proved that all Python application images build, while the
frontend fails before dependency installation because its isolated build
context has neither the root `packageManager` declaration nor the lockfile.

The final reconciliation with `develop` also includes Prometheus and Grafana
from JUP-043. The current Compose topology therefore contains nine services
and four named volumes (`cockroach-data`, `pgvector-data`, `prometheus-data`
and `grafana-data`); the initial seven-service inventory remains historical.

## Decisions

### Pin executable inputs by digest

Dockerfiles keep readable release tags but add the manifest digest observed
from the registry on 2026-08-27. Compose does the same for the three external
infrastructure images. A tag may aid maintenance, but the digest determines the
bytes used by a build or pull.

This digest baseline applies to the four application bases and the three base
infrastructure images. Prometheus and Grafana retain the release tags inherited
from JUP-043; they are not represented as digest-pinned by this change.

### Build the frontend from the monorepo contract

The frontend build context becomes the repository root. Its Dockerfile copies
only the workspace manifests first, activates pnpm 9.0.0, installs with
`--frozen-lockfile`, then copies and builds the frontend. Runtime starts Vite's
preview server from the generated `dist` output; it does not start the source
development server.

Following JUP-093, the runtime copies `vite.config.ts` to `/tmp` before invoking
the installed Vite binary directly. This permits Vite's temporary configuration
output on the read-only application filesystem without running Corepack or
pnpm at startup. `NODE_PATH` preserves dependency resolution from `/tmp`.

### Apply one least-privilege application baseline

Every application image declares a non-root `USER` and image healthcheck.
Compose adds an init process, read-only root filesystem, `/tmp` tmpfs and
`no-new-privileges` to all four applications. Databases and RabbitMQ retain
their vendor-supported runtime users and writable named volumes.

Prometheus/Grafana preserve their JUP-043 runtime configuration. Prometheus has
a container healthcheck and Grafana waits for healthy Prometheus; Grafana
readiness is checked through `/api/health` in the real smoke, without claiming
that Compose declares a Grafana healthcheck or application hardening baseline.

### Separate static CI from the real smoke

CI parses Compose and Dockerfiles to catch missing services, mutable images,
privileged application defaults, unhealthy dependency gates and frontend
package-manager drift without pulling large images in every workflow run. A
full isolated build and health smoke on `dockerserver` verifies the behavior
that static validation cannot prove.

The final topology validator expects all nine services and four named volumes.
It checks the monitoring mounts, persistence, loopback ports and healthy
dependency gates while preserving the original digest and least-privilege
checks on the JUP-049 baseline. The real smoke exercises monitoring readiness
and verifies that both Prometheus application targets are UP.

### Reconciliation with develop on 2026-09-02

The backend image retains `python -m app.run` from JUP-042 so Uvicorn uses the
application's structured logging configuration. Its pinned base, non-root user
and healthcheck from JUP-049 remain in place.

A fresh-volume smoke exposed concurrent migrations in the processor's combined
worker/API runtime. Both threads can create `vector_schema_migrations` before
either transaction commits; `CREATE TABLE IF NOT EXISTS` does not prevent the
observed PostgreSQL catalog uniqueness failure. The processor migration runner
serializes execution between the two threads started by `app.run_all` with a
process-local lock; coordination between separate processor processes or
replicas remains outside this fix.

### Reconciliation with develop on 2026-09-08

The process-local lock covers the entire `MigrationRunner.run()` invocation:
version-table setup, applied-version lookup and all pending migrations. It
preserves JUP-013's transaction per transactional migration and explicit
autocommit mode for migrations requiring it. It does not wrap all migrations
in one database transaction. The regression test verifies serialization in
both transactional and autocommit modes alongside rollback and retry tests.

The frontend preserves JUP-093's TypeScript configuration and JUP-094's locked
dependencies. Monitoring remains the JUP-043 integration described above. The
final evidence is retained in `docs/evidence/JUP-049-validation.md`, including
the nine-service smoke and 270 passing Python tests on the built images.

### Documentary closure on 2026-09-09

PR #16 was approved by Lucia Mateo (`lmatsan`) and squash-merged into `develop`.
The evidence document's "Cierre y participacion acreditada — 2026-09-09"
section distinguishes implementation and integration contributions from the
recorded review and functional validation. The original pairing/coauthorship
assignment has no explicit completion evidence and is not credited as performed.
Task 3.4 records this reconciled evidence and limitation rather than claiming
an undocumented pairing session.

## Risks and mitigations

- Registry images disappear by digest: keep the human-readable tag and record
  the exact digests in version control so a deliberate upgrade is reviewable.
- Read-only filesystems expose hidden writes: give applications only `/tmp` as
  writable scratch space and exercise startup through the remote smoke.
- Vite configuration is build-time: pass `VITE_API_BASE_URL` as a Compose build
  argument and document that changing it requires rebuilding the frontend.
- The shared server contains unrelated workloads: use a unique Compose project,
  non-default host ports and remove only that explicitly named project after
  validation.

## Rollback

Revert the JUP-049 commit. The existing source applications and persistent data
schemas are unchanged; no migration or production deployment is performed.
