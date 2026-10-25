import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { checkReviews } from "./pr-policy.mjs";

const directory = "docs/evidence/JUP-131-pr161-reconciliation";
const marker = "- Excepcion puntual PR161: revision y validacion por agentes independientes, autorizada por el usuario el 2026-10-24";
const body = `- ID: JUP-131
- Liderazgo: Alejandro Aguado
- Pairing/coautoria: Victor Mendez
- Revision de PR: Agente pr161_code_review (excepcion PR161)
- Validacion, pruebas y documentacion: Agente pr161_validation (excepcion PR161)
${marker}`;
const sha = (value) => createHash("sha256").update(value.replaceAll("\r\n", "\n")).digest("hex");

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "pr161-evidence-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const git = (...args) => execFileSync("git", ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
    "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", "-c", "core.hooksPath=.no-hooks", ...args],
  { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
  const write = (name, value) => {
    fs.mkdirSync(path.dirname(path.join(root, name)), { recursive: true });
    fs.writeFileSync(path.join(root, name), typeof value === "string" ? value : JSON.stringify(value));
  };
  const commit = () => { git("add", "."); git("commit", "-qm", "fixture"); return git("rev-parse", "HEAD"); };
  git("init", "-q");
  write("apps/example.py", "original\n");
  const candidate = commit();
  const manifest = { candidate_sha: candidate, reports: [] };
  for (const [kind, title, agent, verdict] of [
    ["revision", "Revision JUP-131", "/root/pr161_code_review", "APPROVE"],
    ["validacion", "Validacion JUP-131", "/root/pr161_validation", "PASS"],
  ]) {
    const report = `${directory}/${kind}.md`;
    const markdown = `${title}\nIndependent checks for ${candidate}\n`;
    write(report, markdown);
    const record = { candidate_sha: candidate, title, agent, verdict, report, report_sha256: sha(markdown) };
    const recordPath = `${directory}/${kind}.json`;
    write(recordPath, record);
    manifest.reports.push({ kind, path: recordPath, sha256: sha(JSON.stringify(record)) });
  }
  write(`${directory}/manifest.json`, manifest);
  const input = { number: 161, repository: "EconomiconFinOps/tfm-economicon", author: "Iber1to",
    title: "JUP-131: Atlas ECS", base: "develop", head: "feat/JUP-131-atlas-ecs", body, reviews: [], headSha: commit() };
  return { root, git, write, commit, candidate, manifest, input,
    check: (value = input) => checkReviews(value, { evidenceRoot: root }) };
}

test("PR161 accepts two independent recorded verdicts without impersonating GitHub reviewers", (t) => {
  const f = fixture(t);
  assert.deepEqual(f.check(), []);
});

test("PR161 evidence never lifts an unresolved request for changes", (t) => {
  const f = fixture(t);
  assert.ok(f.check({ ...f.input, reviews: [{ user: "reviewer", state: "CHANGES_REQUESTED", body: "Fix this",
    submitted_at: "2026-10-25T10:00:00Z" }] }).some((error) => /cambios pedidos/.test(error)));
});

test("PR161 exception fails closed for other identities, branches, bases, roles and hidden declarations", (t) => {
  const f = fixture(t);
  for (const change of [{ number: 162 }, { repository: "other/repo" }, { author: "another" },
    { base: "main" }, { head: "feat/JUP-131-other" }, { title: "JUP-140: other" },
    { body: body.replace("- ID: JUP-131", "- ID: JUP-140") },
    { body: body.replace("pr161_validation", "pr161_code_review") },
    { body: body.replace(marker, `<!-- ${marker} -->`) }, { body: `${body}\n${marker}` }]) {
    assert.notDeepEqual(f.check({ ...f.input, ...change }), [], JSON.stringify(change));
  }
});

test("a code change after review requires fresh agent evidence", (t) => {
  const f = fixture(t);
  f.write("apps/example.py", "unreviewed change\n");
  f.input.headSha = f.commit();
  assert.ok(f.check().some((error) => /candidato|candidate|delta/i.test(error)));
});

test("stale checkout and missing evidence cannot pass", (t) => {
  const f = fixture(t);
  assert.notDeepEqual(f.check({ ...f.input, headSha: f.candidate }), []);
  f.git("rm", `${directory}/validacion.json`);
  f.input.headSha = f.commit();
  assert.notDeepEqual(f.check(), []);
});

test("tampered report bytes, negative verdict and reused agent identity cannot pass", (t) => {
  const f = fixture(t);
  const recordPath = `${directory}/validacion.json`;
  const original = JSON.parse(fs.readFileSync(path.join(f.root, recordPath), "utf8"));
  for (const change of [{ verdict: "FAIL" }, { agent: "/root/pr161_code_review" }, { candidate_sha: "a".repeat(40) }]) {
    const value = { ...original, ...change };
    f.write(recordPath, value);
    f.manifest.reports[1].sha256 = sha(JSON.stringify(value));
    f.write(`${directory}/manifest.json`, f.manifest);
    f.input.headSha = f.commit();
    assert.notDeepEqual(f.check(), [], JSON.stringify(change));
  }
  f.write(recordPath, original);
  f.manifest.reports[1].sha256 = sha(JSON.stringify(original));
  f.write(`${directory}/manifest.json`, f.manifest);
  f.write(`${directory}/validacion.md`, "Forged prose\n");
  f.input.headSha = f.commit();
  assert.notDeepEqual(f.check(), []);
});

test("documentation publication can follow the reviewed candidate", (t) => {
  const f = fixture(t);
  f.write("docs/continuidad/cloud-aws.md", "Publication receipt\n");
  f.input.headSha = f.commit();
  assert.deepEqual(f.check(), []);
});
