import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";

import { validateManifest } from "../src/manifest/validate.js";
import { sha256Text } from "../src/hash.js";
import { renderArtifactTemplate } from "../src/contracts/artifact.js";
import { advanceStory, approveArtifact, recordCheck, registerArtifact, registerEvidence, resolveReview, updateStoryStatus, updateTask } from "../src/orchestrator/commands.js";
import { initializeStory } from "../src/orchestrator/init.js";
import { storyManifestPath } from "../src/orchestrator/paths.js";
import { captureBaseline } from "../src/orchestrator/scope.js";
import { findRepoRoot } from "../src/repo.js";

let repositoryRoot: string;
const temporary: string[] = [];
const execFileAsync = promisify(execFile);

beforeAll(async () => { repositoryRoot = await findRepoRoot(); });
afterEach(async () => { await Promise.all(temporary.splice(0).map((item) => rm(item, { recursive: true, force: true }))); });

describe("deterministic orchestrator", () => {
  it("initializes the next story without overwriting and validates it", async () => {
    const root = await temporaryRepository();
    const first = await initializeStory(root, options("Primera historia"));
    const second = await initializeStory(root, options("Segunda historia"));
    expect([first.story_id, second.story_id]).toEqual(["HU-001", "HU-002"]);
    const report = await validateManifest(root, storyManifestPath(root, "HU-001"));
    expect(report).toMatchObject({ valid: true, story_id: "HU-001" });
  });

  it("creates an immutable snapshot and advances only an approved artifact", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("Aprobación"));
    const approved = await approveArtifact(root, "HU-001", "user-story", "APPROVED", "Reviewer <review@example.com>");
    expect(approved.ok).toBe(true);
    const currentManifest = await manifest(root);
    const approval = currentManifest.artifacts[0].approvals[0];
    expect(await readFile(path.join(root, ...approval.snapshot_path.split("/")), "utf8")).toContain("HU-001");
    const advanced = await advanceStory(root, "HU-001");
    expect(advanced).toMatchObject({ ok: true, transition: "TR-002", stage: "PRD" });
  });

  it("reconciles a changed approved artifact before accepting another command", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("Drift"));
    await approveArtifact(root, "HU-001", "user-story", "APPROVED", "Reviewer");
    await writeFile(path.join(root, "SPEC/HU-001/user-story.md"), "changed after approval\n", "utf8");
    const result = await advanceStory(root, "HU-001");
    expect(result).toMatchObject({ ok: false, command: "next" });
    const current = await manifest(root);
    expect(result.changed).toBe(false);
    expect(current.artifacts[0]).toMatchObject({ version: 1, status: "APPROVED", invalidated_by: null });
    expect(current.workflow.stage).toBe("INTAKE");
  });

  it("detects a tampered journal chain", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("Journal"));
    const journal = path.join(root, "SPEC/HU-001/journal.ndjson");
    await writeFile(journal, (await readFile(journal, "utf8")).replace("story.initialized", "story.modified"), "utf8");
    const report = await validateManifest(root, storyManifestPath(root, "HU-001"));
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-JOURNAL-HASH" }));
  });

  it("marks gate evidence stale when an input changes", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("Evidence"));
    await registerEvidence(root, "HU-001", "no_open_functional_questions", ["docs/ARCHITECTURE.md"], { type: "agent", identity: "prd-agent" });
    await writeFile(path.join(root, "docs/ARCHITECTURE.md"), "changed architecture\n", "utf8");
    const report = await validateManifest(root, storyManifestPath(root, "HU-001"));
    expect(report.errors).toContainEqual(expect.objectContaining({ code: "SDD-EVIDENCE-STALE" }));
  });

  it("reconciles stale evidence and then blocks the affected gate", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("Stale gate"));
    await approveArtifact(root, "HU-001", "user-story", "APPROVED", "Reviewer");
    await advanceStory(root, "HU-001");
    const prd = await artifactContent(root, "prd");
    await writeFile(path.join(root, "SPEC/HU-001/prd.md"), prd, "utf8");
    await registerArtifact(root, "HU-001", "prd", "SPEC/HU-001/prd.md");
    await approveArtifact(root, "HU-001", "prd", "APPROVED", "Reviewer");
    await registerEvidence(root, "HU-001", "no_open_functional_questions", ["docs/ARCHITECTURE.md"], { type: "human", identity: "Reviewer" });
    await writeFile(path.join(root, "docs/ARCHITECTURE.md"), "changed architecture\n", "utf8");
    expect(await advanceStory(root, "HU-001")).toMatchObject({ ok: false, changed: true });
    const blocked = await advanceStory(root, "HU-001");
    expect(blocked.blockers).toContainEqual(expect.objectContaining({ code: "WF-MISSING-APPROVAL" }));
  });

  it("rejects traversal without changing manifest or journal", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("Traversal"));
    const manifestPath = storyManifestPath(root, "HU-001");
    const journalPath = path.join(root, "SPEC/HU-001/journal.ndjson");
    const before = [await readFile(manifestPath, "utf8"), await readFile(journalPath, "utf8")];
    await expect(registerArtifact(root, "HU-001", "prd", "../outside.md")).rejects.toMatchObject({ code: "SDD-PATH-TRAVERSAL" });
    await expect(registerEvidence(root, "HU-001", "condition", ["..\\outside.md"], { type: "human", identity: "Reviewer" })).rejects.toMatchObject({ code: "SDD-PATH-INVALID" });
    expect([await readFile(manifestPath, "utf8"), await readFile(journalPath, "utf8")]).toEqual(before);
  });

  it("enforces declared execution transitions and preserves attempts", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("Attempts"));
    const current = await manifest(root);
    await enterExecution(root, current);
    current.tasks.push({ id: "TASK-001", path: "SPEC/HU-001/user-story.md", status: "PENDING", depends_on: [], required_checks: [], attempts: [] });
    current.traceability.entities.push({ id: "TASK-001", type: "TASK", artifact_path: "SPEC/HU-001/user-story.md" });
    await writeFile(storyManifestPath(root, "HU-001"), stringify(current), "utf8");
    await updateTask(root, "HU-001", "TASK-001", "RUNNING", undefined, undefined, { type: "agent", identity: "implementation-agent" });
    await updateTask(root, "HU-001", "TASK-001", "FAILED", "compiler error", undefined, undefined, ["SPEC/HU-001/user-story.md"]);
    await updateTask(root, "HU-001", "TASK-001", "PENDING", "retry", "Reviewer");
    const result = await manifest(root);
    expect(result.tasks[0].attempts).toMatchObject([{ number: 1, status: "FAILED" }, { number: 2, status: "PENDING" }]);
    expect(result.tasks[0].attempts[1].started_at).toBeNull();
  });

  it("enforces required checks, explicit executors, evidence and retry start time", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("EX contract"));
    const current = await manifest(root);
    await enterExecution(root, current);
    current.tasks.push({ id: "TASK-001", path: "SPEC/HU-001/user-story.md", status: "PENDING", depends_on: [], required_checks: ["TEST-001"], attempts: [] });
    current.checks.push({ id: "TEST-001", name: "unit", command: "external", cwd: ".", status: "PENDING", result: null });
    current.traceability.entities.push({ id: "TASK-001", type: "TASK", artifact_path: "SPEC/HU-001/user-story.md" }, { id: "TEST-001", type: "TEST", artifact_path: null });
    await writeFile(storyManifestPath(root, "HU-001"), stringify(current), "utf8");
    await expect(updateTask(root, "HU-001", "TASK-001", "RUNNING")).rejects.toMatchObject({ code: "SDD-EXECUTOR" });
    await updateTask(root, "HU-001", "TASK-001", "RUNNING", undefined, undefined, { type: "agent", identity: "executor" });
    await expect(updateTask(root, "HU-001", "TASK-001", "COMPLETED")).rejects.toMatchObject({ code: "WF-CHECK-FAILED" });
    await expect(updateTask(root, "HU-001", "TASK-001", "FAILED", "failure")).rejects.toMatchObject({ code: "SDD-ATTEMPT-EVIDENCE" });
    await updateTask(root, "HU-001", "TASK-001", "FAILED", "failure", undefined, undefined, ["SPEC/HU-001/user-story.md"]);
    await updateTask(root, "HU-001", "TASK-001", "PENDING", "retry", "Reviewer");
    await updateTask(root, "HU-001", "TASK-001", "RUNNING", undefined, undefined, { type: "agent", identity: "executor" });
    expect((await manifest(root)).tasks[0].attempts[1].started_at).not.toBeNull();
    await recordCheck(root, "HU-001", "TEST-001", 0, "SPEC/HU-001/user-story.md");
    await updateTask(root, "HU-001", "TASK-001", "COMPLETED");
    expect((await manifest(root)).tasks[0].status).toBe("COMPLETED");
    await expect(updateTask(root, "HU-001", "TASK-001", "PENDING", "manual invalidation", "Reviewer")).rejects.toMatchObject({ code: "WF-INVALID-TRANSITION" });
  });

  it("resolves an approved review and completes the story atomically", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("Review"));
    const reviewContent = await artifactContent(root, "review");
    const verificationContent = await artifactContent(root, "verification-evidence");
    await writeFile(path.join(root, "SPEC/HU-001/review.md"), reviewContent, "utf8");
    await writeFile(path.join(root, "SPEC/HU-001/verification.md"), verificationContent, "utf8");
    const current = await manifest(root);
    current.workflow.stage = "REVIEW";
    current.artifacts.push({ type: "review", schema_version: "1.0.0", path: "SPEC/HU-001/review.md", version: 1, sha256: sha256Text(reviewContent), status: "DRAFT", updated_at: new Date().toISOString(), approvals: [], invalidated_by: null });
    current.artifacts.push({ type: "verification-evidence", schema_version: "1.0.0", path: "SPEC/HU-001/verification.md", version: 1, sha256: sha256Text(verificationContent), status: "DRAFT", updated_at: new Date().toISOString(), approvals: [], invalidated_by: null });
    current.gate_evidence.push({ condition: "architecture_gates_satisfied", satisfied: true, evidence: [{ path: "docs/ARCHITECTURE.md", sha256: sha256Text(await readFile(path.join(root, "docs/ARCHITECTURE.md"), "utf8")) }], actor: { actor_type: "human", identity: "Reviewer" }, recorded_at: new Date().toISOString() });
    await writeFile(storyManifestPath(root, "HU-001"), stringify(current), "utf8");
    const result = await resolveReview(root, "HU-001", "APPROVED", "Reviewer");
    expect(result).toMatchObject({ ok: true, stage: "COMPLETED", status: "COMPLETED" });
    expect((await manifest(root)).artifacts.find((item: any) => item.type === "review").status).toBe("APPROVED");
  });

  it("supports only declared story status transitions", async () => {
    const root = await temporaryRepository();
    await initializeStory(root, options("Story status"));
    await updateStoryStatus(root, "HU-001", "BLOCKED", "external dependency", "Owner");
    expect((await manifest(root)).workflow.status).toBe("BLOCKED");
    await updateStoryStatus(root, "HU-001", "ACTIVE", "dependency resolved", "Owner");
    await updateStoryStatus(root, "HU-001", "CANCELLED", "superseded", "Owner");
    expect((await manifest(root)).workflow.status).toBe("CANCELLED");
    await expect(updateStoryStatus(root, "HU-001", "ACTIVE", "reopen", "Owner")).rejects.toMatchObject({ code: "WF-INVALID-TRANSITION" });
  });
});

function options(title: string) {
  return { title, changeType: "harness-docs", components: ["sdd-harness"], affectedData: [], affectedFlows: ["workflow"], readPaths: ["docs/**"], writePaths: ["packages/sdd-harness/**"], targetGaps: [] };
}

async function manifest(root: string): Promise<any> { return parse(await readFile(storyManifestPath(root, "HU-001"), "utf8")); }

async function temporaryRepository(): Promise<string> {
  const root = await mkdtemp(path.join(os.tmpdir(), "sdd-orchestrator-"));
  temporary.push(root);
  await cp(path.join(repositoryRoot, ".sdd"), path.join(root, ".sdd"), { recursive: true });
  await mkdir(path.join(root, "docs"), { recursive: true });
  for (const name of ["ARCHITECTURE.md", "architecture-status.md", "SDD-WORKFLOW.md", "SDD-HARNESS-IMPLEMENTATION-PLAN.md"]) {
    await cp(path.join(repositoryRoot, "docs", name), path.join(root, "docs", name), { recursive: true });
  }
  await execFileAsync("git", ["init"], { cwd: root });
  return root;
}

async function enterExecution(root: string, current: any): Promise<void> {
  const baseline = await captureBaseline(root, "HU-001");
  await mkdir(path.dirname(path.join(root, ...baseline.path.split("/"))), { recursive: true });
  await writeFile(path.join(root, ...baseline.path.split("/")), baseline.content, "utf8");
  current.execution.baseline = { path: baseline.path, sha256: baseline.sha256, captured_at: baseline.baseline.captured_at };
  current.workflow.stage = "EXECUTION";
}

async function artifactContent(root: string, type: string): Promise<string> {
  const template = await readFile(path.join(root, ".sdd/templates", `${type}.md`), "utf8");
  const architecture = await readFile(path.join(root, "docs/ARCHITECTURE.md"), "utf8");
  return renderArtifactTemplate(template, { STORY_ID: "HU-001", TITLE: "Fixture", ARCHITECTURE_SHA256: sha256Text(architecture) });
}
