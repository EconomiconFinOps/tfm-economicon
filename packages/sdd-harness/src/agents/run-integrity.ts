import { lstat } from "node:fs/promises";

import { contractIssues, createCatalogValidator } from "../contracts/catalog.js";
import { HarnessInputError } from "../errors.js";
import { canonicalJson, sha256File, sha256Text } from "../hash.js";
import { readText } from "../io.js";
import { loadStoryManifest } from "../orchestrator/store.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { AnyRecord, ValidationIssue } from "../types.js";
import { readLease } from "./lease.js";

export interface ValidatedRun extends AnyRecord {
  schema_version: string; run_id: string; story_id: string; skill: string; status: string;
  input_path: string; input_sha256: string; output_path: string; created_at: string;
}

export async function validateStoredRun(root: string, storyId: string, runId: string, prefix: string, requirePermissionBinding = true): Promise<{ run: ValidatedRun; events: AnyRecord[]; issues: ValidationIssue[] }> {
  const issues: ValidationIssue[] = [];
  const runPath = resolveConcreteRepoPath(root, `${prefix}/run.json`);
  if ((await lstat(runPath)).isSymbolicLink()) throw new HarnessInputError("SDD-AGENT-RUN-SYMLINK", "Run record cannot be a symlink");
  const run = JSON.parse(await readText(runPath)) as ValidatedRun;
  const validator = await createCatalogValidator(root, "agent/run@2.0.0");
  if (!validator(run)) issues.push(...contractIssues(validator.errors, "/run"));
  const manifest = await loadStoryManifest(root, storyId);
  const events = (await readText(resolveConcreteRepoPath(root, manifest.journal.path))).split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line) as AnyRecord);
  if (run.run_id !== runId || run.story_id !== storyId) issues.push(issue("SDD-AGENT-RUN-INTEGRITY", "/run", "Run identity does not match its canonical path"));
  if (run.input_path !== `${prefix}/input.json` || run.output_path !== `${prefix}/output.json`) issues.push(issue("SDD-AGENT-RUN-INTEGRITY", "/run", "Run paths are not canonical"));
  const prepared = events.filter((event) => ["skill.prepared", "agent.prepared"].includes(event.event_type) && event.data?.run_id === runId);
  if (prepared.length !== 1) issues.push(issue("SDD-AGENT-RUN-INTEGRITY", "/journal", "Run must have exactly one preparation event"));
  else {
    const event = prepared[0]!; const isAgent = event.event_type === "agent.prepared";
    if ((run.schema_version === "2.0.0") !== isAgent) issues.push(issue("SDD-AGENT-RUN-INTEGRITY", "/run/schema_version", "Run kind contradicts its preparation event"));
    for (const key of ["skill", "input_sha256"] as const) if (event.data?.[key] !== run[key]) issues.push(issue("SDD-AGENT-RUN-INTEGRITY", `/run/${key}`, `${key} is not anchored to the preparation event`));
    if (isAgent) for (const key of ["agent_id", "agent_definition_sha256", "agent_catalog_sha256"] as const) if (event.data?.[key] !== run[key]) issues.push(issue("SDD-AGENT-RUN-INTEGRITY", `/run/${key}`, `${key} is not anchored to agent.prepared`));
  }
  if (run.schema_version === "2.0.0") {
    if (!run.permission_profile || typeof run.permission_profile_sha256 !== "string" || sha256Text(canonicalJson(run.permission_profile)) !== run.permission_profile_sha256) issues.push(issue("SDD-AGENT-PERMISSION-HASH", "/run/permission_profile_sha256", "Permission profile hash is invalid"));
    const bindings = events.filter((event) => event.event_type === "agent.permissions_bound" && event.data?.run_id === runId);
    if (requirePermissionBinding && bindings.length !== 1) issues.push(issue("SDD-AGENT-RUN-INTEGRITY", "/journal", "Agent run must have exactly one permission binding event"));
    if (bindings.length === 1) {
      const binding = bindings[0]!;
      for (const key of ["agent_id", "agent_definition_sha256", "agent_catalog_sha256", "permission_profile_sha256"] as const) if (binding.data?.[key] !== run[key]) issues.push(issue("SDD-AGENT-RUN-INTEGRITY", `/run/${key}`, `${key} is not anchored to agent.permissions_bound`));
      const started = events.find((event) => event.event_type === "agent.started" && event.data?.run_id === runId);
      if (started && Number(binding.sequence) >= Number(started.sequence)) issues.push(issue("SDD-AGENT-RUN-INTEGRITY", "/journal", "Permissions must be bound before agent execution starts"));
    }
  }
  if (run.status === "RUNNING") {
    const lease = await readLease(root, storyId);
    if (!lease || lease.run_id !== runId || lease.agent_id !== run.agent_id) issues.push(issue("SDD-AGENT-LEASE", "/run/status", "RUNNING agent run does not own the story lease"));
  }
  try { if (await sha256File(resolveConcreteRepoPath(root, run.input_path)) !== run.input_sha256) issues.push(issue("SDD-SKILL-INPUT-HASH", "/input", "Prepared input hash is stale")); }
  catch (error) { issues.push(issue("SDD-SKILL-INPUT-HASH", "/input", error instanceof Error ? error.message : String(error))); }
  return { run, events, issues };
}

function issue(code: string, instance_path: string, message: string): ValidationIssue { return { code, instance_path, message }; }
