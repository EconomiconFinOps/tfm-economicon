import { readFile } from "node:fs/promises";

import { validateArtifactContent } from "../contracts/artifact.js";
import { loadConfig, loadWorkflow } from "../config.js";
import { HarnessBlockedError, HarnessInputError } from "../errors.js";
import { sha256File } from "../hash.js";
import { validateManifest } from "../manifest/validate.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { Actor, AnyRecord, CommandResult, ValidationIssue, WorkflowContract } from "../types.js";
import { evaluateNext } from "./gates.js";
import { humanActor } from "./identity.js";
import { applyInvalidation, reconcileManifest } from "./reconcile.js";
import { captureBaseline } from "./scope.js";
import { snapshotArtifact } from "./snapshot.js";
import { mutateStory, type ExtraWrite, type MutationPlan } from "./store.js";
import { storyManifestPath } from "./paths.js";

type Action = (manifest: AnyRecord, workflow: WorkflowContract) => Promise<MutationPlan>;

export async function mutateWithReconciliation(root: string, storyId: string, command: string, action: Action): Promise<CommandResult> {
  const config = await loadConfig(root);
  const workflow = await loadWorkflow(root, config);
  try {
    return await mutateStory(root, storyId, async (manifest) => {
      const current = await validateManifest(root, storyManifestPath(root, storyId));
      const nonReconcilable = current.errors.filter((issue) => !RECONCILABLE_CODES.has(issue.code));
      if (nonReconcilable.length) throw new HarnessBlockedError("Current manifest is invalid", nonReconcilable);
      const reconciliation = await reconcileManifest(root, manifest, workflow);
      if (current.errors.length && !reconciliation.changed) throw new HarnessBlockedError("Manifest drift cannot be reconciled safely", current.errors);
      if (reconciliation.changed) {
        return {
          event_type: "story.reconciled", actor: { type: "system", identity: "sdd-cli" },
          event_data: { requested_command: command, causes: reconciliation.causes, blockers: reconciliation.blockers },
          result: { ok: false, command, story_id: storyId, changed: true, blockers: reconciliation.blockers, next_actions: ["review reconciled state", `retry ${command}`] },
        };
      }
      return action(manifest, workflow);
    });
  } catch (error) {
    if (error instanceof HarnessBlockedError) return { ok: false, command, story_id: storyId, changed: false, blockers: error.issues, next_actions: ["fix validation errors", "run sdd status"] };
    throw error;
  }
}

const RECONCILABLE_CODES = new Set(["SDD-ARTIFACT-HASH", "SDD-DOC-STALE", "SDD-DOC-MISSING", "SDD-EVIDENCE-STALE", "WF-OUT-OF-SCOPE"]);

export async function approveArtifact(root: string, storyId: string, artifactSelector: string, decision: string, identity?: string, comment?: string): Promise<CommandResult> {
  const actor = await humanActor(root, identity);
  return mutateWithReconciliation(root, storyId, "approve", async (manifest, workflow) => {
    const artifact = selectArtifact(manifest, artifactSelector);
    if (artifact.status !== "DRAFT") throw new HarnessInputError("WF-INVALID-TRANSITION", `Artifact must be DRAFT, found ${artifact.status}`);
    if (!new Set(["APPROVED", "CHANGES_REQUESTED", "REJECTED"]).has(decision)) throw new HarnessInputError("SDD-DECISION", `Invalid decision: ${decision}`);
    const contract = await validateArtifactContent(root, await readFile(resolveConcreteRepoPath(root, artifact.path), "utf8"), artifact.type, artifact.schema_version, storyId);
    if (contract.issues.length) throw new HarnessBlockedError("Artifact contract is invalid", contract.issues);
    const snapshot = await snapshotArtifact(root, storyId, artifact);
    const now = new Date().toISOString();
    artifact.status = decision;
    artifact.updated_at = now;
    artifact.approvals.push({ decision, artifact_version: artifact.version, artifact_sha256: artifact.sha256, snapshot_path: snapshot.path, approver: { actor_type: "human", identity: actor.identity }, decided_at: now, comment: comment ?? null });
    if (decision !== "APPROVED") applyInvalidation(manifest, workflow, artifact.type === "task" ? "roadmap_or_tasks" : artifact.type, now);
    return plan("approve", storyId, actor, "artifact.decided", { artifact: artifact.path, version: artifact.version, decision }, [snapshot.write], manifest);
  });
}

export async function registerArtifact(root: string, storyId: string, type: string, artifactPath: string): Promise<CommandResult> {
  const allowed = new Set(["user-story", "prd", "tdr", "roadmap", "task", "execution-summary", "verification-evidence", "review"]);
  if (!allowed.has(type)) throw new HarnessInputError("SDD-ARTIFACT", `Unsupported artifact type: ${type}`);
  return mutateWithReconciliation(root, storyId, "artifact register", async (manifest) => {
    if (manifest.artifacts.some((item: AnyRecord) => item.path === artifactPath)) throw new HarnessInputError("SDD-ARTIFACT-DUPLICATE", `Artifact already registered: ${artifactPath}`);
    const hash = await sha256File(resolveConcreteRepoPath(root, artifactPath));
    const contract = await validateArtifactContent(root, await readFile(resolveConcreteRepoPath(root, artifactPath), "utf8"), type, "1.0.0", storyId);
    if (contract.issues.length) throw new HarnessBlockedError("Artifact contract is invalid", contract.issues);
    manifest.artifacts.push({ type, schema_version: "1.0.0", path: artifactPath, version: 1, sha256: hash, status: "DRAFT", updated_at: new Date().toISOString(), approvals: [], invalidated_by: null });
    return plan("artifact register", storyId, { type: "system", identity: "sdd-cli" }, "artifact.registered", { type, path: artifactPath }, [], manifest);
  });
}

export async function reviseArtifact(root: string, storyId: string, artifactSelector: string, reason: string, identity?: string): Promise<CommandResult> {
  const actor = await humanActor(root, identity);
  if (!reason.trim()) throw new HarnessInputError("SDD-ARGUMENT", "Revision reason is required");
  return mutateWithReconciliation(root, storyId, "revise", async (manifest) => {
    const artifact = selectArtifact(manifest, artifactSelector);
    if (!["CHANGES_REQUESTED", "REJECTED"].includes(artifact.status)) throw new HarnessInputError("WF-INVALID-TRANSITION", `Cannot revise artifact in ${artifact.status}`);
    artifact.version += 1;
    artifact.status = "DRAFT";
    artifact.invalidated_by = "human_revision";
    artifact.updated_at = new Date().toISOString();
    return plan("revise", storyId, actor, "artifact.revision_created", { artifact: artifact.path, version: artifact.version, reason }, [], manifest);
  });
}

export async function registerEvidence(root: string, storyId: string, condition: string, evidencePaths: string[], actor: Actor): Promise<CommandResult> {
  if (!condition.trim() || evidencePaths.length === 0) throw new HarnessInputError("SDD-ARGUMENT", "Condition and at least one evidence path are required");
  return mutateWithReconciliation(root, storyId, "evidence record", async (manifest) => {
    const evidence = [];
    for (const item of evidencePaths) evidence.push({ path: item, sha256: await sha256File(resolveConcreteRepoPath(root, item)) });
    manifest.gate_evidence = manifest.gate_evidence.filter((item: AnyRecord) => item.condition !== condition);
    manifest.gate_evidence.push({ condition, satisfied: true, evidence, actor: { actor_type: actor.type, identity: actor.identity }, recorded_at: new Date().toISOString() });
    return plan("evidence record", storyId, actor, "gate.evidence_recorded", { condition, evidence: evidencePaths }, [], manifest);
  });
}

export async function advanceStory(root: string, storyId: string): Promise<CommandResult> {
  return mutateWithReconciliation(root, storyId, "next", async (manifest, workflow) => {
    const evaluation = await evaluateNext(root, manifest, workflow);
    if (!evaluation.transition || evaluation.blockers.length) {
      return blockedPlan("next", storyId, "transition.blocked", { transition: evaluation.transition?.id ?? null }, evaluation.blockers, manifest);
    }
    const transition = evaluation.transition;
    const extra: ExtraWrite[] = [];
    manifest.workflow.stage = transition.to;
    manifest.workflow.updated_at = new Date().toISOString();
    if (transition.story_status_after) manifest.workflow.status = transition.story_status_after;
    if (transition.id === "TR-005") {
      const captured = await captureBaseline(root, storyId);
      manifest.execution.baseline = { path: captured.path, sha256: captured.sha256, captured_at: captured.baseline.captured_at };
      extra.push({ path: captured.path, content: captured.content });
    }
    return { ...plan("next", storyId, { type: "system", identity: "sdd-cli" }, "stage.transitioned", { transition: transition.id, from: transition.from, to: transition.to }, extra, manifest), result: { ok: true, command: "next", story_id: storyId, changed: true, stage: transition.to, status: manifest.workflow.status, transition: transition.id, blockers: [], next_actions: [`prepare ${transition.to}`] } };
  });
}

export async function updateTask(root: string, storyId: string, taskId: string, target: string, reason?: string, identity?: string, executor?: Actor, evidencePaths: string[] = []): Promise<CommandResult> {
  const human = ["PENDING"].includes(target) ? await humanActor(root, identity) : { type: "system", identity: "sdd-cli" } as Actor;
  return mutateWithReconciliation(root, storyId, "run", async (manifest, workflow) => {
    if (manifest.workflow.stage !== "EXECUTION" || !manifest.execution.baseline) throw new HarnessInputError("WF-INVALID-TRANSITION", "Task execution requires EXECUTION stage with a current baseline");
    const task = manifest.tasks.find((item: AnyRecord) => item.id === taskId);
    if (!task) throw new HarnessInputError("SDD-TASK", `Unknown task: ${taskId}`);
    const transition = workflow.execution_transitions.find((item: AnyRecord) => item.from === task.status && item.to === target);
    if (!transition) throw new HarnessInputError("WF-INVALID-TRANSITION", `Task transition ${task.status} -> ${target} is not allowed`);
    if (transition.id === "EX-007") throw new HarnessInputError("WF-INVALID-TRANSITION", "EX-007 is reserved for automatic reconciler invalidation");
    const now = new Date().toISOString();
    if (["FAILED", "BLOCKED", "PENDING"].includes(target) && !reason?.trim()) throw new HarnessInputError("SDD-ARGUMENT", `${target} requires --reason`);
    const evidence = [];
    for (const item of evidencePaths) evidence.push({ path: item, sha256: await sha256File(resolveConcreteRepoPath(root, item)) });
    if (target === "RUNNING") {
      if (!executor?.identity) throw new HarnessInputError("SDD-EXECUTOR", "RUNNING requires an explicit executor");
      const attempt = task.attempts.at(-1);
      if (attempt?.status === "PENDING") Object.assign(attempt, { status: "RUNNING", started_at: now, executor: { actor_type: executor.type, identity: executor.identity } });
      else if (task.attempts.length === 0) task.attempts.push({ number: 1, status: "RUNNING", started_at: now, completed_at: null, error: null, executor: { actor_type: executor.type, identity: executor.identity }, evidence: [] });
      else throw new HarnessInputError("SDD-ATTEMPT-MISSING", "Task has no pending attempt");
    } else if (target === "PENDING") task.attempts.push({ number: (task.attempts.at(-1)?.number ?? 0) + 1, status: "PENDING", started_at: null, completed_at: null, error: null, executor: null, evidence });
    else {
      const attempt = task.attempts.at(-1);
      if (!attempt) throw new HarnessInputError("SDD-ATTEMPT-MISSING", "Task has no active attempt");
      attempt.status = target;
      if (["COMPLETED", "FAILED", "BLOCKED"].includes(target)) attempt.completed_at = now;
      if (target === "COMPLETED") {
        const checks = new Map((manifest.checks as AnyRecord[]).map((check) => [check.id, check]));
        const failed = task.required_checks.filter((id: string) => checks.get(id)?.status !== "COMPLETED" || checks.get(id)?.result?.exit_code !== 0);
        if (failed.length) throw new HarnessInputError("WF-CHECK-FAILED", `Required checks are not successful: ${failed.join(", ")}`);
      }
      if (["FAILED", "BLOCKED"].includes(target)) {
        if (!evidence.length) throw new HarnessInputError("SDD-ATTEMPT-EVIDENCE", `${target} requires --evidence`);
        attempt.error = reason;
        attempt.evidence = evidence;
      }
    }
    task.status = target;
    if (target === "BLOCKED") manifest.workflow.status = "BLOCKED";
    if (target === "PENDING" && manifest.workflow.status === "BLOCKED") manifest.workflow.status = "ACTIVE";
    return plan("run", storyId, human, "task.transitioned", { task_id: taskId, transition: transition.id, to: target, reason: reason ?? null }, [], manifest);
  });
}

export async function updateStoryStatus(root: string, storyId: string, target: string, reason: string, identity?: string): Promise<CommandResult> {
  const actor = await humanActor(root, identity);
  if (!reason.trim()) throw new HarnessInputError("SDD-ARGUMENT", "Story status transition requires --reason");
  return mutateWithReconciliation(root, storyId, "story", async (manifest) => {
    const from = manifest.workflow.status;
    const allowed = (from === "ACTIVE" && ["BLOCKED", "CANCELLED"].includes(target)) || (from === "BLOCKED" && ["ACTIVE", "CANCELLED"].includes(target));
    if (!allowed) throw new HarnessInputError("WF-INVALID-TRANSITION", `Story transition ${from} -> ${target} is not allowed`);
    manifest.workflow.status = target;
    manifest.workflow.updated_at = new Date().toISOString();
    return plan("story", storyId, actor, "story.status_transitioned", { from, to: target, reason }, [], manifest);
  });
}

export async function recordCheck(root: string, storyId: string, checkId: string, exitCode: number, evidencePath: string): Promise<CommandResult> {
  return mutateWithReconciliation(root, storyId, "run", async (manifest) => {
    const check = manifest.checks.find((item: AnyRecord) => item.id === checkId);
    if (!check) throw new HarnessInputError("SDD-CHECK", `Unknown check: ${checkId}`);
    await sha256File(resolveConcreteRepoPath(root, evidencePath));
    const now = new Date().toISOString();
    const resultNumber = manifest.checks.filter((item: AnyRecord) => item.result).length + 1;
    check.status = exitCode === 0 ? "COMPLETED" : "FAILED";
    check.result = { id: `RESULT-${String(resultNumber).padStart(3, "0")}`, exit_code: exitCode, started_at: now, completed_at: now, evidence_path: evidencePath };
    manifest.traceability.entities.push({ id: check.result.id, type: "RESULT", artifact_path: null });
    manifest.traceability.relations.push({ from: check.id, to: check.result.id, type: "produces" });
    return plan("run", storyId, { type: "system", identity: "sdd-cli" }, "check.recorded", { check_id: checkId, exit_code: exitCode, evidence_path: evidencePath }, [], manifest);
  });
}

export async function resolveReview(root: string, storyId: string, decision: string, identity?: string, cause?: string, comment?: string): Promise<CommandResult> {
  const actor = await humanActor(root, identity);
  return mutateWithReconciliation(root, storyId, "review", async (manifest, workflow) => {
    if (manifest.workflow.stage !== "REVIEW") throw new HarnessInputError("WF-INVALID-TRANSITION", "Story is not in REVIEW");
    const review = selectArtifact(manifest, "review");
    if (review.status !== "DRAFT") throw new HarnessInputError("WF-INVALID-TRANSITION", `Review must be DRAFT, found ${review.status}`);
    const contract = await validateArtifactContent(root, await readFile(resolveConcreteRepoPath(root, review.path), "utf8"), review.type, review.schema_version, storyId);
    if (contract.issues.length) throw new HarnessBlockedError("Review contract is invalid", contract.issues);
    const snapshot = await snapshotArtifact(root, storyId, review);
    const now = new Date().toISOString();
    if (decision === "APPROVED") {
      const original = structuredClone(review);
      review.status = "APPROVED";
      review.approvals.push({ decision, artifact_version: review.version, artifact_sha256: review.sha256, snapshot_path: snapshot.path, approver: { actor_type: "human", identity: actor.identity }, decided_at: now, comment: comment ?? null });
      const evaluation = await evaluateNext(root, manifest, workflow);
      if (evaluation.blockers.length || evaluation.transition?.id !== "TR-008") {
        Object.assign(review, original);
        return blockedPlan("review", storyId, "review.blocked", { decision }, evaluation.blockers, manifest);
      }
      manifest.workflow.stage = "COMPLETED";
      manifest.workflow.status = "COMPLETED";
      manifest.workflow.updated_at = now;
      return plan("review", storyId, actor, "review.approved", { decision, transition: "TR-008" }, [snapshot.write], manifest);
    }
    if (decision !== "CHANGES_REQUESTED" || !cause) throw new HarnessInputError("SDD-ARGUMENT", "Review requires APPROVED or CHANGES_REQUESTED with --cause");
    const correction = workflow.correction_returns.find((item) => item.cause === cause && item.from_stages.includes("REVIEW"));
    if (!correction) throw new HarnessInputError("WF-INVALID-TRANSITION", `Invalid review correction cause: ${cause}`);
    review.status = "CHANGES_REQUESTED";
    review.approvals.push({ decision, artifact_version: review.version, artifact_sha256: review.sha256, snapshot_path: snapshot.path, approver: { actor_type: "human", identity: actor.identity }, decided_at: now, comment: comment ?? null });
    applyInvalidation(manifest, workflow, correctionKey(cause), now);
    manifest.workflow.stage = correction.to;
    manifest.workflow.updated_at = now;
    return plan("review", storyId, actor, "review.changes_requested", { decision, cause, return_to: correction.to }, [snapshot.write], manifest);
  });
}

function selectArtifact(manifest: AnyRecord, selector: string): AnyRecord {
  const matches = manifest.artifacts.filter((item: AnyRecord) => item.type === selector || item.path === selector);
  if (matches.length !== 1) throw new HarnessInputError("SDD-ARTIFACT", `Artifact selector must match exactly one artifact: ${selector}`);
  return matches[0];
}

function plan(command: string, storyId: string, actor: Actor, eventType: string, eventData: AnyRecord, extraWrites: ExtraWrite[], manifest: AnyRecord): MutationPlan {
  return { event_type: eventType, event_data: eventData, actor, extra_writes: extraWrites, result: { ok: true, command, story_id: storyId, changed: true, stage: manifest.workflow.stage, status: manifest.workflow.status, blockers: [], next_actions: ["run sdd status"] } };
}

function blockedPlan(command: string, storyId: string, eventType: string, eventData: AnyRecord, blockers: ValidationIssue[], manifest: AnyRecord): MutationPlan {
  return { event_type: eventType, event_data: { ...eventData, blockers }, actor: { type: "system", identity: "sdd-cli" }, result: { ok: false, command, story_id: storyId, changed: true, stage: manifest.workflow.stage, status: manifest.workflow.status, blockers, next_actions: ["resolve blockers", "run sdd status"] } };
}

function correctionKey(cause: string): string {
  if (cause === "scope_or_story") return "user-story";
  if (cause === "requirements") return "prd";
  if (cause === "design_or_architecture") return "tdr";
  if (cause === "planning_or_dependencies") return "roadmap_or_tasks";
  if (["implementation_or_tests", "verification_failure_requires_implementation_change"].includes(cause)) return "source_or_tests";
  if (cause === "verification_evidence_refresh_without_implementation_change") return "verification-evidence";
  return "review";
}
