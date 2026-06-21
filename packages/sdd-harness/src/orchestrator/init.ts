import { randomUUID } from "node:crypto";
import { mkdir, readdir, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { stringify } from "yaml";

import { renderArtifactTemplate } from "../contracts/artifact.js";
import { loadConfig, loadWorkflow } from "../config.js";
import { canonicalJson, sha256Text } from "../hash.js";
import { HarnessBlockedError, HarnessInputError } from "../errors.js";
import { readText } from "../io.js";
import { validateManifestData } from "../manifest/validate.js";
import { assertRepoPath, resolveConcreteRepoPath } from "../repo.js";
import type { AnyRecord, CommandResult } from "../types.js";
import { withLock } from "./lock.js";

interface InitOptions {
  title: string;
  changeType: string;
  components: string[];
  affectedData: string[];
  affectedFlows: string[];
  readPaths: string[];
  writePaths: string[];
  targetGaps: string[];
}

export async function initializeStory(root: string, options: InitOptions): Promise<CommandResult> {
  if (!options.title.trim()) throw new HarnessInputError("SDD-ARGUMENT", "--title cannot be empty");
  if (!new Set(["feature", "remediation", "harness-docs"]).has(options.changeType)) {
    throw new HarnessInputError("SDD-CHANGE-TYPE", `Unsupported change type: ${options.changeType}`);
  }
  if (options.changeType === "remediation" && options.targetGaps.length === 0) {
    throw new HarnessInputError("SDD-REMEDIATION-GAPS", "remediation requires at least one --target-gap");
  }
  for (const declaredPath of [...options.readPaths, ...options.writePaths]) assertRepoPath(declaredPath);
  return withLock(path.join(root, ".sdd", "init.lock"), async () => {
    const storyId = await nextStoryId(root);
    const finalDir = path.join(root, "SPEC", storyId);
    const temporary = path.join(root, "SPEC", `.${storyId}.${process.pid}.${Date.now()}.tmp`);
    const now = new Date().toISOString();
    const correlationId = randomUUID();
    const userStoryPath = `SPEC/${storyId}/user-story.md`;
    const journalPath = `SPEC/${storyId}/journal.ndjson`;
    const template = await readText(resolveConcreteRepoPath(root, ".sdd/templates/user-story.md"));
    const userStory = renderArtifactTemplate(template, { STORY_ID: storyId, TITLE: options.title.trim() });
    const unsigned = {
      event_id: randomUUID(), event_type: "story.initialized", sequence: 1, previous_event_hash: null,
      occurred_at: now, actor: { type: "system", identity: "sdd-cli" }, story_id: storyId,
      correlation_id: correlationId, data: { schema_version: "2.0.0" },
    };
    const eventHash = sha256Text(canonicalJson(unsigned));
    const event = { ...unsigned, event_hash: eventHash };
    const manifest: AnyRecord = {
      schema_version: "2.0.0", correlation_id: correlationId,
      story: { id: storyId, title: options.title.trim(), slug: slugify(options.title), change_type: options.changeType, is_fixture: false, runtime_changes: false },
      workflow: { stage: "INTAKE", status: "ACTIVE", updated_at: now },
      scope: { components: options.components, affected_data: options.affectedData, affected_flows: options.affectedFlows, read_paths: options.readPaths, write_paths: options.writePaths },
      artifacts: [{ type: "user-story", schema_version: "1.0.0", path: userStoryPath, version: 1, sha256: sha256Text(userStory), status: "DRAFT", updated_at: now, approvals: [], invalidated_by: null }],
      architecture: { invariants: [], gaps: options.targetGaps, adrs: [] },
      tasks: [], checks: [], gate_evidence: [], findings: [], execution: { baseline: null },
      traceability: { entities: [{ id: storyId, type: "HU", artifact_path: userStoryPath }], relations: [] },
      journal: { path: journalPath, head_sequence: 1, head_hash: eventHash },
    };
    try {
      const config = await loadConfig(root);
      const workflow = await loadWorkflow(root, config);
      const overlay = new Map([[userStoryPath, userStory], [journalPath, `${JSON.stringify(event)}\n`]]);
      const report = await validateManifestData(root, path.join(finalDir, "manifest.yaml"), manifest, config, workflow, overlay);
      if (!report.valid) throw new HarnessBlockedError("Initial manifest is invalid", report.errors);
      await mkdir(path.join(temporary, ".harness"), { recursive: true });
      await writeFile(path.join(temporary, "user-story.md"), userStory, { encoding: "utf8", flag: "wx" });
      await writeFile(path.join(temporary, "journal.ndjson"), `${JSON.stringify(event)}\n`, { encoding: "utf8", flag: "wx" });
      await writeFile(path.join(temporary, "manifest.yaml"), stringify(manifest, { lineWidth: 0 }), { encoding: "utf8", flag: "wx" });
      await rename(temporary, finalDir);
    } catch (error) {
      await rm(temporary, { recursive: true, force: true });
      throw error;
    }
    return { ok: true, command: "init", story_id: storyId, changed: true, stage: "INTAKE", status: "ACTIVE", blockers: [], next_actions: [`approve user-story for ${storyId}`], journal_event_id: event.event_id };
  });
}

async function nextStoryId(root: string): Promise<string> {
  await mkdir(path.join(root, "SPEC"), { recursive: true });
  const entries = await readdir(path.join(root, "SPEC"), { withFileTypes: true });
  const values = entries.filter((entry) => entry.isDirectory()).map((entry) => /^HU-(\d+)$/.exec(entry.name)?.[1]).filter((value): value is string => Boolean(value)).map(Number);
  return `HU-${String(Math.max(0, ...values) + 1).padStart(3, "0")}`;
}

function slugify(value: string): string {
  const slug = value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  if (!slug) throw new HarnessInputError("SDD-SLUG", "Title cannot produce a valid slug");
  return slug;
}
