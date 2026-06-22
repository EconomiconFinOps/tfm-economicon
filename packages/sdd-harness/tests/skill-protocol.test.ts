import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";

import { renderArtifactTemplate } from "../src/contracts/artifact.js";
import { createCatalogValidator } from "../src/contracts/catalog.js";
import { sha256Text } from "../src/hash.js";
import { initializeStory } from "../src/orchestrator/init.js";
import { advanceStory, approveArtifact, recordCheck, registerEvidence, resolveReview, updateTask } from "../src/orchestrator/commands.js";
import { storyManifestPath } from "../src/orchestrator/paths.js";
import { captureBaseline } from "../src/orchestrator/scope.js";
import { findRepoRoot } from "../src/repo.js";
import { prepareSkill, submitSkill, validateSkill } from "../src/skills/protocol.js";

let repositoryRoot: string;
const temporary: string[] = [];
const execFileAsync = promisify(execFile);
beforeAll(async () => { repositoryRoot = await findRepoRoot(); });
afterEach(async () => { await Promise.all(temporary.splice(0).map((item) => rm(item, { recursive: true, force: true }))); });

describe("Phase 4 skill protocol", () => {
  it("ships seven explicit project skills with matching UI metadata", async () => {
    for (const skill of ["spec-intake", "prd-generator", "tdr-generator", "task-planner", "plan-executor", "verifier", "reviewer"]) {
      const body = await readFile(path.join(repositoryRoot, ".agents/skills", skill, "SKILL.md"), "utf8");
      const metadata = parse(await readFile(path.join(repositoryRoot, ".agents/skills", skill, "agents/openai.yaml"), "utf8"));
      expect(body).toContain(`name: ${skill}`); expect(body).not.toContain("TODO");
      expect(metadata.policy.allow_implicit_invocation).toBe(false); expect(metadata.interface.default_prompt).toContain(`$${skill}`);
    }
  });
  it.each(["spec-intake", "prd-generator", "tdr-generator", "task-planner", "plan-executor", "verifier", "reviewer"])("validates version 2 contracts for %s", async (skill) => {
    const input = v2Input(skill); const outputPayload = v2Output(skill);
    const inputValidator = await createCatalogValidator(repositoryRoot, `skill/${skill}/input@2.0.0`);
    const outputValidator = await createCatalogValidator(repositoryRoot, `skill/${skill}/output@2.0.0`);
    expect(inputValidator(input), JSON.stringify(inputValidator.errors)).toBe(true);
    expect(outputValidator(outputPayload), JSON.stringify(outputValidator.errors)).toBe(true);
    for (const status of ["BLOCKED", "FAILED"]) expect(outputValidator({ ...outputPayload, status, errors: [{ code: `FIXTURE-${status}`, message: status, path: null }] }), JSON.stringify(outputValidator.errors)).toBe(true);
    expect(inputValidator({ ...input, unexpected: true })).toBe(false);
    expect(outputValidator({ ...outputPayload, input_sha256: "bad" })).toBe(false);
  });
  it("prepares, validates and submits spec-intake without changing stage or approving", async () => {
    const root = await story();
    const prepared = await prepare(root, "spec-intake", { user_story_path: "SPEC/HU-001/user-story.md", validation_rules: ["complete"] });
    const runId = (prepared.data as any).run_id;
    const candidate = await stageArtifact(root, runId, "user-story", "user-story.md");
    await output(root, runId, "spec-intake", { acceptance_criteria: ["AC-001"], gaps: [] }, [candidate], [{ from: "HU-001", to: "AC-001", type: "defines" }]);
    expect(await validateSkill(root, "HU-001", runId)).toMatchObject({ ok: true, changed: false });
    expect(await submitSkill(root, "HU-001", runId, { type: "agent", identity: "fixture" })).toMatchObject({ ok: true, changed: true, stage: "INTAKE" });
    const current = await manifest(root);
    expect(current.workflow.stage).toBe("INTAKE");
    expect(current.artifacts[0]).toMatchObject({ status: "DRAFT", approvals: [] });
    expect(current.traceability.entities).toContainEqual(expect.objectContaining({ id: "AC-001" }));
    expect(await validateSkill(root, "HU-001", runId)).toMatchObject({ ok: false });
    expect(await submitSkill(root, "HU-001", runId, { type: "agent", identity: "fixture" })).toMatchObject({ ok: false, changed: false });
  });

  it("rejects a skill in the wrong stage", async () => {
    const root = await story();
    await expect(prepare(root, "prd-generator", { acceptance_criteria: ["AC-001"] })).rejects.toMatchObject({ code: "WF-INVALID-TRANSITION" });
  });

  it("detects a stale prepared input", async () => {
    const root = await story();
    const prepared = await prepare(root, "spec-intake", { user_story_path: "SPEC/HU-001/user-story.md", validation_rules: [] });
    const runId = (prepared.data as any).run_id;
    const current = await manifest(root);
    current.scope.components.push("changed");
    await writeFile(storyManifestPath(root, "HU-001"), stringify(current), "utf8");
    const result = await validateSkill(root, "HU-001", runId);
    expect(result.blockers).toContainEqual(expect.objectContaining({ code: "SDD-SKILL-STALE" }));
  });

  it.each(["BLOCKED", "FAILED"])("closes a %s run without publishing artifacts", async (status) => {
    const root = await story();
    const prepared = await prepare(root, "spec-intake", { user_story_path: "SPEC/HU-001/user-story.md", validation_rules: [] });
    const runId = (prepared.data as any).run_id;
    await output(root, runId, "spec-intake", { acceptance_criteria: ["AC-001"], gaps: ["missing"] }, [], [], status, [{ code: "INTAKE-MISSING", message: "Missing detail", path: null }]);
    const result = await submitSkill(root, "HU-001", runId, { type: "human", identity: "Owner" });
    expect(result).toMatchObject({ ok: false, changed: true });
    expect(JSON.parse(await readFile(runFile(root, runId), "utf8")).status).toBe(status);
  });

  it("rejects wrong correlation, target traversal and stale candidate hash without a partial commit", async () => {
    const root = await story();
    const prepared = await prepare(root, "spec-intake", { user_story_path: "SPEC/HU-001/user-story.md", validation_rules: [] });
    const runId = (prepared.data as any).run_id;
    const candidate = await stageArtifact(root, runId, "user-story", "user-story.md");
    candidate.target_path = "docs/forbidden.md"; candidate.sha256 = "0".repeat(64);
    await output(root, runId, "spec-intake", { acceptance_criteria: ["AC-001"], gaps: [] }, [candidate]);
    const outputPath = repo(root, `SPEC/HU-001/.harness/skill-runs/${runId}/output.json`);
    const payload = JSON.parse(await readFile(outputPath, "utf8")); payload.correlation_id = "00000000-0000-4000-8000-000000000099"; await writeFile(outputPath, JSON.stringify(payload), "utf8");
    const before = await readFile(storyManifestPath(root, "HU-001"), "utf8");
    const result = await submitSkill(root, "HU-001", runId, { type: "agent", identity: "fixture" });
    expect(result).toMatchObject({ ok: false, changed: false });
    expect(result.blockers.map((item) => item.code)).toEqual(expect.arrayContaining(["SDD-SKILL-CONTEXT", "SDD-SKILL-PATH", "SDD-SKILL-ARTIFACT-HASH"]));
    expect(await readFile(storyManifestPath(root, "HU-001"), "utf8")).toBe(before);
  });

  it("imports roadmap, tasks and checks atomically", async () => {
    const root = await story();
    await setStageWithArtifact(root, "PLAN", "tdr", "APPROVED");
    const prepared = await prepare(root, "task-planner", { decisions: ["DEC-001"], delivery_constraints: [] });
    const runId = (prepared.data as any).run_id;
    const roadmap = await stageArtifact(root, runId, "roadmap", "roadmap.md");
    const task = await stageArtifact(root, runId, "task", "tasks/TASK-001.md");
    const result = { tasks: [{ id: "TASK-001", path: "SPEC/HU-001/tasks/TASK-001.md", depends_on: [], required_checks: ["TEST-001"] }], checks: [{ id: "TEST-001", name: "unit", command: "external", cwd: "." }], execution_order: ["TASK-001"], parallelism_allowed: false };
    await output(root, runId, "task-planner", result, [roadmap, task]);
    expect(await submitSkill(root, "HU-001", runId, { type: "agent", identity: "planner" })).toMatchObject({ ok: true, stage: "PLAN" });
    const current = await manifest(root);
    expect(current.tasks).toContainEqual(expect.objectContaining({ id: "TASK-001", status: "PENDING" }));
    expect(current.checks).toContainEqual(expect.objectContaining({ id: "TEST-001", status: "PENDING" }));
  });

  it("applies only valid RUNNING task terminal transitions", async () => {
    const root = await story();
    await setStageWithArtifact(root, "EXECUTION", "roadmap", "APPROVED");
    await addArtifact(root, "task", "APPROVED", "tasks/TASK-001.md");
    const current = await manifest(root);
    const baseline = await captureBaseline(root, "HU-001");
    await mkdir(path.dirname(repo(root, baseline.path)), { recursive: true }); await writeFile(repo(root, baseline.path), baseline.content, "utf8");
    current.execution.baseline = { path: baseline.path, sha256: baseline.sha256, captured_at: baseline.baseline.captured_at };
    current.tasks.push({ id: "TASK-001", path: "SPEC/HU-001/tasks/TASK-001.md", status: "RUNNING", depends_on: [], required_checks: [], attempts: [{ number: 1, status: "RUNNING", started_at: new Date().toISOString(), completed_at: null, error: null, executor: { actor_type: "agent", identity: "executor" }, evidence: [] }] });
    current.traceability.entities.push({ id: "TASK-001", type: "TASK", artifact_path: "SPEC/HU-001/tasks/TASK-001.md" });
    await writeFile(storyManifestPath(root, "HU-001"), stringify(current), "utf8");
    const prepared = await prepare(root, "plan-executor", { task_ids: ["TASK-001"], required_checks: [] });
    const runId = (prepared.data as any).run_id;
    const summary = await stageArtifact(root, runId, "execution-summary", "execution-summary.md");
    await output(root, runId, "plan-executor", { task_results: [{ task_id: "TASK-001", status: "COMPLETED", reason: null, evidence: [] }], modified_files: [], executed_checks: [] }, [summary]);
    expect(await submitSkill(root, "HU-001", runId, { type: "agent", identity: "executor" })).toMatchObject({ ok: true });
    expect((await manifest(root)).tasks[0]).toMatchObject({ status: "COMPLETED", attempts: [{ status: "COMPLETED" }] });
  });

  it("imports reviewer findings with contractual traceability", async () => {
    const root = await story();
    await setStageWithArtifact(root, "REVIEW", "verification-evidence", "DRAFT");
    const current = await manifest(root);
    current.architecture.invariants.push("ARCH-01"); current.traceability.entities.push({ id: "ARCH-01", type: "ARCH", artifact_path: "docs/ARCHITECTURE.md" });
    await writeFile(storyManifestPath(root, "HU-001"), stringify(current), "utf8");
    const prepared = await prepare(root, "reviewer", { evaluated_commit: "abcdef1", target_gaps: [] });
    const runId = (prepared.data as any).run_id;
    const review = await stageArtifact(root, runId, "review", "review.md");
    const evidence = { path: "docs/ARCHITECTURE.md", sha256: sha256Text(await readFile(path.join(root, "docs/ARCHITECTURE.md"), "utf8")) };
    const finding = { id: "FIND-001", summary: "Violation", severity: "HIGH", status: "OPEN", cause: "design_or_architecture", requirement_ids: [], task_ids: [], invariant_ids: ["ARCH-01"], evidence: [evidence], resolution: null };
    await output(root, runId, "reviewer", { verdict: "CHANGES_REQUESTED", findings: [finding] }, [review], [{ from: "FIND-001", to: "ARCH-01", type: "finds" }]);
    expect(await submitSkill(root, "HU-001", runId, { type: "agent", identity: "reviewer" })).toMatchObject({ ok: true, stage: "REVIEW" });
    expect((await manifest(root)).findings).toContainEqual(expect.objectContaining({ id: "FIND-001", severity: "HIGH" }));
  });

  it("runs all seven skills while only the orchestrator changes stages and approvals", async () => {
    const root = await story();
    const submit = async (skill: string, parameters: unknown, result: unknown, types: Array<[string, string]>, trace: unknown[] = []) => {
      const prepared = await prepare(root, skill, parameters); const runId = (prepared.data as any).run_id;
      const candidates = []; for (const [type, target] of types) candidates.push(await stageArtifact(root, runId, type, target));
      await output(root, runId, skill, result, candidates, trace);
      expect((await submitSkill(root, "HU-001", runId, { type: "agent", identity: `${skill}-fixture` })).ok).toBe(true);
    };
    await submit("spec-intake", { user_story_path: "SPEC/HU-001/user-story.md", validation_rules: [] }, { acceptance_criteria: ["AC-001"], gaps: [] }, [["user-story", "user-story.md"]], [{ from: "HU-001", to: "AC-001", type: "defines" }]);
    await approveArtifact(root, "HU-001", "user-story", "APPROVED", "Owner"); await advanceStory(root, "HU-001");
    await submit("prd-generator", { acceptance_criteria: ["AC-001"] }, { requirements: ["REQ-001"], assumptions: [], exclusions: [] }, [["prd", "prd.md"]], [{ from: "AC-001", to: "REQ-001", type: "defines" }]);
    await approveArtifact(root, "HU-001", "prd", "APPROVED", "Owner"); await evidence(root, "no_open_functional_questions"); await advanceStory(root, "HU-001");
    await submit("tdr-generator", { repository_context: ["docs/ARCHITECTURE.md"], technical_constraints: [] }, { decisions: ["DEC-001"], components: ["harness"], risks: [] }, [["tdr", "tdr.md"]], [{ from: "REQ-001", to: "DEC-001", type: "satisfies" }]);
    await approveArtifact(root, "HU-001", "tdr", "APPROVED", "Owner");
    for (const condition of ["architecture_invariants_evaluated", "architecture_gaps_evaluated", "change_type_policy_satisfied"]) await evidence(root, condition);
    await advanceStory(root, "HU-001");
    const plan = { tasks: [{ id: "TASK-001", path: "SPEC/HU-001/tasks/TASK-001.md", depends_on: [], required_checks: ["TEST-001"] }], checks: [{ id: "TEST-001", name: "fixture", command: "external", cwd: "." }], execution_order: ["TASK-001"], parallelism_allowed: false };
    await submit("task-planner", { decisions: ["DEC-001"], delivery_constraints: [] }, plan, [["roadmap", "roadmap.md"], ["task", "tasks/TASK-001.md"]], [{ from: "DEC-001", to: "TASK-001", type: "implements" }]);
    await approveArtifact(root, "HU-001", "roadmap", "APPROVED", "Owner"); await approveArtifact(root, "HU-001", "SPEC/HU-001/tasks/TASK-001.md", "APPROVED", "Owner"); await advanceStory(root, "HU-001");
    await updateTask(root, "HU-001", "TASK-001", "RUNNING", undefined, undefined, { type: "agent", identity: "executor" });
    await recordCheck(root, "HU-001", "TEST-001", 0, "docs/ARCHITECTURE.md");
    await submit("plan-executor", { task_ids: ["TASK-001"], required_checks: ["TEST-001"] }, { task_results: [{ task_id: "TASK-001", status: "COMPLETED", reason: null, evidence: [] }], modified_files: [], executed_checks: ["TEST-001"] }, [["execution-summary", "execution-summary.md"]]);
    await evidence(root, "source_hashes_current");
    await advanceStory(root, "HU-001");
    const current = await manifest(root);
    await submit("verifier", { baseline_sha256: current.execution.baseline.sha256, required_checks: ["TEST-001"] }, { check_results: [current.checks[0].result.id], verdict: "PASSED" }, [["verification-evidence", "verification-evidence.md"]], [{ from: "TEST-001", to: current.checks[0].result.id, type: "produces" }]);
    await evidence(root, "verification_matches_evaluated_commit"); await advanceStory(root, "HU-001");
    await submit("reviewer", { evaluated_commit: "abcdef1", target_gaps: [] }, { verdict: "APPROVED", findings: [] }, [["review", "review.md"]]);
    await evidence(root, "architecture_gates_satisfied");
    expect(await resolveReview(root, "HU-001", "APPROVED", "Owner")).toMatchObject({ ok: true, stage: "COMPLETED", status: "COMPLETED" });

    async function evidence(repoRoot: string, condition: string): Promise<void> { await registerEvidence(repoRoot, "HU-001", condition, ["docs/ARCHITECTURE.md"], { type: "human", identity: "Owner" }); }
  }, 30_000);
});

async function story(): Promise<string> { const root = await temporaryRepository(); await initializeStory(root, { title: "Skill fixture", changeType: "harness-docs", components: ["sdd-harness"], affectedData: [], affectedFlows: ["workflow"], readPaths: ["docs/**"], writePaths: ["packages/sdd-harness/**"], targetGaps: [] }); return root; }
async function prepare(root: string, skill: string, parameters: unknown) { const file = `SPEC/HU-001/.harness/parameters/${skill}.yaml`; await mkdir(path.dirname(repo(root, file)), { recursive: true }); await writeFile(repo(root, file), stringify(parameters), "utf8"); return prepareSkill(root, "HU-001", skill, file); }
async function manifest(root: string): Promise<any> { return parse(await readFile(storyManifestPath(root, "HU-001"), "utf8")); }
function repo(root: string, value: string): string { return path.join(root, ...value.split("/")); }
function runFile(root: string, runId: string): string { return repo(root, `SPEC/HU-001/.harness/skill-runs/${runId}/run.json`); }

async function output(root: string, runId: string, skill: string, result: unknown, artifacts: unknown[], traceability: unknown[] = [], status = "COMPLETED", errors: unknown[] = []): Promise<void> {
  const prefix = `SPEC/HU-001/.harness/skill-runs/${runId}`;
  const run = JSON.parse(await readFile(repo(root, `${prefix}/run.json`), "utf8"));
  const input = JSON.parse(await readFile(repo(root, run.input_path), "utf8"));
  const payload = { schema_version: "2.0.0", run_id: runId, input_sha256: run.input_sha256, correlation_id: input.correlation_id, skill, status, artifacts, docs_consulted: input.docs_context.applicable, doc_conflicts: [], traceability, errors, result };
  await writeFile(repo(root, run.output_path), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

async function stageArtifact(root: string, runId: string, type: string, target: string): Promise<any> {
  const content = await artifactContent(root, type);
  const staged = `SPEC/HU-001/.harness/skill-runs/${runId}/artifacts/${target}`;
  await mkdir(path.dirname(repo(root, staged)), { recursive: true }); await writeFile(repo(root, staged), content, "utf8");
  return { type, artifact_schema_version: "1.0.0", staged_path: staged, target_path: `SPEC/HU-001/${target}`, sha256: sha256Text(content) };
}

async function setStageWithArtifact(root: string, stage: string, type: string, status: string): Promise<void> { const current = await manifest(root); current.workflow.stage = stage; await writeFile(storyManifestPath(root, "HU-001"), stringify(current), "utf8"); await addArtifact(root, type, status, `${type}.md`); }
async function addArtifact(root: string, type: string, status: string, target: string): Promise<void> {
  const content = await artifactContent(root, type); const targetPath = `SPEC/HU-001/${target}`; await mkdir(path.dirname(repo(root, targetPath)), { recursive: true }); await writeFile(repo(root, targetPath), content, "utf8");
  const current = await manifest(root); const hash = sha256Text(content); const approvals: any[] = [];
  if (status === "APPROVED") { const snapshot = `SPEC/HU-001/history/${type}/v0001/${path.basename(target)}`; await mkdir(path.dirname(repo(root, snapshot)), { recursive: true }); await writeFile(repo(root, snapshot), content, "utf8"); approvals.push({ decision: "APPROVED", artifact_version: 1, artifact_sha256: hash, snapshot_path: snapshot, approver: { actor_type: "human", identity: "Fixture" }, decided_at: new Date().toISOString(), comment: null }); }
  current.artifacts.push({ type, schema_version: "1.0.0", path: targetPath, version: 1, sha256: hash, status, updated_at: new Date().toISOString(), approvals, invalidated_by: null }); await writeFile(storyManifestPath(root, "HU-001"), stringify(current), "utf8");
}

async function artifactContent(root: string, type: string): Promise<string> { const template = await readFile(path.join(root, ".sdd/templates", `${type}.md`), "utf8"); const architecture = await readFile(path.join(root, "docs/ARCHITECTURE.md"), "utf8"); return renderArtifactTemplate(template, { STORY_ID: "HU-001", TITLE: "Skill fixture", ARCHITECTURE_SHA256: sha256Text(architecture) }); }
async function temporaryRepository(): Promise<string> { const root = await mkdtemp(path.join(os.tmpdir(), "sdd-skill-")); temporary.push(root); await cp(path.join(repositoryRoot, ".sdd"), path.join(root, ".sdd"), { recursive: true }); await mkdir(path.join(root, "docs"), { recursive: true }); for (const name of ["ARCHITECTURE.md", "architecture-status.md", "SDD-WORKFLOW.md", "SDD-HARNESS-IMPLEMENTATION-PLAN.md"]) await cp(path.join(repositoryRoot, "docs", name), path.join(root, "docs", name)); await execFileAsync("git", ["init"], { cwd: root }); return root; }

function v2Input(skill: string): any {
  const parameters: Record<string, unknown> = {
    "spec-intake": { user_story_path: "SPEC/HU-001/user-story.md", validation_rules: [] },
    "prd-generator": { acceptance_criteria: ["AC-001"] },
    "tdr-generator": { repository_context: ["docs/ARCHITECTURE.md"], technical_constraints: [] },
    "task-planner": { decisions: ["DEC-001"], delivery_constraints: [] },
    "plan-executor": { task_ids: ["TASK-001"], required_checks: [] },
    verifier: { baseline_sha256: "a".repeat(64), required_checks: ["TEST-001"] },
    reviewer: { evaluated_commit: "abcdef1", target_gaps: [] },
  };
  const stages: Record<string, string> = { "spec-intake": "INTAKE", "prd-generator": "PRD", "tdr-generator": "TDR", "task-planner": "PLAN", "plan-executor": "EXECUTION", verifier: "VERIFICATION", reviewer: "REVIEW" };
  return { schema_version: "2.0.0", run_id: "00000000-0000-4000-8000-000000000001", correlation_id: "00000000-0000-4000-8000-000000000002", skill, story_id: "HU-001", workflow_stage: stages[skill], state_sha256: "a".repeat(64), artifact_versions: [], docs_context: { inventory: [], applicable: [], excluded: [] }, requested_scope: { components: [], affected_data: [], affected_flows: [], read_paths: [], write_paths: [] }, parameters: parameters[skill] };
}

function v2Output(skill: string): any {
  const results: Record<string, unknown> = {
    "spec-intake": { acceptance_criteria: ["AC-001"], gaps: [] },
    "prd-generator": { requirements: ["REQ-001"], assumptions: [], exclusions: [] },
    "tdr-generator": { decisions: ["DEC-001"], components: [], risks: [] },
    "task-planner": { tasks: [{ id: "TASK-001", path: "SPEC/HU-001/tasks/TASK-001.md", depends_on: [], required_checks: [] }], checks: [], execution_order: ["TASK-001"], parallelism_allowed: false },
    "plan-executor": { task_results: [{ task_id: "TASK-001", status: "COMPLETED", reason: null, evidence: [] }], modified_files: [], executed_checks: [] },
    verifier: { check_results: ["RESULT-001"], verdict: "PASSED" },
    reviewer: { verdict: "APPROVED", findings: [] },
  };
  return { schema_version: "2.0.0", run_id: "00000000-0000-4000-8000-000000000001", input_sha256: "a".repeat(64), correlation_id: "00000000-0000-4000-8000-000000000002", skill, status: "COMPLETED", artifacts: [], docs_consulted: [], doc_conflicts: [], traceability: [], errors: [], result: results[skill] };
}
