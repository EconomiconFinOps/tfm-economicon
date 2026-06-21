import { readText } from "../io.js";
import type { AnyRecord, ValidationIssue, WorkflowContract } from "../types.js";

export interface TransitionEvaluation {
  transition: AnyRecord | null;
  blockers: ValidationIssue[];
}

export async function evaluateNext(root: string, manifest: AnyRecord, workflow: WorkflowContract): Promise<TransitionEvaluation> {
  const transition = workflow.forward_transitions.find((item) => item.from === manifest.workflow.stage) ?? null;
  if (!transition) {
    return { transition: null, blockers: [{ code: "WF-INVALID-TRANSITION", instance_path: "/workflow/stage", message: `No forward transition from ${manifest.workflow.stage}` }] };
  }
  const blockers: ValidationIssue[] = [];
  const availableTypes = new Set((manifest.artifacts as AnyRecord[]).map((artifact) => artifact.type));
  for (const requiredType of workflow.stage_contracts[manifest.workflow.stage]?.required_artifacts ?? []) {
    const available = requiredType === "tasks" ? availableTypes.has("task") : availableTypes.has(requiredType);
    if (!available) blockers.push({ code: "WF-MISSING-ARTIFACT", instance_path: "/artifacts", message: `Stage ${manifest.workflow.stage} requires artifact type ${requiredType}` });
  }
  for (const condition of transition.conditions ?? []) {
    const issue = await evaluateCondition(root, manifest, condition, transition.id);
    if (issue) blockers.push(issue);
  }
  return { transition, blockers };
}

async function evaluateCondition(root: string, manifest: AnyRecord, condition: string, transitionId: string): Promise<ValidationIssue | null> {
  const artifacts = manifest.artifacts as AnyRecord[];
  const approved = (type: string): boolean => artifacts.some((item) => item.type === type && item.status === "APPROVED" && item.approvals.some((approval: AnyRecord) => approval.decision === "APPROVED" && approval.artifact_version === item.version && approval.artifact_sha256 === item.sha256));
  const evidence = (name: string): boolean => manifest.gate_evidence.some((item: AnyRecord) => item.condition === name && item.satisfied);
  const fail = (code: string, message: string): ValidationIssue => ({ code, instance_path: `/gates/${condition}`, message });
  switch (condition) {
    case "user_story_approved": return approved("user-story") ? null : fail("WF-MISSING-APPROVAL", "Current user story is not approved");
    case "prd_approved": return approved("prd") ? null : fail("WF-MISSING-APPROVAL", "Current PRD is not approved");
    case "tdr_approved": return approved("tdr") ? null : fail("WF-MISSING-APPROVAL", "Current TDR is not approved");
    case "roadmap_approved": return approved("roadmap") ? null : fail("WF-MISSING-APPROVAL", "Current roadmap is not approved");
    case "all_tasks_approved": {
      const taskArtifacts = artifacts.filter((item) => item.type === "task");
      return taskArtifacts.length > 0 && taskArtifacts.every((item) => approvedPath(item)) ? null : fail("WF-MISSING-APPROVAL", "All task artifacts must be approved");
    }
    case "approval_hash_current":
    case "approval_hashes_current": return null;
    case "no_open_functional_questions": return evidence(condition) ? null : fail("WF-OPEN-QUESTIONS", "Functional questions require current evidence");
    case "architecture_invariants_evaluated":
    case "architecture_gaps_evaluated":
    case "source_hashes_current":
    case "verification_matches_evaluated_commit": return evidence(condition) ? null : fail("WF-HUMAN-DECISION", `Missing current evidence: ${condition}`);
    case "change_type_policy_satisfied": return evaluateChangeTypePolicy(root, manifest, transitionId, evidence);
    case "write_scope_declared": return manifest.scope.write_paths.length > 0 ? null : fail("WF-OUT-OF-SCOPE", "Write scope is empty");
    case "all_required_tasks_completed": return manifest.tasks.length > 0 && manifest.tasks.every((task: AnyRecord) => task.status === "COMPLETED") ? null : fail("WF-CHECK-FAILED", "Required tasks are not completed");
    case "execution_summary_current": return artifacts.some((item) => item.type === "execution-summary" && item.status !== "REJECTED") ? null : fail("WF-MISSING-ARTIFACT", "Execution summary is missing or rejected");
    case "all_required_checks_executed": return manifest.checks.length > 0 && manifest.checks.every((check: AnyRecord) => ["COMPLETED", "FAILED"].includes(check.status)) ? null : fail("WF-CHECK-FAILED", "Required checks have not all executed");
    case "all_required_checks_passed": return manifest.checks.length > 0 && manifest.checks.every((check: AnyRecord) => check.status === "COMPLETED" && check.result?.exit_code === 0) ? null : fail("WF-CHECK-FAILED", "A required check did not pass");
    case "review_approved": return approved("review") ? null : fail("WF-MISSING-APPROVAL", "Current review is not approved");
    case "no_blocking_findings": return manifest.findings.some((finding: AnyRecord) => finding.severity === "BLOCKING" && finding.status === "OPEN") ? fail("WF-CHECK-FAILED", "Blocking review findings remain open") : null;
    case "architecture_gates_satisfied": return evidence(condition) ? null : fail("WF-ARCH-VIOLATION", "Architecture gates require current evidence");
    default: return evidence(condition) ? null : fail("WF-HUMAN-DECISION", `Condition has no current evidence: ${condition}`);
  }
}

function approvedPath(artifact: AnyRecord): boolean {
  return artifact.status === "APPROVED" && artifact.approvals.some((approval: AnyRecord) => approval.decision === "APPROVED" && approval.artifact_version === artifact.version && approval.artifact_sha256 === artifact.sha256);
}

async function evaluateChangeTypePolicy(
  root: string,
  manifest: AnyRecord,
  transitionId: string,
  evidence: (name: string) => boolean,
): Promise<ValidationIssue | null> {
  const fail = (code: string, message: string): ValidationIssue => ({ code, instance_path: "/story/change_type", message });
  if (manifest.story.change_type === "harness-docs") return manifest.story.runtime_changes ? fail("WF-OUT-OF-SCOPE", "harness-docs cannot change runtime") : null;
  if (manifest.story.change_type === "feature") {
    if (!manifest.scope.components.length || !manifest.scope.affected_data.length || !manifest.scope.affected_flows.length) return fail("WF-HUMAN-DECISION", "Feature scope declarations are incomplete");
    if (["TR-004", "TR-008"].includes(transitionId) && await hasBlockingGap(root, manifest.architecture.gaps)) return fail("WF-ARCH-GAP", "An applicable architecture gap remains BLOCKING");
    return null;
  }
  if (manifest.story.change_type === "remediation") {
    if (!manifest.architecture.gaps.length) return fail("WF-ARCH-GAP", "Remediation has no target gaps");
    if (transitionId === "TR-008") {
      if (await hasBlockingGap(root, manifest.architecture.gaps)) return fail("WF-ARCH-GAP", "A target remediation gap remains BLOCKING");
      for (const condition of ["no_new_gaps", "no_remaining_gap_worsened", "architecture_status_updated_by_review"]) {
        if (!evidence(condition)) return fail("WF-HUMAN-DECISION", `Missing remediation evidence: ${condition}`);
      }
    }
  }
  return null;
}

async function hasBlockingGap(root: string, gaps: string[]): Promise<boolean> {
  const status = await readText(`${root}/docs/architecture-status.md`);
  const lines = status.split(/\r?\n/);
  return gaps.some((gap) => lines.some((line) => line.includes("| `" + gap + "` |") && line.includes("| `BLOCKING` |")));
}
