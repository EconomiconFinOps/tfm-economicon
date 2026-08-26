import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const read = (...parts) => fs.readFileSync(path.join(root, ...parts), "utf8");
const settings = JSON.parse(read(".github", "repository-settings.json"));
const rulesets = Object.fromEntries(
  ["develop", "main"].map((branch) => [
    branch,
    JSON.parse(read(".github", "rulesets", `${branch}.json`)),
  ]),
);
const contributing = read("CONTRIBUTING.md");
const strategy = read("docs", "governance", "repository-and-branch-strategy.md");

test("pins the canonical repository and permanent branch", () => {
  assert.equal(settings.repository, "EconomiconFinOps/tfm-economicon");
  assert.equal(settings.default_branch, "main");
  assert.match(strategy, /Estado: vigente/);
  assert.match(strategy, /`develop` -> `main`/);
});

test("automatically removes merged task branches", () => {
  assert.equal(settings.delete_branch_on_merge, true);
  assert.match(contributing, /delete\s+the remote task branch/i);
  assert.match(strategy, /elimina automaticamente la rama remota/i);
});

test("disables merge commits while retaining reviewable merge methods", () => {
  assert.equal(settings.allow_merge_commit, false);
  assert.equal(settings.allow_squash_merge, true);
  assert.equal(settings.allow_rebase_merge, true);

  for (const ruleset of Object.values(rulesets)) {
    const pullRequest = ruleset.rules.find(({ type }) => type === "pull_request");
    assert.deepEqual(pullRequest.parameters.allowed_merge_methods, ["squash", "rebase"]);
  }
});

test("keeps legacy branches until their ancestry is audited", () => {
  assert.match(strategy, /setup\/sdd/);
  assert.match(strategy, /no se elimina/i);
  assert.match(strategy, /git merge-base --is-ancestor/);
});

test("requires individually verified GitHub access", () => {
  assert.match(strategy, /permiso efectivo/i);
  assert.match(strategy, /no demuestra permiso de escritura/i);
});
