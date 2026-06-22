import { cp, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeAll, describe, expect, it } from "vitest";

import { loadAgentCatalog, loadAgentDefinition } from "../src/agents/catalog.js";
import { agentLeasePath } from "../src/agents/lease.js";
import { compilePermissions } from "../src/agents/permissions.js";
import { agentStatus, recoverAbandonedAgent, runAgent } from "../src/agents/protocol.js";
import { createCatalogValidator } from "../src/contracts/catalog.js";
import { updateStoryStatus } from "../src/orchestrator/commands.js";
import { initializeStory } from "../src/orchestrator/init.js";
import { prepareSkill, submitSkill } from "../src/skills/protocol.js";
import { findRepoRoot } from "../src/repo.js";

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
    const analyst = compilePermissions("HU-001", "SPEC/HU-001/.harness/skill-runs/x", "spec-intake", catalog.agents["product-analyst"]!, { write_paths: ["apps/backend/**"] });
    expect(analyst.profile.write_paths).toEqual(["SPEC/HU-001/.harness/skill-runs/x/artifacts", "SPEC/HU-001/.harness/skill-runs/x/output.json", "SPEC/HU-001/.harness/skill-runs/x/receipt.json"]);
    const implementation = compilePermissions("HU-001", "SPEC/HU-001/.harness/skill-runs/x", "plan-executor", catalog.agents["implementation-agent"]!, { write_paths: ["apps/backend/**"] });
    expect(implementation.profile.write_paths).toContain("apps/backend");
    expect(implementation.profile.read_only_paths).toContain("docs/ARCHITECTURE.md");
    expect(() => compilePermissions("HU-001", "run", "plan-executor", catalog.agents["implementation-agent"]!, { write_paths: ["apps/*/src"] })).toThrowError(expect.objectContaining({ code: "SDD-AGENT-SCOPE-UNENFORCEABLE" }));
    expect(() => compilePermissions("HU-001", "run", "plan-executor", catalog.agents["implementation-agent"]!, { write_paths: ["SPEC/HU-001/**"] })).toThrowError(expect.objectContaining({ code: "SDD-AGENT-SCOPE-UNENFORCEABLE" }));
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
    const result = await runAgent(root, "HU-001", "product-analyst", "spec-intake", parameters);
    expect(result).toMatchObject({ ok: false, data: { status: "FAILED" } });
  });

  it("blocks mutations owned by another live agent lease", async () => {
    const root = await story(); const lease = agentLeasePath(root, "HU-001"); await mkdir(path.dirname(lease), { recursive: true });
    await writeFile(lease, JSON.stringify({ run_id: "run", agent_id: "product-analyst", pid: process.pid, process_start_ms: 1, hostname: os.hostname(), created_at: new Date().toISOString() }), "utf8");
    await expect(updateStoryStatus(root, "HU-001", "BLOCKED", "test", "Fixture")).rejects.toMatchObject({ code: "SDD-AGENT-ACTIVE" });
  });

  it("recovers a dead agent lease and preserves the aborted run", async () => {
    const root = await story(); const parameters = ".sdd/agent-parameters.yaml"; await writeFile(path.join(root, parameters), "user_story_path: SPEC/HU-001/user-story.md\nvalidation_rules: []\n", "utf8");
    const loaded = await loadAgentCatalog(root); const policy = loaded.catalog.agents["product-analyst"]!; const definition = await loadAgentDefinition(root, "product-analyst", policy);
    const permissions = compilePermissions("HU-001", "SPEC/HU-001/.harness/skill-runs/pending", "spec-intake", policy, { write_paths: [] });
    const prepared = await prepareSkill(root, "HU-001", "spec-intake", parameters, { agent_id: "product-analyst", agent_definition_sha256: definition.sha256, agent_catalog_sha256: loaded.sha256, permission_profile: permissions.profile, permission_profile_sha256: permissions.sha256 });
    const runId = (prepared.data as any).run_id; await writeFile(agentLeasePath(root, "HU-001"), JSON.stringify({ run_id: runId, agent_id: "product-analyst", pid: 2147483647, process_start_ms: 1, hostname: os.hostname(), created_at: new Date().toISOString() }), "utf8");
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

const FAKE_CODEX = String.raw`
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
if (process.argv.includes("--version")) { console.log("codex-cli 0.140.0"); process.exit(0); }
const prompt = process.argv.at(-1); const run = prompt.match(/run ([0-9a-f-]{36})/i)[1];
const inputPath = prompt.match(/Read ([^ ]+) and/)[1]; const outputPath = prompt.match(/to ([^ ]+\/output\.json)/)[1];
const inputRaw = await readFile(inputPath, "utf8"); const input = JSON.parse(inputRaw);
const output = { schema_version: "2.0.0", run_id: run, input_sha256: createHash("sha256").update(inputRaw).digest("hex"), correlation_id: input.correlation_id, skill: input.skill, status: "BLOCKED", artifacts: [], docs_consulted: input.docs_context.applicable, doc_conflicts: [], traceability: [], errors: [{ code: "FIXTURE-BLOCKED", message: "fixture", path: null }], result: { acceptance_criteria: ["AC-001"], gaps: ["fixture"] } };
await writeFile(outputPath, JSON.stringify(output)); const receiptPath = process.argv[process.argv.indexOf("-o") + 1]; await writeFile(receiptPath, JSON.stringify({ run_id: run, status: "BLOCKED", output_path: outputPath }));
console.log(JSON.stringify({ type: "thread.started", thread_id: "thread-fixture", model: "fixture" }));
console.log(JSON.stringify({ type: "turn.completed", usage: { input_tokens: 1, output_tokens: 1 } }));
`;
