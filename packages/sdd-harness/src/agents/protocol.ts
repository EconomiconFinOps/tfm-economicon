import { readdir } from "node:fs/promises";
import path from "node:path";

import { HarnessInputError } from "../errors.js";
import { canonicalJson, sha256Text } from "../hash.js";
import { readText } from "../io.js";
import { mutateWithReconciliation } from "../orchestrator/commands.js";
import { storyDirectory } from "../orchestrator/paths.js";
import { loadStoryManifest, type ExtraWrite, type MutationPlan } from "../orchestrator/store.js";
import { resolveConcreteRepoPath } from "../repo.js";
import { contractIssues, createCatalogValidator } from "../contracts/catalog.js";
import type { AnyRecord, CommandResult, ValidationIssue } from "../types.js";
import { inspectSkillRun, prepareSkill, runPrefix, type RunRecord } from "../skills/protocol.js";
import { assertAgentAssignment, loadAgentCatalog, loadAgentDefinition } from "./catalog.js";
import { acquireAgentLease, recoverAgentLease, releaseAgentLease } from "./lease.js";
import { compilePermissions } from "./permissions.js";
import { executeCodexAgent } from "./runtime.js";

export async function runAgent(root: string, storyId: string, agentId: string, skill: string, parametersPath: string): Promise<CommandResult> {
  const manifest = await loadStoryManifest(root, storyId);
  const { catalog, sha256: catalogSha } = await loadAgentCatalog(root);
  const policy = catalog.agents[agentId];
  if (!policy) throw new HarnessInputError("SDD-AGENT", `Unknown agent: ${agentId}`);
  assertAgentAssignment(agentId, policy, skill, manifest.workflow.stage);
  const definition = await loadAgentDefinition(root, agentId, policy);
  const provisional = compilePermissions(storyId, `${runRoot(root, storyId)}/pending`, skill, policy, manifest.scope);
  const prepared = await prepareSkill(root, storyId, skill, parametersPath, { agent_id: agentId, agent_definition_sha256: definition.sha256, agent_catalog_sha256: catalogSha, permission_profile: provisional.profile, permission_profile_sha256: provisional.sha256 });
  if (!prepared.ok) return { ...prepared, command: "agent run" };
  const runId = (prepared.data as AnyRecord).run_id as string;
  const prefix = runPrefix(root, storyId, runId);
  const permissions = compilePermissions(storyId, prefix, skill, policy, manifest.scope);
  await replacePreparedPermissions(root, storyId, runId, permissions.profile, permissions.sha256);
  const lease = await acquireAgentLease(root, storyId, runId, agentId);
  const startedAt = new Date().toISOString();
  await recordRun(root, storyId, runId, "RUNNING", "agent.started", { provider: "codex-cli", status: "RUNNING", started_at: startedAt, completed_at: null, duration_ms: null, exit_code: null, codex_version: null, model: null, thread_id: null, usage: null, stdout_sha256: null, stderr_excerpt: "" });
  let runtime;
  try {
    const run = await readRun(root, storyId, runId);
    runtime = await executeCodexAgent(root, run, definition, policy, catalog, permissions.toml, permissions.profile);
  } catch (error) {
    await releaseAgentLease(root, storyId, lease);
    const execution = { provider: "codex-cli", status: "FAILED", started_at: startedAt, completed_at: new Date().toISOString(), duration_ms: Math.max(0, Date.now() - Date.parse(startedAt)), exit_code: null, codex_version: null, model: null, thread_id: null, usage: null, stdout_sha256: sha256Text(""), stderr_excerpt: error instanceof Error ? error.message.slice(0, 4096) : String(error).slice(0, 4096) };
    await recordRun(root, storyId, runId, "FAILED", "agent.failed", execution);
    throw error;
  }
  await releaseAgentLease(root, storyId, lease);
  const report = await inspectSkillRun(root, storyId, runId);
  const receiptIssues = await validateReceipt(root, report.run!, report.output?.status);
  const outputStatus = report.output?.status as string | undefined;
  const independence = await independenceIssues(root, storyId, runId, agentId, policy.independent_from, runtime.execution.thread_id);
  const blockers = [...report.issues, ...receiptIssues, ...independence];
  const nextStatus = runtime.execution.status === "COMPLETED" && blockers.length === 0 ? (outputStatus === "COMPLETED" ? "VALID" : outputStatus === "BLOCKED" ? "BLOCKED" : "FAILED") : "FAILED";
  const event = nextStatus === "VALID" ? "agent.completed" : nextStatus === "BLOCKED" ? "agent.blocked" : "agent.failed";
  await recordRun(root, storyId, runId, nextStatus, event, runtime.execution, [{ path: `${prefix}/events.ndjson`, content: runtime.events }]);
  if (runtime.timed_out) throw new HarnessInputError("SDD-CODEX-TIMEOUT", `Agent ${agentId} exceeded its timeout`);
  const ok = nextStatus === "VALID";
  return { ok, command: "agent run", story_id: storyId, changed: true, blockers: ok ? [] : blockers.length ? blockers : [{ code: `SDD-AGENT-${nextStatus}`, instance_path: "/output", message: `Agent finished as ${nextStatus}` }], next_actions: ok ? ["run sdd skill validate", "run sdd skill submit"] : ["inspect agent status", "prepare a new run after resolving the cause"], data: { run_id: runId, agent_id: agentId, skill, status: nextStatus } };
}

export async function agentStatus(root: string, storyId: string, runId: string): Promise<CommandResult> {
  const run = await readRun(root, storyId, runId);
  if (!run.agent_id) throw new HarnessInputError("SDD-AGENT-RUN", "Run is not agent-bound");
  return { ok: !["FAILED", "BLOCKED", "ABORTED"].includes(run.status), command: "agent status", story_id: storyId, changed: false, blockers: [], next_actions: run.status === "VALID" ? ["run sdd skill validate", "run sdd skill submit"] : [], data: run };
}

export async function recoverAbandonedAgent(root: string, storyId: string): Promise<boolean> {
  const lease = await recoverAgentLease(root, storyId);
  if (!lease) return false;
  const run = await readRun(root, storyId, lease.run_id);
  const execution = { ...(run.execution ?? {}), provider: "codex-cli", status: "ABORTED", started_at: run.execution?.started_at ?? lease.created_at, completed_at: new Date().toISOString(), duration_ms: Math.max(0, Date.now() - Date.parse(run.execution?.started_at ?? lease.created_at)), exit_code: null, codex_version: run.execution?.codex_version ?? null, model: run.execution?.model ?? null, thread_id: run.execution?.thread_id ?? null, usage: run.execution?.usage ?? null, stdout_sha256: run.execution?.stdout_sha256 ?? sha256Text(""), stderr_excerpt: "Agent process disappeared before completion" };
  await recordRun(root, storyId, lease.run_id, "ABORTED", "agent.aborted", execution);
  return true;
}

async function replacePreparedPermissions(root: string, storyId: string, runId: string, profile: AnyRecord, sha256: string): Promise<void> {
  await mutateWithReconciliation(root, storyId, "agent bind permissions", async () => {
    const run = await readRun(root, storyId, runId); run.permission_profile = profile; run.permission_profile_sha256 = sha256;
    return runPlan(root, storyId, run, "agent.permissions_bound", { run_id: runId, agent_id: run.agent_id });
  });
}

async function recordRun(root: string, storyId: string, runId: string, status: string, eventType: string, execution: AnyRecord, extra: ExtraWrite[] = []): Promise<void> {
  const apply = () => mutateWithReconciliation(root, storyId, eventType, async () => {
    const run = await readRun(root, storyId, runId); run.status = status; run.execution = execution;
    return runPlan(root, storyId, run, eventType, { run_id: runId, agent_id: run.agent_id, status }, extra);
  });
  const first = await apply();
  if (!first.ok && first.changed && first.command === eventType) await apply();
}

function runPlan(root: string, storyId: string, run: RunRecord, eventType: string, data: AnyRecord, extra: ExtraWrite[] = []): MutationPlan {
  return { event_type: eventType, event_data: data, actor: { type: "system", identity: "sdd-cli" }, extra_writes: [{ path: `${runPrefix(root, storyId, run.run_id)}/run.json`, content: `${JSON.stringify(run, null, 2)}\n` }, ...extra], result: { ok: true, command: eventType, story_id: storyId, changed: true, blockers: [], next_actions: [] } };
}

async function readRun(root: string, storyId: string, runId: string): Promise<RunRecord> { return JSON.parse(await readText(resolveConcreteRepoPath(root, `${runPrefix(root, storyId, runId)}/run.json`))) as RunRecord; }
function runRoot(root: string, storyId: string): string { return path.relative(root, path.join(storyDirectory(root, storyId), ".harness", "skill-runs")).replaceAll("\\", "/"); }

async function independenceIssues(root: string, storyId: string, runId: string, agentId: string, independentFrom: string[], threadId: string | null): Promise<ValidationIssue[]> {
  if (independentFrom.length === 0) return [];
  if (!threadId) return [{ code: "SDD-AGENT-INDEPENDENCE", instance_path: "/execution/thread_id", message: `${agentId} did not provide an independent thread ID` }];
  const directory = path.join(storyDirectory(root, storyId), ".harness", "skill-runs");
  let entries: string[] = []; try { entries = await readdir(directory); } catch { return []; }
  for (const entry of entries) {
    if (entry === runId) continue;
    try { const other = await readRun(root, storyId, entry); if (independentFrom.includes(other.agent_id) && other.execution?.thread_id === threadId) return [{ code: "SDD-AGENT-INDEPENDENCE", instance_path: "/execution/thread_id", message: `${agentId} reused a thread from ${other.agent_id}` }]; } catch { /* unrelated entry */ }
  }
  return [];
}

async function validateReceipt(root: string, run: RunRecord, outputStatus?: string): Promise<ValidationIssue[]> {
  try {
    const receiptPath = `${path.posix.dirname(run.output_path)}/receipt.json`;
    const receipt = JSON.parse(await readText(resolveConcreteRepoPath(root, receiptPath))) as AnyRecord;
    const validator = await createCatalogValidator(root, "agent/codex-receipt@1.0.0");
    const issues = validator(receipt) ? [] : contractIssues(validator.errors, "/receipt");
    if (receipt.run_id !== run.run_id || receipt.output_path !== run.output_path || (outputStatus && receipt.status !== outputStatus)) issues.push({ code: "SDD-AGENT-RECEIPT", instance_path: "/receipt", message: "Receipt is not bound to the run output" });
    return issues;
  } catch (error) { return [{ code: "SDD-AGENT-RECEIPT", instance_path: "/receipt", message: error instanceof Error ? error.message : String(error) }]; }
}
