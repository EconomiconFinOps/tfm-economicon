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
- [ ] Run `pnpm hu:check:pre-code -- --change <change-name>` before product code changes.
- [ ] Execute with `/opsx:apply <change-name>`.
- [ ] Mark completed tasks in `tasks.md`.
- [ ] Run required checks: install, validate, test, lint, build, or focused checks accepted for the selected carril.
- [ ] Record exact validation commands and any environment setup used for checks.
- [ ] Review docs/code drift.
- [ ] Run structural anti-harness checks.
- [ ] Interpret `rg` anti-harness output as informational when matches are documentation-only.
- [ ] Record review.
- [ ] Record review findings in `review.md`.
- [ ] Add every out-of-scope, unresolved, or deferred finding to `openspec/findings/backlog.md`.
- [ ] Link each backlog finding to its HU origin.
- [ ] If this HU fixes an existing finding, update its status in `openspec/findings/backlog.md`.
- [ ] Run `pnpm hu:check:findings` when the findings backlog changes.
- [ ] Confirm there are no findings without a decision before HiTL final.
- [ ] Record post-review HiTL approval.
- [ ] Run `pnpm hu:check:approval-format`.
- [ ] Run `pnpm hu:check -- --change <change-name>` before archive.
- [ ] Sync specs if applicable.
- [ ] Archive change; use `--skip-specs` for doc-only/process changes.
```
