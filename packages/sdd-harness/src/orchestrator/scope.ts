import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

import { canonicalJson, sha256File, sha256Text } from "../hash.js";
import { readText } from "../io.js";
import { resolveConcreteRepoPath } from "../repo.js";
import type { AnyRecord, ValidationIssue } from "../types.js";

const execFileAsync = promisify(execFile);

interface BaselineFile { path: string; sha256: string }
interface Baseline { captured_at: string; files: BaselineFile[] }

export async function captureBaseline(root: string, storyId: string): Promise<{ baseline: Baseline; path: string; sha256: string; content: string }> {
  const files = await gitFiles(root);
  const ownPrefix = `SPEC/${storyId}/`;
  const entries: BaselineFile[] = [];
  for (const file of files.filter((item) => !item.startsWith(ownPrefix)).sort()) {
    try { entries.push({ path: file, sha256: await sha256File(resolveConcreteRepoPath(root, file)) }); } catch { /* deletion */ }
  }
  const baseline = { captured_at: new Date().toISOString(), files: entries };
  const content = `${JSON.stringify(baseline, null, 2)}\n`;
  return {
    baseline,
    path: `SPEC/${storyId}/.harness/execution-baseline.json`,
    sha256: sha256Text(content),
    content,
  };
}

export async function validateScope(root: string, manifest: AnyRecord, overlay: Map<string, string> = new Map()): Promise<ValidationIssue[]> {
  if (!manifest.execution.baseline) return [];
  const baselinePath = resolveConcreteRepoPath(root, manifest.execution.baseline.path);
  const content = overlay.get(manifest.execution.baseline.path) ?? await readText(baselinePath);
  if (sha256Text(content) !== manifest.execution.baseline.sha256) {
    return [{ code: "SDD-BASELINE-HASH", instance_path: "/execution/baseline", message: "Execution baseline hash is stale" }];
  }
  const baseline = JSON.parse(content) as Baseline;
  const before = new Map(baseline.files.map((file) => [file.path, file.sha256]));
  const currentFiles = await gitFiles(root);
  const ownPrefix = `SPEC/${manifest.story.id}/`;
  const current = new Map<string, string>();
  for (const file of currentFiles.filter((item) => !item.startsWith(ownPrefix))) {
    try { current.set(file, await sha256File(resolveConcreteRepoPath(root, file))); } catch { /* deletion */ }
  }
  const changed = new Set([...before.keys(), ...current.keys()].filter((file) => before.get(file) !== current.get(file)));
  return [...changed]
    .filter((file) => !(manifest.scope.write_paths as string[]).some((glob) => globMatches(glob, file)))
    .sort()
    .map((file) => ({ code: "WF-OUT-OF-SCOPE", instance_path: "/scope/write_paths", message: `Changed path is outside approved scope: ${file}` }));
}

async function gitFiles(root: string): Promise<string[]> {
  const { stdout } = await execFileAsync("git", ["ls-files", "--cached", "--others", "--exclude-standard"], { cwd: root, maxBuffer: 10 * 1024 * 1024 });
  return stdout.split(/\r?\n/).filter(Boolean).map((item) => item.replaceAll("\\", "/"));
}

function globMatches(glob: string, value: string): boolean {
  const escaped = glob.replace(/[.+^${}()|[\]\\]/g, "\\$&").replaceAll("**", "\u0000").replaceAll("*", "[^/]*").replaceAll("?", "[^/]").replaceAll("\u0000", ".*");
  return new RegExp(`^${escaped}$`).test(value);
}
