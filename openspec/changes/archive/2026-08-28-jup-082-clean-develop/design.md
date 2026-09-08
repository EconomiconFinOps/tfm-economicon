JUP: JUP-082
ADR: not applicable

## Context

The current `develop` branch contains 11 commits above `main`. Those commits include useful frontend migration research, backend health timestamps and tests, normalized demo authentication, OpenSpec specifications and architectural guidance. They also add personal agent skills, a 19,732,480-byte Windows executable, unrelated memory tooling and a parallel task inventory that conflicts with Trello.

## Goals / Non-Goals

**Goals:**

- Preserve all existing product code and useful project documentation.
- Keep OpenSpec operational while identifying every new change with its Trello `JUP-XXX` task.
- Remove unrelated tracked assets and prevent their accidental reintroduction.
- Deliver the cleanup as a reviewable pull request targeting `develop`.

**Non-Goals:**

- Rewriting shared Git history or pushing directly to `develop` or `main`.
- Implementing the separate frontend migration, documentary corpus or CI tasks.
- Replacing Trello with repository-local planning or introducing assistant-specific dependencies.

## Decisions

### Preserve useful work by cleaning the existing branch contents

The cleanup branch starts at the current `develop` HEAD. Unrelated assets are removed selectively while application code, existing capability specifications, architecture documentation and the frontend migration spike are preserved. Obsolete workflow references inside the spike are updated without changing its technical findings. This keeps the original commit history available and avoids rewriting shared branches.

### Use Trello as operational truth and OpenSpec as technical evidence

Every change references a direct Trello URL and the same `JUP-XXX` identifier in its branch, proposal and design. A lightweight Node.js checker verifies required OpenSpec artifacts and detects identifier drift.

### Enforce repository hygiene through tracked-file inspection

A separate Node.js checker inspects tracked and untracked non-ignored repository files. It rejects personal assistant configuration, vendored memory executables, platform-specific binaries and duplicate active or archived task proposals. Unit tests document the supported and rejected cases.

## Risks / Trade-offs

- [Existing feature branches were created from the unclean base] -> Rebase them onto cleaned `develop` after this PR is merged, preserving their valid independent changes.
- [Archived duplicate task proposals are removed] -> Their historical contents remain recoverable from the original commits in Git history.
- [OpenSpec dependencies differ across machines] -> Pin a known compatible CLI release and validate the committed lockfile.
- [The existing frontend baseline reports 49 missing react/prop-types declarations] -> Record RF-082-002 and handle it in a dedicated Trello task; do not modify product code or frontend lint configuration in this cleanup.
