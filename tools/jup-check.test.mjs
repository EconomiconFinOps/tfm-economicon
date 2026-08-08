import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { checkChange, parseChange } from "./jup-check.mjs";

function fixture(change = "jup-078-llm-provider-adr") {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "jup-check-"));
  const dir = path.join(root, "openspec", "changes", change);
  fs.mkdirSync(path.join(dir, "specs", "llm-gateway"), { recursive: true });
  fs.writeFileSync(path.join(dir, ".openspec.yaml"), "schema: spec-driven\n");
  fs.writeFileSync(path.join(dir, "proposal.md"), "JUP: JUP-078\nTrello: https://trello.com/c/example\n");
  fs.writeFileSync(path.join(dir, "design.md"), "# JUP-078 design\n");
  fs.writeFileSync(path.join(dir, "tasks.md"), "- [ ] JUP-078 task\n");
  fs.writeFileSync(path.join(dir, "specs", "llm-gateway", "spec.md"), "# JUP-078 spec\n");
  return root;
}

test("parses the forwarded change argument", () => {
  assert.equal(parseChange(["--change", "jup-078-llm-provider-adr"]), "jup-078-llm-provider-adr");
});

test("accepts a complete JUP-linked change", () => {
  const root = fixture();
  try {
    assert.deepEqual(checkChange(root, "jup-078-llm-provider-adr"), []);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("rejects parallel numbering and missing Trello links", () => {
  const root = fixture();
  const proposal = path.join(root, "openspec", "changes", "jup-078-llm-provider-adr", "proposal.md");
  fs.writeFileSync(proposal, "JUP: JUP-078\nRelated: HU-078\n");
  try {
    const errors = checkChange(root, "jup-078-llm-provider-adr");
    assert.ok(errors.some((error) => error.includes("Trello")));
    assert.ok(errors.some((error) => error.includes("paralela")));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("rejects invalid change names", () => {
  assert.deepEqual(checkChange(".", "hu-078-provider"), ["El change debe usar jup-NNN-descripcion-en-kebab-case."]);
});
