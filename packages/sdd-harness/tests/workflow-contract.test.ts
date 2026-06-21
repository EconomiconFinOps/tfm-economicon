import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { parse } from "yaml";

import { validateWorkflowApproval } from "../src/workflow/validate-approval.js";
import { readText } from "../src/io.js";
import { findRepoRoot } from "../src/repo.js";
import type { HarnessConfig, WorkflowContract } from "../src/types.js";

describe("approved workflow contract", () => {
  it("contains all declared transitions and acceptance scenarios", async () => {
    const root = await findRepoRoot();
    const workflow = parse(await readText(path.join(root, ".sdd/policies/workflow.yaml")));

    expect(workflow.forward_transitions.map((item: any) => item.id)).toEqual(ids("TR", 8));
    expect(workflow.artifact_transitions.map((item: any) => item.id)).toEqual(ids("AT", 6));
    expect(workflow.execution_transitions.map((item: any) => item.id)).toEqual(ids("EX", 7));
    expect(workflow.acceptance_scenarios.map((item: any) => item.id)).toEqual(ids("WF-SC", 14));
  });

  it("rejects a stale contract approval", async () => {
    const root = await mkdtemp(path.join(os.tmpdir(), "sdd-workflow-"));
    await mkdir(path.join(root, "docs"), { recursive: true });
    await mkdir(path.join(root, ".sdd/policies"), { recursive: true });
    await writeFile(path.join(root, "docs/SDD-WORKFLOW.md"), "contract", "utf8");
    await writeFile(path.join(root, ".sdd/policies/workflow.yaml"), "status: approved", "utf8");
    await writeFile(
      path.join(root, ".sdd/policies/workflow.approval.yaml"),
      [
        'contract_version: "1.0.0"',
        "decision: APPROVED",
        "artifacts:",
        "  - path: docs/SDD-WORKFLOW.md",
        `    sha256: ${"0".repeat(64)}`,
        "  - path: .sdd/policies/workflow.yaml",
        `    sha256: ${"0".repeat(64)}`,
        "approver:",
        "  actor_type: human",
        "  identity: test",
        'approved_at: "2026-06-20T00:00:00Z"',
      ].join("\n"),
      "utf8",
    );

    const config = {
      contracts: {
        workflow: ".sdd/policies/workflow.yaml",
        workflow_approval: ".sdd/policies/workflow.approval.yaml",
      },
    } as HarnessConfig;
    const workflow = { contract_version: "1.0.0" } as WorkflowContract;

    await expect(validateWorkflowApproval(root, config, workflow)).rejects.toMatchObject({
      code: "SDD-WORKFLOW-APPROVAL-STALE",
    });
  });
});

function ids(prefix: string, count: number): string[] {
  return Array.from({ length: count }, (_, index) => `${prefix}-${String(index + 1).padStart(3, "0")}`);
}

