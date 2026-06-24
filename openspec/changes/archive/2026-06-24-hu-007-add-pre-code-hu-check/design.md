## Context

The project now has `hu:check` as a pre-archive gate. That command intentionally requires review and post-review approval, so it cannot validate the earlier checkpoint before implementation starts.

## Goals / Non-Goals

**Goals:**

- Add a pre-code gate for active OpenSpec changes.
- Align approval parsing with the structured HU templates.
- Block product code changes that appear before pre-code approval.
- Keep the harness local, dependency-free, and structural.

**Non-Goals:**

- No product test/lint/build execution.
- No CI or hooks.
- No old approval format compatibility for future HUs.
- No fix for `RF-004-001`.

## Decisions

- Add a `pre-code` command to the existing `tools/hu-check.mjs` CLI.
- Require `Approval type: pre-code` and `Decision: approved` inside a `## Human Approval` block.
- Update the existing `check` command to require structured `pre-code` and `post-review` approvals.
- Treat `apps/**` and `packages/**` as product code paths for the pre-code product-change guard.
- Allow docs, OpenSpec artifacts, and tools changes before execution because the HU itself is documented and planned before code work starts.

## Risks / Trade-offs

- Older archived HUs use the previous approval wording -> Accepted; the new harness governs future active HUs.
- Git status path checks are simple -> Accepted; they are enough to distinguish current product paths from process/tooling paths.
- A tooling HU can modify `tools/**` before pre-code check -> Accepted; this gate is specifically about preventing product changes before approval.

## Open Questions

- None for this phase.
