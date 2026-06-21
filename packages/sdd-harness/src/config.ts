import path from "node:path";

import { HarnessInputError } from "./errors.js";
import { readYaml } from "./io.js";
import { resolveConcreteRepoPath } from "./repo.js";
import type { HarnessConfig, WorkflowContract } from "./types.js";

export async function loadConfig(root: string): Promise<HarnessConfig> {
  const config = await readYaml<HarnessConfig>(path.join(root, ".sdd", "config.yaml"));
  if (config.config_version !== "1.0.0" || config.hash_algorithm !== "sha256") {
    throw new HarnessInputError("SDD-CONFIG-UNSUPPORTED", "Unsupported harness configuration");
  }
  for (const reference of config.required_references) {
    resolveConcreteRepoPath(root, reference);
  }
  return config;
}

export async function loadWorkflow(root: string, config: HarnessConfig): Promise<WorkflowContract> {
  const workflowPath = resolveConcreteRepoPath(root, config.contracts.workflow);
  const workflow = await readYaml<WorkflowContract>(workflowPath);
  if (workflow.status !== "approved") {
    throw new HarnessInputError("SDD-WORKFLOW-NOT-APPROVED", "Workflow contract is not approved");
  }
  return workflow;
}

