import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
// Windows checkouts may use CRLF; section lookups below expect LF.
const read = (...parts) => fs.readFileSync(path.join(root, ...parts), "utf8").replace(/\r\n/g, "\n");
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

const agents = () => read("AGENTS.md");
const template = () => read(".github", "pull_request_template.md");
const section = (text, heading) => {
  const start = text.indexOf(`${heading}\n`);
  assert.ok(start >= 0, `missing heading ${heading}`);
  const level = heading.match(/^#+/)[0].length;
  const rest = text.slice(start + heading.length + 1);
  const next = rest.search(new RegExp(`^#{1,${level}} `, "m"));
  return next < 0 ? rest : rest.slice(0, next);
};

test("defines what each rotating role does, when, what it delivers and what it does not do", () => {
  const roles = section(contributing, "## Rotating roles");
  for (const role of ["### Leadership", "### Pairing and co-authorship", "### PR review", "### Validation, tests and documentation"]) {
    const text = section(roles, role);
    for (const label of ["Does:", "When:", "Delivers:", "Does not:"]) {
      assert.match(text, new RegExp(`\\*\\*${label}\\*\\*`), `${role} ${label}`);
    }
  }
  assert.match(roles, /reassign/i);
});

test("documents the review and validation flow the JUP reviews check links to", async () => {
  const { REVIEW_FLOW_LINK, SAME_PERSON_EXCEPTION } = await import("./pr-policy.mjs");
  assert.equal(
    REVIEW_FLOW_LINK,
    `https://github.com/${settings.repository}/blob/develop/CONTRIBUTING.md#review-and-validation-flow`,
  );
  const flow = section(contributing, "## Review and validation flow");
  for (const text of ["Revision JUP-XXX", "Validacion JUP-XXX", "JUP reviews", "Update branch", SAME_PERSON_EXCEPTION]) {
    assert.ok(flow.includes(text), text);
  }
  assert.match(flow, /inline/i);
  assert.match(flow, /not validated/i);
  assert.match(flow, /a Comment does not lift/i);
  assert.match(flow, /whoever requested (the )?changes approves/i);
  assert.match(flow, /author never dismisses/i);
  assert.match(flow, /tools\/pr-policy\.mjs/);
  assert.match(flow, /\.github\/workflows\//);
  assert.ok(template().includes(SAME_PERSON_EXCEPTION));
});

test("keeps one process version in AGENTS.md and CONTRIBUTING.md", () => {
  const version = /^Process version: (.+)$/m;
  const inContributing = contributing.match(version);
  const inAgents = agents().match(version);
  assert.ok(inContributing && inAgents);
  assert.equal(inAgents[1], inContributing[1]);
});

test("gives local tooling the rules the check cannot verify, without naming any assistant", () => {
  const rules = section(agents(), "## Pull Request Review And Validation");
  for (const pattern of [/CONTRIBUTING\.md/, /not validated/i, /push/i, /Comment/, /inline/i, /Update branch/, /both/i, /local tool/i]) {
    assert.match(rules, pattern);
  }
  assert.doesNotMatch(agents(), /\b(claude|codex|copilot|cursor|gemini|chatgpt|openai|anthropic)\b/i);
});

test("carries the flow checklist into every pull request", () => {
  const text = template();
  for (const item of ["Revision JUP-XXX", "Validacion JUP-XXX", "CONTRIBUTING.md#review-and-validation-flow"]) {
    assert.ok(text.includes(item), item);
  }
  const checklist = section(text, "## Checklist");
  for (const rule of [/no suben commits/i, /todas las reviews/i, /en linea/i, /Update branch/, /revalid/i]) {
    assert.match(checklist, rule);
  }
  assert.match(section(text, "## Validacion"), /lider|leader/i);
});

test("links the approved flow and the activation of the new check", () => {
  assert.match(section(strategy, "## Flujo aprobado"), /CONTRIBUTING\.md#review-and-validation-flow/);
  assert.match(read("docs", "governance", "github-branch-protection.md"), /JUP reviews/);
});

test("lists in the branch-protection guide exactly the required checks of the rulesets", () => {
  const guide = section(read("docs", "governance", "github-branch-protection.md"), "## Required status checks");
  const listed = [...guide.matchAll(/^- `([^`]+)`/gm)].map((match) => match[1]);
  const required = rulesets.develop.rules
    .find(({ type }) => type === "required_status_checks")
    .parameters.required_status_checks.map(({ context }) => context);
  assert.deepEqual(listed, required);
});
