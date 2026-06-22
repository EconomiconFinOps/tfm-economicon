import { lstat } from "node:fs/promises";

import { loadConfig } from "../config.js";
import { contractIssues, createCatalogValidator } from "../contracts/catalog.js";
import { HarnessBlockedError, HarnessInputError } from "../errors.js";
import { sha256Text } from "../hash.js";
import { readText, readYaml } from "../io.js";
import { resolveConcreteRepoPath } from "../repo.js";

export interface AgentPolicy {
  definition: string;
  skills: string[];
  stages: string[];
  reasoning_effort: "low" | "medium" | "high";
  timeout_seconds: number;
  may_modify_product_code: boolean;
  independent_from: string[];
}
export interface AgentCatalog {
  catalog_version: "1.0.0";
  run_contract_version: "2.0.0";
  runtime: { provider: "codex-cli"; network: "disabled"; approval_policy: "never"; max_output_bytes: number; max_error_bytes: number };
  forbidden_actions: string[];
  agents: Record<string, AgentPolicy>;
}
export interface AgentDefinition { name: string; description: string; developer_instructions: string; model_reasoning_effort: string; sha256: string }

export async function loadAgentCatalog(root: string): Promise<{ catalog: AgentCatalog; sha256: string }> {
  const config = await loadConfig(root);
  const absolute = resolveConcreteRepoPath(root, config.agents.catalog);
  const raw = await readText(absolute);
  const catalog = await readYaml<AgentCatalog>(absolute);
  const validator = await createCatalogValidator(root, "agent/catalog@1.0.0");
  if (!validator(catalog)) throw new HarnessBlockedError("Agent catalog is invalid", contractIssues(validator.errors, "/agents"));
  for (const [id, policy] of Object.entries(catalog.agents)) {
    for (const dependency of policy.independent_from) if (!catalog.agents[dependency]) throw new HarnessInputError("SDD-AGENT-CATALOG", `Unknown independence target ${dependency} for ${id}`);
  }
  return { catalog, sha256: sha256Text(raw) };
}

export async function loadAgentDefinition(root: string, agentId: string, policy: AgentPolicy): Promise<AgentDefinition> {
  const absolute = resolveConcreteRepoPath(root, policy.definition);
  if ((await lstat(absolute)).isSymbolicLink()) throw new HarnessInputError("SDD-AGENT-SYMLINK", "Agent definitions cannot be symlinks");
  const raw = await readText(absolute);
  const name = scalar(raw, "name");
  const description = scalar(raw, "description");
  const effort = scalar(raw, "model_reasoning_effort");
  const instructions = raw.match(/^developer_instructions\s*=\s*"""\r?\n([\s\S]*?)\r?\n"""\s*$/m)?.[1]?.trim();
  if (name !== agentId || !description || !instructions || effort !== policy.reasoning_effort) throw new HarnessInputError("SDD-AGENT-DEFINITION", `Invalid agent definition: ${policy.definition}`);
  return { name, description, developer_instructions: instructions, model_reasoning_effort: effort, sha256: sha256Text(raw) };
}

export function assertAgentAssignment(agentId: string, policy: AgentPolicy, skill: string, stage: string): void {
  if (!policy.skills.includes(skill)) throw new HarnessInputError("SDD-AGENT-SKILL", `${agentId} cannot use ${skill}`);
  if (!policy.stages.includes(stage)) throw new HarnessInputError("SDD-AGENT-STAGE", `${agentId} cannot run in ${stage}`);
}

function scalar(raw: string, key: string): string | undefined {
  return raw.match(new RegExp(`^${key}\\s*=\\s*"([^"]+)"\\s*$`, "m"))?.[1];
}
