import { loadConfig, loadWorkflow } from "../config.js";
import { validateManifest } from "../manifest/validate.js";
import type { AnyRecord, CommandResult } from "../types.js";
import { evaluateNext } from "./gates.js";
import { reconcileManifest } from "./reconcile.js";
import { hasPendingTransaction, loadStoryManifest } from "./store.js";
import { storyManifestPath } from "./paths.js";

export async function storyStatus(root: string, storyId: string): Promise<CommandResult> {
  const manifest = await loadStoryManifest(root, storyId);
  const report = await validateManifest(root, storyManifestPath(root, storyId));
  const config = await loadConfig(root);
  const workflow = await loadWorkflow(root, config);
  const blockers = [...report.errors];
  if (manifest.workflow.status === "BLOCKED") blockers.push({ code: "WF-HUMAN-DECISION", instance_path: "/workflow/status", message: "Story is BLOCKED and requires a recorded human resolution" });
  if (await hasPendingTransaction(root, storyId)) blockers.push({ code: "SDD-RECOVERY-REQUIRED", instance_path: "/", message: "A pending transaction requires a mutating command to recover" });
  const reconciliation = await reconcileManifest(root, structuredClone(manifest) as AnyRecord, workflow);
  if (reconciliation.changed) blockers.push({ code: "SDD-RECONCILIATION-REQUIRED", instance_path: "/", message: `Pending reconciliation: ${reconciliation.causes.join(", ")}` });
  const evaluation = await evaluateNext(root, manifest, workflow);
  const allBlockers = uniqueIssues([...blockers, ...evaluation.blockers]);
  return { ok: allBlockers.length === 0, command: "status", story_id: storyId, changed: false, stage: manifest.workflow.stage, status: manifest.workflow.status, transition: evaluation.transition?.id, blockers: allBlockers, next_actions: allBlockers.length ? ["resolve blockers before transition"] : [`run next for ${evaluation.transition?.id}`] };
}

function uniqueIssues(issues: CommandResult["blockers"]): CommandResult["blockers"] {
  const seen = new Set<string>();
  return issues.filter((issue) => { const key = `${issue.code}|${issue.instance_path}|${issue.message}`; if (seen.has(key)) return false; seen.add(key); return true; });
}
