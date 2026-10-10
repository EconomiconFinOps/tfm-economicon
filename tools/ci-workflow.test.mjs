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
  assert.deepEqual(workflow.on.pull_request.types, [
    "opened", "synchronize", "reopened", "edited", "ready_for_review",
  ]);
  assert.equal(workflow.on.pull_request_target, undefined);
});

test("runs every branch push without tag or path filters and retains event policy", () => {
  assert.equal(workflow.on.workflow_dispatch, null);
  assert.equal(workflow.jobs["pr-policy"].if, "github.event_name == 'pull_request'");
  assert.deepEqual(workflow.concurrency, {
    group: "ci-${{ github.workflow }}-${{ github.ref }}",
    "cancel-in-progress": true,
  });
  assert.deepEqual(workflow.on.push, { branches: ["**"] });
});

test("requires Python lint/build once per service after dependencies and before pytest", () => {
  const job = workflow.jobs["python-tests"];
  for (const service of job.strategy.matrix.service) {
    assert.equal(service.path, `apps/${service.name}`);
    const manifest = JSON.parse(fs.readFileSync(path.join(root, service.path, "package.json"), "utf8"));
    assert.equal(manifest.scripts.lint, "python -m compileall app");
    assert.equal(manifest.scripts.build, manifest.scripts.lint);
  }

  const steps = job.steps;
  const compilation = steps.filter(({ run }) => /\bcompileall\b/.test(run ?? ""));
  assert.equal(compilation.length, 1, "expected exactly one Python compileall step");
  const [compile] = compilation;
  assert.equal(compile.run, "python -m compileall -q app");
  assert.equal(compile["working-directory"], "${{ matrix.service.path }}");
  const dependencies = steps.findIndex(({ run }) => run === "python -m pip install -r requirements-dev.txt");
  const tests = steps.findIndex(({ run }) => run === "python -m pytest tests -q");
  const syntax = steps.indexOf(compile);
  assert.ok(dependencies >= 0 && syntax > dependencies && tests > syntax);
  assert.equal(steps[tests]["working-directory"], "${{ matrix.service.path }}");
  for (const mandatory of [job, compile, steps[tests]]) {
    assert.equal(mandatory.if, undefined);
    assert.equal(mandatory["continue-on-error"], undefined);
  }
  assert.equal(compile.shell, undefined);
  assert.equal(job.defaults?.run?.shell, undefined);
  assert.equal(workflow.defaults?.run?.shell, undefined);
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

test("keeps the seven branch-protection check contexts stable", () => {
  assert.equal(workflow.jobs["pr-policy"].name, "JUP policy");
  assert.equal(workflow.jobs.governance.name, "OpenSpec");
  assert.equal(workflow.jobs["frontend-build"].name, "Frontend build");
  // JUP-093: septimo check obligatorio, tsc --noEmit del frontend (ADR-0003, decision 3).
  assert.equal(workflow.jobs["frontend-typecheck"].name, "Frontend type check");
  // Reconciliacion JUP-095/JUP-087: un octavo job ("frontend-tests") duplicaba
  // la ejecucion de test que "frontend-build" ya hacia tras fusionar develop;
  // se retiro para conservar los siete checks ya confirmados activos en
  // GitHub (docs/governance/github-branch-protection.md) sin duplicar CI.
  assert.equal(workflow.jobs["frontend-tests"], undefined);
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
    "roadmap:test",
    "repository:governance:test",
    "jup:check:all",
    "jup:cleanup:test",
    "jup:cleanup:check",
    "assistant-corpus:test",
    "validation-questions:validate",
    "validation-questions:test",
    "retrieval-labels:validate",
    "retrieval-labels:test",
    "retrieval-calibration:test",
    "assistant-metrics:test",
    "assistant-eval:test",
    "synthetic-costs:test",
    "assistant-corpus:validate",
    "llm-gateway:test",
    "llm-alerts:test",
    "docker:validate",
    "local:test",
    "collaboration:test",
    "openspec:validate",
  ]) {
    assert.match(commands, new RegExp(`pnpm ${check.replaceAll(":", "\\:")}`));
  }
});

test("executes real LLM PromQL thresholds and recovery without network access", () => {
  const step = workflow.jobs.governance.steps.find(({ name }) => name === "Validate LLM thresholds and recovery with Prometheus");
  assert.ok(step);
  assert.equal(step.if, undefined);
  assert.equal(step["continue-on-error"], undefined);
  assert.match(step.run, /llm-alerts-promtool\.mjs --prepare/);
  assert.match(step.run, /prom\/prometheus:v2\.55\.1 check rules llm-rules\.yml/);
  assert.match(step.run, /--tmpfs \/tmp:rw,nosuid,size=128m.*prom\/prometheus:v2\.55\.1 test rules llm-tests\.yml/);
  assert.equal((step.run.match(/docker run --rm --network none --read-only/g) ?? []).length, 2);
});

test("requires real frontend tests and lint before the mandatory build", () => {
  const steps = workflow.jobs["frontend-build"].steps;
  const lint = steps.findIndex(({ run }) => run === "corepack pnpm lint --filter=@finops/frontend");
  const tests = steps.findIndex(({ run }) => run === "corepack pnpm test --filter=@finops/frontend");
  const build = steps.findIndex(({ run }) => run === "corepack pnpm --filter @finops/frontend build");
  assert.ok(lint >= 0 && tests > lint && build > tests);
  assert.equal(steps[lint]["continue-on-error"], undefined);
  assert.equal(steps[tests]["continue-on-error"], undefined);
  assert.equal(workflow.jobs["frontend-build"]["continue-on-error"], undefined);
  const frontend = JSON.parse(fs.readFileSync(path.join(root, "apps/frontend/package.json"), "utf8"));
  assert.equal(frontend.scripts.test, "vitest run");
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

const loadReviewsWorkflow = () =>
  parse(fs.readFileSync(path.join(root, ".github", "workflows", "pr-reviews.yml"), "utf8"));

test("keeps review events out of the main CI workflow", () => {
  // A review event there would rerun every job, cancel running CI and report skipped jobs as passing.
  assert.equal(workflow.on.pull_request_review, undefined);
});

test("runs JUP reviews on pull request and review activity with read-only access", () => {
  const reviews = loadReviewsWorkflow();
  assert.deepEqual(reviews.on.pull_request.branches, ["main", "develop"]);
  for (const type of ["opened", "synchronize", "reopened", "edited", "ready_for_review"]) {
    assert.ok(reviews.on.pull_request.types.includes(type), type);
  }
  assert.deepEqual(reviews.on.pull_request_review.types, ["submitted", "edited", "dismissed"]);
  assert.equal(reviews.on.pull_request_target, undefined);
  assert.deepEqual(reviews.permissions, { contents: "read", "pull-requests": "read" });

  const jobs = Object.values(reviews.jobs);
  assert.equal(jobs.length, 1);
  const [job] = jobs;
  assert.equal(job.name, "JUP reviews");
  assert.equal(job["continue-on-error"], undefined);
  for (const step of job.steps) {
    if (step.uses) {
      assert.match(step.uses, /^actions\/checkout@[a-f0-9]{40}$/);
      assert.equal(step.with["persist-credentials"], false);
    }
    assert.equal(step["continue-on-error"], undefined);
  }
  const run = job.steps.find(({ run }) => run?.includes("tools/pr-policy.mjs"));
  assert.match(run.run, /--reviews/);
  assert.equal(run.env.GITHUB_TOKEN, "${{ secrets.GITHUB_TOKEN }}");
});

test("requires the same eight stable CI checks in both branch rulesets", () => {
  const expected = [
    "JUP policy",
    "OpenSpec",
    "Python tests (azure-cost-api)",
    "Python tests (backend)",
    "Python tests (processor)",
    "Frontend build",
    // JUP-093: agrupado junto al otro check del frontend (ADR-0003, decision 3).
    "Frontend type check",
    "JUP reviews",
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

test("restricts permanent branches to squash or rebase and keeps main linear", () => {
  assert.ok(rulesets.main.rules.some(({ type }) => type === "required_linear_history"));
  assert.ok(
    !rulesets.develop.rules.some(({ type }) => type === "required_linear_history"),
  );
  const mainPullRequest = rulesets.main.rules.find(({ type }) => type === "pull_request");
  const developPullRequest = rulesets.develop.rules.find(({ type }) => type === "pull_request");
  assert.deepEqual(mainPullRequest.parameters.allowed_merge_methods, ["squash", "rebase"]);
  assert.deepEqual(developPullRequest.parameters.allowed_merge_methods, ["squash", "rebase"]);
});
