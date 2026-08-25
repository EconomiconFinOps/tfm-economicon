import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { checkChange, parseChange } from "./jup-check.mjs";

function fixture(change = "jup-082-clean-develop") {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "economicon-jup-check-"));
  const dir = path.join(root, "openspec", "changes", change);
  fs.mkdirSync(path.join(dir, "specs", "repository-jup-hygiene"), {
    recursive: true,
  });
  fs.writeFileSync(path.join(dir, ".openspec.yaml"), "schema: spec-driven\n");
  fs.writeFileSync(
    path.join(dir, "proposal.md"),
    "JUP: JUP-082\nTrello: https://trello.com/c/example\n",
  );
  fs.writeFileSync(path.join(dir, "design.md"), "JUP: JUP-082\n");
  fs.writeFileSync(path.join(dir, "tasks.md"), "- [ ] Verify the change\n");
  fs.writeFileSync(
    path.join(dir, "specs", "repository-jup-hygiene", "spec.md"),
    "## ADDED Requirements\n",
  );
  return root;
}

test("parses the forwarded change argument", () => {
  assert.equal(
    parseChange(["--change", "jup-082-clean-develop"]),
    "jup-082-clean-develop",
  );
});

test("accepts a complete Trello-linked JUP change", () => {
  const root = fixture();
  try {
    assert.deepEqual(checkChange(root, "jup-082-clean-develop"), []);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("rejects parallel numbering and missing Trello links", () => {
  const root = fixture();
  const proposal = path.join(
    root,
    "openspec",
    "changes",
    "jup-082-clean-develop",
    "proposal.md",
  );
  fs.writeFileSync(proposal, "JUP: JUP-082\nRelated: HU-082\n");
  try {
    const errors = checkChange(root, "jup-082-clean-develop");
    assert.ok(errors.some((error) => error.includes("Trello")));
    assert.ok(errors.some((error) => error.includes("HU")));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("rejects identifiers that do not match the change directory", () => {
  const root = fixture("jup-083-different-task");
  try {
    const errors = checkChange(root, "jup-083-different-task");
    assert.ok(errors.some((error) => error.includes("JUP-083")));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("rejects invalid change names", () => {
  assert.deepEqual(checkChange(".", "hu-082-clean-develop"), [
    "El change debe usar jup-NNN-descripcion-en-kebab-case.",
  ]);
});

test("requires the proposal, design, metadata and delta specifications", () => {
  const root = fixture();
  const changeDir = path.join(
    root,
    "openspec",
    "changes",
    "jup-082-clean-develop",
  );
  fs.unlinkSync(path.join(changeDir, ".openspec.yaml"));
  fs.unlinkSync(path.join(changeDir, "tasks.md"));
  fs.unlinkSync(
    path.join(changeDir, "specs", "repository-jup-hygiene", "spec.md"),
  );
  try {
    const errors = checkChange(root, "jup-082-clean-develop");
    assert.ok(errors.some((error) => error.includes(".openspec.yaml")));
    assert.ok(errors.some((error) => error.includes("tasks.md")));
    assert.ok(errors.some((error) => error.includes("delta spec")));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
