import { access } from "node:fs/promises";
import path from "node:path";

import { sha256File, sha256Text } from "../hash.js";
import { readText } from "../io.js";
import { assertRepoPath, resolveConcreteRepoPath } from "../repo.js";
import type { HarnessConfig, JsonObject, ValidationIssue, WorkflowContract } from "../types.js";
import { validateJournalEvents } from "../orchestrator/journal.js";
import { validateScope } from "../orchestrator/scope.js";
import { validateArtifactContent } from "../contracts/artifact.js";

type AnyRecord = Record<string, any>;

export async function validateManifestSemantics(
  root: string,
  manifestPath: string,
  manifest: JsonObject,
  config: HarnessConfig,
  workflow: WorkflowContract,
  overlay: Map<string, string> = new Map(),
): Promise<ValidationIssue[]> {
  const issues: ValidationIssue[] = [];
  const data = manifest as AnyRecord;
  const add = (code: string, instancePath: string, message: string): void => {
    issues.push({ code, instance_path: instancePath, message });
  };

  if (!workflow.change_types.includes(data.story.change_type)) {
    add("SDD-CHANGE-TYPE", "/story/change_type", "Change type is not allowed by the approved workflow");
  }
  if (!workflow.workflow.stages.includes(data.workflow.stage)) {
    add("SDD-WORKFLOW-STAGE", "/workflow/stage", "Stage is not allowed by the approved workflow");
  }
  if (!workflow.workflow.story_statuses.includes(data.workflow.status)) {
    add("SDD-WORKFLOW-STATUS", "/workflow/status", "Story status is not allowed by the approved workflow");
  }
  if ((data.workflow.stage === "COMPLETED") !== (data.workflow.status === "COMPLETED")) {
    add("SDD-WORKFLOW-COMPLETION", "/workflow", "COMPLETED stage and status must be set together");
  }
  requireUtc(data.workflow.updated_at, "/workflow/updated_at", add);

  const relativeManifest = path.relative(root, manifestPath).replaceAll("\\", "/");
  const isExamplePath = relativeManifest.startsWith(`${config.paths.examples}/`);
  if (data.story.id === "HU-000" && (!data.story.is_fixture || !isExamplePath)) {
    add("SDD-FIXTURE-ID", "/story/id", "HU-000 is reserved for fixtures under SPEC/examples");
  }
  if (data.story.id !== "HU-000" && data.story.is_fixture) {
    add("SDD-FIXTURE-ID", "/story/is_fixture", "Only HU-000 may be marked as fixture");
  }
  if (data.story.change_type === "harness-docs" && data.story.runtime_changes) {
    add("SDD-HARNESS-RUNTIME", "/story/runtime_changes", "harness-docs cannot declare runtime changes");
  }
  if (data.story.change_type === "remediation" && data.architecture.gaps.length === 0) {
    add("SDD-REMEDIATION-GAPS", "/architecture/gaps", "remediation must declare at least one target gap");
  }

  for (const [field, values] of Object.entries({
    "/scope/read_paths": data.scope.read_paths,
    "/scope/write_paths": data.scope.write_paths,
  })) {
    for (const [index, value] of (values as string[]).entries()) {
      try {
        assertRepoPath(value);
      } catch (error) {
        add("SDD-PATH-INVALID", `${field}/${index}`, error instanceof Error ? error.message : String(error));
      }
    }
  }

  const artifactPaths = new Set<string>();
  for (const [index, artifact] of (data.artifacts as AnyRecord[]).entries()) {
    const base = `/artifacts/${index}`;
    if (artifactPaths.has(artifact.path)) {
      add("SDD-ARTIFACT-DUPLICATE", `${base}/path`, `Duplicate artifact path: ${artifact.path}`);
      continue;
    }
    artifactPaths.add(artifact.path);
    const concrete = await existingConcretePath(root, artifact.path, `${base}/path`, add, overlay);
    if (concrete) {
      const actualHash = await hashRepoFile(root, artifact.path, overlay);
      if (actualHash !== artifact.sha256) {
        add("SDD-ARTIFACT-HASH", `${base}/sha256`, `Hash does not match ${artifact.path}`);
      }
      const contract = await validateArtifactContent(root, await readRepoFile(root, artifact.path, overlay), artifact.type, artifact.schema_version, data.story.id, artifact.status === "APPROVED");
      for (const issue of contract.issues) add(issue.code, `${base}${issue.instance_path}`, issue.message);
    }
    requireUtc(artifact.updated_at, `${base}/updated_at`, add);
    for (const [approvalIndex, approval] of artifact.approvals.entries()) {
      requireUtc(approval.decided_at, `${base}/approvals/${approvalIndex}/decided_at`, add);
      const snapshot = await existingConcretePath(root, approval.snapshot_path, `${base}/approvals/${approvalIndex}/snapshot_path`, add, overlay);
      if (snapshot && await hashRepoFile(root, approval.snapshot_path, overlay) !== approval.artifact_sha256) {
        add("SDD-SNAPSHOT-HASH", `${base}/approvals/${approvalIndex}/snapshot_path`, "Snapshot does not match approved artifact hash");
      }
    }
    const latestDecision = artifact.approvals.at(-1)?.decision;
    if (artifact.status === "APPROVED") {
      const validApproval = artifact.approvals.some(
        (approval: AnyRecord) =>
          approval.decision === "APPROVED" &&
          approval.artifact_version === artifact.version &&
          approval.artifact_sha256 === artifact.sha256 &&
          approval.approver.actor_type === "human",
      );
      if (!validApproval) {
        add("SDD-APPROVAL-MISSING", `${base}/approvals`, "APPROVED artifact requires a current human approval");
      }
    }
    if (["CHANGES_REQUESTED", "REJECTED"].includes(artifact.status) && latestDecision !== artifact.status) {
      add("SDD-ARTIFACT-DECISION", `${base}/status`, "Artifact status must match its latest decision");
    }
  }

  const taskIds = uniqueIds(data.tasks, "/tasks", "SDD-TASK-DUPLICATE", add);
  const dependencyGraph = new Map<string, string[]>();
  for (const [index, task] of (data.tasks as AnyRecord[]).entries()) {
    dependencyGraph.set(task.id, task.depends_on);
    for (const dependency of task.depends_on) {
      if (!taskIds.has(dependency)) {
        add("SDD-TASK-DEPENDENCY", `/tasks/${index}/depends_on`, `Unknown task dependency: ${dependency}`);
      }
    }
    for (const requiredCheck of task.required_checks) {
      if (!(data.checks as AnyRecord[]).some((check) => check.id === requiredCheck)) {
        add("SDD-TASK-CHECK", `/tasks/${index}/required_checks`, `Unknown required check: ${requiredCheck}`);
      }
    }
    await existingConcretePath(root, task.path, `/tasks/${index}/path`, add, overlay);
    const attemptNumbers = task.attempts.map((attempt: AnyRecord) => attempt.number);
    if (new Set(attemptNumbers).size !== attemptNumbers.length) {
      add("SDD-ATTEMPT-DUPLICATE", `/tasks/${index}/attempts`, "Attempt numbers must be unique");
    }
    const latestAttempt = task.attempts.at(-1);
    for (const [attemptIndex, attempt] of task.attempts.entries()) {
      if (attempt.started_at) requireUtc(attempt.started_at, `/tasks/${index}/attempts/${attemptIndex}/started_at`, add);
      if (attempt.completed_at) requireUtc(attempt.completed_at, `/tasks/${index}/attempts/${attemptIndex}/completed_at`, add);
      if (attempt.status === "RUNNING" && (!attempt.started_at || !attempt.executor)) add("SDD-ATTEMPT-EXECUTOR", `/tasks/${index}/attempts/${attemptIndex}`, "Running attempt requires start time and executor");
      if (["FAILED", "BLOCKED"].includes(attempt.status) && (!attempt.error || !attempt.evidence.length)) add("SDD-ATTEMPT-EVIDENCE", `/tasks/${index}/attempts/${attemptIndex}`, "Failed or blocked attempt requires reason and evidence");
      for (const [evidenceIndex, evidence] of attempt.evidence.entries()) {
        await existingConcretePath(root, evidence.path, `/tasks/${index}/attempts/${attemptIndex}/evidence/${evidenceIndex}/path`, add, overlay);
        if (await hashRepoFile(root, evidence.path, overlay) !== evidence.sha256) add("SDD-ATTEMPT-EVIDENCE", `/tasks/${index}/attempts/${attemptIndex}/evidence/${evidenceIndex}/sha256`, "Attempt evidence hash is stale");
      }
    }
    if (latestAttempt && latestAttempt.status !== task.status) {
      add("SDD-ATTEMPT-STATUS", `/tasks/${index}/status`, "Task status must match its latest attempt");
    }
    if (!latestAttempt && task.status !== "PENDING") {
      add("SDD-ATTEMPT-MISSING", `/tasks/${index}/attempts`, "Non-pending task requires an attempt");
    }
  }
  detectCycles(dependencyGraph, add);

  const checkIds = uniqueIds(data.checks, "/checks", "SDD-CHECK-DUPLICATE", add);
  const resultIds = new Set<string>();
  for (const [index, check] of (data.checks as AnyRecord[]).entries()) {
    await existingConcretePath(root, check.cwd, `/checks/${index}/cwd`, add, overlay);
    const result = check.result;
    if (["COMPLETED", "FAILED"].includes(check.status) && !result) {
      add("SDD-CHECK-RESULT", `/checks/${index}/result`, "Completed or failed check requires a result");
    }
    if (!["COMPLETED", "FAILED"].includes(check.status) && result) {
      add("SDD-CHECK-RESULT", `/checks/${index}/result`, "Only completed or failed checks may contain a result");
    }
    if (result) {
      if (resultIds.has(result.id)) {
        add("SDD-RESULT-DUPLICATE", `/checks/${index}/result/id`, `Duplicate result ID: ${result.id}`);
      }
      resultIds.add(result.id);
      requireUtc(result.started_at, `/checks/${index}/result/started_at`, add);
      requireUtc(result.completed_at, `/checks/${index}/result/completed_at`, add);
      if ((check.status === "COMPLETED") !== (result.exit_code === 0)) {
        add("SDD-CHECK-EXIT", `/checks/${index}/result/exit_code`, "Exit code must agree with check status");
      }
      await existingConcretePath(root, result.evidence_path, `/checks/${index}/result/evidence_path`, add, overlay);
    }
  }

  const evidenceConditions = new Set<string>();
  for (const [index, evidence] of (data.gate_evidence as AnyRecord[]).entries()) {
    if (evidenceConditions.has(evidence.condition)) {
      add("SDD-EVIDENCE-DUPLICATE", `/gate_evidence/${index}/condition`, `Duplicate gate evidence: ${evidence.condition}`);
    }
    evidenceConditions.add(evidence.condition);
    requireUtc(evidence.recorded_at, `/gate_evidence/${index}/recorded_at`, add);
    for (const [inputIndex, input] of evidence.evidence.entries()) {
      const concrete = await existingConcretePath(root, input.path, `/gate_evidence/${index}/evidence/${inputIndex}/path`, add, overlay);
      if (evidence.satisfied && concrete && await hashRepoFile(root, input.path, overlay) !== input.sha256) {
        add("SDD-EVIDENCE-STALE", `/gate_evidence/${index}/evidence/${inputIndex}/sha256`, `Evidence input is stale: ${input.path}`);
      }
    }
  }

  const findingIds = uniqueIds(data.findings, "/findings", "SDD-FINDING-DUPLICATE", add);
  for (const [index, finding] of (data.findings as AnyRecord[]).entries()) {
    if (finding.resolution) requireUtc(finding.resolution.resolved_at, `/findings/${index}/resolution/resolved_at`, add);
    for (const [evidenceIndex, evidence] of finding.evidence.entries()) {
      const concrete = await existingConcretePath(root, evidence.path, `/findings/${index}/evidence/${evidenceIndex}/path`, add, overlay);
      if (concrete && await hashRepoFile(root, evidence.path, overlay) !== evidence.sha256) add("SDD-FINDING-EVIDENCE", `/findings/${index}/evidence/${evidenceIndex}/sha256`, `Finding evidence is stale: ${evidence.path}`);
    }
  }

  const entities = data.traceability.entities as AnyRecord[];
  const entityIds = uniqueIds(entities, "/traceability/entities", "SDD-TRACE-ENTITY-DUPLICATE", add);
  const requiredEntities = new Set<string>([
    data.story.id,
    ...data.architecture.invariants,
    ...data.architecture.gaps,
    ...data.architecture.adrs,
    ...taskIds,
    ...checkIds,
    ...resultIds,
    ...findingIds,
  ]);
  for (const required of requiredEntities) {
    if (!entityIds.has(required)) {
      add("SDD-TRACE-ENTITY-MISSING", "/traceability/entities", `Missing traceability entity: ${required}`);
    }
  }
  for (const [index, entity] of entities.entries()) {
    if (entity.artifact_path) {
      await existingConcretePath(root, entity.artifact_path, `/traceability/entities/${index}/artifact_path`, add, overlay);
    }
  }

  const architectureDoc = await readText(resolveConcreteRepoPath(root, "docs/ARCHITECTURE.md"));
  for (const invariant of data.architecture.invariants as string[]) {
    if (!architectureDoc.includes(`### ${invariant} `)) {
      add("SDD-ARCH-UNKNOWN", "/architecture/invariants", `Unknown architecture invariant: ${invariant}`);
    }
  }
  const architectureStatus = await readText(resolveConcreteRepoPath(root, "docs/architecture-status.md"));
  for (const gap of data.architecture.gaps as string[]) {
    if (!architectureStatus.includes(`\`${gap}\``)) {
      add("SDD-GAP-UNKNOWN", "/architecture/gaps", `Unknown architecture gap: ${gap}`);
    }
  }
  for (const [index, adr] of (data.architecture.adrs as string[]).entries()) {
    await existingConcretePath(root, `docs/decisions/${adr}.md`, `/architecture/adrs/${index}`, add, overlay);
  }
  const relationKeys = new Set<string>();
  for (const [index, relation] of (data.traceability.relations as AnyRecord[]).entries()) {
    const key = `${relation.from}|${relation.type}|${relation.to}`;
    if (relationKeys.has(key)) {
      add("SDD-TRACE-RELATION-DUPLICATE", `/traceability/relations/${index}`, "Duplicate traceability relation");
    }
    relationKeys.add(key);
    if (!entityIds.has(relation.from) || !entityIds.has(relation.to)) {
      add("SDD-TRACE-RELATION-BROKEN", `/traceability/relations/${index}`, "Traceability relation references an unknown entity");
    }
  }
  for (const [index, finding] of (data.findings as AnyRecord[]).entries()) {
    for (const target of [...finding.requirement_ids, ...finding.task_ids, ...finding.invariant_ids]) {
      if (!entityIds.has(target)) add("SDD-FINDING-TARGET", `/findings/${index}`, `Finding target is unknown: ${target}`);
      if (!relationKeys.has(`${finding.id}|finds|${target}`)) add("SDD-FINDING-TRACE", `/findings/${index}`, `Finding is not traced to target: ${target}`);
    }
  }

  const journalPath = await existingConcretePath(root, data.journal.path, "/journal/path", add, overlay);
  if (journalPath) {
    const lines = (await readRepoFile(root, data.journal.path, overlay)).split(/\r?\n/).filter(Boolean);
    for (const issue of validateJournalEvents(lines, data)) issues.push(issue);
  }

  if (data.execution.baseline) {
    const baseline = await existingConcretePath(root, data.execution.baseline.path, "/execution/baseline/path", add, overlay);
    if (baseline && await hashRepoFile(root, data.execution.baseline.path, overlay) !== data.execution.baseline.sha256) {
      add("SDD-BASELINE-HASH", "/execution/baseline/sha256", "Execution baseline hash does not match");
    }
    requireUtc(data.execution.baseline.captured_at, "/execution/baseline/captured_at", add);
    if (["EXECUTION", "VERIFICATION", "REVIEW"].includes(data.workflow.stage)) {
      for (const issue of await validateScope(root, data, overlay)) issues.push(issue);
    }
  }

  for (const [index, reference] of config.required_references.entries()) {
    await existingConcretePath(root, reference, `/config/required_references/${index}`, add, overlay);
  }
  return issues;
}

function requireUtc(
  value: string,
  instancePath: string,
  add: (code: string, instancePath: string, message: string) => void,
): void {
  if (!value.endsWith("Z")) {
    add("SDD-TIMESTAMP-NOT-UTC", instancePath, "Timestamp must use UTC with a Z suffix");
  }
}

function uniqueIds(
  items: AnyRecord[],
  instancePath: string,
  code: string,
  add: (code: string, instancePath: string, message: string) => void,
): Set<string> {
  const ids = new Set<string>();
  for (const [index, item] of items.entries()) {
    if (ids.has(item.id)) {
      add(code, `${instancePath}/${index}/id`, `Duplicate ID: ${item.id}`);
    }
    ids.add(item.id);
  }
  return ids;
}

function detectCycles(
  graph: Map<string, string[]>,
  add: (code: string, instancePath: string, message: string) => void,
): void {
  const visiting = new Set<string>();
  const visited = new Set<string>();
  const visit = (id: string): boolean => {
    if (visiting.has(id)) return true;
    if (visited.has(id)) return false;
    visiting.add(id);
    for (const dependency of graph.get(id) ?? []) {
      if (graph.has(dependency) && visit(dependency)) return true;
    }
    visiting.delete(id);
    visited.add(id);
    return false;
  };
  for (const id of graph.keys()) {
    if (visit(id)) {
      add("SDD-TASK-CYCLE", "/tasks", "Task dependency graph contains a cycle");
      return;
    }
  }
}

async function existingConcretePath(
  root: string,
  value: string,
  instancePath: string,
  add: (code: string, instancePath: string, message: string) => void,
  overlay: Map<string, string> = new Map(),
): Promise<string | null> {
  let concrete: string;
  try {
    concrete = resolveConcreteRepoPath(root, value);
    if (!overlay.has(value)) await access(concrete);
    return concrete;
  } catch (error) {
    add("SDD-PATH-MISSING", instancePath, error instanceof Error ? error.message : String(error));
    return null;
  }
}

async function hashRepoFile(root: string, value: string, overlay: Map<string, string>): Promise<string> {
  const staged = overlay.get(value);
  return staged === undefined ? sha256File(resolveConcreteRepoPath(root, value)) : sha256Text(staged);
}

async function readRepoFile(root: string, value: string, overlay: Map<string, string>): Promise<string> {
  return overlay.get(value) ?? readText(resolveConcreteRepoPath(root, value));
}
