#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { parse, stringify } from "yaml";
import { createScenarios } from "./fixtures/llm-alerts/scenarios.mjs";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
export const alertConfig = path.join(root, "apps/monitoring/grafana/provisioning/alerting/llm-degradation.yml");
export const promtoolVersion = "2.55.1";

export function loadAlertRules(filename = alertConfig) {
  const config = parse(fs.readFileSync(filename, "utf8"));
  return config.groups.flatMap(({ rules }) => rules);
}

export function extractPrometheusRules(rules = loadAlertRules()) {
  return {
    groups: [{
      name: "llm-degradation",
      interval: "1m",
      rules: rules.map((rule) => {
        const query = rule.data.find(({ refId }) => refId === "A");
        const condition = rule.data.find(({ refId }) => refId === rule.condition);
        const model = condition?.model;
        if (query?.datasourceUid !== "prometheus" || query.model.instant !== true ||
            condition?.datasourceUid !== "__expr__" || model?.type !== "threshold" ||
            model.expression !== "A" || model.conditions.length !== 1 ||
            model.conditions[0].evaluator.type !== "gt" ||
            JSON.stringify(model.conditions[0].evaluator.params) !== "[0]") {
          throw new Error(`Unsupported Grafana condition for ${rule.uid}; update extraction explicitly.`);
        }
        // Native Prometheus fires on a present vector. Apply the SAME Grafana
        // C > 0 condition to A; do not reproduce either query in test fixtures.
        // Human-facing annotations are verified statically, not by promtool.
        return { alert: rule.uid, expr: `(${query.model.expr}) > 0`, for: rule.for, labels: rule.labels };
      }),
    }],
  };
}

export function prepareTests(directory) {
  const rules = loadAlertRules();
  const expressions = Object.fromEntries(rules.map((rule) => [rule.uid, rule.data.find(({ refId }) => refId === "A").model.expr]));
  fs.mkdirSync(directory, { recursive: true });
  const ruleFile = path.join(directory, "llm-rules.yml");
  const testFile = path.join(directory, "llm-tests.yml");
  fs.writeFileSync(ruleFile, stringify(extractPrometheusRules(rules)));
  fs.writeFileSync(testFile, stringify({
    rule_files: ["llm-rules.yml"],
    evaluation_interval: "1m",
    tests: createScenarios(expressions),
  }));
  return { ruleFile, testFile };
}

export function runPromtool(binary = "promtool") {
  const version = spawnSync(binary, ["--version"], { encoding: "utf8" });
  if (version.error) throw version.error;
  if (version.status !== 0 || !`${version.stdout}${version.stderr}`.includes(`version ${promtoolVersion}`)) {
    throw new Error(`Expected promtool ${promtoolVersion}; received ${version.stdout}${version.stderr}`);
  }
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "economicon-llm-alerts-"));
  try {
    prepareTests(directory);
    for (const args of [["check", "rules", "llm-rules.yml"], ["test", "rules", "llm-tests.yml"]]) {
      const result = spawnSync(binary, args, { cwd: directory, stdio: "inherit" });
      if (result.error) throw result.error;
      if (result.status !== 0) return result.status ?? 1;
    }
    return 0;
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv[2] === "--prepare" && process.argv[3] && process.argv.length === 4) {
      console.log(JSON.stringify(prepareTests(path.resolve(process.argv[3]))));
    } else if (process.argv.length <= 3) {
      process.exitCode = runPromtool(process.argv[2]);
    } else {
      throw new Error("Usage: node tools/llm-alerts-promtool.mjs [promtool-binary | --prepare output-directory]");
    }
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
