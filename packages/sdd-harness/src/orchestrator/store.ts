import { access, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";

import { loadConfig, loadWorkflow } from "../config.js";
import { HarnessBlockedError, HarnessInputError } from "../errors.js";
import { canonicalJson, sha256File, sha256Text } from "../hash.js";
import { appendLine, readText, readYaml, writeTextAtomic, writeYamlAtomic } from "../io.js";
import { validateManifestData } from "../manifest/validate.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { Actor, AnyRecord, CommandResult, JournalEvent } from "../types.js";
import { createJournalEvent } from "./journal.js";
import { withLock } from "./lock.js";
import { relativeRepoPath, storyDirectory, storyManifestPath } from "./paths.js";
import { assertMutationAllowed } from "../agents/lease.js";

export interface ExtraWrite { path: string; content: string; immutable?: boolean }
export interface MutationPlan {
  event_type: string;
  event_data: AnyRecord;
  actor: Actor;
  extra_writes?: ExtraWrite[];
  result: Omit<CommandResult, "journal_event_id">;
}

interface TransactionIntent {
  story_id: string;
  correlation_id: string;
  source_manifest_sha256: string;
  target_manifest: AnyRecord;
  event: JournalEvent;
  extra_writes: ExtraWrite[];
}

export async function loadStoryManifest(root: string, storyId: string): Promise<AnyRecord> {
  return readYaml<AnyRecord>(storyManifestPath(root, storyId));
}

export async function mutateStory(
  root: string,
  storyId: string,
  planner: (manifest: AnyRecord) => Promise<MutationPlan>,
): Promise<CommandResult> {
  await assertMutationAllowed(root, storyId);
  const internal = path.join(storyDirectory(root, storyId), ".harness");
  return withLock(path.join(internal, "state.lock"), async () => {
    await recoverTransaction(root, storyId);
    const manifest = await loadStoryManifest(root, storyId);
    const targetManifest = structuredClone(manifest);
    const plan = await planner(targetManifest);
    const event = createJournalEvent(manifest, plan.event_type, plan.actor, plan.event_data);
    plan.result.stage ??= targetManifest.workflow.stage;
    plan.result.status ??= targetManifest.workflow.status;
    targetManifest.journal.head_sequence = event.sequence;
    targetManifest.journal.head_hash = event.event_hash;
    const intent: TransactionIntent = {
      story_id: storyId,
      correlation_id: manifest.correlation_id,
      source_manifest_sha256: await sha256File(storyManifestPath(root, storyId)),
      target_manifest: targetManifest,
      event,
      extra_writes: plan.extra_writes ?? [],
    };
    await validateIntent(root, storyId, intent, manifest);
    await writeTextAtomic(path.join(internal, "transaction.json"), JSON.stringify(intent));
    await applyIntent(root, storyId, intent);
    await rm(path.join(internal, "transaction.json"), { force: true });
    return { ...plan.result, journal_event_id: event.event_id };
  });
}

export async function recoverTransaction(root: string, storyId: string): Promise<boolean> {
  const intentPath = path.join(storyDirectory(root, storyId), ".harness", "transaction.json");
  try {
    const intent = JSON.parse(await readFile(intentPath, "utf8")) as TransactionIntent;
    const current = await loadStoryManifest(root, storyId);
    await validateIntent(root, storyId, intent, current, true);
    await applyIntent(root, storyId, intent);
    await rm(intentPath, { force: true });
    return true;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return false;
    throw error;
  }
}

async function applyIntent(root: string, storyId: string, intent: TransactionIntent): Promise<void> {
  for (const item of intent.extra_writes) {
    const absolute = resolveConcreteRepoPath(root, item.path);
    await mkdir(path.dirname(absolute), { recursive: true });
    if (item.immutable) {
      try {
        const current = await readFile(absolute, "utf8");
        if (current !== item.content) throw new Error(`Immutable snapshot differs: ${item.path}`);
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code === "ENOENT") {
          await writeFile(absolute, item.content, { encoding: "utf8", flag: "wx" });
        } else throw error;
      }
    } else {
      await writeTextAtomic(absolute, item.content);
    }
  }
  const journalPath = resolveConcreteRepoPath(root, intent.target_manifest.journal.path);
  let journal = "";
  try { journal = await readFile(journalPath, "utf8"); } catch { /* created by init */ }
  if (!journal.split(/\r?\n/).some((line) => line.includes(intent.event.event_hash))) {
    await appendLine(journalPath, JSON.stringify(intent.event));
  }
  await writeYamlAtomic(storyManifestPath(root, storyId), intent.target_manifest);
}

async function validateIntent(root: string, storyId: string, intent: TransactionIntent, current: AnyRecord, recovering = false): Promise<void> {
  if (!intent || intent.story_id !== storyId || intent.correlation_id !== current.correlation_id || intent.target_manifest?.story?.id !== storyId || intent.target_manifest?.correlation_id !== current.correlation_id) {
    throw new HarnessInputError("SDD-TRANSACTION-CONTEXT", "Transaction intent context is invalid");
  }
  const expectedJournal = relativeRepoPath(root, path.join(storyDirectory(root, storyId), "journal.ndjson"));
  if (intent.target_manifest.journal?.path !== expectedJournal) throw new HarnessInputError("SDD-TRANSACTION-JOURNAL", "Transaction journal path is not canonical");
  if (intent.event.story_id !== storyId || intent.event.correlation_id !== current.correlation_id || intent.target_manifest.journal.head_hash !== intent.event.event_hash || intent.target_manifest.journal.head_sequence !== intent.event.sequence) {
    throw new HarnessInputError("SDD-TRANSACTION-EVENT", "Transaction event does not match target manifest");
  }
  const { event_hash: eventHash, ...unsigned } = intent.event;
  if (sha256Text(canonicalJson(unsigned)) !== eventHash) throw new HarnessInputError("SDD-TRANSACTION-EVENT", "Transaction event hash is invalid");
  const currentHash = await sha256File(storyManifestPath(root, storyId));
  const alreadyApplied = current.journal?.head_hash === eventHash;
  if (currentHash !== intent.source_manifest_sha256 && !(recovering && alreadyApplied)) throw new HarnessInputError("SDD-TRANSACTION-SOURCE", "Transaction source manifest hash is stale");
  if (!alreadyApplied && (intent.event.previous_event_hash !== current.journal?.head_hash || intent.event.sequence !== current.journal?.head_sequence + 1)) {
    throw new HarnessInputError("SDD-TRANSACTION-ORDER", "Transaction event does not follow current journal head");
  }
  const storyPrefix = storyId === "HU-000" ? `SPEC/examples/${storyId}-fixture/` : `SPEC/${storyId}/`;
  const allowedPrefixes = [`${storyPrefix}history/`, `${storyPrefix}.harness/`];
  const artifactPaths = new Set((intent.target_manifest.artifacts as AnyRecord[]).map((item) => item.path));
  for (const item of intent.extra_writes) {
    resolveConcreteRepoPath(root, item.path);
    if (!allowedPrefixes.some((prefix) => item.path.startsWith(prefix)) && !artifactPaths.has(item.path)) throw new HarnessInputError("SDD-TRANSACTION-PATH", `Transaction write is outside story-owned state: ${item.path}`);
    if (item.path.endsWith("/manifest.yaml") || item.path.endsWith("/journal.ndjson")) throw new HarnessInputError("SDD-TRANSACTION-PATH", `Reserved story path: ${item.path}`);
  }
  const overlay = new Map(intent.extra_writes.map((item) => [item.path, item.content]));
  let journal = "";
  try { journal = await readFile(resolveConcreteRepoPath(root, expectedJournal), "utf8"); } catch { /* init only */ }
  if (!journal.split(/\r?\n/).some((line) => line.includes(eventHash))) journal += `${JSON.stringify(intent.event)}\n`;
  overlay.set(expectedJournal, journal);
  const config = await loadConfig(root);
  const workflow = await loadWorkflow(root, config);
  const report = await validateManifestData(root, storyManifestPath(root, storyId), intent.target_manifest, config, workflow, overlay);
  if (!report.valid) throw new HarnessBlockedError("Staged mutation would create an invalid manifest", report.errors);
}

export async function hasPendingTransaction(root: string, storyId: string): Promise<boolean> {
  try {
    await access(path.join(storyDirectory(root, storyId), ".harness", "transaction.json"));
    return true;
  } catch { return false; }
}

export function repoWrite(root: string, absolutePath: string, content: string, immutable = false): ExtraWrite {
  return { path: relativeRepoPath(root, absolutePath), content, immutable };
}
