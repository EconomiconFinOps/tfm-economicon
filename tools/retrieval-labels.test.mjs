import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { digest, suitePath } from "./validation-questions.mjs";
import { labelsPath, root, validateLabels } from "./retrieval-labels.mjs";

const DOC_A = ["# Guia", "", "## Tags", "Texto.", "", "## Umbrales", "Texto.", "", "## Repetido", "a", "", "## Repetido", "b", ""].join("\n");
const DOC_B = ["# Otra", "", "## Definicion", "Texto.", "", "```text", "## Falso encabezado", "```", ""].join("\n");

// A tiny repository with a two-source bank and three cases, so each rule can be broken on its own.
function fixture() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "jup022-labels-"));
  fs.mkdirSync(path.join(dir, "docs"), { recursive: true });
  fs.writeFileSync(path.join(dir, "docs/a.md"), DOC_A);
  fs.writeFileSync(path.join(dir, "docs/b.md"), DOC_B);
  const sources = {
    a: { path: "docs/a.md", sha256: digest(DOC_A) },
    b: { path: "docs/b.md", sha256: digest(DOC_B) },
  };
  const suite = {
    suite_version: "1.0.0",
    sources,
    cases: [
      { id: "JUP-069-001", sources: ["a"] },
      { id: "JUP-069-002", sources: ["a", "b"] },
      { id: "JUP-069-003", sources: ["b"] },
    ],
  };
  const labels = {
    schema_version: 1,
    jup: "JUP-022",
    trello: "https://trello.com/c/DPZpQ09b",
    bank: { path: suitePath, suite_version: "1.0.0" },
    sources: structuredClone(sources),
    labels: [
      { case: "JUP-069-001", coverage: "direct", expect: [{ source: "a", heading: "Tags" }] },
      { case: "JUP-069-002", coverage: "partial", expect: [{ source: "a", heading: "Umbrales" }, { source: "b", heading: "Definicion" }] },
      { case: "JUP-069-003", coverage: "none", expect: [], note: "El corpus no trata este tema." },
    ],
  };
  return { dir, suite, labels };
}
const run = ({ dir, suite, labels }) => validateLabels(labels, { repoRoot: dir, suite }).join("\n");

test("a consistent labels file has no errors", () => {
  assert.equal(run(fixture()), "");
});

test("rejects a case that the bank does not contain and a case without a label", () => {
  const f = fixture();
  f.labels.labels[0].case = "JUP-069-099";
  const errors = run(f);
  assert.match(errors, /JUP-069-099/);
  assert.match(errors, /JUP-069-001.*sin etiqueta/);
});

test("rejects a case labelled twice", () => {
  const f = fixture();
  f.labels.labels.push({ ...f.labels.labels[0] });
  assert.match(run(f), /JUP-069-001.*duplicad/);
});

test("rejects a source that the case does not declare", () => {
  const f = fixture();
  f.labels.labels[0].expect = [{ source: "b", heading: "Definicion" }];
  assert.match(run(f), /JUP-069-001.*fuente b/);
});

test("rejects a heading that does not exist in the document", () => {
  const f = fixture();
  f.labels.labels[0].expect = [{ source: "a", heading: "No existe" }];
  assert.match(run(f), /JUP-069-001.*No existe/);
});

test("ignores heading-like lines inside code fences", () => {
  const f = fixture();
  f.labels.labels[1].expect = [{ source: "b", heading: "Falso encabezado" }];
  assert.match(run(f), /JUP-069-002.*Falso encabezado/);
});

test("rejects an ambiguous heading", () => {
  const f = fixture();
  f.labels.labels[0].expect = [{ source: "a", heading: "Repetido" }];
  assert.match(run(f), /JUP-069-001.*ambiguo/);
});

test("rejects a label that repeats the same section", () => {
  const f = fixture();
  f.labels.labels[0].expect = [{ source: "a", heading: "Tags" }, { source: "a", heading: "Tags" }];
  assert.match(run(f), /JUP-069-001.*repetida/);
});

test("rejects a document that changed after labelling", () => {
  const f = fixture();
  fs.writeFileSync(path.join(f.dir, "docs/a.md"), DOC_A + "\nNueva linea.\n");
  assert.match(run(f), /contenido cambiado.*etiquetas/);
});

test("rejects labels whose sources or bank version differ from the bank", () => {
  const f = fixture();
  f.labels.sources.a.sha256 = "0".repeat(64);
  f.labels.bank.suite_version = "9.9.9";
  const errors = run(f);
  assert.match(errors, /fuente a/);
  assert.match(errors, /banco cambiado/);
});

test("enforces the coverage rules", () => {
  const f = fixture();
  f.labels.labels[0].expect = [];
  f.labels.labels[1].coverage = "none";
  f.labels.labels[2].note = "";
  f.labels.labels.push({ case: "JUP-069-001", coverage: "mal", expect: [] });
  const errors = run(f);
  assert.match(errors, /JUP-069-001.*cobertura direct o partial/);
  assert.match(errors, /JUP-069-002.*cobertura none/);
  assert.match(errors, /JUP-069-003.*nota/);
  assert.match(errors, /cobertura invalida/);
});

test("accepts a gap with coverage none and a note", () => {
  const f = fixture();
  assert.equal(f.labels.labels[2].coverage, "none");
  assert.equal(run(f), "");
});

test("gives the same result whatever the line endings of the documents", () => {
  const f = fixture();
  fs.writeFileSync(path.join(f.dir, "docs/a.md"), DOC_A.replaceAll("\n", "\r\n"));
  fs.writeFileSync(path.join(f.dir, "docs/b.md"), DOC_B.replaceAll("\n", "\r\n"));
  assert.equal(run(f), "");
});

test("rejects a source path outside the repository", () => {
  const f = fixture();
  f.suite.sources.a.path = "../fuera.md";
  f.labels.sources.a.path = "../fuera.md";
  assert.match(run(f), /fuente a.*fuera del repositorio/);
});

test("the committed labels file matches the committed question bank and leaves the bank untouched", () => {
  const bankFile = path.join(root, suitePath);
  const before = digest(fs.readFileSync(bankFile, "utf8"));
  const labels = JSON.parse(fs.readFileSync(path.join(root, labelsPath), "utf8"));
  assert.deepEqual(validateLabels(labels), []);
  assert.equal(digest(fs.readFileSync(bankFile, "utf8")), before);
});

test("the command line validates the committed file and rejects an unknown argument", () => {
  const ok = spawnSync(process.execPath, [path.join(root, "tools/retrieval-labels.mjs"), "validate"], { encoding: "utf8" });
  assert.equal(ok.status, 0, ok.stderr);
  assert.match(ok.stdout, /\[OK\]/);
  const bad = spawnSync(process.execPath, [path.join(root, "tools/retrieval-labels.mjs"), "otra"], { encoding: "utf8" });
  assert.equal(bad.status, 2);
});

test("rejects an expect field that is not a list, whatever the coverage", () => {
  for (const bad of ["Tags", { source: "a", heading: "Tags" }, 7]) {
    for (const coverage of ["none", "direct"]) {
      const f = fixture();
      f.labels.labels[2] = { case: "JUP-069-003", coverage, expect: bad, note: "El corpus no trata este tema." };
      assert.match(run(f), /JUP-069-003.*expect debe ser una lista/);
    }
  }
});
