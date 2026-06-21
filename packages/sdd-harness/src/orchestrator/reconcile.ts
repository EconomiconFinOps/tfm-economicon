import { readFile } from "node:fs/promises";

import { parseArtifactMarkdown } from "../contracts/artifact.js";
import { sha256File } from "../hash.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { AnyRecord, ValidationIssue, WorkflowContract } from "../types.js";
import { validateScope } from "./scope.js";

export interface ReconcileResult { changed: boolean; causes: string[]; blockers: ValidationIssue[] }

export async function reconcileManifest(root: string, manifest: AnyRecord, workflow: WorkflowContract): Promise<ReconcileResult> {
  const changedTypes = new Set<string>();
  const causes: string[] = [];
  const now = new Date().toISOString();
  for (const artifact of manifest.artifacts as AnyRecord[]) {
    const artifactPath = resolveConcreteRepoPath(root, artifact.path);
    const actual = await sha256File(artifactPath);
    if (actual !== artifact.sha256) {
      const wasApproved = artifact.status === "APPROVED";
      artifact.sha256 = actual;
      artifact.updated_at = now;
      artifact.invalidated_by = "content_hash_changed";
      if (wasApproved) {
        artifact.version += 1;
        artifact.status = "DRAFT";
        changedTypes.add(ruleKey(artifact.type));
      }
      causes.push(`${artifact.path}:content_hash_changed`);
      continue;
    }
    const parsed = parseArtifactMarkdown(await readFile(artifactPath, "utf8"));
    let staleDocument = false;
    for (const reference of parsed.metadata.documentation_consulted ?? []) {
      try { staleDocument ||= await sha256File(resolveConcreteRepoPath(root, reference.path)) !== reference.sha256; } catch { staleDocument = true; }
    }
    if (staleDocument) {
      if (artifact.status === "DRAFT" && artifact.invalidated_by === "documentation_hash_changed") continue;
      const wasApproved = artifact.status === "APPROVED";
      artifact.updated_at = now;
      artifact.invalidated_by = "documentation_hash_changed";
      if (wasApproved) {
        artifact.version += 1;
        artifact.status = "DRAFT";
        changedTypes.add(ruleKey(artifact.type));
      }
      causes.push(`${artifact.path}:documentation_hash_changed`);
    }
  }
  for (const evidence of manifest.gate_evidence as AnyRecord[]) {
    if (!evidence.satisfied) continue;
    for (const input of evidence.evidence as AnyRecord[]) {
      const actual = await sha256File(resolveConcreteRepoPath(root, input.path));
      if (actual !== input.sha256) {
        evidence.satisfied = false;
        causes.push(`${evidence.condition}:evidence_stale`);
        break;
      }
    }
  }
  for (const key of changedTypes) applyInvalidation(manifest, workflow, key, now);

  const scopeIssues = await validateScope(root, manifest);
  if (scopeIssues.length > 0 && ["EXECUTION", "VERIFICATION", "REVIEW"].includes(manifest.workflow.stage)) {
    applyInvalidation(manifest, workflow, "outside_approved_scope", now);
    manifest.workflow.status = "BLOCKED";
    causes.push("outside_approved_scope");
  }
  if (causes.length) manifest.workflow.updated_at = now;
  return { changed: causes.length > 0, causes, blockers: scopeIssues };
}

export function applyInvalidation(manifest: AnyRecord, workflow: WorkflowContract, changed: string, now = new Date().toISOString()): void {
  const rule = workflow.invalidation_rules.find((item) => item.changed === changed);
  if (!rule) return;
  for (const artifact of manifest.artifacts as AnyRecord[]) {
    if (!matchesInvalidatedType(artifact.type, rule.invalidates)) continue;
    if (artifact.status !== "DRAFT" || artifact.invalidated_by !== changed) artifact.version += 1;
    artifact.status = "DRAFT";
    artifact.invalidated_by = changed;
    artifact.updated_at = now;
  }
  if (rule.invalidates.some((item: string) => ["tasks", "plan", "execution"].includes(item))) {
    for (const task of manifest.tasks as AnyRecord[]) {
      if (task.status !== "COMPLETED") continue;
      task.status = "PENDING";
      task.attempts.push({ number: (task.attempts.at(-1)?.number ?? 0) + 1, status: "PENDING", started_at: null, completed_at: null, error: null, executor: null, evidence: [] });
    }
  }
  if (rule.return_to) manifest.workflow.stage = rule.return_to;
  if (manifest.workflow.status !== "CANCELLED") manifest.workflow.status = "ACTIVE";
}

function ruleKey(type: string): string {
  if (["roadmap", "task"].includes(type)) return "roadmap_or_tasks";
  return type;
}

function matchesInvalidatedType(type: string, invalidates: string[]): boolean {
  return invalidates.includes(type) || (invalidates.includes("tasks") && type === "task") || (invalidates.includes("plan") && ["roadmap", "task"].includes(type)) || (invalidates.includes("execution") && type === "execution-summary") || (invalidates.includes("verification") && type === "verification-evidence");
}
