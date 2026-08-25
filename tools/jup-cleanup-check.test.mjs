import assert from "node:assert/strict";
import test from "node:test";

import { validateTrackedFiles } from "./jup-cleanup-check.mjs";

test("accepts project files and Trello-aligned OpenSpec changes", () => {
  assert.deepEqual(
    validateTrackedFiles([
      "AGENTS.md",
      "apps/backend/app/main.py",
      "docs/spikes/frontend-migration.md",
      "openspec/changes/jup-082-clean-develop/proposal.md",
      "openspec/specs/health-status/spec.md",
    ]),
    [],
  );
});

test("rejects personal assistant configuration", () => {
  const errors = validateTrackedFiles([
    ".claude/skills/personal/SKILL.md",
    ".codex/skills/personal/SKILL.md",
  ]);
  assert.equal(errors.length, 2);
});

test("rejects vendor memory tools and unrelated Windows executables", () => {
  const errors = validateTrackedFiles([
    "tools/engram/README.md",
    "downloads/vendor.exe",
  ]);
  assert.equal(errors.length, 2);
  assert.ok(errors.some((error) => error.includes("vendor.exe")));
});

test("rejects active and archived parallel task proposals", () => {
  const errors = validateTrackedFiles([
    "openspec/changes/hu-082-clean-develop/proposal.md",
    "openspec/changes/archive/2026-08-25-hu-082-clean-develop/proposal.md",
  ]);
  assert.equal(errors.length, 2);
});

test("rejects obsolete task templates and task-specific tooling", () => {
  const errors = validateTrackedFiles([
    "docs/templates/hu/proposal.md",
    "tools/hu-check.mjs",
  ]);
  assert.equal(errors.length, 2);
});

test("normalizes Windows separators before checking repository paths", () => {
  const errors = validateTrackedFiles([
    ".codex\\skills\\personal\\SKILL.md",
    "openspec\\changes\\hu-082-clean-develop\\proposal.md",
  ]);
  assert.equal(errors.length, 2);
});
