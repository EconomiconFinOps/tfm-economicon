import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { execFileSync, spawnSync } from "node:child_process";
import test from "node:test";
import { digest, prepareInputs, root, suitePath, validateSuite } from "./validation-questions.mjs";

const read = () => JSON.parse(fs.readFileSync(path.join(root, suitePath), "utf8"));

test("versioned battery has complete coverage and unchanged source documents", () => {
  assert.deepEqual(validateSuite(read()), []);
});

test("rejects duplicate IDs, missing context, unknown sources and empty rubrics", () => {
  const suite = read();
  suite.cases[1].id = suite.cases[0].id;
  suite.cases[0].context = "";
  suite.cases[0].sources = ["missing"];
  suite.cases[0].expected.required = [];
  const errors = validateSuite(suite).join("\n");
  for (const pattern of [/ID inválido o duplicado/, /falta pregunta o contexto/, /referencias desconocidas/, /faltan criterios/]) {
    assert.match(errors, pattern);
  }
});

test("rejects missing topic and abstention coverage", () => {
  const suite = read();
  suite.cases = suite.cases.filter((item) => item.category !== "scope");
  const errors = validateSuite(suite).join("\n");
  assert.match(errors, /Sin cobertura: scope/);
  assert.match(errors, /Sin comportamiento: abstain/);
});

test("source drift, missing files and paths outside the repository fail closed", () => {
  for (const mutation of [
    (source) => { source.sha256 = "0".repeat(64); },
    (source) => { source.path = "docs/does-not-exist.md"; },
    (source) => { source.path = "../outside.md"; },
  ]) {
    const suite = read();
    mutation(suite.sources.rules);
    assert.ok(validateSuite(suite).some((error) => error.startsWith("Fuente rules:")));
  }
  assert.equal(digest("a\r\nb\r\n"), digest("a\nb\n"));
});

test("malformed structures and invalid numerical tolerances produce errors", () => {
  for (const bad of [null, [], {}, { ...read(), cases: null }, { ...read(), sources: [] }]) {
    assert.ok(validateSuite(bad).length > 0);
  }
  for (const bad of [null, { value: 2, tolerance: -1 }, { label: "cost", value: Infinity, unit: "EUR", tolerance: 0.01 }]) {
    const suite = read();
    suite.cases[0].expected.numbers = [bad];
    assert.ok(validateSuite(suite).some((error) => error.includes("numérica inválida")));
  }
});

test("prepared prompts are stable, isolated and do not leak answer keys", () => {
  const suite = read();
  const prepared = prepareInputs(suite);
  assert.deepEqual(prepareInputs(suite), prepared);
  assert.equal(prepared.cases.length, suite.cases.length);
  for (const item of prepared.cases) assert.deepEqual(Object.keys(item), ["id", "prompt"]);
  const changed = structuredClone(suite);
  changed.cases[0].expected.required = ["SECRET ANSWER KEY"];
  changed.cases[0].behavior = "SECRET BEHAVIOR";
  assert.deepEqual(prepareInputs(changed).cases, prepared.cases);
  assert.notEqual(prepareInputs(changed).suite_sha256, prepared.suite_sha256);
  assert.ok(!JSON.stringify(prepareInputs(changed)).includes("SECRET"));
});

test("numeric answer keys agree with independently calculated scenario arithmetic", () => {
  const values = (suffix) => read().cases.find((item) => item.id === `JUP-069-${suffix}`).expected.numbers.map((n) => n.value);
  assert.deepEqual(values("001"), [600 + 250 + 150, 600, 600 / 1000 * 100]);
  assert.deepEqual(values("002"), [1000 - 800, (1000 - 800) / 800 * 100]);
  assert.deepEqual(values("005"), [700 + 200 + 100, 100 / 1000 * 100]);
  assert.deepEqual(values("011"), [100 / (100 + 900) * 100]);
  assert.deepEqual(values("013"), [1200 - 1000, 200 / 1000 * 100]);
  assert.deepEqual(values("016"), [550 - 400, 150 / 400 * 100]);
  assert.deepEqual(values("017"), [500 - 400, 100 / 400 * 100]);
  assert.deepEqual(values("018"), [1200 - 1000, 200 / 1000 * 100]);
  assert.deepEqual(values("021"), [80, 80 / 200 * 100]);
  assert.deepEqual(values("027"), [1000 / 100, 1200 / 200, (10 - 6) / 10 * 100]);
});

test("CLI emits parseable prompts from another working directory and rejects unknown commands", () => {
  const cli = path.join(root, "tools/validation-questions.mjs");
  const output = execFileSync(process.execPath, [cli, "prepare"], { cwd: path.dirname(root), encoding: "utf8" });
  assert.deepEqual(JSON.parse(output), prepareInputs(read()));
  assert.equal(spawnSync(process.execPath, [cli, "evaluate"]).status, 2);
});
