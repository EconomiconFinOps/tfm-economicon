import { lstat, readdir } from "node:fs/promises";
import path from "node:path";

import { HarnessInputError } from "../errors.js";
import { sha256File, sha256Text } from "../hash.js";
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
import { compilePermissions, verifyPermissionAnchors } from "./permissions.js";
import { executeCodexAgent } from "./runtime.js";
import { validateStoredRun, type ValidatedRun } from "./run-integrity.js";

export async function runAgent(root: string, storyId: string, agentId: string, skill: string, parametersPath: string): Promise<CommandResult> {
  const manifest = await loadStoryManifest(root, storyId);
  const { catalog, sha256: catalogSha } = await loadAgentCatalog(root);
  const policy = catalog.agents[agentId];
  if (!policy) throw new HarnessInputError("SDD-AGENT", `Unknown agent: ${agentId}`);
  assertAgentAssignment(agentId, policy, skill, manifest.workflow.stage);
  const definition = await loadAgentDefinition(root, agentId, policy);
  const provisional = await compilePermissions(root, storyId, `${runRoot(root, storyId)}/pending`, skill, policy, manifest.scope);
  const prepared = await prepareSkill(root, storyId, skill, parametersPath, { agent_id: agentId, agent_definition_sha256: definition.sha256, agent_catalog_sha256: catalogSha, permission_profile: provisional.profile, permission_profile_sha256: provisional.sha256 });
  if (!prepared.ok) return { ...prepared, command: "agent run" };
  const runId = (prepared.data as AnyRecord).run_id as string;
  const prefix = runPrefix(root, storyId, runId);
  const permissions = await compilePermissions(root, storyId, prefix, skill, policy, manifest.scope);
  await replacePreparedPermissions(root, storyId, runId, permissions.profile, permissions.sha256);
  const lease = await acquireAgentLease(root, storyId, runId, agentId); const startedAt = new Date().toISOString(); let terminalCommitted = false;
  try {
    await recordRun(root, storyId, runId, "RUNNING", "agent.started", runningExecution(startedAt));
    const run = await requireValidRun(root, storyId, runId); const runtime = await executeCodexAgent(root, run, definition, policy, catalog, permissions.toml, permissions.profile);
    await verifyPermissionAnchors(root, permissions.anchors);
    if (runtime.timed_out || runtime.malformed || runtime.execution.exit_code !== 0) {
      await recordRun(root, storyId, runId, "FAILED", "agent.failed", runtime.execution, [{ path: `${prefix}/events.ndjson`, content: runtime.events }]); terminalCommitted = true;
      if (runtime.timed_out) throw new HarnessInputError("SDD-CODEX-TIMEOUT", `Agent ${agentId} exceeded its timeout`);
      if (runtime.malformed) throw new HarnessInputError("SDD-CODEX-JSONL", "Codex emitted malformed JSONL");
      throw new HarnessInputError("SDD-CODEX-EXIT", `Codex exited with code ${runtime.execution.exit_code ?? "null"}`);
    }
    const report = await inspectSkillRun(root, storyId, runId); const receiptIssues = await validateReceipt(root, report.run!, report.output?.status);
    const outputStatus = report.output?.status as string | undefined;
    const independence = await independenceIssues(root, storyId, runId, agentId, policy.independent_from, runtime.execution.thread_id);
    const blockers = [...report.issues, ...receiptIssues, ...independence];
    const nextStatus = blockers.length === 0 ? (outputStatus === "COMPLETED" ? "VALID" : outputStatus === "BLOCKED" ? "BLOCKED" : "FAILED") : "FAILED";
    const event = nextStatus === "VALID" ? "agent.completed" : nextStatus === "BLOCKED" ? "agent.blocked" : "agent.failed";
    await recordRun(root, storyId, runId, nextStatus, event, runtime.execution, [{ path: `${prefix}/events.ndjson`, content: runtime.events }]); terminalCommitted = true;
    const ok = nextStatus === "VALID";
    return { ok, command: "agent run", story_id: storyId, changed: true, blockers: ok ? [] : blockers.length ? blockers : [{ code: `SDD-AGENT-${nextStatus}`, instance_path: "/output", message: `Agent finished as ${nextStatus}` }], next_actions: ok ? ["run sdd skill validate", "run sdd skill submit"] : ["inspect agent status", "prepare a new run after resolving the cause"], data: { run_id: runId, agent_id: agentId, skill, status: nextStatus } };
  } catch (error) {
    let failure = error;
    try { await verifyPermissionAnchors(root, permissions.anchors); } catch (scopeError) { failure = scopeError; }
    if (!terminalCommitted) {
      const execution = failedExecution(startedAt, failure);
      await recordRun(root, storyId, runId, "FAILED", "agent.failed", execution); terminalCommitted = true;
    }
    throw failure;
  } finally { if (terminalCommitted) await releaseAgentLease(root, storyId, lease); }
}

export async function agentStatus(root: string, storyId: string, runId: string): Promise<CommandResult> {
  const validated = await validateStoredRun(root, storyId, runId, runPrefix(root, storyId, runId)); const run = validated.run;
  if (run.schema_version !== "2.0.0") throw new HarnessInputError("SDD-AGENT-RUN", "Run is not agent-bound");
  const ok = validated.issues.length === 0 && !["FAILED", "BLOCKED", "ABORTED"].includes(run.status);
  return { ok, command: "agent status", story_id: storyId, changed: false, blockers: validated.issues, next_actions: ok && run.status === "VALID" ? ["run sdd skill validate", "run sdd skill submit"] : [], data: run };
}

export async function recoverAbandonedAgent(root: string, storyId: string): Promise<boolean> {
  const lease = await recoverAgentLease(root, storyId);
  if (!lease) return false;
  let committed = false;
  try {
    const run = await requireValidRun(root, storyId, lease.run_id);
    const execution = { ...(run.execution ?? {}), provider: "codex-cli", status: "ABORTED", started_at: run.execution?.started_at ?? lease.created_at, completed_at: new Date().toISOString(), duration_ms: Math.max(0, Date.now() - Date.parse(run.execution?.started_at ?? lease.created_at)), exit_code: null, codex_version: run.execution?.codex_version ?? null, model: run.execution?.model ?? null, thread_id: run.execution?.thread_id ?? null, usage: run.execution?.usage ?? null, stdout_sha256: run.execution?.stdout_sha256 ?? sha256Text(""), stderr_excerpt: "Agent process disappeared before completion" };
    await recordRun(root, storyId, lease.run_id, "ABORTED", "agent.aborted", execution); committed = true; return true;
  } finally { if (committed) await releaseAgentLease(root, storyId, lease); }
}

async function replacePreparedPermissions(root: string, storyId: string, runId: string, profile: AnyRecord, sha256: string): Promise<void> {
  await mutateWithReconciliation(root, storyId, "agent bind permissions", async () => {
    const current = await validateStoredRun(root, storyId, runId, runPrefix(root, storyId, runId), false); assertNoIntegrityIssues(current.issues); const run = current.run; run.permission_profile = profile; run.permission_profile_sha256 = sha256;
    return runPlan(root, storyId, run, "agent.permissions_bound", { run_id: runId, agent_id: run.agent_id, agent_definition_sha256: run.agent_definition_sha256, agent_catalog_sha256: run.agent_catalog_sha256, permission_profile_sha256: sha256 });
  });
}

async function recordRun(root: string, storyId: string, runId: string, status: string, eventType: string, execution: AnyRecord, extra: ExtraWrite[] = []): Promise<void> {
  const apply = () => mutateWithReconciliation(root, storyId, eventType, async () => {
    const run = await requireValidRun(root, storyId, runId); run.status = status; run.execution = execution;
    return runPlan(root, storyId, run, eventType, { run_id: runId, agent_id: run.agent_id, status }, extra);
  });
  const first = await apply();
  if (!first.ok && first.changed && first.command === eventType) await apply();
}

function runPlan(root: string, storyId: string, run: RunRecord, eventType: string, data: AnyRecord, extra: ExtraWrite[] = []): MutationPlan {
  return { event_type: eventType, event_data: data, actor: { type: "system", identity: "sdd-cli" }, extra_writes: [{ path: `${runPrefix(root, storyId, run.run_id)}/run.json`, content: `${JSON.stringify(run, null, 2)}\n` }, ...extra], result: { ok: true, command: eventType, story_id: storyId, changed: true, blockers: [], next_actions: [] } };
}

async function requireValidRun(root: string, storyId: string, runId: string): Promise<ValidatedRun> { const result = await validateStoredRun(root, storyId, runId, runPrefix(root, storyId, runId)); assertNoIntegrityIssues(result.issues); return result.run; }
function assertNoIntegrityIssues(issues: ValidationIssue[]): void { if (issues.length) throw new HarnessInputError(issues[0]!.code, issues.map((item) => item.message).join("; ")); }
function runRoot(root: string, storyId: string): string { return path.relative(root, path.join(storyDirectory(root, storyId), ".harness", "skill-runs")).replaceAll("\\", "/"); }

async function independenceIssues(root: string, storyId: string, runId: string, agentId: string, independentFrom: string[], threadId: string | null): Promise<ValidationIssue[]> {
  if (independentFrom.length === 0) return [];
  if (!threadId) return [{ code: "SDD-AGENT-INDEPENDENCE", instance_path: "/execution/thread_id", message: `${agentId} did not provide an independent thread ID` }];
  const directory = path.join(storyDirectory(root, storyId), ".harness", "skill-runs");
  let entries: string[] = []; try { entries = await readdir(directory); } catch { return []; }
  for (const entry of entries) {
    if (entry === runId) continue;
    try {
      const prior = await validateStoredRun(root, storyId, entry, runPrefix(root, storyId, entry));
      if (prior.issues.length) return [{ code: "SDD-AGENT-INDEPENDENCE", instance_path: "/execution/thread_id", message: `Cannot prove independence from invalid run ${entry}` }];
      const other = prior.run; if (independentFrom.includes(other.agent_id) && other.execution?.thread_id === threadId) return [{ code: "SDD-AGENT-INDEPENDENCE", instance_path: "/execution/thread_id", message: `${agentId} reused a thread from ${other.agent_id}` }];
    } catch { return [{ code: "SDD-AGENT-INDEPENDENCE", instance_path: "/execution/thread_id", message: `Cannot inspect prior run ${entry}` }]; }
  }
  return [];
}

async function validateReceipt(root: string, run: RunRecord, outputStatus?: string): Promise<ValidationIssue[]> {
  try {
    const receiptPath = `${path.posix.dirname(run.output_path)}/receipt.json`;
    if ((await lstat(resolveConcreteRepoPath(root, receiptPath))).isSymbolicLink()) throw new Error("Receipt cannot be a symlink");
    const receipt = JSON.parse(await readText(resolveConcreteRepoPath(root, receiptPath))) as AnyRecord;
    const validator = await createCatalogValidator(root, "agent/codex-receipt@1.0.0");
    const issues = validator(receipt) ? [] : contractIssues(validator.errors, "/receipt");
    const outputSha = await sha256File(resolveConcreteRepoPath(root, run.output_path));
    if (receipt.run_id !== run.run_id || receipt.output_path !== run.output_path || receipt.input_sha256 !== run.input_sha256 || receipt.output_sha256 !== outputSha || (outputStatus && receipt.status !== outputStatus)) issues.push({ code: "SDD-AGENT-RECEIPT", instance_path: "/receipt", message: "Receipt is not bound to the run input and output" });
    return issues;
  } catch (error) { return [{ code: "SDD-AGENT-RECEIPT", instance_path: "/receipt", message: error instanceof Error ? error.message : String(error) }]; }
}
function runningExecution(startedAt: string): AnyRecord { return { provider: "codex-cli", status: "RUNNING", started_at: startedAt, completed_at: null, duration_ms: null, exit_code: null, codex_version: null, model: null, thread_id: null, usage: null, stdout_sha256: null, stderr_excerpt: "" }; }
function failedExecution(startedAt: string, error: unknown): AnyRecord { return { provider: "codex-cli", status: "FAILED", started_at: startedAt, completed_at: new Date().toISOString(), duration_ms: Math.max(0, Date.now() - Date.parse(startedAt)), exit_code: null, codex_version: null, model: null, thread_id: null, usage: null, stdout_sha256: sha256Text(""), stderr_excerpt: error instanceof Error ? error.message.slice(0, 4096) : String(error).slice(0, 4096) }; }
