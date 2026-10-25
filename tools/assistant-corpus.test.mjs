import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { stringify } from "yaml";

import { validateAssistantCorpus } from "./assistant-corpus.mjs";

const DOCS = [
  ["finops", "finops.md", "finops.azure-cost-management-mvp"],
  ["business-rules", "rules.md", "business-rules.economicon-mvp"],
  ["glossary", "glossary.md", "glossary.economicon-mvp"],
  ["product-architecture", "architecture.md", "product-architecture.economicon-functional"],
];

function createFixture() {
  const rootDir = fs.mkdtempSync(path.join(os.tmpdir(), "assistant-corpus-"));
  const corpusRoot = path.join(rootDir, "docs", "assistant-corpus");
  fs.mkdirSync(corpusRoot, { recursive: true });

  const documents = DOCS.map(([category, fileName, id]) => {
    const dir = path.join(corpusRoot, category);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, fileName), `# ${id}\n\nFixture content.\n`, "utf8");

    return {
      id,
      title: id,
      path: `docs/assistant-corpus/${category}/${fileName}`,
      category,
      tags: [category, "mvp"],
      language: "es",
      version: "1.0.0",
      scope: category === "business-rules" ? "dataset" : "global",
      tenant_id: null,
      dataset_id: category === "business-rules" ? "economicon-mvp-azure-simulated" : null,
      source_type: category === "business-rules" ? "internal_business_rules" : "curated_reference",
      updated_at: "2026-08-12",
    };
  });

  return { rootDir, manifest: { version: 1, corpus: "assistant-document-corpus", documents } };
}

function writeManifest(rootDir, manifest) {
  fs.writeFileSync(
    path.join(rootDir, "docs", "assistant-corpus", "manifest.yaml"),
    stringify(manifest),
    "utf8",
  );
}

function validateFixture(mutator = () => {}) {
  const fixture = createFixture();
  mutator(fixture);
  writeManifest(fixture.rootDir, fixture.manifest);
  return validateAssistantCorpus(fixture.rootDir);
}

function hasIssue(issues, expected) {
  return issues.some((issue) => issue.includes(expected));
}

test("accepts a valid minimal assistant corpus manifest", () => {
  assert.deepEqual(validateFixture(), []);
});

test("rejects duplicate document IDs", () => {
  const issues = validateFixture(({ manifest }) => {
    manifest.documents[1].id = manifest.documents[0].id;
  });

  assert.equal(hasIssue(issues, "Duplicate document id"), true);
});

test("rejects invalid categories", () => {
  const issues = validateFixture(({ manifest }) => {
    manifest.documents[0].category = "invalid";
  });

  assert.equal(hasIssue(issues, "category has invalid value"), true);
  assert.equal(hasIssue(issues, "Missing required corpus category in manifest: finops"), true);
});

test("rejects invalid scopes", () => {
  const issues = validateFixture(({ manifest }) => {
    manifest.documents[0].scope = "workspace";
  });

  assert.equal(hasIssue(issues, "scope has invalid value"), true);
});

test("rejects inconsistent dataset scope metadata", () => {
  const issues = validateFixture(({ manifest }) => {
    manifest.documents[1].dataset_id = null;
  });

  assert.equal(hasIssue(issues, "scope dataset must set dataset_id"), true);
});

test("rejects missing referenced paths", () => {
  const issues = validateFixture(({ manifest }) => {
    manifest.documents[0].path = "docs/assistant-corpus/finops/missing.md";
  });

  assert.equal(hasIssue(issues, "path does not exist"), true);
});

test("rejects empty referenced documents", () => {
  const issues = validateFixture(({ rootDir }) => {
    fs.writeFileSync(path.join(rootDir, "docs", "assistant-corpus", "finops", "finops.md"), "", "utf8");
  });

  assert.equal(hasIssue(issues, "references an empty document"), true);
});

test("rejects indexable markdown files that are not declared in the manifest", () => {
  const issues = validateFixture(({ rootDir }) => {
    fs.writeFileSync(
      path.join(rootDir, "docs", "assistant-corpus", "finops", "extra.md"),
      "# Extra\n",
      "utf8",
    );
  });

  assert.equal(hasIssue(issues, "not declared in manifest"), true);
});
