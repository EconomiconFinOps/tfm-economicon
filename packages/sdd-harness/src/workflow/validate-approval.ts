import { access } from "node:fs/promises";

import { HarnessInputError } from "../errors.js";
import { sha256File } from "../hash.js";
import { readYaml } from "../io.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { ApprovalRecord, HarnessConfig, WorkflowContract } from "../types.js";

export async function validateWorkflowApproval(
  root: string,
  config: HarnessConfig,
  workflow: WorkflowContract,
): Promise<void> {
  const approvalPath = resolveConcreteRepoPath(root, config.contracts.workflow_approval);
  const approval = await readYaml<ApprovalRecord>(approvalPath);

  if (
    approval.decision !== "APPROVED" ||
    approval.approver.actor_type !== "human" ||
    !approval.approver.identity ||
    approval.contract_version !== workflow.contract_version
  ) {
    throw new HarnessInputError("SDD-WORKFLOW-APPROVAL-INVALID", "Workflow approval record is invalid");
  }

  const expectedPaths = new Set([
    "docs/SDD-WORKFLOW.md",
    config.contracts.workflow,
  ]);
  const actualPaths = new Set(approval.artifacts.map((artifact) => artifact.path));
  if (expectedPaths.size !== actualPaths.size || [...expectedPaths].some((value) => !actualPaths.has(value))) {
    throw new HarnessInputError("SDD-WORKFLOW-APPROVAL-INVALID", "Workflow approval does not cover the required artifacts");
  }

  for (const artifact of approval.artifacts) {
    const artifactPath = resolveConcreteRepoPath(root, artifact.path);
    try {
      await access(artifactPath);
    } catch {
      throw new HarnessInputError("SDD-WORKFLOW-ARTIFACT-MISSING", `Approved workflow artifact is missing: ${artifact.path}`);
    }
    const actualHash = await sha256File(artifactPath);
    if (actualHash !== artifact.sha256) {
      throw new HarnessInputError("SDD-WORKFLOW-APPROVAL-STALE", `Approved workflow hash is stale: ${artifact.path}`);
    }
  }
}

