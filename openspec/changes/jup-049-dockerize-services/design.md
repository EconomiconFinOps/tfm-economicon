JUP: JUP-049

## Context

`develop` already contains Docker coverage for backend, frontend, processor and
the simulated Azure Cost API, plus CockroachDB, RabbitMQ and Postgres/pgvector.
JUP-049 reconciles that inherited foundation instead of rewriting it. The first
clean remote audit proved that all Python application images build, while the
frontend fails before dependency installation because its isolated build
context has neither the root `packageManager` declaration nor the lockfile.

## Decisions

### Pin executable inputs by digest

Dockerfiles keep readable release tags but add the manifest digest observed
from the registry on 2026-08-27. Compose does the same for the three external
infrastructure images. A tag may aid maintenance, but the digest determines the
bytes used by a build or pull.

### Build the frontend from the monorepo contract

The frontend build context becomes the repository root. Its Dockerfile copies
only the workspace manifests first, activates pnpm 9.0.0, installs with
`--frozen-lockfile`, then copies and builds the frontend. Runtime starts Vite's
preview server from the generated `dist` output; it does not start the source
development server.

### Apply one least-privilege application baseline

Every application image declares a non-root `USER` and image healthcheck.
Compose adds an init process, read-only root filesystem, `/tmp` tmpfs and
`no-new-privileges` to all four applications. Databases and RabbitMQ retain
their vendor-supported runtime users and writable named volumes.

### Separate static CI from the real smoke

CI parses Compose and Dockerfiles to catch missing services, mutable images,
privileged application defaults, unhealthy dependency gates and frontend
package-manager drift without pulling large images in every workflow run. A
full isolated build and health smoke on `dockerserver` verifies the behavior
that static validation cannot prove.

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
