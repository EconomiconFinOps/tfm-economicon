JUP: JUP-049
Trello: https://trello.com/c/yZnjgiSp

## Why

The repository declares Dockerfiles for the four MVP applications and a root
Compose topology, but the complete build is not reproducible. On 2026-08-27 a
clean build on `dockerserver` failed because the frontend image let Corepack
select pnpm 11 on Node 20. The backend and processor also ran as root, three
application filesystems remained writable and several base or infrastructure
images could change without a repository change.

## What Changes

- Pin application base images and infrastructure images by immutable digest.
- Install the repository-declared pnpm 9 release and the locked frontend
  dependency graph from the monorepo root.
- Build the frontend before starting a preview server instead of exposing the
  Vite development server.
- Run every application as a non-root user with an init process, a read-only
  root filesystem, a writable temporary directory and no privilege escalation.
- Require healthchecks and healthy dependency gates for the complete topology.
- Add a fast topology validator to the existing OpenSpec CI context and retain
  a real isolated build and smoke test as JUP-049 evidence.

## Capabilities

### New Capabilities

- containerized-runtime: reproducible, least-privilege application images and
  an automatically validated seven-service MVP topology.

### Modified Capabilities

- None.

## Out of Scope

- Claiming that one command starts a fully configured developer environment;
  that acceptance belongs to JUP-050.
- Deploying automatically to `dockerserver`; that belongs to JUP-052.
- Rotating or provisioning real secrets; that belongs to JUP-053.
- Adding the production LiteLLM gateway or replacing the current mock provider;
  that belongs to JUP-023.

## Impact

Changes the four application Dockerfiles, the root Compose topology, frontend
Docker build context, CI governance validation and container documentation.
The validation uses an isolated Compose project on `dockerserver` and does not
replace or restart unrelated containers.
