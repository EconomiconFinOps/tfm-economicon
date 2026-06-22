import { randomUUID } from "node:crypto";
import { lstat, readFile } from "node:fs/promises";
import path from "node:path";
import { parseDocument } from "yaml";

import { loadConfig } from "../config.js";
import { contractIssues, createCatalogValidator } from "../contracts/catalog.js";
import { validateArtifactContent } from "../contracts/artifact.js";
import { HarnessBlockedError, HarnessInputError } from "../errors.js";
import { canonicalJson, sha256File, sha256Text } from "../hash.js";
import { readText, readYaml } from "../io.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { Actor, AnyRecord, CommandResult, ValidationIssue } from "../types.js";
import { mutateWithReconciliation } from "../orchestrator/commands.js";
import { storyDirectory, storyManifestPath } from "../orchestrator/paths.js";
import { validateScope } from "../orchestrator/scope.js";
import { loadStoryManifest, type ExtraWrite, type MutationPlan } from "../orchestrator/store.js";
import { loadAgentCatalog, loadAgentDefinition } from "../agents/catalog.js";
import { validateStoredRun } from "../agents/run-integrity.js";

interface SkillPolicy {
  stage: string;
  input_schema: string;
  output_schema: string;
  consumes: Array<{ type: string; status: string }>;
  produces: string[];
  targets: string[];
}
interface SkillCatalog { catalog_version: string; protocol_version: string; skills: Record<string, SkillPolicy> }
export interface RunRecord extends AnyRecord {
  schema_version: string; run_id: string; story_id: string; skill: string; status: string;
  input_path: string; input_sha256: string; output_path: string; created_at: string;
}

export interface SkillAgentBinding {
  agent_id: string;
  agent_definition_sha256: string;
  agent_catalog_sha256: string;
  permission_profile: AnyRecord;
  permission_profile_sha256: string;
}

export async function prepareSkill(root: string, storyId: string, skill: string, parametersPath: string, agent?: SkillAgentBinding): Promise<CommandResult> {
  const catalog = await loadSkillCatalog(root);
  const policy = policyFor(catalog, skill);
  const parameterFile = resolveConcreteRepoPath(root, parametersPath);
  if ((await lstat(parameterFile)).isSymbolicLink()) throw new HarnessInputError("SDD-SKILL-SYMLINK", "Symlink parameters are forbidden");
  const parameters = await parsePayload(root, parametersPath);
  return mutateWithReconciliation(root, storyId, "skill prepare", async (manifest) => {
    assertSkillReady(manifest, skill, policy);
    const runId = randomUUID();
    const prefix = runPrefix(root, storyId, runId);
    const inputPath = `${prefix}/input.json`;
    const outputPath = `${prefix}/output.json`;
    const docs = [];
    const config = await loadConfig(root);
    for (const item of config.required_references) docs.push({ path: item, sha256: await sha256File(resolveConcreteRepoPath(root, item)) });
    const input = {
      schema_version: catalog.protocol_version, run_id: runId, correlation_id: manifest.correlation_id,
      skill, story_id: storyId, workflow_stage: manifest.workflow.stage, state_sha256: skillStateHash(manifest),
      artifact_versions: manifest.artifacts.map((item: AnyRecord) => ({ type: item.type, path: item.path, version: item.version, sha256: item.sha256, status: item.status })),
      docs_context: { inventory: config.required_references, applicable: docs, excluded: [{ path: "sdd-planing.md", reason: "Referencia no normativa" }] },
      requested_scope: structuredClone(manifest.scope), parameters,
    };
    const validator = await createCatalogValidator(root, policy.input_schema);
    if (!validator(input)) throw new HarnessBlockedError("Skill input is invalid", contractIssues(validator.errors, "/input"));
    const inputContent = `${JSON.stringify(input, null, 2)}\n`;
    const now = new Date().toISOString();
    const run: RunRecord = { schema_version: agent ? "2.0.0" : "1.0.0", run_id: runId, story_id: storyId, skill, status: "PREPARED", input_path: inputPath, input_sha256: sha256Text(inputContent), output_path: outputPath, created_at: now, submitted_at: null, producer: null, ...(agent ?? {}) };
    const writes: ExtraWrite[] = [
      { path: inputPath, content: inputContent, immutable: true },
      { path: `${prefix}/run.json`, content: jsonFile(run) },
      { path: `${prefix}/artifacts/.keep`, content: "", immutable: true },
    ];
    return {
      event_type: agent ? "agent.prepared" : "skill.prepared", event_data: { run_id: runId, skill, input_sha256: run.input_sha256, ...(agent ? { agent_id: agent.agent_id, agent_definition_sha256: agent.agent_definition_sha256, agent_catalog_sha256: agent.agent_catalog_sha256 } : {}) }, actor: { type: "system", identity: "sdd-cli" }, extra_writes: writes,
      result: { ok: true, command: "skill prepare", story_id: storyId, changed: true, blockers: [], next_actions: [`invoke $${skill} with ${inputPath} and write ${outputPath}`], data: { run_id: runId, input_path: inputPath, output_path: outputPath, artifacts_path: `${prefix}/artifacts` } },
    };
  });
}

export async function validateSkill(root: string, storyId: string, runId: string): Promise<CommandResult> {
  const report = await inspectSkillRun(root, storyId, runId);
  return { ok: report.issues.length === 0, command: "skill validate", story_id: storyId, changed: false, blockers: report.issues, next_actions: report.issues.length ? ["fix staged skill output"] : ["run sdd skill submit"], data: { run_id: runId, skill: report.run?.skill, status: report.output?.status } };
}

export async function submitSkill(root: string, storyId: string, runId: string, suppliedProducer?: Actor): Promise<CommandResult> {
  const stored = await validateStoredRun(root, storyId, runId, runPrefix(root, storyId, runId));
  const prepared = stored.events.filter((event) => ["skill.prepared", "agent.prepared"].includes(event.event_type) && event.data?.run_id === runId);
  const agentBound = prepared.length === 1 && prepared[0]!.event_type === "agent.prepared";
  if (agentBound && suppliedProducer) throw new HarnessInputError("SDD-AGENT-IDENTITY", "Producer flags are forbidden for agent-bound runs");
  if (!agentBound && !suppliedProducer?.identity) throw new HarnessInputError("SDD-SKILL-PRODUCER", "Producer identity is required for manual runs");
  if (stored.issues.length) throw new HarnessBlockedError("Run integrity validation failed", stored.issues);
  return mutateWithReconciliation(root, storyId, "skill submit", async (manifest) => {
    const report = await inspectSkillRun(root, storyId, runId, manifest);
    if (report.issues.length) throw new HarnessBlockedError("Skill output is invalid", report.issues);
    const { run, output, policy } = report as { run: RunRecord; output: AnyRecord; policy: SkillPolicy; issues: ValidationIssue[] };
    if (run.agent_id && run.status !== "VALID") throw new HarnessInputError("SDD-AGENT-RUN", "Agent-bound run must be VALID before submit");
    const producer: Actor = run.agent_id ? { type: "agent", identity: run.agent_id } : suppliedProducer!;
    const now = new Date().toISOString();
    const writes: ExtraWrite[] = [];
    if (output.status === "COMPLETED") {
      await applyCompletedOutput(root, manifest, output, policy, writes, now);
    }
    const closed = { ...run, status: output.status === "COMPLETED" ? "SUBMITTED" : output.status, submitted_at: now, producer: { actor_type: producer.type, identity: producer.identity }, output_sha256: await sha256File(resolveConcreteRepoPath(root, run.output_path)) };
    writes.push({ path: `${runPrefix(root, storyId, runId)}/run.json`, content: jsonFile(closed) });
    const ok = output.status === "COMPLETED";
    return {
      event_type: run.agent_id ? "agent.submitted" : `skill.${output.status.toLowerCase()}`, event_data: { run_id: runId, skill: run.skill, status: output.status, ...(run.agent_id ? { agent_id: run.agent_id } : {}) }, actor: producer, extra_writes: writes,
      result: { ok, command: "skill submit", story_id: storyId, changed: true, blockers: ok ? [] : [...output.errors.map((item: AnyRecord) => ({ code: item.code, instance_path: item.path ?? "/", message: item.message })), ...output.doc_conflicts.filter((item: AnyRecord) => item.blocking).map((item: AnyRecord) => ({ code: "DOC-CONFLICT", instance_path: "/docs", message: item.summary }))], next_actions: ok ? ["review produced artifacts", "run sdd status"] : ["resolve skill blockers and prepare a new run"], data: { run_id: runId, skill: run.skill, status: output.status } },
    };
  });
}

export async function inspectSkillRun(root: string, storyId: string, runId: string, suppliedManifest?: AnyRecord): Promise<{ run?: RunRecord; output?: AnyRecord; policy?: SkillPolicy; issues: ValidationIssue[] }> {
  if (!/^[0-9a-f]{8}-[0-9a-f-]{27}$/i.test(runId)) throw new HarnessInputError("SDD-SKILL-RUN", `Invalid run ID: ${runId}`);
  const issues: ValidationIssue[] = [];
  const prefix = runPrefix(root, storyId, runId);
  const stored = await validateStoredRun(root, storyId, runId, prefix); const run = stored.run as RunRecord; issues.push(...stored.issues);
  if (run.run_id !== runId || run.story_id !== storyId || !["PREPARED", "RUNNING", "VALID"].includes(run.status)) issues.push(issue("SDD-SKILL-RUN", "/run", "Run is invalid or already closed"));
  if (run.input_path !== `${prefix}/input.json` || run.output_path !== `${prefix}/output.json`) issues.push(issue("SDD-SKILL-RUN", "/run", "Run paths are not canonical"));
  const catalog = await loadSkillCatalog(root);
  const policy = policyFor(catalog, run.skill);
  if (run.agent_id) {
    try {
      const current = await loadAgentCatalog(root); const agentPolicy = current.catalog.agents[run.agent_id];
      if (!agentPolicy || current.sha256 !== run.agent_catalog_sha256) issues.push(issue("SDD-AGENT-CATALOG-STALE", "/run/agent_catalog_sha256", "Agent catalog changed after prepare"));
      else {
        const definition = await loadAgentDefinition(root, run.agent_id, agentPolicy);
        if (definition.sha256 !== run.agent_definition_sha256) issues.push(issue("SDD-AGENT-DEFINITION-STALE", "/run/agent_definition_sha256", "Agent definition changed after prepare"));
      }
      if (sha256Text(canonicalJson(run.permission_profile)) !== run.permission_profile_sha256) issues.push(issue("SDD-AGENT-PERMISSION-HASH", "/run/permission_profile_sha256", "Permission profile hash is invalid"));
      const permissionValidator = await createCatalogValidator(root, "agent/permission-profile@1.0.0");
      if (!permissionValidator(run.permission_profile)) issues.push(...contractIssues(permissionValidator.errors, "/run/permission_profile"));
    } catch (error) { issues.push(issue("SDD-AGENT-BINDING", "/run", error instanceof Error ? error.message : String(error))); }
  }
  const inputContent = await readText(resolveConcreteRepoPath(root, run.input_path));
  const input = JSON.parse(inputContent) as AnyRecord;
  if (sha256Text(inputContent) !== run.input_sha256) issues.push(issue("SDD-SKILL-INPUT-HASH", "/input", "Prepared input hash is stale"));
  const manifest = suppliedManifest ?? await loadStoryManifest(root, storyId);
  const events = stored.events;
  if (events.some((event) => ["skill.completed", "skill.blocked", "skill.failed", "agent.submitted"].includes(event.event_type) && event.data?.run_id === runId)) issues.push(issue("SDD-SKILL-RUN", "/run", "Run has already been submitted"));
  if (input.state_sha256 !== skillStateHash(manifest)) issues.push(issue("SDD-SKILL-STALE", "/input/state_sha256", "Story state changed after prepare"));
  if (input.correlation_id !== manifest.correlation_id || input.run_id !== runId || input.skill !== run.skill) issues.push(issue("SDD-SKILL-CONTEXT", "/input", "Input context does not match the run"));
  const inputValidator = await createCatalogValidator(root, policy.input_schema);
  if (!inputValidator(input)) issues.push(...contractIssues(inputValidator.errors, "/input"));
  for (const doc of input.docs_context?.applicable ?? []) {
    try { if (await sha256File(resolveConcreteRepoPath(root, doc.path)) !== doc.sha256) issues.push(issue("SDD-SKILL-DOC-STALE", "/input/docs_context", `Document changed: ${doc.path}`)); }
    catch { issues.push(issue("SDD-SKILL-DOC-MISSING", "/input/docs_context", `Document missing: ${doc.path}`)); }
  }
  let output: AnyRecord;
  try {
    const outputFile = resolveConcreteRepoPath(root, run.output_path);
    if ((await lstat(outputFile)).isSymbolicLink()) issues.push(issue("SDD-SKILL-SYMLINK", "/output", "Symlink output is forbidden"));
    output = JSON.parse(await readText(outputFile)) as AnyRecord;
  }
  catch (error) { issues.push(issue("SDD-SKILL-OUTPUT", "/output", error instanceof Error ? error.message : String(error))); return { run, policy, issues }; }
  const outputValidator = await createCatalogValidator(root, policy.output_schema);
  if (!outputValidator(output)) issues.push(...contractIssues(outputValidator.errors, "/output"));
  if (output.run_id !== runId || output.input_sha256 !== run.input_sha256 || output.correlation_id !== manifest.correlation_id || output.skill !== run.skill) issues.push(issue("SDD-SKILL-CONTEXT", "/output", "Output is not bound to the prepared input"));
  if (output.status === "COMPLETED" && (output.errors?.length || output.doc_conflicts?.some((item: AnyRecord) => item.blocking))) issues.push(issue("SDD-SKILL-STATUS", "/output/status", "COMPLETED cannot contain errors or blocking conflicts"));
  if (output.status === "BLOCKED" && !output.errors?.length && !output.doc_conflicts?.some((item: AnyRecord) => item.blocking)) issues.push(issue("SDD-SKILL-STATUS", "/output/status", "BLOCKED requires a cause"));
  if (output.status === "FAILED" && !output.errors?.length) issues.push(issue("SDD-SKILL-STATUS", "/output/errors", "FAILED requires errors"));
  const inputDocs = new Map((input.docs_context?.applicable ?? []).map((item: AnyRecord) => [item.path, item.sha256]));
  const consulted = new Map((output.docs_consulted ?? []).map((item: AnyRecord) => [item.path, item.sha256]));
  for (const [docPath, hash] of inputDocs) if (consulted.get(docPath) !== hash) issues.push(issue("SDD-SKILL-DOC", "/output/docs_consulted", `Required document was not consulted: ${docPath}`));
  for (const doc of output.docs_consulted ?? []) {
    if (inputDocs.get(doc.path) !== doc.sha256) issues.push(issue("SDD-SKILL-DOC", "/output/docs_consulted", `Unprepared or stale document: ${doc.path}`));
  }
  const candidateTypes = new Set<string>();
  const candidateTargets = new Set<string>();
  for (const [index, candidate] of (output.artifacts ?? []).entries()) {
    candidateTypes.add(candidate.type);
    if (candidateTargets.has(candidate.target_path)) issues.push(issue("SDD-SKILL-ARTIFACT", `/output/artifacts/${index}/target_path`, "Duplicate candidate target"));
    candidateTargets.add(candidate.target_path);
    if (!policy.produces.includes(candidate.type)) issues.push(issue("SDD-SKILL-ARTIFACT", `/output/artifacts/${index}/type`, `Skill cannot produce ${candidate.type}`));
    const expectedPrefix = `${prefix}/artifacts/`;
    if (!candidate.staged_path.startsWith(expectedPrefix) || !matchesAny(policy.targets.map((item) => item.replace("{story}", storyId)), candidate.target_path)) issues.push(issue("SDD-SKILL-PATH", `/output/artifacts/${index}`, "Staged or target path is not allowed"));
    try {
      const staged = resolveConcreteRepoPath(root, candidate.staged_path);
      if ((await lstat(staged)).isSymbolicLink()) issues.push(issue("SDD-SKILL-SYMLINK", `/output/artifacts/${index}/staged_path`, "Symlink candidates are forbidden"));
      const content = await readFile(staged, "utf8");
      if (sha256Text(content) !== candidate.sha256) issues.push(issue("SDD-SKILL-ARTIFACT-HASH", `/output/artifacts/${index}/sha256`, "Candidate hash is stale"));
      const contract = await validateArtifactContent(root, content, candidate.type, candidate.artifact_schema_version, storyId);
      issues.push(...contract.issues.map((item) => ({ ...item, instance_path: `/output/artifacts/${index}${item.instance_path}` })));
    } catch (error) { issues.push(issue("SDD-SKILL-ARTIFACT-MISSING", `/output/artifacts/${index}`, error instanceof Error ? error.message : String(error))); }
  }
  if (output.status === "COMPLETED" && policy.produces.some((type) => !candidateTypes.has(type))) issues.push(issue("SDD-SKILL-ARTIFACT", "/output/artifacts", "Completed output is missing a required artifact type"));
  if (run.skill === "task-planner") for (const task of output.result?.tasks ?? []) if (!candidateTargets.has(task.path)) issues.push(issue("SDD-SKILL-TASK", "/output/result/tasks", `Task has no staged artifact: ${task.path}`));
  if (run.skill === "plan-executor") issues.push(...await validateExecutorOutput(root, manifest, output));
  const known = knownIds(manifest, output);
  for (const [index, relation] of (output.traceability ?? []).entries()) if (!known.has(relation.from) || !known.has(relation.to)) issues.push(issue("SDD-SKILL-TRACE", `/output/traceability/${index}`, "Traceability relation references an unknown ID"));
  return { run, output, policy, issues };
}

async function applyCompletedOutput(root: string, manifest: AnyRecord, output: AnyRecord, policy: SkillPolicy, writes: ExtraWrite[], now: string): Promise<void> {
  for (const candidate of output.artifacts as AnyRecord[]) {
    const content = await readText(resolveConcreteRepoPath(root, candidate.staged_path));
    writes.push({ path: candidate.target_path, content });
    const existing = manifest.artifacts.find((item: AnyRecord) => item.path === candidate.target_path);
    if (existing) {
      if (existing.status !== "DRAFT") throw new HarnessInputError("WF-INVALID-TRANSITION", `Cannot replace ${existing.status} artifact: ${candidate.target_path}`);
      Object.assign(existing, { sha256: candidate.sha256, updated_at: now, invalidated_by: null });
    } else manifest.artifacts.push({ type: candidate.type, schema_version: candidate.artifact_schema_version, path: candidate.target_path, version: 1, sha256: candidate.sha256, status: "DRAFT", updated_at: now, approvals: [], invalidated_by: null });
  }
  if (output.skill === "task-planner") {
    for (const check of output.result.checks) {
      if (manifest.checks.some((item: AnyRecord) => item.id === check.id)) throw new HarnessInputError("SDD-CHECK-DUPLICATE", `Duplicate check: ${check.id}`);
      manifest.checks.push({ ...check, status: "PENDING", result: null }); addEntity(manifest, check.id, "TEST", null);
    }
    for (const task of output.result.tasks) {
      if (manifest.tasks.some((item: AnyRecord) => item.id === task.id)) throw new HarnessInputError("SDD-TASK-DUPLICATE", `Duplicate task: ${task.id}`);
      manifest.tasks.push({ ...task, status: "PENDING", attempts: [] }); addEntity(manifest, task.id, "TASK", task.path);
    }
  }
  if (output.skill === "plan-executor") applyTaskResults(manifest, output.result.task_results, now);
  if (output.skill === "reviewer") {
    for (const finding of output.result.findings) {
      if (manifest.findings.some((item: AnyRecord) => item.id === finding.id)) throw new HarnessInputError("SDD-FINDING-DUPLICATE", `Duplicate finding: ${finding.id}`);
      manifest.findings.push(finding); addEntity(manifest, finding.id, "FIND", output.artifacts.find((item: AnyRecord) => item.type === "review")?.target_path ?? null);
    }
  }
  for (const id of producedIds(output)) addEntity(manifest, id, id.split("-")[0]!, output.artifacts[0]?.target_path ?? null);
  for (const relation of output.traceability as AnyRecord[]) if (!manifest.traceability.relations.some((item: AnyRecord) => canonicalJson(item) === canonicalJson(relation))) manifest.traceability.relations.push(relation);
  if (policy.stage !== manifest.workflow.stage) throw new HarnessInputError("WF-INVALID-TRANSITION", "Stage changed during skill submission");
}

function applyTaskResults(manifest: AnyRecord, results: AnyRecord[], now: string): void {
  for (const result of results) {
    const task = manifest.tasks.find((item: AnyRecord) => item.id === result.task_id);
    if (!task || task.status !== "RUNNING") throw new HarnessInputError("WF-INVALID-TRANSITION", `Task must be RUNNING: ${result.task_id}`);
    if (["FAILED", "BLOCKED"].includes(result.status) && (!result.reason || !result.evidence.length)) throw new HarnessInputError("SDD-ATTEMPT-EVIDENCE", `${result.status} requires reason and evidence`);
    if (result.status === "COMPLETED" && task.required_checks.some((id: string) => !manifest.checks.some((check: AnyRecord) => check.id === id && check.status === "COMPLETED"))) throw new HarnessInputError("WF-CHECK-FAILED", `Required checks have not passed: ${task.id}`);
    const attempt = task.attempts.at(-1);
    if (!attempt || attempt.status !== "RUNNING") throw new HarnessInputError("SDD-ATTEMPT-MISSING", `Task has no running attempt: ${task.id}`);
    Object.assign(attempt, { status: result.status, completed_at: now, error: result.reason, evidence: result.evidence });
    task.status = result.status;
  }
}

async function validateExecutorOutput(root: string, manifest: AnyRecord, output: AnyRecord): Promise<ValidationIssue[]> {
  const issues = await validateScope(root, manifest);
  const requested = new Set(output.result?.task_results?.map((item: AnyRecord) => item.task_id) ?? []);
  for (const id of requested) if (!manifest.tasks.some((item: AnyRecord) => item.id === id && item.status === "RUNNING")) issues.push(issue("WF-INVALID-TRANSITION", "/output/result/task_results", `Task is not RUNNING: ${id}`));
  return issues;
}

function assertSkillReady(manifest: AnyRecord, skill: string, policy: SkillPolicy): void {
  if (manifest.workflow.stage !== policy.stage || manifest.workflow.status !== "ACTIVE") throw new HarnessInputError("WF-INVALID-TRANSITION", `${skill} requires active ${policy.stage} stage`);
  for (const required of policy.consumes) if (!manifest.artifacts.some((item: AnyRecord) => item.type === required.type && item.status === required.status)) throw new HarnessInputError("WF-MISSING-ARTIFACT", `${skill} requires ${required.status} ${required.type}`);
  if (skill === "plan-executor" && !manifest.execution.baseline) throw new HarnessInputError("SDD-BASELINE-HASH", "plan-executor requires an execution baseline");
}

async function loadSkillCatalog(root: string): Promise<SkillCatalog> {
  const config = await loadConfig(root);
  const catalog = await readYaml<SkillCatalog>(resolveConcreteRepoPath(root, config.skills.catalog));
  if (catalog.catalog_version !== "1.0.0" || catalog.protocol_version !== "2.0.0") throw new HarnessInputError("SDD-SKILL-CATALOG", "Unsupported skill catalog");
  return catalog;
}
function policyFor(catalog: SkillCatalog, skill: string): SkillPolicy { const policy = catalog.skills[skill]; if (!policy) throw new HarnessInputError("SDD-SKILL", `Unknown skill: ${skill}`); return policy; }
export function runPrefix(root: string, storyId: string, runId: string): string { return path.relative(root, path.join(storyDirectory(root, storyId), ".harness", "skill-runs", runId)).replaceAll("\\", "/"); }
function skillStateHash(manifest: AnyRecord): string { return sha256Text(canonicalJson({ workflow: manifest.workflow, scope: manifest.scope, artifacts: manifest.artifacts, architecture: manifest.architecture, tasks: manifest.tasks, checks: manifest.checks, execution: manifest.execution })); }
function jsonFile(value: unknown): string { return `${JSON.stringify(value, null, 2)}\n`; }
function issue(code: string, instance_path: string, message: string): ValidationIssue { return { code, instance_path, message }; }
function matchesAny(patterns: string[], value: string): boolean { return patterns.some((pattern) => new RegExp(`^${pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&").replaceAll("*", "[^/]*")}$`).test(value)); }
async function parsePayload(root: string, payloadPath: string): Promise<unknown> { const document = parseDocument(await readText(resolveConcreteRepoPath(root, payloadPath)), { schema: "core", uniqueKeys: true }); if (document.errors.length) throw new HarnessInputError("SDD-CONTRACT-PARSE", document.errors[0]!.message); return document.toJS({ maxAliasCount: 0 }); }
function knownIds(manifest: AnyRecord, output: AnyRecord): Set<string> { return new Set([...manifest.traceability.entities.map((item: AnyRecord) => item.id), ...producedIds(output)]); }
function producedIds(output: AnyRecord): string[] { const values: string[] = []; const collect = (value: unknown): void => { if (typeof value === "string" && /^(AC|REQ|DEC|TASK|TEST|RESULT|FIND|ADR)-\d{3,}$|^ARCH-\d{2}$|^GAP-\d{3}$/.test(value)) values.push(value); else if (Array.isArray(value)) value.forEach(collect); else if (value && typeof value === "object") Object.values(value).forEach(collect); }; collect(output.result); return [...new Set(values)]; }
function addEntity(manifest: AnyRecord, id: string, type: string, artifactPath: string | null): void { if (!manifest.traceability.entities.some((item: AnyRecord) => item.id === id)) manifest.traceability.entities.push({ id, type, artifact_path: artifactPath }); }
