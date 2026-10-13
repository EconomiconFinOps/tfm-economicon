import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { calculateMetrics, validateRun } from "./business-metrics.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const filename = path.join(root, "docs/validation/JUP-068-example.json");
const example = () => JSON.parse(fs.readFileSync(filename, "utf8"));

test("calculates paired time including negative savings and excludes incorrect answers", () => {
  const report = calculateMetrics(example());
  assert.equal(report.provenance, "synthetic");
  assert.equal(report.time.saved_ms, 360000);
  assert.equal(report.time.saved_percent, 40);
  assert.equal(report.time.pairs[1].saved_ms, -60000);
  assert.deepEqual(report.time.results, { pass: 2, fail: 1, blocked: 0, not_run: 0 });
});
test("uses cost weights and separates shared from assigned and excluded", () => {
  const a = calculateMetrics(example()).allocation;
  assert.equal(a.total_minor, 105000);
  assert.equal(a.eligible_minor, 100000);
  assert.equal(a.assigned_percent, 70);
  assert.equal(a.governed_percent, 90);
  assert.equal(a.unallocated_percent, 10);
});
test("sums supported potential only, preserving candidates and unknown realized savings", () => {
  const s = calculateMetrics(example()).savings;
  assert.equal(s.potential_minor, 14000);
  assert.ok(Math.abs(s.potential_percent - 14) < 1e-10);
  assert.equal(s.candidate_count, 1);
  assert.equal(s.realized_minor, null);
});
test("empty measurements and zero denominators remain unavailable", () => {
  const run = example(); run.trials = []; run.costs = []; run.opportunities = [];
  const report = calculateMetrics(run);
  assert.equal(report.time.saved_ms, null);
  assert.equal(report.time.saved_percent, null);
  assert.equal(report.allocation.assigned_percent, null);
  assert.equal(report.savings.potential_minor, null);
  run.costs = [{ ...example().costs[0], amount_minor: 0 }];
  assert.equal(calculateMetrics(run).allocation.governed_percent, null);
});
test("known zero saving differs from no quantified opportunity", () => {
  const run = example(); run.opportunities[0].savings_minor = 0;
  assert.equal(calculateMetrics(run).savings.potential_minor, 0);
});
test("blocked and not_run count without improving time savings", () => {
  const run = example(); run.trials[0].result = "blocked"; run.trials[0].assisted_ms = null;
  run.trials[1].result = "not_run"; run.trials[1].assisted_ms = null;
  const report = calculateMetrics(run);
  assert.equal(report.time.saved_percent, null);
  assert.deepEqual(report.time.results, { pass: 0, fail: 1, blocked: 1, not_run: 1 });
});
for (const [name, mutate] of [
  ["negative cost", (r) => { r.costs[0].amount_minor = -1; }],
  ["fractional money", (r) => { r.costs[0].amount_minor = 1.5; }],
  ["unsafe money", (r) => { r.costs[0].amount_minor = Number.MAX_SAFE_INTEGER + 1; }],
  ["duplicate lines", (r) => { r.costs.push(structuredClone(r.costs[0])); }],
  ["duplicate pair", (r) => { r.trials.push({ ...r.trials[0], id: "different-id" }); }],
  ["missing shared rule", (r) => { delete r.costs[1].rule; }],
  ["missing owner", (r) => { delete r.costs[0].owner; }],
  ["missing evidence", (r) => { r.trials[0].evidence = []; }],
  ["missing risk", (r) => { delete r.opportunities[0].risk; }],
  ["invented candidate savings", (r) => { r.opportunities[1].savings_minor = 100; }],
  ["saving beyond resource cost", (r) => { r.opportunities[0].savings_minor = 70001; }],
  ["excluded resource saving", (r) => { r.opportunities[0].resource_id = "excluded-demo"; }],
  ["overlapping estimates", (r) => { r.opportunities.push({ ...r.opportunities[0], id: "overlap" }); }],
  ["zero manual time", (r) => { r.trials[0].manual_ms = 0; }],
  ["missing assisted time", (r) => { r.trials[0].assisted_ms = null; }],
  ["invalid date", (r) => { r.period.start = "2026-02-30"; }],
  ["reversed period", (r) => { r.period.end = "2026-08-01"; }],
  ["unknown provenance", (r) => { r.provenance = "real-looking"; }],
  ["invalid basis", (r) => { r.cost_basis = "mixed"; }],
  ["mixed currencies", (r) => { r.costs[0].currency = "USD"; }],
  ["mixed periods", (r) => { r.opportunities[0].period = { start: "2026-08-01", end: "2026-08-31" }; }],
  ["malformed row", (r) => { r.trials[0] = null; }],
]) test(`rejects ${name}`, () => {
  const run = example(); mutate(run);
  assert.throws(() => calculateMetrics(run));
});
test("rejects safe rows whose total overflows", () => {
  const run = example(); run.costs[0].amount_minor = Number.MAX_SAFE_INTEGER;
  assert.throws(() => calculateMetrics(run), /rango entero seguro/);
});
test("rejects malformed root and sections", () => {
  for (const run of [null, [], { ...example(), costs: null }]) assert.ok(validateRun(run).length > 0);
});
test("CLI emits reproducible JSON from another directory and returns usage errors", () => {
  const tool = path.join(root, "tools/business-metrics.mjs");
  const result = spawnSync(process.execPath, [tool, "report", filename], { cwd: path.dirname(root), encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout), calculateMetrics(example()));
  assert.equal(spawnSync(process.execPath, [tool, "report"], { encoding: "utf8" }).status, 2);
  assert.equal(spawnSync(process.execPath, [tool, "report", "missing.json"], { encoding: "utf8" }).status, 1);
});
