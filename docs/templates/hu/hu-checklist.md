# HU Checklist

Copy this into each OpenSpec change and adapt it to the selected carril.

```md
## HU Checklist

- [ ] Create OpenSpec change with name `hu-NNN-slug`.
- [ ] Complete PRD/proposal.
- [ ] Complete TD/design.
- [ ] Complete specs if OpenSpec requires them.
- [ ] Complete verifiable tasks.
- [ ] Record pre-code HiTL approval.
- [ ] Run `pnpm openspec:validate`.
- [ ] Execute with `/opsx:apply <change-name>`.
- [ ] Mark completed tasks in `tasks.md`.
- [ ] Run required checks: install, validate, test, lint, build.
- [ ] Review docs/code drift.
- [ ] Run structural anti-harness checks.
- [ ] Interpret `rg` anti-harness output as informational when matches are documentation-only.
- [ ] Record review.
- [ ] Record review findings in `review.md`.
- [ ] Add every out-of-scope, unresolved, or deferred finding to `openspec/findings/backlog.md`.
- [ ] Link each backlog finding to its HU origin.
- [ ] If this HU fixes an existing finding, update its status in `openspec/findings/backlog.md`.
- [ ] Confirm there are no findings without a decision before HiTL final.
- [ ] Record post-review HiTL approval.
- [ ] Sync specs if applicable.
- [ ] Archive change; use `--skip-specs` for doc-only/process changes.
```
