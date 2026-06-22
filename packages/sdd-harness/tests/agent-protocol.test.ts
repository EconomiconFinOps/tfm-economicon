import { cp, mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeAll, describe, expect, it } from "vitest";

import { loadAgentCatalog, loadAgentDefinition } from "../src/agents/catalog.js";
import { agentLeasePath } from "../src/agents/lease.js";
import { compilePermissions, verifyPermissionAnchors } from "../src/agents/permissions.js";
import { selectCompatibleCodex } from "../src/agents/runtime.js";
import { agentStatus, recoverAbandonedAgent, runAgent } from "../src/agents/protocol.js";
import { createCatalogValidator } from "../src/contracts/catalog.js";
import { mutateWithReconciliation, updateStoryStatus } from "../src/orchestrator/commands.js";
import { initializeStory } from "../src/orchestrator/init.js";
import { prepareSkill, submitSkill } from "../src/skills/protocol.js";
import { findRepoRoot } from "../src/repo.js";
import { canonicalJson, sha256Text } from "../src/hash.js";

let repositoryRoot: string;
const temporary: string[] = [];
beforeAll(async () => { repositoryRoot = await findRepoRoot(); });
afterEach(async () => { delete process.env.SDD_CODEX_BIN; await Promise.all(temporary.splice(0).map((item) => rm(item, { recursive: true, force: true }))); });

describe("Phase 5 agents and permissions", () => {
  it("ships six valid, narrow Codex agents", async () => {
    const { catalog } = await loadAgentCatalog(repositoryRoot);
    expect(Object.keys(catalog.agents)).toEqual(["product-analyst", "technical-architect", "delivery-planner", "implementation-agent", "verification-agent", "review-agent"]);
    const validator = await createCatalogValidator(repositoryRoot, "agent/catalog@1.0.0");
    expect(validator(catalog), JSON.stringify(validator.errors)).toBe(true);
    for (const [id, policy] of Object.entries(catalog.agents)) {
      const definition = await loadAgentDefinition(repositoryRoot, id, policy);
      expect(definition.developer_instructions).toContain("no ");
    }
  });

  it("compiles fail-closed permissions and only grants product scope to implementation", async () => {
    const { catalog } = await loadAgentCatalog(repositoryRoot);
    const analyst = await compilePermissions(repositoryRoot, "HU-001", "SPEC/HU-001/.harness/skill-runs/x", "spec-intake", catalog.agents["product-analyst"]!, { write_paths: ["apps/backend/**"] });
    expect(analyst.profile.write_paths).toEqual(["SPEC/HU-001/.harness/skill-runs/x/artifacts", "SPEC/HU-001/.harness/skill-runs/x/output.json", "SPEC/HU-001/.harness/skill-runs/x/receipt.json"]);
    const implementation = await compilePermissions(repositoryRoot, "HU-001", "SPEC/HU-001/.harness/skill-runs/x", "plan-executor", catalog.agents["implementation-agent"]!, { write_paths: ["apps/backend/**"] });
    expect(implementation.profile.write_paths).toContain("apps/backend");
    expect(implementation.profile.read_only_paths).toContain("docs/ARCHITECTURE.md");
    await expect(compilePermissions(repositoryRoot, "HU-001", "run", "plan-executor", catalog.agents["implementation-agent"]!, { write_paths: ["apps/*/src"] })).rejects.toMatchObject({ code: "SDD-AGENT-SCOPE-UNENFORCEABLE" });
    await expect(compilePermissions(repositoryRoot, "HU-001", "run", "plan-executor", catalog.agents["implementation-agent"]!, { write_paths: ["SPEC/HU-001/**"] })).rejects.toMatchObject({ code: "SDD-AGENT-SCOPE-UNENFORCEABLE" });
  });

  it("runs a bound Codex process, audits it and preserves the staged result", async () => {
    const root = await story();
    const fake = path.join(root, "fake-codex.mjs"); await writeFile(fake, FAKE_CODEX, "utf8"); process.env.SDD_CODEX_BIN = fake;
    const parameters = ".sdd/agent-parameters.yaml"; await writeFile(path.join(root, parameters), "user_story_path: SPEC/HU-001/user-story.md\nvalidation_rules: []\n", "utf8");
    const result = await runAgent(root, "HU-001", "product-analyst", "spec-intake", parameters);
    expect(result).toMatchObject({ ok: false, command: "agent run", data: { agent_id: "product-analyst", status: "BLOCKED" } });
    const runId = (result.data as any).run_id;
    const status = await agentStatus(root, "HU-001", runId);
    expect(status).toMatchObject({ ok: false, data: { schema_version: "2.0.0", status: "BLOCKED", execution: { provider: "codex-cli", thread_id: "thread-fixture" } } });
    const runValidator = await createCatalogValidator(root, "agent/run@2.0.0"); expect(runValidator(status.data), JSON.stringify(runValidator.errors)).toBe(true);
    const prefix = path.join(root, "SPEC/HU-001/.harness/skill-runs", runId);
    expect(await readFile(path.join(prefix, "events.ndjson"), "utf8")).toContain("turn.completed");
    await expect(readFile(agentLeasePath(root, "HU-001"), "utf8")).rejects.toMatchObject({ code: "ENOENT" });
    await expect(submitSkill(root, "HU-001", runId, { type: "agent", identity: "spoof" })).rejects.toMatchObject({ code: "SDD-AGENT-IDENTITY" });
  });

  it("rejects unknown role assignments before creating a run", async () => {
    const root = await story();
    const parameters = ".sdd/agent-parameters.yaml"; await writeFile(path.join(root, parameters), "acceptance_criteria: [AC-001]\n", "utf8");
    await expect(runAgent(root, "HU-001", "technical-architect", "prd-generator", parameters)).rejects.toMatchObject({ code: "SDD-AGENT-SKILL" });
  });

  it("fails closed for an incompatible Codex version and releases the lease", async () => {
    const root = await story(); const fake = path.join(root, "old-codex.mjs");
    await writeFile(fake, FAKE_CODEX.replace("codex-cli 0.140.0", "codex-cli 0.58.0"), "utf8"); process.env.SDD_CODEX_BIN = fake;
    const parameters = ".sdd/agent-parameters.yaml"; await writeFile(path.join(root, parameters), "user_story_path: SPEC/HU-001/user-story.md\nvalidation_rules: []\n", "utf8");
    await expect(runAgent(root, "HU-001", "product-analyst", "spec-intake", parameters)).rejects.toMatchObject({ code: "SDD-CODEX-VERSION" });
    const [runId] = await readdir(path.join(root, "SPEC/HU-001/.harness/skill-runs"));
    expect(JSON.parse(await readFile(path.join(root, "SPEC/HU-001/.harness/skill-runs", runId!, "run.json"), "utf8"))).toMatchObject({ status: "FAILED" });
    await expect(readFile(agentLeasePath(root, "HU-001"), "utf8")).rejects.toMatchObject({ code: "ENOENT" });
  });

  it("rejects a malformed Codex JSONL stream", async () => {
    const root = await story(); const fake = path.join(root, "malformed-codex.mjs");
    await writeFile(fake, FAKE_CODEX.replace('console.log(JSON.stringify({ type: "turn.completed", usage: { input_tokens: 1, output_tokens: 1 } }));', 'console.log("not-json");'), "utf8"); process.env.SDD_CODEX_BIN = fake;
    const parameters = ".sdd/agent-parameters.yaml"; await writeFile(path.join(root, parameters), "user_story_path: SPEC/HU-001/user-story.md\nvalidation_rules: []\n", "utf8");
    await expect(runAgent(root, "HU-001", "product-analyst", "spec-intake", parameters)).rejects.toMatchObject({ code: "SDD-CODEX-JSONL" });
  });

  it("derives agent identity from the journal and rejects a downgrade to a manual run", async () => {
    const { root, runId } = await completedAgentRun(); const runPath = path.join(root, "SPEC/HU-001/.harness/skill-runs", runId, "run.json");
    const run = JSON.parse(await readFile(runPath, "utf8")); delete run.agent_id; await writeFile(runPath, JSON.stringify(run), "utf8");
    expect(await agentStatus(root, "HU-001", runId)).toMatchObject({ ok: false });
    await expect(submitSkill(root, "HU-001", runId, { type: "human", identity: "spoof" })).rejects.toMatchObject({ code: "SDD-AGENT-IDENTITY" });
  });

  it("detects a broadened permission profile even when its self hash is recomputed", async () => {
    const { root, runId } = await completedAgentRun(); const runPath = path.join(root, "SPEC/HU-001/.harness/skill-runs", runId, "run.json");
    const run = JSON.parse(await readFile(runPath, "utf8")); run.permission_profile.write_paths.push("docs"); run.permission_profile_sha256 = sha256Text(canonicalJson(run.permission_profile)); await writeFile(runPath, JSON.stringify(run), "utf8");
    const status = await agentStatus(root, "HU-001", runId); expect(status.ok).toBe(false); expect(status.blockers.some((item) => item.code === "SDD-AGENT-RUN-INTEGRITY")).toBe(true);
  });

  it("rejects duplicate permission binding events", async () => {
    const { root, runId } = await completedAgentRun(); const runPath = path.join(root, "SPEC/HU-001/.harness/skill-runs", runId, "run.json"); const run = JSON.parse(await readFile(runPath, "utf8"));
    await mutateWithReconciliation(root, "HU-001", "duplicate binding", async () => ({ event_type: "agent.permissions_bound", event_data: { run_id: runId, agent_id: run.agent_id, agent_definition_sha256: run.agent_definition_sha256, agent_catalog_sha256: run.agent_catalog_sha256, permission_profile_sha256: run.permission_profile_sha256 }, actor: { type: "system", identity: "test" }, extra_writes: [], result: { ok: true, command: "duplicate binding", story_id: "HU-001", changed: true, blockers: [], next_actions: [] } }));
    const status = await agentStatus(root, "HU-001", runId); expect(status.ok).toBe(false); expect(status.blockers.some((item) => item.message.includes("exactly one permission binding"))).toBe(true);
  });

  it("classifies a non-zero Codex exit as a runtime error and persists FAILED", async () => {
    const root = await story(); const fake = path.join(root, "failed-codex.mjs"); await writeFile(fake, FAKE_CODEX.replace("const prompt =", "process.exit(7);\nconst prompt ="), "utf8"); process.env.SDD_CODEX_BIN = fake;
    const parameters = await parametersFor(root); await expect(runAgent(root, "HU-001", "product-analyst", "spec-intake", parameters)).rejects.toMatchObject({ code: "SDD-CODEX-EXIT" });
    const [runId] = await readdir(path.join(root, "SPEC/HU-001/.harness/skill-runs")); expect(await agentStatus(root, "HU-001", runId!)).toMatchObject({ ok: false, data: { status: "FAILED" } });
  });

  it("terminates a timed-out Codex process and closes the run before releasing its lease", async () => {
    const root = await story(); const catalogPath = path.join(root, ".sdd/agents/catalog.yaml"); const catalog = (await readFile(catalogPath, "utf8")).replace("timeout_seconds: 900", "timeout_seconds: 1"); await writeFile(catalogPath, catalog, "utf8");
    const fake = path.join(root, "timeout-codex.mjs"); await writeFile(fake, FAKE_CODEX.replace("const prompt =", "setInterval(() => {}, 1000); await new Promise(() => {});\nconst prompt ="), "utf8"); process.env.SDD_CODEX_BIN = fake;
    await expect(runAgent(root, "HU-001", "product-analyst", "spec-intake", await parametersFor(root))).rejects.toMatchObject({ code: "SDD-CODEX-TIMEOUT" });
    const [runId] = await readdir(path.join(root, "SPEC/HU-001/.harness/skill-runs")); expect(await agentStatus(root, "HU-001", runId!)).toMatchObject({ ok: false, data: { status: "FAILED" } }); await expect(readFile(agentLeasePath(root, "HU-001"), "utf8")).rejects.toMatchObject({ code: "ENOENT" });
  });

  it("enforces exact runtime output limits and records the failure", async () => {
    const root = await story(); const catalogPath = path.join(root, ".sdd/agents/catalog.yaml"); const catalog = (await readFile(catalogPath, "utf8")).replace("max_output_bytes: 1048576", "max_output_bytes: 1024"); await writeFile(catalogPath, catalog, "utf8");
    const fake = path.join(root, "noisy-codex.mjs"); await writeFile(fake, FAKE_CODEX.replace('console.log(JSON.stringify({ type: "thread.started"', 'console.log("x".repeat(2048));\nconsole.log(JSON.stringify({ type: "thread.started"'), "utf8"); process.env.SDD_CODEX_BIN = fake;
    await expect(runAgent(root, "HU-001", "product-analyst", "spec-intake", await parametersFor(root))).rejects.toMatchObject({ code: "SDD-CODEX-OUTPUT-LIMIT" });
  });

  it("selects the highest compatible Codex candidate and ignores an older installation", async () => {
    const root = await story(); const old = path.join(root, "old.mjs"); const current = path.join(root, "current.mjs"); await writeFile(old, 'console.log("codex-cli 0.58.0")', "utf8"); await writeFile(current, 'console.log("codex-cli 0.140.0")', "utf8");
    const selected = await selectCompatibleCodex([{ file: process.execPath, prefix: [old], label: "old" }, { file: process.execPath, prefix: [current], label: "current" }], root); expect(selected.command.label).toBe("current");
  });

  it("rejects a symlink in a product write scope", async () => {
    const root = await story(); const outside = await mkdtemp(path.join(os.tmpdir(), "sdd-outside-")); temporary.push(outside); await symlink(outside, path.join(root, "linked"), "junction");
    const { catalog } = await loadAgentCatalog(root);
    await expect(compilePermissions(root, "HU-001", "run", "plan-executor", catalog.agents["implementation-agent"]!, { write_paths: ["linked/**"] })).rejects.toMatchObject({ code: "SDD-AGENT-SCOPE-SYMLINK" });
  });

  it("detects replacement of a permission root after preflight", async () => {
    const root = await story(); await mkdir(path.join(root, "product")); const { catalog } = await loadAgentCatalog(root); const permissions = await compilePermissions(root, "HU-001", "run", "plan-executor", catalog.agents["implementation-agent"]!, { write_paths: ["product/**"] });
    await rm(path.join(root, "product"), { recursive: true }); await mkdir(path.join(root, "product")); await expect(verifyPermissionAnchors(root, permissions.anchors)).rejects.toMatchObject({ code: "SDD-AGENT-SCOPE-CHANGED" });
  });

  it("blocks mutations owned by another live agent lease", async () => {
    const root = await story(); const lease = agentLeasePath(root, "HU-001"); await mkdir(path.dirname(lease), { recursive: true });
    await writeFile(lease, JSON.stringify({ run_id: "run", agent_id: "product-analyst", pid: process.pid, process_start_ms: 1, hostname: os.hostname(), created_at: new Date().toISOString() }), "utf8");
    await expect(updateStoryStatus(root, "HU-001", "BLOCKED", "test", "Fixture")).rejects.toMatchObject({ code: "SDD-AGENT-ACTIVE" });
  });

  it("recovers a dead agent lease and preserves the aborted run", async () => {
    const root = await story(); const parameters = ".sdd/agent-parameters.yaml"; await writeFile(path.join(root, parameters), "user_story_path: SPEC/HU-001/user-story.md\nvalidation_rules: []\n", "utf8");
    const loaded = await loadAgentCatalog(root); const policy = loaded.catalog.agents["product-analyst"]!; const definition = await loadAgentDefinition(root, "product-analyst", policy);
    const permissions = await compilePermissions(root, "HU-001", "SPEC/HU-001/.harness/skill-runs/pending", "spec-intake", policy, { write_paths: [] });
    const prepared = await prepareSkill(root, "HU-001", "spec-intake", parameters, { agent_id: "product-analyst", agent_definition_sha256: definition.sha256, agent_catalog_sha256: loaded.sha256, permission_profile: permissions.profile, permission_profile_sha256: permissions.sha256 });
    const runId = (prepared.data as any).run_id; const prefix = `SPEC/HU-001/.harness/skill-runs/${runId}`; const runPath = path.join(root, prefix, "run.json");
    await mutateWithReconciliation(root, "HU-001", "fixture bind", async () => {
      const run = JSON.parse(await readFile(runPath, "utf8"));
      return { event_type: "agent.permissions_bound", event_data: { run_id: runId, agent_id: run.agent_id, agent_definition_sha256: run.agent_definition_sha256, agent_catalog_sha256: run.agent_catalog_sha256, permission_profile_sha256: run.permission_profile_sha256 }, actor: { type: "system", identity: "test" }, extra_writes: [], result: { ok: true, command: "fixture bind", story_id: "HU-001", changed: true, blockers: [], next_actions: [] } };
    });
    await mutateWithReconciliation(root, "HU-001", "fixture start", async () => {
      const run = JSON.parse(await readFile(runPath, "utf8")); const started = new Date().toISOString(); run.status = "RUNNING"; run.execution = { provider: "codex-cli", status: "RUNNING", started_at: started, completed_at: null, duration_ms: null, exit_code: null, codex_version: null, model: null, thread_id: null, usage: null, stdout_sha256: null, stderr_excerpt: "" };
      return { event_type: "agent.started", event_data: { run_id: runId, agent_id: run.agent_id, status: "RUNNING" }, actor: { type: "system", identity: "test" }, extra_writes: [{ path: `${prefix}/run.json`, content: `${JSON.stringify(run, null, 2)}\n` }], result: { ok: true, command: "fixture start", story_id: "HU-001", changed: true, blockers: [], next_actions: [] } };
    });
    const stranded = await agentStatus(root, "HU-001", runId); expect(stranded.ok).toBe(false); expect(stranded.blockers.some((item) => item.code === "SDD-AGENT-LEASE")).toBe(true);
    await writeFile(agentLeasePath(root, "HU-001"), JSON.stringify({ run_id: runId, agent_id: "product-analyst", pid: 2147483647, process_start_ms: 1, hostname: os.hostname(), created_at: new Date().toISOString() }), "utf8");
    expect(await recoverAbandonedAgent(root, "HU-001")).toBe(true);
    expect(await agentStatus(root, "HU-001", runId)).toMatchObject({ ok: false, data: { status: "ABORTED" } });
  });
});

async function story(): Promise<string> {
  const root = await mkdtemp(path.join(os.tmpdir(), "sdd-agent-")); temporary.push(root);
  await cp(path.join(repositoryRoot, ".sdd"), path.join(root, ".sdd"), { recursive: true });
  await cp(path.join(repositoryRoot, ".codex"), path.join(root, ".codex"), { recursive: true });
  await mkdir(path.join(root, "docs"), { recursive: true });
  for (const name of ["ARCHITECTURE.md", "architecture-status.md", "SDD-WORKFLOW.md", "SDD-HARNESS-IMPLEMENTATION-PLAN.md"]) await cp(path.join(repositoryRoot, "docs", name), path.join(root, "docs", name));
  await initializeStory(root, { title: "Agent fixture", changeType: "harness-docs", components: [], affectedData: [], affectedFlows: [], readPaths: [], writePaths: [], targetGaps: [] });
  return root;
}

async function parametersFor(root: string): Promise<string> { const parameters = ".sdd/agent-parameters.yaml"; await writeFile(path.join(root, parameters), "user_story_path: SPEC/HU-001/user-story.md\nvalidation_rules: []\n", "utf8"); return parameters; }
async function completedAgentRun(): Promise<{ root: string; runId: string }> {
  const root = await story(); const fake = path.join(root, "fake-codex.mjs"); await writeFile(fake, FAKE_CODEX, "utf8"); process.env.SDD_CODEX_BIN = fake;
  const result = await runAgent(root, "HU-001", "product-analyst", "spec-intake", await parametersFor(root)); return { root, runId: (result.data as any).run_id };
}

const FAKE_CODEX = String.raw`
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
if (process.argv.includes("--version")) { console.log("codex-cli 0.140.0"); process.exit(0); }
const prompt = process.argv.at(-1); const run = prompt.match(/run ([0-9a-f-]{36})/i)[1];
const inputPath = prompt.match(/Read ([^ ]+) and/)[1]; const outputPath = prompt.match(/to ([^ ]+\/output\.json)/)[1];
const inputRaw = await readFile(inputPath, "utf8"); const input = JSON.parse(inputRaw);
const output = { schema_version: "2.0.0", run_id: run, input_sha256: createHash("sha256").update(inputRaw).digest("hex"), correlation_id: input.correlation_id, skill: input.skill, status: "BLOCKED", artifacts: [], docs_consulted: input.docs_context.applicable, doc_conflicts: [], traceability: [], errors: [{ code: "FIXTURE-BLOCKED", message: "fixture", path: null }], result: { acceptance_criteria: ["AC-001"], gaps: ["fixture"] } };
const outputRaw = JSON.stringify(output); await writeFile(outputPath, outputRaw); const receiptPath = process.argv[process.argv.indexOf("-o") + 1]; await writeFile(receiptPath, JSON.stringify({ run_id: run, status: "BLOCKED", output_path: outputPath, input_sha256: createHash("sha256").update(inputRaw).digest("hex"), output_sha256: createHash("sha256").update(outputRaw).digest("hex") }));
console.log(JSON.stringify({ type: "thread.started", thread_id: "thread-fixture", model: "fixture" }));
console.log(JSON.stringify({ type: "turn.completed", usage: { input_tokens: 1, output_tokens: 1 } }));
`;
