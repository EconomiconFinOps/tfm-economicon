import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { parse } from "yaml";
import { alertConfig, extractPrometheusRules, loadAlertRules, prepareTests } from "./llm-alerts-promtool.mjs";

const rules = loadAlertRules();

test("three provisioned LLM alerts preserve distinct missing-data and evaluation-error states", () => {
  assert.deepEqual(rules.map(({ uid }) => uid), [
    "llm-provider-error-ratio", "llm-embedding-latency", "llm-generation-latency",
  ]);
  const config = parse(fs.readFileSync(alertConfig, "utf8"));
  assert.equal(config.groups[0].interval, "1m");
  for (const rule of rules) {
    assert.equal(rule.for, "2m");
    assert.equal(rule.noDataState, "NoData");
    assert.equal(rule.execErrState, "Error");
    assert.equal(rule.isPaused ?? false, false);
    assert.equal(rule.labels.jup, "JUP-046");
    assert.ok(rule.annotations.summary);
    assert.ok(rule.annotations.description);
    assert.equal(rule.annotations.runbook_url, "https://github.com/EconomiconFinOps/tfm-economicon/blob/develop/docs/runbooks/llm-degradation.md");
    assert.equal(rule.notification_settings, undefined);
  }
  assert.equal(config.contactPoints, undefined);
  assert.equal(config.policies, undefined);
});

test("promtool extracts the provisioned query, labels, pending period and Grafana threshold", () => {
  const extracted = extractPrometheusRules(rules).groups[0].rules;
  for (const [index, rule] of rules.entries()) {
    const query = rule.data.find(({ refId }) => refId === "A");
    assert.equal(extracted[index].expr, `(${query.model.expr}) > 0`);
    assert.equal(extracted[index].for, rule.for);
    assert.deepEqual(extracted[index].labels, rule.labels);
    assert.match(query.model.expr, /sum by \(job, instance, operation/);
    assert.match(query.model.expr, />= bool 5/);
    assert.doesNotMatch(query.model.expr, /\bor vector\(0\)/);
  }
  const mutated = structuredClone(rules);
  mutated[0].data[1].model.conditions[0].evaluator.params = [1];
  assert.throws(() => extractPrometheusRules(mutated), /Unsupported Grafana condition/);
});

test("generated promtool suite binds edge cases to the exact deployed expressions", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "llm-alerts-static-"));
  try {
    const { testFile, ruleFile } = prepareTests(directory);
    const suite = parse(fs.readFileSync(testFile, "utf8"));
    assert.deepEqual(parse(fs.readFileSync(ruleFile, "utf8")), extractPrometheusRules(rules));
    assert.deepEqual(suite.rule_files, ["llm-rules.yml"]);
    assert.equal(suite.evaluation_interval, "1m");
    assert.equal(suite.tests.length, 19);
    const expressions = new Set(rules.map(({ data }) => data[0].model.expr));
    for (const scenario of suite.tests) {
      assert.ok(scenario.name);
      assert.ok(scenario.alert_rule_test.length);
      for (const query of scenario.promql_expr_test) assert.ok(expressions.has(query.expr));
    }
    const absent = suite.tests.find(({ name }) => name.startsWith("no samples"));
    assert.deepEqual(absent.input_series, []);
    assert.ok(absent.promql_expr_test.every(({ exp_samples }) => exp_samples.length === 0));
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});

test("LLM dashboard exposes alert states and supporting volume by isolated dimensions", () => {
  const dashboardPath = path.join(path.dirname(alertConfig), "../../dashboards/llm-degradation.json");
  const dashboard = JSON.parse(fs.readFileSync(dashboardPath, "utf8"));
  assert.equal(dashboard.uid, "economicon-llm-degradation");
  assert.equal(new Set(dashboard.panels.map(({ id }) => id)).size, dashboard.panels.length);
  for (const rule of rules) {
    assert.equal(rule.annotations.__dashboardUid__, dashboard.uid);
    assert.ok(dashboard.panels.some(({ id }) => id === Number(rule.annotations.__panelId__)));
  }
  const alertlist = dashboard.panels.find(({ type }) => type === "alertlist");
  assert.equal(alertlist.options.alertInstanceLabelFilter, '{jup="JUP-046"}');
  assert.deepEqual(alertlist.options.stateFilter, { firing: true, pending: true, normal: true, noData: true, error: true });
  for (const panel of dashboard.panels.filter(({ type }) => type === "timeseries")) {
    assert.equal(panel.datasource.uid, "prometheus");
    for (const target of panel.targets) {
      assert.match(target.expr, /sum by \(job, instance, operation/);
      assert.equal(target.legendFormat, "{{job}} / {{instance}} / {{operation}}");
    }
  }
});
