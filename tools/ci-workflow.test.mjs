import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { parse } from "yaml";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const source = fs.readFileSync(
  path.join(root, ".github", "workflows", "ci.yml"),
  "utf8",
);
const workflow = parse(source);
const rulesets = Object.fromEntries(
  ["develop", "main"].map((branch) => [
    branch,
    JSON.parse(
      fs.readFileSync(
        path.join(root, ".github", "rulesets", `${branch}.json`),
        "utf8",
      ),
    ),
  ]),
);

test("runs pull request policy again when its metadata changes", () => {
  assert.deepEqual(workflow.on.pull_request.branches, ["main", "develop"]);
  assert.ok(workflow.on.pull_request.types.includes("edited"));
  assert.ok(workflow.on.pull_request.types.includes("synchronize"));
  assert.equal(workflow.on.pull_request_target, undefined);
});

test("limits GitHub token permissions and pins official actions by commit", () => {
  assert.deepEqual(workflow.permissions, { contents: "read" });

  for (const job of Object.values(workflow.jobs)) {
    for (const step of job.steps ?? []) {
      if (!step.uses) continue;
      assert.match(step.uses, /^actions\/(?:checkout|setup-node|setup-python)@[a-f0-9]{40}$/);
      if (step.uses.startsWith("actions/checkout@")) {
        assert.equal(step.with["persist-credentials"], false);
      }
    }
  }
});

test("keeps the six branch-protection check contexts stable", () => {
  assert.equal(workflow.jobs["pr-policy"].name, "JUP policy");
  assert.equal(workflow.jobs.governance.name, "OpenSpec");
  assert.equal(workflow.jobs["frontend-build"].name, "Frontend build");
  assert.equal(workflow.jobs["python-tests"].name, "Python tests (${{ matrix.service.name }})");
  assert.deepEqual(
    workflow.jobs["python-tests"].strategy.matrix.service.map(({ name }) => name),
    ["azure-cost-api", "backend", "processor"],
  );
});

test("retains all existing governance, corpus and gateway validations", () => {
  const commands = workflow.jobs.governance.steps
    .map(({ run }) => run ?? "")
    .join("\n");

  for (const check of [
    "jup:check:test",
    "pr:check:test",
    "ci:check:test",
    "jup:check:all",
    "jup:cleanup:test",
    "jup:cleanup:check",
    "assistant-corpus:test",
    "assistant-corpus:validate",
    "llm-gateway:test",
    "openspec:validate",
  ]) {
    assert.match(commands, new RegExp(`pnpm ${check.replaceAll(":", "\\:")}`));
  }
});

test("requires pull requests while keeping administrator bypass PR-only", () => {
  for (const [branch, ruleset] of Object.entries(rulesets)) {
    assert.equal(ruleset.enforcement, "active");
    assert.deepEqual(ruleset.conditions.ref_name.include, [`refs/heads/${branch}`]);
    assert.deepEqual(ruleset.bypass_actors, [
      { actor_id: 5, actor_type: "RepositoryRole", bypass_mode: "pull_request" },
    ]);
    assert.ok(ruleset.rules.some(({ type }) => type === "deletion"));
    assert.ok(ruleset.rules.some(({ type }) => type === "non_fast_forward"));

    const pullRequest = ruleset.rules.find(({ type }) => type === "pull_request");
    assert.equal(pullRequest.parameters.dismiss_stale_reviews_on_push, true);
    assert.equal(pullRequest.parameters.require_last_push_approval, true);
    assert.equal(pullRequest.parameters.required_review_thread_resolution, true);
    assert.equal(
      pullRequest.parameters.required_approving_review_count,
      branch === "main" ? 2 : 1,
    );
  }
});

test("requires the same six stable CI checks in both branch rulesets", () => {
  const expected = [
    "JUP policy",
    "OpenSpec",
    "Python tests (azure-cost-api)",
    "Python tests (backend)",
    "Python tests (processor)",
    "Frontend build",
  ];

  for (const ruleset of Object.values(rulesets)) {
    const checks = ruleset.rules.find(({ type }) => type === "required_status_checks");
    assert.equal(checks.parameters.strict_required_status_checks_policy, true);
    assert.deepEqual(
      checks.parameters.required_status_checks.map(({ context }) => context),
      expected,
    );
  }
});

test("requires linear release history only on main", () => {
  assert.ok(rulesets.main.rules.some(({ type }) => type === "required_linear_history"));
  assert.ok(
    !rulesets.develop.rules.some(({ type }) => type === "required_linear_history"),
  );
  const mainPullRequest = rulesets.main.rules.find(({ type }) => type === "pull_request");
  assert.deepEqual(mainPullRequest.parameters.allowed_merge_methods, ["squash", "rebase"]);
});
