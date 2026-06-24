import test from "node:test";
import assert from "node:assert/strict";

import {
  hasAnyTask,
  hasOpenTasks,
  hasProductChanges,
  hasStructuredApproval,
  legacyApprovalMatchesInText,
  parseArgs,
  parseMarkdownTable,
  parseReviewFindings,
  reviewFindingNeedsBacklog,
  validateBacklogMarkdown,
} from "./hu-check.mjs";

test("parses pnpm forwarded arguments", () => {
  assert.deepEqual(parseArgs(["node", "tools/hu-check.mjs", "check", "--", "--change", "hu-006"]), {
    command: "check",
    change: "hu-006",
  });
  assert.deepEqual(parseArgs(["node", "tools/hu-check.mjs", "pre-code", "--", "--change", "hu-007"]), {
    command: "pre-code",
    change: "hu-007",
  });
});

test("detects open, completed, and present tasks", () => {
  assert.equal(hasOpenTasks("- [ ] pending\n- [x] done"), true);
  assert.equal(hasOpenTasks("- [x] done\n- [X] also done"), false);
  assert.equal(hasAnyTask("No tasks here"), false);
  assert.equal(hasAnyTask("- [ ] pending"), true);
});

test("detects only structured HiTL approvals", () => {
  const markdown = `
## Human Approval

- Approval type: pre-code
- Decision: approved

## Other

text

## Human Approval

- Approval type: post-review
- Decision: approved
`;
  assert.equal(hasStructuredApproval(markdown, "pre-code"), true);
  assert.equal(hasStructuredApproval(markdown, "post-review"), true);
  const legacy = ["Pre-code", " approval", ": approved"].join("");
  assert.equal(hasStructuredApproval(`- ${legacy}`, "pre-code"), false);
});

test("detects legacy approval wording without storing it directly", () => {
  const preLegacy = ["Pre-code", " approval", ": approved"].join("");
  const postLegacy = ["Post-review", " approval", ": approved"].join("");
  const matches = legacyApprovalMatchesInText(`- ${preLegacy}\n- ${postLegacy}`, "fixture.md");
  assert.deepEqual(matches.map((match) => `${match.filePath}:${match.line}`), ["fixture.md:1", "fixture.md:2"]);
});

test("does not flag structured approval templates", () => {
  const markdown = `
## Human Approval

- Approval type: pre-code
- Decision: approved
`;
  assert.deepEqual(legacyApprovalMatchesInText(markdown), []);
});

test("parses markdown tables with required columns", () => {
  const markdown = `
| ID | Scope | Backlog |
|----|-------|---------|
| RF-004-001 | Out of scope | Added |
`;

  const tables = parseMarkdownTable(markdown, ["ID", "Scope"]);
  assert.equal(tables.length, 1);
  assert.equal(tables[0].rows[0].ID, "RF-004-001");
});

test("parses review findings and backlog requirement", () => {
  const markdown = `
## Review Findings

| ID | Tipo | Severidad | Scope | Descripcion | Accion | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-004-001 | Test drift | Medium | Out of scope | Fails | Create HU | Added |
`;

  const parsed = parseReviewFindings(markdown);
  assert.equal(parsed.missingSection, false);
  assert.equal(parsed.findings.length, 1);
  assert.equal(reviewFindingNeedsBacklog(parsed.findings[0]), true);
});

test("validates findings backlog ids and states", () => {
  const valid = `
| ID | Fecha | Origen | Tipo | Severidad | Scope | Estado | Owner | Accion | Change/Fix |
|----|-------|--------|------|-----------|-------|--------|-------|--------|------------|
| RF-004-001 | 2026-06-24 | hu-004 | Test drift | Medium | Out of scope | Open | TBD | Fix | TBD |
`;
  assert.deepEqual(validateBacklogMarkdown(valid), []);

  const invalid = valid.replace("RF-004-001", "BAD-1").replace("Open", "Pending");
  assert.deepEqual(validateBacklogMarkdown(invalid), [
    "Invalid finding ID: BAD-1",
    "Invalid finding state for BAD-1: Pending",
  ]);
});

test("detects product changes in git porcelain output", () => {
  assert.equal(hasProductChanges(" M apps/backend/app/main.py\n?? docs/new.md"), true);
  assert.equal(hasProductChanges("?? packages/new/file.ts"), true);
  assert.equal(hasProductChanges(" M docs/plan.md\n?? tools/hu-check.mjs\n?? openspec/changes/x/proposal.md"), false);
});
